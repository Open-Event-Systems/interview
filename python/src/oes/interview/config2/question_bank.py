"""Question bank module."""
from collections.abc import Iterator, MutableMapping

from loguru import logger
from oes.interview.config2.locator import Access
from oes.interview.config2.question import Question
from oes.interview.config2.types import Context, Locator


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

    def get_questions_providing_var(
        self, loc: Locator, context: Context
    ) -> Iterator[Question]:
        """Yield :class:`Question` objects that provide the value at ``loc``."""
        for question in self._questions.values():
            if _check_question_provides_var(question, loc, context):
                yield question


def _check_question_provides_var(
    question: Question, loc: Locator, context: Context
) -> bool:
    locs = (
        _evaluate_access_names(field.set, context)
        for field in question.fields
        if field.set
    )

    eval_loc = _evaluate_access_names(loc, context)
    return any(loc_ == eval_loc for loc_ in locs)


def _evaluate_access_names(loc: Locator, context: Context) -> Locator:
    if isinstance(loc, Access):
        evaluated = loc.evaluate_name(context)
        return Access(_evaluate_access_names(evaluated.target, context), evaluated.name)
    else:
        return loc
