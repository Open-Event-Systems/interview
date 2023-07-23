"""Question bank module."""
from collections.abc import Iterator, MutableMapping

from loguru import logger
from oes.interview.config2.question import Question


class QuestionBank(MutableMapping[str, Question]):
    """A collection of questions."""

    _questions: dict[str, Question]

    def __init__(self):
        self._questions = {}

    def __setitem__(self, key: str, value: Question) -> None:
        if key in self._questions:
            logger.warning(f"Duplicate question ID: {key}")
        self._questions[key] = value

    def __delitem__(self, key: str):
        del self._questions[key]

    def __getitem__(self, key: str) -> Question:
        return self._questions[key]

    def __len__(self) -> int:
        return len(self._questions)

    def __iter__(self) -> Iterator[str]:
        return iter(self._questions)
