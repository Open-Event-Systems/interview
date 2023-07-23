"""Field module."""
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Mapping, Optional

import attr
from attrs import Attribute, frozen
from oes.interview.config2.types import Field, Locator
from oes.template import Template


@frozen(kw_only=True)
class BaseField(Field, ABC):
    """The field implementation base class."""

    set: Optional[Locator] = None
    optional: bool = False
    label: Optional[Template] = None
    error_messages: Optional[Mapping[str, str]] = None

    @property
    @abstractmethod
    def value_type(self) -> object:
        """The type of the value of this field."""
        ...

    @property
    def optional_type(self) -> object:
        """The :attr:`value_type` according to the :attr:`optional` value."""
        if self.optional:
            return Optional[self.value_type]
        else:
            return self.value_type

    @property
    def field_info(self) -> Any:
        """An attrs field info object."""

        return attr.ib(type=self.optional_type, default=self.default)


def validate_optional(
    optional: Optional[bool] = None,
) -> Callable[[object, Attribute, object], None]:
    """Get a validator to check for null values."""

    def validate(i: object, a: Attribute, v: object):
        if v is None and not optional:
            raise ValueError("A value is required")

    return validate
