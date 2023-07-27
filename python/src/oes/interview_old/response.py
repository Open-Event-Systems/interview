"""Response types."""
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from attrs import frozen
from cattrs import Converter
from oes.interview_old.config.field import AskField

if TYPE_CHECKING:
    from oes.interview_old.config.question import Button, Question
    from oes.interview_old.config.step import Ask, Exit
    from oes.interview_old.state import InterviewState


@frozen
class AskResultButton:
    """A button available in an :class:`AskResult`."""

    label: str
    primary: bool = False
    default: bool = False

    @classmethod
    def create_from_button(
        cls, button: Button, context: dict[str, Any]
    ) -> AskResultButton:
        return cls(
            label=button.label.render(**context),
            primary=button.primary,
            default=button.default,
        )


@frozen
class AskResult:
    """Result of an :class:`Ask` step."""

    type: Literal["question"] = "question"

    title: Optional[str] = None
    """The question title."""

    description: Optional[str] = None
    """The question description."""

    fields: dict[str, AskField] = {}
    """The fields."""

    buttons: Optional[Sequence[AskResultButton]] = None
    """The buttons shown."""

    @classmethod
    def create_from_question(
        cls, question: Question, state: InterviewState
    ) -> AskResult:
        """Create an :class:`AskResult` from a :class:`Question`.

        Returns:
            The :class:`AskResult`.
        """
        context = state.template_context
        title = question.title.render(**context) if question.title else None
        desc = question.description.render(**context) if question.description else None
        fields = question.get_ask_fields(context)

        if question.buttons:
            buttons = (
                AskResultButton.create_from_button(b, context) for b in question.buttons
            )
        else:
            buttons = None

        return cls(
            title=title,
            description=desc,
            fields=fields,
            buttons=tuple(buttons) if buttons is not None else None,
        )

    @classmethod
    def create_from_step(cls, step: Ask, state: InterviewState) -> AskResult:
        """Create an :class:`AskResult` from an :class:`Ask` step.

        Returns:
            The :class:`AskResult`.
        """
        return cls.create_from_question(step.question, state)


@frozen
class ExitResult:
    """Result of an :class:`Exit` step."""

    title: str
    """The exit info title."""

    type: Literal["exit"] = "exit"

    description: Optional[str] = None
    """A description of the exit reason."""

    @classmethod
    def create_from_step(cls, step: Exit, state: InterviewState) -> ExitResult:
        """Create an :class:`ExitResult` from an :class:`Exit` step."""
        context = state.template_context
        title = step.exit.render(**context)
        desc = step.description.render(**context) if step.description else None
        return cls(
            title=title,
            description=desc,
        )


Result = Union[AskResult, ExitResult]


@frozen
class IncompleteInterviewStateResponse:
    """Model of a response containing an interview_old state."""

    state: str
    """The state."""

    update_url: str
    """The update URL."""

    content: Optional[Result]
    """The response content."""


@frozen
class CompleteInterviewStateResponse:
    """Model of a response containing a completed interview_old state."""

    state: str
    """The state."""

    target_url: str
    """The target URL."""

    complete: Literal[True] = True
    """Whether the state is complete."""


InterviewStateResponse = Union[
    CompleteInterviewStateResponse, IncompleteInterviewStateResponse
]


def create_state_response(
    state: InterviewState,
    *,
    key: bytes,
    content: Union[AskResult, ExitResult, None] = None,
    update_url: Optional[str] = None,
) -> InterviewStateResponse:
    """Create an interview_old state response.

    Args:
        state: The :class:`InterviewState`.
        key: The encryption key.
        content: The result content.
        update_url: The update URL.

    Returns:
        The response body.
    """
    res: InterviewStateResponse

    state_str = state.encrypt(key=key)
    if state.complete:
        res = CompleteInterviewStateResponse(
            state=state_str,
            complete=True,
            target_url=state.target_url,
        )
    else:
        if not update_url:
            raise ValueError("`update_url` is required")
        res = IncompleteInterviewStateResponse(
            state=state_str,
            update_url=update_url,
            content=content,
        )

    return res


def parse_result_type(converter: Converter, value):
    if value is None:
        return None
    elif isinstance(value, dict) and "type" in value:
        type_ = value["type"]
        if type_ == "question":
            return converter.structure(value, AskResult)
        elif type_ == "exit":
            return converter.structure(value, ExitResult)

    raise TypeError(f"Invalid type: {value}")
