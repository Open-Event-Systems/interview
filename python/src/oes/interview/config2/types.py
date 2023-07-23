"""Type declarations."""
from abc import abstractmethod
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import Any, Optional, TypeVar, Union

from oes.template import Template
from openapi3.schemas import Schema
from typing_extensions import Protocol, TypeAlias, runtime_checkable

Context: TypeAlias = MutableMapping[str, object]
"""A template rendering context."""


class Locator(Protocol):
    """A variable locator."""

    @abstractmethod
    def evaluate(self, context: Context) -> object:
        """Return the value of this locator."""
        ...

    @abstractmethod
    def set(self, context: Context, value: object):
        """Set the value at this locator."""
        ...


UserResponse: TypeAlias = Mapping[str, object]
"""A user response."""

ResponseParser: TypeAlias = Callable[[UserResponse], Mapping[Locator, object]]
"""A callable that parses a response into a  mapping of variable locations/values."""

T = TypeVar("T")


class Parseable(Protocol):
    """A user input field that can be parsed."""

    @property
    @abstractmethod
    def field_info(self) -> Any:
        """The :func:`attr.ib` object for this field."""
        ...

    @property
    @abstractmethod
    def set(self) -> Optional[Locator]:
        """The variable location to set."""
        ...


class Field(Parseable, Protocol):
    """An input field."""

    @property
    @abstractmethod
    def type(self) -> str:
        """The field type."""
        ...

    @abstractmethod
    def get_schema(self, context: Context) -> Union[Schema, Mapping[str, object]]:
        """Get the OpenAPI 3 schema representing this field.

        Args:
            context: The context for rendering templates.
        """
        ...

    @property
    @abstractmethod
    def label(self) -> Optional[Union[Template, str]]:
        """A label for the field."""
        ...

    @property
    @abstractmethod
    def default(self) -> Optional[object]:
        """A default value.

        Only used for displaying in the client, not used for parsing.
        """
        ...

    @property
    @abstractmethod
    def optional(self) -> bool:
        """Whether the field is optional."""
        ...

    @property
    @abstractmethod
    def error_messages(self) -> Optional[Mapping[str, str]]:
        """Optional overrides to error messages."""
        ...


@runtime_checkable
class Evaluable(Protocol):
    """An object that can be evaluated."""

    @abstractmethod
    def evaluate(self, context: Context) -> object:
        """Evaluate this evaluable."""
        ...


class Value(Protocol):
    """Literal value type."""

    pass


Expression: TypeAlias = Union[Evaluable, Value]
"""A literal value or an evaluable."""


class Whenable(Protocol):
    """An object with a ``when`` condition."""

    @property
    def when(self) -> Union[Sequence[Expression], Expression]:
        """The ``when`` condition."""
        return ()
