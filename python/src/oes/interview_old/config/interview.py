"""Interview module."""
from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from contextvars import ContextVar
from pathlib import Path
from typing import Optional, Union

from attrs import Factory, field, frozen
from cattrs import Converter
from loguru import logger
from oes.interview_old.config.question import Question
from oes.interview_old.config.question_bank import QuestionBank
from oes.interview_old.config.step import Ask, Step, StepOrBlock, flatten_steps
from oes.interview_old.parsing.template import default_jinja2_env
from oes.interview_old.parsing.types import validate_identifier
from oes.template import jinja2_env_context
from ruamel.yaml import YAML
from typing_extensions import TypeAlias

yaml = YAML(typ="safe")

interviews_context: ContextVar[Optional[InterviewConfig]] = ContextVar(
    "interviews_context", default=None
)
"""Interviews context var."""

config_path_context: ContextVar[Optional[Path]] = ContextVar(
    "config_path_context", default=None
)
"""Config file path context var."""


InterviewQuestion: TypeAlias = Union[Question, Path]


def _build_question_bank(interview: Interview):
    from oes.interview_old.serialization import converter

    questions: list[Question] = []

    for entry in interview.questions:
        if isinstance(entry, Path):
            questions.extend(_load_questions(converter, entry))
        else:
            questions.append(entry)

    return QuestionBank(questions)


def _build_flattened_steps(interview: Interview):
    return flatten_steps(interview.steps)


@frozen
class Interview:
    """Interview model."""

    id: str = field(validator=[validate_identifier])
    title: Optional[str] = None
    questions: Sequence[InterviewQuestion] = ()
    question_bank: QuestionBank = field(
        init=False, eq=False, default=Factory(_build_question_bank, takes_self=True)
    )
    steps: Sequence[StepOrBlock] = ()
    flattened_steps: Sequence[Step] = field(
        init=False, eq=False, default=Factory(_build_flattened_steps, takes_self=True)
    )

    def __attrs_post_init__(self):
        # Check that all questions are found
        for step in self.flattened_steps:
            if isinstance(step, Ask) and not self.question_bank.get_question(step.ask):
                raise ValueError(f"Question ID not found: {step.ask}")


InterviewEntry: TypeAlias = Union[Interview, Path]


def _read_interviews(obj: InterviewEntry) -> Iterable[Interview]:
    from oes.interview_old.serialization import converter

    if isinstance(obj, Path):
        return _load_interviews(converter, obj)
    else:
        return [obj]


def _build_interviews(config: InterviewConfig):
    by_id = {}

    for entry in config.interviews:
        for item in _read_interviews(entry):
            if item.id in by_id:
                logger.warning(f"Duplicate interview_old ID: {item.id}")
            by_id[item.id] = item

    return by_id


@frozen
class InterviewConfig:
    """Interview configuration."""

    interviews: Sequence[InterviewEntry]
    _interviews_by_id: dict[str, Interview] = field(
        init=False, eq=False, default=Factory(_build_interviews, takes_self=True)
    )

    def __iter__(self) -> Iterator[Interview]:
        yield from self._interviews_by_id.values()

    def get_interview(self, id: str) -> Optional[Interview]:
        """Get an interview_old by ID."""
        return self._interviews_by_id.get(id)


def load_interview_config(path: Path) -> InterviewConfig:
    """Load the interview_old config from a file."""
    from oes.interview_old.serialization import converter

    full_path = path.resolve()
    token = config_path_context.set(full_path.parent)
    jinja2_env_token = jinja2_env_context.set(default_jinja2_env)
    try:
        doc = yaml.load(full_path)
        return converter.structure(doc, InterviewConfig)
    finally:
        jinja2_env_context.reset(jinja2_env_token)
        config_path_context.reset(token)


def _get_cwd() -> Path:
    ctx_path = config_path_context.get()
    return ctx_path if ctx_path is not None else Path.cwd()


def _resolve_path(path: Path) -> Path:
    if path.root:
        return path
    else:
        return (_get_cwd() / path).resolve()


def _load_questions(converter: Converter, path: Path) -> tuple[Question, ...]:
    data = yaml.load(_resolve_path(path))
    return converter.structure(data, tuple[Question, ...])


def _load_interviews(converter: Converter, path: Path) -> tuple[Interview, ...]:
    full_path = _resolve_path(path)
    token = config_path_context.set(full_path.parent)
    try:
        data = yaml.load(_resolve_path(path))
        return converter.structure(data, tuple[Interview, ...])
    finally:
        config_path_context.reset(token)


def parse_question_entry(converter: Converter, v):
    if isinstance(v, (str, Path)):
        return Path(v)
    else:
        return converter.structure(v, Question)


def parse_interview_entry(converter: Converter, v):
    if isinstance(v, (str, Path)):
        return Path(v)
    else:
        return converter.structure(v, Interview)
