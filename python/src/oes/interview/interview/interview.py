"""Interview module."""
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Union

from attrs import field, frozen
from cattrs import Converter
from oes.interview.input.question import Question
from oes.interview.input.question_bank import QuestionBank
from oes.interview.input.types import validate_identifier


@frozen(kw_only=True)
class Interview:
    """An interview."""

    id: str = field(validator=validate_identifier)
    """The interview ID."""

    questions: Sequence[Union[Path, Question]] = ()
    """The available questions in the interview."""

    steps: Sequence[Any] = ()
    """The steps."""

    question_bank: QuestionBank
    """The question bank."""


def structure_interview(converter: Converter, v: object, t: object) -> Interview:
    """Structure an :class:`Interview` from a config object."""
    if not isinstance(v, Mapping):
        raise TypeError(f"Invalid interview: {v}")

    question_bank = QuestionBank(converter)
    questions = converter.structure(
        v.get("questions", ()), Sequence[Union[Path, Question]]
    )

    for question in questions:
        question_bank[question.id] = question

    interview = Interview(
        id=v["id"],
        questions=questions,
        question_bank=question_bank,
    )

    return interview
