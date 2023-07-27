"""Functions for updating state."""
import copy
from collections.abc import Mapping
from typing import Any, Optional

from attrs import evolve
from oes.interview.input.question_bank import QuestionBank
from oes.interview.input.types import ResponseParser
from oes.interview.state.state import InterviewState


class InterviewError(ValueError):
    """Raised when there is an issue with the interview configuration."""

    pass


def _validate_and_apply_responses(
    state: InterviewState,
    parser: ResponseParser,
    responses: Optional[Mapping[str, Any]],
    button: Optional[int],
) -> Mapping[str, Any]:
    """Validate and apply responses."""

    values = parser(responses or {})
    data = dict(state.data)
    new_data = copy.deepcopy(data)

    for path, val in values.items():
        path.set(val, new_data)

    return new_data


def _apply_responses(
    state: InterviewState,
    questions: QuestionBank,
    responses: Optional[dict[str, Any]],
    button: Optional[int],
) -> InterviewState:
    # Apply responses if a question was asked
    if state.question_id is not None:
        question = questions.get(state.question_id)
        if not question:
            raise InterviewError(f"Question ID not found: {state.question_id}")

        # Apply responses
        parser = questions.get_parser(question.id)
        new_data = _validate_and_apply_responses(state, parser, responses, button)

        # Unset question ID
        return evolve(state, data=new_data, question_id=None)
    else:
        return state
