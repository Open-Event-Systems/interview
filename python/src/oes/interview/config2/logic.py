"""Logic module."""
from collections.abc import Mapping, Sequence
from typing import Union

from attrs import frozen
from cattrs import Converter
from oes.interview.config2.types import Context, Evaluable, Expression, Value, Whenable
from oes.template import Expression as TemplateExpression


@frozen
class LogicAnd(Evaluable):
    """A logic AND expression."""

    and_: Sequence[Expression] = ()

    def evaluate(self, context: Context) -> object:
        """Evaluate the AND."""
        return all(_eval(expr, context) for expr in self.and_)


@frozen
class LogicOr(Evaluable):
    """A logic OR expression."""

    or_: Sequence[Expression] = ()

    def evaluate(self, context: Context) -> object:
        """Evaluate the OR."""
        return any(_eval(expr, context) for expr in self.or_)


@frozen
class LogicNot(Evaluable):
    """A logic NOT expression."""

    not_: Expression

    def evaluate(self, context: Context) -> object:
        """Evaluate the NOT."""
        return not _eval(self.not_, context)


def evaluate_whenable(whenable: Whenable, context: Context) -> bool:
    """Evaluate the conditions of a :class:`Whenable`."""
    conditions = (
        whenable.when
        if isinstance(whenable.when, Sequence) and not isinstance(whenable.when, str)
        else (whenable.when,)
    )

    return all(_eval(c, context) for c in conditions)


def _eval(expr: Expression, context: Context) -> object:
    if isinstance(expr, Evaluable):
        return expr.evaluate(**context)
    else:
        return expr


def structure_expression_or_sequence(
    converter: Converter, v: object, t: object
) -> Union[Sequence[Expression], Expression]:
    """Structure a single expression or sequence of expressions."""
    if isinstance(v, Sequence) and not isinstance(v, str):
        return converter.structure(v, Sequence[Expression])
    else:
        return converter.structure(v, Expression)


def structure_expression(converter: Converter, v: object, t: object) -> Expression:
    """Structure an expression."""
    if (
        isinstance(v, Mapping)
        and len(v) == 1
        and ("and" in v or "or" in v or "not" in v)
    ):
        return structure_logic(converter, v, t)
    elif isinstance(v, str):
        # assume all strings are template expressions
        return converter.structure(v, TemplateExpression)
    else:
        return converter.structure(v, Value)


def structure_logic(converter: Converter, v: object, t: object) -> Evaluable:
    """Structure a logic expression."""
    if isinstance(v, Mapping) and len(v) == 1:
        if "and" in v:
            return LogicAnd(converter.structure(v["and"], Sequence[Expression]))
        elif "or" in v:
            return LogicOr(converter.structure(v["or"], Sequence[Expression]))
        elif "not" in v:
            return LogicNot(converter.structure(v["not"], Expression))

    raise ValueError(f"Invalid logic expression: {v}")


def structure_value(v: object, t: object) -> Value:
    """Structure a literal value."""
    return v
