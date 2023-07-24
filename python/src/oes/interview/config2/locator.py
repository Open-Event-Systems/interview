"""Variable locator."""
from __future__ import annotations

import re
from typing import Union

import pyparsing as pp
from attrs import frozen
from oes.interview.config2.types import Context, Locator

# Types


class InvalidLocatorError(ValueError):
    """Raised when a locator cannot be parsed."""

    pass


@frozen
class Literal(Locator):
    """A literal value."""

    value: Union[str, int]

    def evaluate(self, context: Context) -> object:
        """Return the value of this locator."""
        return self.value

    def set(self, value: object, context: Context):
        """Set the value at this locator."""
        raise TypeError("Cannot assign a literal")

    def compare(self, other: Locator, context: Context) -> bool:
        """Whether two locators are equal."""
        return isinstance(other, Literal) and other.value == self.value


@frozen
class Variable(Locator):
    """A top-level variable."""

    name: str

    def evaluate(self, context: Context) -> object:
        """Return the value of this locator."""
        return context[self.name]

    def set(self, value: object, context: Context):
        """Set the value at this locator."""
        context[self.name] = value

    def compare(self, other: Locator, context: Context) -> bool:
        """Whether two locators are equal."""
        return isinstance(other, Variable) and other.name == self.name


@frozen
class Index(Locator):
    """An index/property access, like ``a.b`` or ``a["b"]``."""

    target: Locator
    index: Union[str, int]

    def evaluate(self, context: Context) -> object:
        """Return the value of this locator."""
        target_val = self.target.evaluate(context)
        if hasattr(target_val, "__getitem__"):
            return target_val[self.index]
        else:
            raise TypeError(f"Not a list/dict: {target_val}")

    def set(self, value: object, context: Context):
        """Set the value at this locator."""
        target_val = self.target.evaluate(context)
        if hasattr(target_val, "__setitem__"):
            target_val[self.index] = value
        else:
            raise TypeError(f"Not a list/dict: {target_val}")

    def compare(self, other: Locator, context: Context) -> bool:
        """Whether two locators are equal."""
        if isinstance(other, ParametrizedIndex):
            return self.compare(other.evaluate_index(context), context)
        else:
            return (
                isinstance(other, Index)
                and other.index == self.index
                and self.target.compare(other.target, context)
            )


@frozen
class ParametrizedIndex(Locator):
    """An index/property access with a variable, like ``a[n]``."""

    target: Locator
    index: Locator

    def evaluate_index(self, context: Context) -> Index:
        """Evaluate the ``index``, returning a :class:`Index`."""
        index_val = self.index.evaluate(context)
        if isinstance(index_val, (str, int)):
            return Index(self.target, index_val)
        else:
            raise TypeError(f"Not a valid index: {index_val}")

    def evaluate(self, context: Context) -> object:
        """Return the value of this locator."""
        return self.evaluate_index(context).evaluate(context)

    def set(self, value: object, context: Context):
        """Set the value at this locator."""
        return self.evaluate_index(context).set(value, context)

    def compare(self, other: Locator, context: Context) -> bool:
        """Whether two locators are equal."""
        return self.evaluate_index(context).compare(other, context)


# numbers
zero = pp.Literal("0")
non_zero_number = pp.Word("123456789", pp.nums)
number = zero | non_zero_number


@number.set_parse_action
def _parse_number(res: pp.ParseResults) -> Literal:
    return Literal(int(res[0]))


# A string literal
string_literal = pp.QuotedString(
    quote_char='"',
    esc_char="\\",
)


@string_literal.set_parse_action
def _parse_string_literal(res: pp.ParseResults) -> Literal:
    return Literal(res[0])


# A literal expression
literal = string_literal | number

# An identifier
name = pp.Regex(r"(?![0-9_])[a-z0-9_]+(?<!-)", re.I)

# A top-level variable
variable = name.copy()


@variable.set_parse_action
def _parse_variable(res: pp.ParseResults) -> Variable:
    return Variable(res[0])


name_literal = name.copy()


@name_literal.set_parse_action
def _parse_name_literal(res: pp.ParseResults) -> Literal:
    return Literal(res[0])


locator = pp.Forward()

property_access = "." + name_literal("index")
index_access = "[" + literal("index") + "]"
param_index_access = "[" + locator("index_param") + "]"

locator << variable + pp.Group(property_access | param_index_access | index_access)[...]


@locator.set_parse_action
def _parse_locator(res: pp.ParseResults) -> Locator:
    return _parse_locator_recursive(res[:-1], res[-1])


def _parse_locator_recursive(
    left: list[Union[Locator, pp.ParseResults]], right: Union[Locator, pp.ParseResults]
) -> Locator:
    if isinstance(right, pp.ParseResults):
        target = _parse_locator_recursive(left[:-1], left[-1])
        if "index_param" in right:
            return ParametrizedIndex(target, right["index_param"])
        else:
            return Index(target, right["index"].value)
    else:
        return right


def parse_locator(value: str) -> Locator:
    """Parse a :class:`Locator` from a string."""
    try:
        return locator.parse_string(value, parse_all=True)[0]
    except pp.ParseException as e:
        raise InvalidLocatorError(f"Invalid locator: {e}") from e
