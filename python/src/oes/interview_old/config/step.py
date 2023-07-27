"""Step module."""
from __future__ import annotations

import asyncio
import copy
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Iterable, Sequence
from contextvars import ContextVar
from enum import Enum
from inspect import iscoroutinefunction
from typing import Any, Optional, Union

from attr import Factory
from attrs import evolve, field, frozen
from cattrs import Converter
from oes.hook import ExecutableHookConfig
from oes.hook import Hook as HookFunc
from oes.hook import (
    HttpHookConfig,
    PythonHookConfig,
    executable_hook_factory,
    http_hook_factory,
    python_hook_factory,
)
from oes.interview_old.config.question import Question
from oes.interview_old.config.question_bank import question_bank_context
from oes.interview_old.parsing.location import Location, UndefinedError
from oes.interview_old.parsing.types import Whenable, validate_identifier
from oes.interview_old.parsing.undefined import Undefined
from oes.interview_old.response import AskResult, ExitResult
from oes.interview_old.state import InterviewState
from oes.template import Condition, Evaluable, Expression, LogicAnd, Template
from typing_extensions import Protocol, TypeAlias

Value: TypeAlias = Union[None, str, int, float, bool, dict, list, tuple]
"""Value literal types."""

ValueTypes = (str, int, float, bool, dict, list, tuple)

ValueOrExpression: TypeAlias = Union[Value, Expression]
"""A literal value type, or a template expression."""


class StepResultStatus(str, Enum):
    not_changed = "skipped"
    """The step did not cause a change."""

    changed = "changed"
    """The step resulted in the state being changed."""

    completed = "completed"
    """The interview_old is complete."""


StepResult: TypeAlias = Union[AskResult, ExitResult, StepResultStatus]
"""The result of handling a :class:`Step`."""

http_func_ctx: ContextVar[
    Callable[
        [InterviewState, HttpHookConfig], Awaitable[tuple[InterviewState, StepResult]]
    ]
] = ContextVar("http_func_ctx")
"""Context var for the HTTP hook function"""


class AbstractStep(Whenable, Protocol):
    """Step base class."""

    @abstractmethod
    async def handle(self, state: InterviewState) -> tuple[InterviewState, StepResult]:
        """Handle this step, returning the updated state and a result."""
        ...


@frozen
class Block(Whenable):
    """A block of steps."""

    block: list[StepOrBlock]
    when: Condition = ()


@frozen
class Set(AbstractStep):
    """Set a value."""

    set: Location
    value: ValueOrExpression
    always: bool = False
    """Whether to always set the value, or only if undefined."""

    when: Condition = ()

    def _check_defined(self, context: dict[str, Any]):
        try:
            self.set.evaluate(**context)
            return True
        except UndefinedError:
            return False

    async def handle(self, state: InterviewState) -> tuple[InterviewState, StepResult]:
        if self._check_defined(state.template_context) and not self.always:
            return state, StepResultStatus.not_changed  # skip if already defined

        if isinstance(self.value, Evaluable):
            value = self.value.evaluate(**state.template_context)
        else:
            value = self.value

        new_data = copy.deepcopy(state.data)
        self.set.set(value, new_data)
        state = evolve(state, data=new_data)
        return state, StepResultStatus.changed


@frozen
class Ask(AbstractStep):
    """Ask a question."""

    ask: str = field(validator=[validate_identifier])
    when: Condition = ()

    @property
    def question(self) -> Question:
        bank = question_bank_context.get()
        if bank is None:
            raise RuntimeError("Question bank not available")

        question = bank.get_question(self.ask)

        if question is None:
            raise ValueError(f"Question ID not found: {self.ask!r}")

        return question

    async def handle(self, state: InterviewState) -> tuple[InterviewState, StepResult]:
        if self.ask in state.answered_question_ids:
            return state, StepResultStatus.not_changed
        else:
            response = AskResult.create_from_step(self, state)
            state = state.update_with_question(self.ask)
            return state, response


@frozen
class Exit(AbstractStep):
    """Exit an interview_old."""

    exit: Template
    description: Optional[Template] = None
    when: Condition = ()

    async def handle(self, state: InterviewState) -> tuple[InterviewState, StepResult]:
        return state, ExitResult.create_from_step(self, state)


@frozen
class Eval(AbstractStep):
    """Evaluate values."""

    eval: Union[ValueOrExpression, Sequence[ValueOrExpression]]
    when: Condition = ()

    async def handle(self, state: InterviewState) -> tuple[InterviewState, StepResult]:
        as_list = self.eval if isinstance(self.eval, (list, tuple)) else [self.eval]

        for val in as_list:
            if isinstance(val, Evaluable):
                res = val.evaluate(**state.template_context)
                if isinstance(res, Undefined):
                    res._fail_with_undefined_error()

        return state, StepResultStatus.not_changed


@frozen
class URLOnlyHttpHookConfig:
    """HTTP hook."""

    url: str = field(repr=False)


def _make_hook_func(s):
    obj = s.hook

    if isinstance(obj, URLOnlyHttpHookConfig):

        async def _http_func(body: Any, config: HttpHookConfig):
            http_func = http_func_ctx.get()
            return await http_func(body, config)

        return http_hook_factory(HttpHookConfig(obj.url, _http_func))
    elif isinstance(obj, ExecutableHookConfig):
        return executable_hook_factory(obj)
    elif isinstance(obj, PythonHookConfig):
        return python_hook_factory(obj)
    else:
        raise TypeError(f"Invalid hook: {obj}")


@frozen
class Hook(AbstractStep):
    """Invoke a hook."""

    hook: Union[PythonHookConfig, ExecutableHookConfig, URLOnlyHttpHookConfig]
    _hook_func: HookFunc = field(
        init=False,
        default=Factory(_make_hook_func, takes_self=True),
    )

    when: Condition = ()

    @property
    def hook_func(self) -> HookFunc:
        """The hook function."""
        return self._hook_func

    async def handle(self, state: InterviewState) -> tuple[InterviewState, StepResult]:
        hook_func = self.hook_func
        if iscoroutinefunction(hook_func):
            return await hook_func(state)
        else:
            return await asyncio.to_thread(hook_func, state)


@frozen
class HookResult:
    """Return value from a web hook."""

    state: InterviewState
    result: StepResult


Step: TypeAlias = Union[Set, Ask, Exit, Eval, Hook]
StepOrBlock: TypeAlias = Union[Step, Block]


def _get_step_type(value: dict):
    if "block" in value:
        return Block
    elif "set" in value:
        return Set
    elif "ask" in value:
        return Ask
    elif "exit" in value:
        return Exit
    elif "eval" in value:
        return Eval
    elif "hook" in value:
        return Hook
    else:
        raise TypeError(f"Invalid type: {value}")


def parse_step(converter: Converter, value: object) -> StepOrBlock:
    if not isinstance(value, dict):
        raise TypeError(f"Invalid type: {value}")

    cls = _get_step_type(value)
    return converter.structure(value, cls)


def parse_hook_config(converter: Converter, value: object) -> object:
    if isinstance(value, dict):
        if "url" in value:
            return converter.structure(value, URLOnlyHttpHookConfig)
        elif "python" in value:
            return converter.structure(value, PythonHookConfig)
        elif "executable" in value:
            return converter.structure(value, ExecutableHookConfig)

    raise ValueError(f"Invalid hook: {value}")


def parse_step_result(converter: Converter, value: object) -> StepResult:
    if isinstance(value, str):
        return converter.structure(value, StepResultStatus)
    elif isinstance(value, dict):
        if value.get("type") == "exit":
            return converter.structure(value, ExitResult)
        elif value.get("type") == "question":
            return converter.structure(value, AskResult)

    raise ValueError(f"Invalid result: {value}")


def parse_value(v):
    if v is None or isinstance(v, ValueTypes):
        return v
    else:
        raise TypeError(f"Invalid type {v}")


def _get_when(obj: Whenable) -> Evaluable:
    if isinstance(obj.when, tuple):
        conds = obj.when
    else:
        conds = (obj.when,) if obj.when else ()

    return LogicAnd(and_=conds)


def flatten_block(step: Block) -> list[StepOrBlock]:
    """Flatten a :class:`Block` step into a list of its inner steps.

    Combines the ``when`` conditions.
    """
    steps = []
    block_when = _get_when(step)
    for inner_step in step.block:
        step_when = _get_when(inner_step)
        new_inner_step = evolve(inner_step, when=(block_when, step_when))
        steps.append(new_inner_step)

    return steps


def flatten_steps(steps: Iterable[StepOrBlock]) -> list[Step]:
    """Recursively flatten :class:`Block` steps."""
    final_steps = []
    for step in steps:
        if isinstance(step, Block):
            flattened_block = flatten_block(step)
            flattened_steps = flatten_steps(flattened_block)
            final_steps.extend(flattened_steps)
        else:
            final_steps.append(step)

    return final_steps
