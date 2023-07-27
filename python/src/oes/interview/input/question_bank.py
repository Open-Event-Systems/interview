"""Question bank module."""
from __future__ import annotations

from collections.abc import Iterable, Iterator, MutableMapping

from cattrs import Converter
from loguru import logger
from oes.interview.input.question import Question
from oes.interview.input.response import create_response_parser
from oes.interview.input.types import Context, Locator, ResponseParser


class QuestionBank(MutableMapping[str, Question]):
    """A collection of questions."""

    _questions: dict[str, Question]
    _parsers: dict[str, ResponseParser]
    _converter: Converter

    def __init__(self, converter: Converter):
        self._questions = {}
        self._converter = converter
        self._parsers = {}

    def __setitem__(self, key: str, value: Question) -> None:
        if key in self._questions:
            logger.warning(f"Duplicate question ID: {key}")
        self._questions[key] = value
        self._parsers[key] = create_response_parser(key, value.fields, self._converter)

    def __delitem__(self, key: str):
        del self._questions[key]
        del self._parsers[key]

    def __getitem__(self, key: str) -> Question:
        return self._questions[key]

    def get_parser(self, id: str) -> ResponseParser:
        return self._parsers[id]

    def __len__(self) -> int:
        return len(self._questions)

    def __iter__(self) -> Iterator[str]:
        return iter(self._questions)


def get_questions_providing_var(
    questions: Iterable[Question], loc: Locator, context: Context
) -> Iterator[Question]:
    """Yield :class:`Question` objects that provide the value at ``loc``.

    Args:
        questions: The questions.
        loc: The variable to be provided.
        context: The template context.
    """
    for q in questions:
        locs = (f.set for f in q.fields if f.set)
        if any(other.compare(loc, context) for other in locs):
            yield q
