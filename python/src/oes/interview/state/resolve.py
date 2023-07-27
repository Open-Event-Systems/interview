"""Functions for resolving values."""
from collections.abc import Iterable, Iterator, Mapping

from oes.interview.input.logic import evaluate_whenable
from oes.interview.input.question import Question, get_question_schema
from oes.interview.input.question_bank import QuestionBank, get_questions_providing_var
from oes.interview.input.response import get_field_names
from oes.interview.input.types import Locator
from oes.interview.state.state import InterviewState
from oes.interview.state.update import InterviewError
from oes.interview.variables.locator import UndefinedError


def get_question_schema_for_variable(
    bank: QuestionBank,
    state: InterviewState,
    loc: Locator,
) -> tuple[str, Mapping[str, object]]:
    """Get the JSON schema for a question providing a value for ``loc``.

    Args:
        bank: The :class:`QuestionBank`.
        state: The :class:`InterviewState`.
        loc: The variable :class:`Locator`.

    Returns:
        A pair of the question ID and the JSON schema.
    """
    return _recursive_get_question_schema_for_variable(bank, state, loc)


def _recursive_get_question_schema_for_variable(
    bank: QuestionBank,
    state: InterviewState,
    loc: Locator,
) -> tuple[str, Mapping[str, object]]:
    try:
        question = _get_question_for_variable(bank, state, loc)
        fields = get_field_names(question.fields)
        schema = get_question_schema(
            question.title,
            question.description,
            fields,
            state.template_context,
        )
        return question.id, schema
    except UndefinedError as e:
        return _recursive_get_question_schema_for_variable(bank, state, e.locator)


def _get_question_for_variable(
    question_bank: QuestionBank,
    state: InterviewState,
    loc: Locator,
) -> Question:
    questions = question_bank.values()
    questions = _get_unanswered_questions(questions, state)
    questions = _get_questions_matching_conditions(questions, state)
    questions = get_questions_providing_var(questions, loc, state.template_context)

    question = next(questions, None)

    if question is None:
        raise InterviewError(f"No question providing {loc}")

    return question


def _get_unanswered_questions(
    questions: Iterable[Question],
    state: InterviewState,
) -> Iterator[Question]:
    for question in questions:
        if question.id not in state.answered_question_ids:
            yield question


def _get_questions_matching_conditions(
    questions: Iterable[Question],
    state: InterviewState,
) -> Iterator[Question]:
    for question in questions:
        if evaluate_whenable(question, state.template_context):
            yield question
