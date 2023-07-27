"""Variable location."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union

import pyparsing as pp
from attrs import frozen
from oes.template import Evaluable

# Variable location
var_location = pp.Forward()

# Const number
number = pp.Group(pp.Regex(r"((?!0)[0-9]+|0)"))("number")
number.set_parse_action(lambda r: Const(int(r["number"][0])))

# Variable name
var_name = pp.Word(pp.srange("[a-zA-Z]"), pp.srange("[a-zA-Z0-9_]"))

# Top level name
name = pp.Group(var_name.copy())("name")
name.set_parse_action(lambda r: Name(r["name"][0]))

# Index access
index_access = pp.Group("[" + (number | var_location)("key") + "]")("index_access")

# Attribute access
attribute_access = pp.Group("." + var_name("attribute"))("attribute_access")


# set variable expression
var_location << (name + (attribute_access | index_access)[...])


# Types

ConstTypes = (str, int)
ConstVal = Union[str, int]


class Location(Evaluable, ABC):
    @abstractmethod
    def set(self, value: Any, context: dict[str, Any]):
        """Set the value at this location."""
        ...

    @classmethod
    def parse(cls, expr: str) -> Location:
        return var_location.parse_string(expr, True)[0]

    @classmethod
    def _parse(cls, expr: object) -> Location:
        if isinstance(expr, str):
            return cls.parse(expr)
        elif isinstance(expr, Location):
            return expr
        else:
            raise TypeError(f"Cannot parse variable location: {expr}")


@frozen
class Const(Location):
    """A constant value."""

    value: ConstVal

    def __str__(self) -> str:
        return str(self.value)

    def evaluate(self, **context: object) -> object:
        return self.value

    def set(self, value: Any, context: dict[str, Any]):
        raise TypeError("Cannot assign a constant")


@frozen
class Name(Location):
    """A top level variable name."""

    name: str

    def __str__(self) -> str:
        return str(self.name)

    def evaluate(self, **context: Any) -> Any:
        try:
            return context[self.name]
        except LookupError:
            raise UndefinedError(self)

    def set(self, value: Any, context: dict[str, Any]):
        context[self.name] = value


def _get_index(obj: object, index: Any) -> object:
    if not isinstance(obj, (dict, list)):
        raise TypeError(f"Not a dict/list: {obj}")

    return obj[index]


def _set_index(obj: object, index: Any, value: object):
    if not isinstance(obj, (dict, list)):
        raise TypeError(f"Not a dict/list: {obj}")

    # TODO: handle list append
    obj[index] = value


@frozen
class IndexAccess(Location):
    """An index access, e.g. ``a[x]``."""

    target: Location
    """The index target."""

    index: Location
    """The index."""

    def __str__(self) -> str:
        return f"{self.target}[{self.index}]"

    def evaluate(self, **context: Any) -> Any:
        index = self.index.evaluate(**context)

        if not isinstance(index, ConstTypes):
            raise TypeError(f"Invalid index type: {index}")

        target = self.target.evaluate(**context)
        try:
            return _get_index(target, index)
        except LookupError:
            raise UndefinedError(IndexAccess(self.target, Const(index)))

    def set(self, value: Any, context: dict[str, Any]):
        index = self.index.evaluate(**context)

        if not isinstance(index, ConstTypes):
            raise TypeError(f"Invalid index type: {index}")

        target = self.target.evaluate(**context)
        _set_index(target, index, value)


@frozen
class AttributeAccess(Location):
    """Attribute access, e.g. ``a.b``.

    Note:
        This is implemented internally as ``a["b"]``.
    """

    target: Location
    """The target object."""

    attribute: str
    """The attribute name."""

    def __str__(self) -> str:
        return f"{self.target}.{self.attribute}"

    def evaluate(self, **context: Any) -> Any:
        target = self.target.evaluate(**context)

        if not isinstance(target, dict):
            raise TypeError(f"Not a dict: {target}")

        try:
            return target[self.attribute]
        except KeyError:
            raise UndefinedError(self)

    def set(self, value: Any, context: dict[str, Any]):
        target = self.target.evaluate(**context)

        if not isinstance(target, dict):
            raise TypeError(f"Not a dict: {target}")

        target[self.attribute] = value


def _parse_element_type(
    left: Location, right_el: Union[pp.ParseResults, Location]
) -> Location:
    if isinstance(right_el, Location):
        return right_el
    elif right_el.get_name() == "index_access":
        return IndexAccess(left, right_el["key"][0])
    elif right_el.get_name() == "attribute_access":
        return AttributeAccess(left, right_el["attribute"])
    else:
        raise TypeError(right_el)


def _parse_loc_recursive(results: pp.ParseResults) -> Location:
    left_els = results[:-1]
    right_el = results[-1]

    if len(left_els) > 0:
        left = _parse_loc_recursive(left_els)
        return _parse_element_type(left, right_el)
    else:
        return right_el


var_location.set_parse_action(_parse_loc_recursive)


class UndefinedError(LookupError):
    """Exception raised when an undefined location is accessed."""

    location: Location

    def __init__(self, location: Location):
        self.location = location

    def __repr__(self) -> str:
        return f"UndefinedError({self.location})"


def evaluate_indexes(loc: Location, context: dict[str, Any]) -> Location:
    """Return the :class:`Location` with all indexes replaced with consts."""
    if isinstance(loc, IndexAccess):
        index = loc.index.evaluate(**context)

        if not isinstance(index, ConstTypes):
            raise TypeError(f"Invalid index type: {index}")

        return IndexAccess(
            evaluate_indexes(loc.target, context),
            Const(index),
        )
    elif isinstance(loc, AttributeAccess):
        return AttributeAccess(evaluate_indexes(loc.target, context), loc.attribute)
    else:
        return loc
