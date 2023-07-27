"""Number field."""
from typing import Any, Literal, Optional

import attr
from attrs import frozen, validators
from oes.interview_old.config.field import AskField, FieldBase
from oes.interview_old.parsing.location import Location
from oes.template import Template


@frozen
class NumberAskField(AskField):
    """AskField for a number field."""

    type: Literal["number"] = "number"
    optional: bool = False
    default: Optional[float] = None
    label: Optional[str] = None

    require_value: Optional[float] = None
    require_value_message: Optional[str] = None

    min: Optional[float] = None
    """The minimum value."""

    max: Optional[float] = None
    """The maximum value."""

    integer: bool = False
    """Whether only integers are accepted."""

    input_mode: Optional[str] = None
    """The HTML input mode for this field."""

    autocomplete: Optional[str] = None
    """The autocomplete type for this field's input."""


@frozen
class NumberField(FieldBase):
    """Number field."""

    type: Literal["number"] = "number"
    set: Optional[Location] = None
    optional: bool = False
    default: Optional[float] = None
    label: Optional[Template] = None

    min: Optional[float] = None
    """The minimum value."""

    max: Optional[float] = None
    """The maximum value."""

    integer: bool = False
    """Whether only integers are accepted."""

    input_mode: Optional[str] = None
    """The HTML input mode for this field."""

    autocomplete: Optional[str] = None
    """The autocomplete type for this field's input."""

    require_value: Optional[float] = None
    require_value_message: Optional[str] = None

    def get_python_type(self) -> object:
        return int if self.integer else float

    def get_ask_field(self, context: dict[str, Any]) -> NumberAskField:
        return NumberAskField(
            type=self.type,
            optional=self.optional,
            default=self.default,
            label=self.label.render(**context) if self.label else None,
            min=self.min,
            max=self.max,
            integer=self.integer,
            input_mode=self.input_mode,
            autocomplete=self.autocomplete,
            require_value=self.require_value,
            require_value_message=self.require_value_message,
        )

    def get_field_info(self) -> Any:
        v = []

        if self.min is not None:
            v.append(validators.ge(self.min))

        if self.max is not None:
            v.append(validators.le(self.max))

        return attr.ib(
            type=self.get_optional_type(),
            validator=[
                self.validate_required,
                validators.optional(v),
            ],
        )
