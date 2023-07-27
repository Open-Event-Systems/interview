"""Type declarations."""
from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union

from oes.template import Context, Evaluable, ValueOrEvaluable
from typing_extensions import Protocol, TypeAlias

if TYPE_CHECKING:
    from attrs import Attribute

MutableContext: TypeAlias = MutableMapping[str, Any]
"""Mutable :class:`Context`."""


class Locator(Evaluable, Protocol):
    """A variable locator."""

    @abstractmethod
    def evaluate(self, __context: Context) -> object:
        """Return the value of this locator."""
        ...

    @abstractmethod
    def set(self, __value: object, __context: MutableContext):
        """Set the value at this locator."""
        ...

    @abstractmethod
    def compare(self, __other: Locator, __context: Context) -> bool:
        """Whether two locators are equal."""
        ...


UserResponse: TypeAlias = Mapping[str, object]
"""A user response."""

ResponseParser: TypeAlias = Callable[[UserResponse], Mapping[Locator, object]]
"""A callable that parses a response into a mapping of variable locations/values."""

T = TypeVar("T")

IDENTIFIER_PATTERN = r"^(?![0-9_-])[a-zA-Z0-9_-]+(?<!-)$"
"""Valid identifier pattern."""


class Field(Protocol):
    """A user input field.

    Provides a JSON schema, an :func:`attr.ib` field for parsing/validating the
    input, and where to store the value.
    """

    @property
    @abstractmethod
    def field_info(self) -> Any:
        """The :func:`attr.ib` object for this field."""
        ...

    @abstractmethod
    def get_schema(self, __context: Context) -> Mapping[str, object]:
        """Get the JSON schema representing this field.

        Args:
            context: The context for rendering templates.
        """
        ...

    @property
    @abstractmethod
    def set(self) -> Optional[Locator]:
        """The variable location to set."""
        ...


class FieldWithType(Field, Protocol):
    """A field with a ``type`` attribute."""

    @property
    @abstractmethod
    def type(self) -> str:
        """The field type."""
        ...


class Option(Protocol):
    """A select option."""

    @property
    @abstractmethod
    def id(self) -> Optional[str]:
        """The option ID."""
        ...

    @property
    @abstractmethod
    def value(self) -> Any:
        """The option value."""
        ...

    def get_schema(
        self, __context: Context, *, id: Optional[str] = None
    ) -> Mapping[str, object]:
        """Get the JSON schema for this option."""

        if id is None and self.id is None:
            raise ValueError("An ID must be provided")

        schema = {
            "const": id or self.id,
        }
        return schema


class FieldWithOptions(Field, Protocol):
    """A field with multiple options."""

    @property
    @abstractmethod
    def options(self) -> Sequence[Option]:
        """The options."""
        ...


class Whenable(Protocol):
    """An object with a ``when`` condition."""

    @property
    def when(self) -> Union[Sequence[ValueOrEvaluable], ValueOrEvaluable]:
        """The ``when`` condition."""
        return ()


def validate_identifier(instance: object, attribute: Attribute, value: object):
    """Raise :class:`ValueError` if the object is not a valid identifier."""
    if not isinstance(value, str) or not re.match(IDENTIFIER_PATTERN, value, re.I):
        raise ValueError(f"Invalid identifier: {value}")
