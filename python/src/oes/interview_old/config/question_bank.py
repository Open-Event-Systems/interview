"""Question bank module."""
from collections.abc import Iterable, Sequence
from contextvars import ContextVar
from typing import Any, Iterator, Optional

from attrs import Factory, field, frozen
from loguru import logger
from oes.interview_old.config.question import Question
from oes.interview_old.parsing.location import (
    AttributeAccess,
    IndexAccess,
    Location,
    Name,
    evaluate_indexes,
)


def _make_question_dict(bank) -> dict[str, Question]:
    result = {}
    for question in bank.questions:
        if question.id in result:
            logger.warning(f"Duplicate question ID: {question.id}")
        result[question.id] = question

    return result


def _make_by_var_question_bank(bank) -> dict:
    by_var: dict = {}

    for q in bank.questions:
        _add_by_var(by_var, q)

    return by_var


@frozen
class QuestionBank:
    """Bank of :class:`Question` models."""

    questions: Sequence[Question]

    _by_id: dict[str, Question] = field(
        init=False, eq=False, default=Factory(_make_question_dict, takes_self=True)
    )

    _by_var: dict = field(
        init=False,
        eq=False,
        default=Factory(_make_by_var_question_bank, takes_self=True),
    )
    """Organizes questions in a tree by provided variable locations.

    Maps expression elements to other dicts representing the next nodes. Each node
    may also have a ``"."`` key, which maps to a list of questions providing that
    expression.
    """

    def _get_evaluated_keys(self, obj: dict, context: dict[str, Any]) -> dict:
        """Returns a dict with all keys passed to :func:`evaluate_indices`."""
        new_dict = {}
        for k, v in obj.items():
            if isinstance(k, Location):
                new_dict[evaluate_indexes(k, context)] = v
            else:
                new_dict[k] = v

        return new_dict

    def _get_node_by_eval_indexed_var(
        self, loc: Location, context: dict[str, Any]
    ) -> dict:
        if isinstance(loc, (IndexAccess, AttributeAccess)):
            parent_node = self._get_node_by_eval_indexed_var(loc.target, context)
        elif isinstance(loc, Name):
            parent_node = self._by_var
        else:
            raise TypeError(f"Invalid expression type: {loc!r}")

        eval_parent_node = self._get_evaluated_keys(parent_node, context)
        return eval_parent_node.get(loc, {})

    def get_question(self, id: str) -> Optional[Question]:
        """Get a :class:`Question` by ID."""
        return self._by_id.get(id)

    def get_questions_providing_variable(
        self, loc: Location, context: dict[str, Any]
    ) -> Iterable[Question]:
        """Get :class:`Question` instances that provide the given variable location."""

        evaluated = evaluate_indexes(loc, context)
        node = self._get_node_by_eval_indexed_var(evaluated, context)

        yield from node.get(".", [])

    def __iter__(self) -> Iterator[Question]:
        yield from self.questions

    def __len__(self) -> int:
        return len(self.questions)


def _get_node_by_var(by_var: dict, loc: Location) -> dict:
    """Recursively get a node in the tree for the given variable."""
    if isinstance(loc, (IndexAccess, AttributeAccess)):
        parent_node = _get_node_by_var(by_var, loc.target)
    elif isinstance(loc, Name):
        parent_node = by_var
    else:
        raise TypeError(f"Invalid variable: {loc!r}")

    return parent_node.setdefault(loc, {})


def _add_by_var(by_var: dict, question: Question):
    """Add a question to the tree by its provided variables."""

    for provides in question.provides:
        node = _get_node_by_var(by_var, provides)
        provided_list = node.setdefault(".", [])
        provided_list.append(question)


question_bank_context: ContextVar[Optional[QuestionBank]] = ContextVar(
    "question_bank_context", default=None
)
"""Question bank context."""
