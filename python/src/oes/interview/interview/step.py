"""Steps."""
import copy
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from typing import Literal, Optional, Union

from attrs import evolve, frozen
from oes.interview.input.question import get_question_schema
from oes.interview.input.response import get_field_names
from oes.interview.input.types import Locator, Whenable
from oes.interview.interview.interview import Interview
from oes.interview.state.state import InterviewState
from oes.interview.variables.locator import UndefinedError
from oes.interview.variables.undefined import Undefined
from oes.template import Context, Expression, Template, ValueOrEvaluable, evaluate
from typing_extensions import Protocol


@frozen(kw_only=True)
class AskResult:
    """A result asking a question."""

    type: Literal["question"] = "question"
    schema: Mapping[str, object]


@frozen(kw_only=True)
class ExitResult:
    """An exit result."""

    type: Literal["exit"] = "exit"
    title: str
    description: Optional[str] = None


@frozen
class StepResult:
    """The result of a step."""

    state: InterviewState
    """The updated :class:`InterviewState`."""

    changed: bool
    """Whether a change was made."""

    content: object = None
    """Result content."""


class Step(Whenable, Protocol):
    """Abstract step."""

    @abstractmethod
    async def __call__(
        self, __interview: Interview, __state: InterviewState
    ) -> StepResult:
        """Handle the step."""
        ...


@frozen
class AskStep(Step):
    """Ask a question."""

    ask: str
    """The question ID."""

    when: Union[ValueOrEvaluable, Sequence[ValueOrEvaluable]] = ()
    """``when`` conditions."""

    async def __call__(self, interview: Interview, state: InterviewState) -> StepResult:
        # skip if the question was already asked
        if self.ask in state.answered_question_ids:
            return StepResult(state, changed=False)

        question = interview.question_bank[self.ask]
        schema = get_question_schema(
            question.title,
            question.description,
            get_field_names(question.fields),
            state.template_context,
        )

        updated = evolve(
            state,
            question_id=question.id,
            answered_question_ids=state.answered_question_ids | {question.id},
        )

        return StepResult(
            state=updated,
            changed=True,
            content=AskResult(schema=schema),
        )


@frozen
class SetStep(Step):
    """Set a value."""

    set: Locator
    """The variable to set."""

    value: Expression
    """The value to set."""

    when: Union[ValueOrEvaluable, Sequence[ValueOrEvaluable]] = ()
    """``when`` conditions."""

    async def __call__(self, interview: Interview, state: InterviewState) -> StepResult:
        ctx = state.template_context
        is_set, cur_val = self._get_value(state.template_context)

        val = self.value.evaluate(ctx)

        if val != cur_val:
            new_data = dict(copy.deepcopy(state.data))
            self.set.set(val, new_data)

            changed = True
            updated_state = evolve(
                state,
                data=new_data,
            )
        else:
            changed = False
            updated_state = state

        return StepResult(
            state=updated_state,
            changed=changed,
        )

    def _get_value(
        self, context: Context
    ) -> Union[tuple[Literal[False], None], tuple[Literal[True], object]]:
        try:
            val = self.set.evaluate(context)
            return (False, None) if isinstance(val, Undefined) else (True, val)
        except UndefinedError:
            return False, None


@frozen
class EvalStep(Step):
    """Ensure values are present."""

    eval: Union[ValueOrEvaluable, Sequence[ValueOrEvaluable]]
    """The value or values to evaluate."""

    when: Union[ValueOrEvaluable, Sequence[ValueOrEvaluable]] = ()
    """``when`` conditions."""

    async def __call__(self, interview: Interview, state: InterviewState) -> StepResult:
        ctx = state.template_context
        if isinstance(self.eval, Sequence) and not isinstance(self.eval, str):
            for item in self.eval:
                evaluate(item, ctx)
        else:
            evaluate(self.eval, ctx)

        return StepResult(
            state=state,
            changed=False,
        )


@frozen
class ExitStep(Step):
    """Stop the interview."""

    exit: Template
    """The reason."""

    description: Optional[Template] = ""
    """An optional description."""

    when: Union[ValueOrEvaluable, Sequence[ValueOrEvaluable]] = ()
    """``when`` conditions."""

    async def __call__(self, interview: Interview, state: InterviewState) -> StepResult:
        return StepResult(
            state=state,
            changed=True,
            content=ExitResult(
                title=self.exit.render(state.template_context),
                description=self.description.render(state.template_context)
                if self.description
                else None,
            ),
        )
