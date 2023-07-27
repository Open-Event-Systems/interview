"""Question module."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional, Type, TypeVar, Union

from attrs import Factory
from attrs import field as attr_field
from attrs import frozen
from oes.interview_old.config.field import (
    AbstractField,
    AskField,
    build_class_from_fields,
    get_field_name,
    parse_response_values,
)
from oes.interview_old.parsing.location import Location
from oes.interview_old.parsing.types import Whenable
from oes.template import Condition, Template

T = TypeVar("T")


@frozen
class Button:
    """A button."""

    label: Template
    """The button label."""

    value: Any = None
    """The button value."""

    primary: bool = True
    """Whether this should have the "primary" style."""

    default: bool = True
    """Whether this is the "default" button."""


def _build_class(question):
    return build_class_from_fields(question.id, question.fields)


def _build_provides(question):
    return frozenset(f.set for f in question.fields if f.set is not None)


@frozen
class Question(Whenable):
    """A question."""

    id: str
    title: Optional[Template] = None
    description: Optional[Template] = None
    fields: Sequence[AbstractField] = ()
    buttons: Optional[Sequence[Button]] = None
    buttons_set: Optional[Location] = None

    when: Condition = ()

    _response_class: Type = attr_field(
        init=False, eq=False, default=Factory(_build_class, takes_self=True)
    )
    """The model for the fields."""

    _provides: frozenset[Location] = attr_field(
        init=False, eq=False, default=Factory(_build_provides, takes_self=True)
    )
    """Set of provided variables."""

    @property
    def provides(self) -> frozenset[Location]:
        """The set of provided variables."""
        return self._provides

    @property
    def response_class(self) -> Type:
        """The question response class."""
        return self._response_class

    def get_ask_fields(self, context: dict[str, Any]) -> dict[str, AskField]:
        """Get :class:`AskField` instances for fields in this question."""
        return {
            get_field_name(i, field): field.get_ask_field(context)
            for i, field in enumerate(self.fields)
        }

    def parse_response_fields(self, responses: dict[str, Any]) -> dict[Location, Any]:
        """Parse/validate submitted response fields.

        Args:
            responses: The raw responses, as a dict.

        Returns:
            A ``dict`` of the :class:`Expression` to set and the value to set.

        Raises:
            cattrs.BaseValidationError: If the responses are invalid.
        """
        by_path = {}
        parsed = parse_response_values(self._response_class, responses)

        for i, field in enumerate(self.fields):
            name = get_field_name(i, field)
            path = field.set
            value = parsed[name]

            if path is not None:
                by_path[path] = value

        return by_path

    def parse_button_value(
        self, button_id: Optional[int]
    ) -> Union[tuple[Location, Any], tuple[None, None]]:
        """Parse a submitted button ID.

        Args:
            button_id: The button ID.

        Returns:
            A pair of the expression to set, and the value.
        """
        if button_id is None:
            if self.buttons is not None:
                raise ValueError("Button value required")
            else:
                return None, None
        else:
            if self.buttons is None:
                return None, None

        try:
            button = self.buttons[button_id]
        except LookupError:
            raise ValueError("Invalid button value")

        if self.buttons_set is not None:
            return self.buttons_set, button.value
        else:
            return None, None

    def parse_response(
        self, responses: Optional[dict[str, Any]] = None, button: Optional[int] = None
    ) -> dict[Location, Any]:
        """Parse a :class:`QuestionResponse` and return the paths/values.

        Args:
            body: The submitted response body.

        Returns:
            A mapping of the :class:`Path` instances and the values to set.

        Raises:
            BaseValidationError: If the response is invalid.
        """
        result = {}

        result.update(self.parse_response_fields(responses or {}))

        button_path, button_value = self.parse_button_value(button)

        if button_path is not None:
            result[button_path] = button_value

        return result
