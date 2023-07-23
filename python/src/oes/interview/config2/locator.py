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

    def set(self, context: Context, value: object):
        """Set the value at this locator."""
        raise TypeError("Cannot assign a literal")


@frozen
class Variable(Locator):
    """A top-level variable."""

    name: str

    def evaluate(self, context: Context) -> object:
        """Return the value of this locator."""
        return context[self.name]

    def set(self, context: Context, value: object):
        """Set the value at this locator."""
        context[self.name] = value


@frozen
class Access:
    """A property access, like ``a.b`` or ``a["b"]``."""

    target: Locator
    name: Locator

    def evaluate(self, context: Context) -> object:
        """Return the value of this locator."""

        if isinstance(self.name, Literal):
            target_val = self.target.evaluate(context)
            if hasattr(target_val, "__getitem__"):
                return target_val[self.name.value]
            else:
                raise TypeError(f"Not a list/dict: {target_val}")
        else:
            return self.evaluate_name(context).evaluate(context)

    def evaluate_name(self, context: Context) -> Access:
        """Return a :class:`Access` with the ``name`` evaluated to a literal."""
        name_val = self.name.evaluate(context)
        if isinstance(name_val, (str, int)):
            return Access(self.target, Literal(name_val))
        else:
            raise TypeError(f"Invalid index/property: {name_val}")

    def set(self, context: Context, value: object):
        """Set the value at this locator."""
        name_val = self.name.evaluate(context)
        target_val = self.target.evaluate(context)
        if hasattr(target_val, "__setitem__"):
            target_val[name_val] = value
        else:
            raise TypeError(f"Not a list/dict: {target_val}")


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

property_access = "." + name_literal("key")
index_access = "[" + (locator | literal)("key") + "]"

locator << variable + pp.Group(property_access("property") | index_access("index"))[...]


@locator.set_parse_action
def _parse_locator(res: pp.ParseResults) -> Locator:
    return _parse_locator_recursive(res[:-1], res[-1])


def _parse_locator_recursive(
    left: list[Union[Locator, pp.ParseResults]], right: Union[Locator, pp.ParseResults]
) -> Locator:
    if isinstance(right, pp.ParseResults):
        target = _parse_locator_recursive(left[:-1], left[-1])
        return Access(target, right["key"])
    else:
        return right


def parse_locator(value: str) -> Locator:
    """Parse a :class:`Locator` from a string."""
    try:
        return locator.parse_string(value, parse_all=True)[0]
    except pp.ParseException as e:
        raise InvalidLocatorError(f"Invalid locator: {e}") from e
