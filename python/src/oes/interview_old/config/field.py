"""Field types."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Optional, Type, TypeVar

import importlib_metadata
from attrs import frozen, make_class
from cattrs import Converter
from loguru import logger

if TYPE_CHECKING:
    from oes.interview_old.parsing.location import Location
    from oes.template import Template

DEFAULT_MAX_FIELD_LENGTH = 300
"""Default max length of a text field."""

ENTRY_POINT_GROUP = "oes.interview_old.field"
"""The group for entry points."""

T = TypeVar("T")


class AskField(ABC):
    """A field in a :class:`AskResult`."""

    @property
    @abstractmethod
    def type(self) -> str:
        """The field type."""
        ...

    @property
    @abstractmethod
    def optional(self) -> bool:
        """Whether ``None`` is permitted."""
        ...

    @property
    @abstractmethod
    def default(self) -> Any:
        """The default value (used by frontends)."""
        ...

    @property
    @abstractmethod
    def label(self) -> Optional[str]:
        """The default value (used by frontends)."""
        ...

    @property
    @abstractmethod
    def require_value(self) -> Optional[Any]:
        """Require a specific value."""
        ...

    @property
    @abstractmethod
    def require_value_message(self) -> Optional[str]:
        """A specific error message for the required value."""
        ...


@frozen
class _BaseAskField(AskField):
    type: str
    optional: bool = False
    default: Any = None
    label: Optional[str] = None
    require_value: Optional[Any] = None
    require_value_message: Optional[str] = None


class AbstractField(ABC):
    """Abstract field type class."""

    @property
    @abstractmethod
    def type(self) -> str:
        ...

    """The field type."""

    @property
    @abstractmethod
    def set(self) -> Optional[Location]:
        """The value to set."""
        ...

    @property
    @abstractmethod
    def optional(self) -> bool:
        """Whether ``None`` is permitted."""
        ...

    @property
    @abstractmethod
    def default(self) -> Any:
        """The default value (used by frontends)."""
        ...

    @property
    @abstractmethod
    def label(self) -> Optional[Template]:
        """The field label."""
        ...

    @property
    @abstractmethod
    def require_value(self) -> Optional[Any]:
        """A specific required value."""
        ...

    @property
    @abstractmethod
    def require_value_message(self) -> Optional[str]:
        """A specific error message for the required value."""
        ...

    @abstractmethod
    def get_field_info(self) -> Any:
        """Get the :func:`attr.ib` result for this field."""
        ...

    @classmethod
    @abstractmethod
    def parse(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance of this class from a dictionary."""
        ...

    @abstractmethod
    def get_ask_field(self, context: dict[str, Any]) -> AskField:
        """Get a :class:`AskField` instance to show to the client."""
        ...


class FieldBase(AbstractField, ABC):
    """Base field model."""

    @classmethod
    def parse(cls: Type[T], data: dict[str, Any]) -> T:
        from oes.interview_old.serialization import converter

        return converter.structure(data, cls)

    @abstractmethod
    def get_python_type(self) -> object:
        ...

    def get_optional_type(self) -> object:
        if self.optional:
            return Optional[self.get_python_type()]
        else:
            return self.get_python_type()

    def validate_required(self, i, a, v):
        """Re-usable validator for checking for required values."""
        if not self.optional and v is None:
            raise ValueError(f"{a.name}: a value is required")
        if v is not None and self.require_value is not None and v != self.require_value:
            raise ValueError(f"{a.name}: {self.require_value_message or 'Required'}")


def get_field_name(idx: int, field: AbstractField) -> str:
    """Get the name for a field."""
    return f"field_{idx}"


def load_fields() -> dict[str, Type[AbstractField]]:
    """Load field types."""
    modules: dict[str, str] = {}
    mapping: dict[str, Type[AbstractField]] = {}

    eps = importlib_metadata.entry_points().select(group=ENTRY_POINT_GROUP)
    for ep in eps:
        if ep.name in mapping:
            logger.warning(
                f"Duplicate field type {ep.name!r} defined in {ep.module} "
                f"(previously defined in {modules[ep.name]})"
            )
        mapping[ep.name] = ep.load()
        modules[ep.name] = ep.module

    return mapping


def get_field_class_by_type(type_: str) -> Type[AbstractField]:
    """Get a :class:`AbstractField` type by its ``type`` value."""
    fields = load_fields()
    try:
        return fields[type_]
    except KeyError as e:
        raise LookupError(f"Field type not found: {type_!r}") from e


def _safe_name(name: str) -> str:
    """Replace invalid characters for a class name."""
    safe_name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    return safe_name


def build_class_from_fields(name: str, fields: Iterable[AbstractField]) -> Type:
    """Create a class for the given fields."""

    attr_map: dict[str, Any] = {}

    for i, field in enumerate(fields):
        field_name = get_field_name(i, field)
        field_config = field.get_field_info()
        attr_map[field_name] = field_config

    class_ = make_class(_safe_name(name), attr_map)
    return class_


def parse_response_values(class_: T, responses: dict[str, Any]) -> dict[str, Any]:
    """Parse response values for a class.

    Raises:
        cattrs.BaseValidationError: If the response is invalid.
    """
    from oes.interview_old.serialization import converter

    obj = converter.structure(responses, class_)
    return converter.unstructure(obj)


def parse_field(converter: Converter, v):
    if not isinstance(v, dict) or "type" not in v:
        raise TypeError(f"Invalid field: {v}")

    cls = get_field_class_by_type(v["type"])
    return converter.structure(v, cls)
