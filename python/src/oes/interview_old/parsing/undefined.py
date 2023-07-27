"""Custom Jinja2 Undefined module"""
from typing import Union

import jinja2
from jinja2.sandbox import ImmutableSandboxedEnvironment
from oes.interview_old.parsing.location import (
    AttributeAccess,
    Const,
    IndexAccess,
    Location,
    Name,
    UndefinedError,
)


class Proxy:
    """Dict/list proxy that keeps track of its path."""

    expression: Location
    target: Union[dict, list]

    def __init__(self, expression: Location, target: Union[dict, list]):
        self.expression = expression
        self.target = target

    @staticmethod
    def _make_proxy(expression: Location, target: object) -> object:
        if isinstance(target, (list, dict)):
            return Proxy(expression, target)
        else:
            return target

    def __getitem__(self, item):
        if isinstance(self.target, list):
            new_expr = IndexAccess(self.expression, Const(item))
        else:
            new_expr = AttributeAccess(self.expression, item)

        val = self.target.__getitem__(item)
        return self._make_proxy(new_expr, val)


class Context(jinja2.environment.Context):
    """Jinja2 context that returns :class:`Proxy` instances when appropriate."""

    def resolve_or_missing(self, key: str):
        val = super().resolve_or_missing(key)
        return Proxy._make_proxy(Name(key), val)


class Environment(ImmutableSandboxedEnvironment):
    """Jinja2 environment using the custom :class:`Context` class."""

    context_class = Context


class Undefined(jinja2.StrictUndefined):
    """Custom :class:`jinja2.Undefined` instance to raise a custom UndefinedError."""

    def _fail_with_undefined_error(self, *args, **kwargs):
        obj = self._undefined_obj
        name = self._undefined_name

        if isinstance(obj, Proxy):
            if isinstance(obj.target, list):
                expr = IndexAccess(obj.expression, Const(name))
            else:
                expr = AttributeAccess(obj.expression, name)
        else:
            expr = Name(name)

        raise UndefinedError(expr)


# Override _fail_with_undefined_error
for attr in dir(Undefined):
    attr_val = getattr(Undefined, attr)
    if attr_val is jinja2.Undefined._fail_with_undefined_error:
        setattr(Undefined, attr, Undefined._fail_with_undefined_error)
