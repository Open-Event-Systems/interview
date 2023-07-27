from collections.abc import Sequence
from datetime import date
from typing import Any, Optional, Tuple, Union, get_args, get_origin

from attrs import Attribute, fields
from cattrs import override
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn
from cattrs.preconf.orjson import make_converter
from oes.hook import ExecutableHookConfig, PythonHookConfig
from oes.interview_old.config.field import (
    AbstractField,
    AskField,
    _BaseAskField,
    parse_field,
)
from oes.interview_old.config.interview import (
    Interview,
    InterviewEntry,
    InterviewQuestion,
    parse_interview_entry,
    parse_question_entry,
)
from oes.interview_old.config.question import Question
from oes.interview_old.config.step import StepOrBlock, StepResult, URLOnlyHttpHookConfig
from oes.interview_old.config.step import Value as StepValue
from oes.interview_old.config.step import (
    ValueOrExpression,
    ValueTypes,
    parse_hook_config,
    parse_step,
    parse_step_result,
    parse_value,
)
from oes.interview_old.parsing.location import Location
from oes.interview_old.response import Result, parse_result_type
from oes.template import (
    Condition,
    Expression,
    Template,
    structure_condition,
    structure_expression,
    structure_template,
)

converter = make_converter()


# Basic types


# Any attrs classes should omit None if it is the default
def make_unstructure_omitting_none(cls: Any):
    args = {}
    field: Attribute
    for field in fields(cls):
        if field.default is None:
            args[field.name] = override(omit_if_default=True)

    return make_dict_unstructure_fn(cls, converter, **args)


converter.register_unstructure_hook_factory(
    lambda cls: hasattr(cls, "__attrs_attrs__"),
    lambda cls: make_unstructure_omitting_none(cls),
)


# parse Sequence as a non-mutable sequence
def parse_non_mutable_sequence(v, t):
    args = get_args(t)
    return converter.structure(v, Tuple[args[0], ...])


converter.register_structure_hook_func(
    lambda cls: get_origin(cls) is Sequence, parse_non_mutable_sequence
)


# structure plain values without casting them
def structure_without_cast(v, t):
    if t in (float, int) and isinstance(v, (float, int)) or isinstance(v, t):
        return t(v)
    else:
        raise TypeError(f"Invalid type: {v!r}")


for cls in (int, float, str, bool):
    converter.register_structure_hook(cls, structure_without_cast)


# handle dates
def structure_date(v, t):
    if isinstance(v, date):
        return v
    elif isinstance(v, str):
        return date.fromisoformat(v)
    else:
        raise TypeError(f"Invalid date: {v}")


converter.register_structure_hook(date, structure_date)


# Var location


def structure_location(v, t):
    if isinstance(v, str):
        return Location.parse(v)
    else:
        raise TypeError(f"Not a string: {v}")


converter.register_structure_hook(Location, structure_location)


def structure_int_or_sequence(c, v):
    if v is None or isinstance(v, int):
        return v
    else:
        return c.structure(v, Sequence[int])


converter.register_structure_hook(
    Union[int, Sequence[int], None],
    lambda v, t: structure_int_or_sequence(converter, v),
)

# Logic and templates

converter.register_structure_hook(Template, lambda v, t: structure_template(v))
converter.register_structure_hook(Expression, lambda v, t: structure_expression(v))
converter.register_structure_hook(
    Condition, lambda v, t: structure_condition(converter, v)
)

# Field

converter.register_structure_hook_func(
    lambda cls: cls is AbstractField, lambda v, t: parse_field(converter, v)
)

# workaround used for tests
converter.register_structure_hook_func(
    lambda cls: cls is AskField, lambda v, t: converter.structure(v, _BaseAskField)
)

# unstructure AskField abstract class as its main type
converter.register_unstructure_hook_func(
    lambda cls: cls is AskField, lambda v: converter.unstructure(v, type(v))
)

# Question

converter.register_structure_hook(
    Question,
    make_dict_structure_fn(
        Question,
        converter,
        _provides=override(omit=True),
        _response_class=override(omit=True),
    ),
)


# Steps


def structure_value_or_expression(v):
    if isinstance(v, str):
        return converter.structure(v, Expression)
    elif v is None or isinstance(v, ValueTypes):
        return v
    else:
        raise TypeError(f"Invalid value: {v!r}")


def structure_value_or_expression_sequence(v):
    if isinstance(v, str):
        return converter.structure(v, ValueOrExpression)
    elif isinstance(v, Sequence):
        return converter.structure(v, Sequence[ValueOrExpression])
    else:
        raise TypeError(f"Invalid value: {v!r}")


converter.register_structure_hook(
    ValueOrExpression, lambda v, t: structure_value_or_expression(v)
)
converter.register_structure_hook(
    Union[ValueOrExpression, Sequence[ValueOrExpression]],
    lambda v, t: structure_value_or_expression_sequence(v),
)
converter.register_structure_hook(StepValue, lambda v, t: parse_value(v))
converter.register_structure_hook(StepOrBlock, lambda v, t: parse_step(converter, v))
converter.register_structure_hook(
    Union[PythonHookConfig, ExecutableHookConfig, URLOnlyHttpHookConfig],
    lambda v, t: parse_hook_config(converter, v),
)

converter.register_structure_hook(
    StepResult, lambda v, t: parse_step_result(converter, v)
)

# Interviews

converter.register_structure_hook(
    Interview,
    make_dict_structure_fn(
        Interview,
        converter,
        question_bank=override(omit=True),
        flattened_steps=override(omit=True),
    ),
)
converter.register_structure_hook(
    InterviewQuestion, lambda v, t: parse_question_entry(converter, v)
)
converter.register_structure_hook(
    InterviewEntry, lambda v, t: parse_interview_entry(converter, v)
)

# Results
converter.register_structure_hook(
    Optional[Result], lambda v, t: parse_result_type(converter, v)
)
