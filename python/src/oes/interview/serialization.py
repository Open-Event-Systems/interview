"""Serialization module."""
from collections.abc import Sequence
from datetime import date, datetime
from functools import singledispatch
from pathlib import Path
from typing import Tuple, Union, get_args, get_origin

from cattrs import Converter
from cattrs.preconf.orjson import make_converter
from oes.interview.config.question import structure_questions
from oes.interview.input.field import structure_field
from oes.interview.input.logic import structure_evaluable_or_sequence
from oes.interview.input.question import Question
from oes.interview.input.types import Field, Locator
from oes.interview.interview.interview import Interview, structure_interview
from oes.interview.variables.locator import parse_locator
from oes.template import (
    Expression,
    Template,
    ValueOrEvaluable,
    structure_expression,
    structure_template,
)


@singledispatch
def json_default(obj: object) -> object:
    raise TypeError(f"Unsupported type: {type(obj)}")


@json_default.register
def _(obj: datetime) -> int:
    return int(obj.timestamp())


@json_default.register
def _(obj: date) -> str:
    return obj.isoformat()


def structure_datetime(obj: object, t: object) -> datetime:
    """Structure a :obj:`datetime`."""
    if isinstance(obj, datetime):
        dt = obj
    elif isinstance(obj, str):
        dt = datetime.fromisoformat(obj)
    elif isinstance(obj, (int, float)):
        dt = datetime.fromtimestamp(obj)
    else:
        raise TypeError(f"Invalid datetime: {obj}")

    return dt.astimezone() if dt.tzinfo is None else dt


def configure_converter(converter: Converter):
    """Configure the given converter."""
    converter.register_structure_hook(
        datetime,
        lambda v, t: structure_datetime,
    )
    converter.register_structure_hook(Template, structure_template)
    converter.register_structure_hook(Expression, structure_expression)
    converter.register_structure_hook(Locator, lambda v, t: parse_locator(v))

    converter.register_structure_hook_func(
        lambda cls: get_origin(cls) is Sequence,
        lambda v, t: converter.structure(v, Tuple[get_args(t)[0], ...]),
    )

    converter.register_structure_hook_func(
        lambda cls: cls is Field, lambda v, t: structure_field(converter, v, t)
    )

    converter.register_structure_hook_func(
        lambda cls: cls == Union[ValueOrEvaluable, Sequence[ValueOrEvaluable]],
        lambda v, t: structure_evaluable_or_sequence(converter, v, t),
    )

    converter.register_structure_hook_func(
        lambda cls: cls == Sequence[Union[Path, Question]],
        lambda v, t: structure_questions(converter, v, t),
    )

    converter.register_structure_hook(
        Interview, lambda v, t: structure_interview(converter, v, t)
    )


converter = make_converter()
"""The default converter."""


configure_converter(converter)
