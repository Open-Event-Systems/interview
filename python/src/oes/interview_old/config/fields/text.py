"""Text field."""
import re
from typing import Any, Literal, Optional

import attr
from attrs import field, frozen, validators
from attrs.converters import pipe
from oes.interview_old.config.field import DEFAULT_MAX_FIELD_LENGTH, AskField, FieldBase
from oes.interview_old.parsing.location import Location
from oes.template import Template


@frozen
class TextAskField(AskField):
    """AskField for a text field."""

    type: Literal["text"] = "text"
    optional: bool = False
    default: Optional[str] = None
    label: Optional[str] = None
    require_value: Optional[str] = None
    require_value_message: Optional[str] = None

    min: int = 0
    """Minimum length."""

    max: int = DEFAULT_MAX_FIELD_LENGTH
    """Maximum length."""

    input_mode: Optional[str] = None
    """The HTML input mode."""

    autocomplete: Optional[str] = None
    """The HTML autocomplete type."""

    regex: Optional[str] = None
    """A regex for client-side validation."""


def _validate_regex(instance, attr, value):
    if value is not None:
        re.compile(value)


def _strip_strings(value):
    return value.strip() if value is not None else None


def _coerce_none(value):
    return value if value else None


@frozen
class TextField(FieldBase):
    """Text field."""

    type: Literal["text"] = "text"
    set: Optional[Location] = None
    optional: bool = False
    default: Optional[str] = None
    label: Optional[Template] = None
    require_value: Optional[str] = None
    require_value_message: Optional[str] = None

    min: int = field(default=0, validator=[validators.ge(0)])
    """Minimum length."""

    max: int = field(default=DEFAULT_MAX_FIELD_LENGTH)
    """Maximum length."""

    regex: Optional[str] = field(default=None, validator=[_validate_regex])
    """A pattern the text must match."""

    regex_js: Optional[str] = None
    """A pattern the text must match.

    Used for validation in a client-side JS UI only.
    """

    input_mode: Optional[str] = None
    """The HTML input mode for this field."""

    autocomplete: Optional[str] = None
    """The autocomplete type for this field's input."""

    def get_python_type(self) -> object:
        return str

    def get_ask_field(self, context: dict[str, Any]) -> TextAskField:
        return TextAskField(
            type=self.type,
            optional=self.optional,
            default=self.default,
            label=self.label.render(**context) if self.label else None,
            min=self.min,
            max=self.max,
            input_mode=self.input_mode,
            autocomplete=self.autocomplete,
            regex=self.regex_js or self.regex or None,
            require_value=self.require_value,
            require_value_message=self.require_value_message,
        )

    def _check_regex(self, regex, instance, attribute, value):
        if regex is not None and not regex.match(value):
            raise ValueError(f"{attribute.name}: Invalid format")

    def get_field_info(self) -> Any:
        regex = re.compile(self.regex) if self.regex is not None else None

        return attr.ib(
            type=self.get_optional_type(),
            converter=pipe(_strip_strings, _coerce_none),
            validator=[
                self.validate_required,
                validators.optional(
                    [
                        validators.min_len(self.min),
                        validators.max_len(self.max),
                        lambda i, a, v: self._check_regex(regex, i, a, v),
                    ]
                ),
            ],
        )
