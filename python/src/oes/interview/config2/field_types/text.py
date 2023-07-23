"""Text field type."""
from typing import Any, Literal, Mapping, Optional

import attr
from attrs import converters, frozen, validators
from oes.interview.config2.field import BaseField, validate_optional
from oes.interview.config2.types import Context

DEFAULT_MAX_LEN = 300
"""The default string max length."""


@frozen(kw_only=True)
class TextField(BaseField):
    """A text field."""

    type: Literal["text"] = "text"
    default: Optional[str] = None
    min: int = 0
    """The minimum length."""

    max: int = DEFAULT_MAX_LEN
    """The maximum length."""

    regex: Optional[str] = None
    """A regex that the value must match."""

    regex_js: Optional[str] = None
    """A JS-compatible regex used for validation at the client side."""

    input_mode: Optional[str] = None
    """The HTML input mode for this field."""

    autocomplete: Optional[str] = None
    """The autocomplete type for this field's input."""

    @property
    def value_type(self) -> object:
        return str

    @property
    def field_info(self) -> Any:
        validators_ = []

        if self.regex is not None:
            validators_.append(validators.matches_re(self.regex))

        return attr.ib(
            type=self.optional_type,
            converter=converters.pipe(
                _strip_strings,
                _coerce_null,
            ),
            validator=[
                validate_optional(self.optional),
                validators.optional(
                    [
                        validators.instance_of(str),
                        validators.min_len(self.min),
                        validators.max_len(self.max),
                        *validators_,
                    ]  # type: ignore
                ),
            ],
        )

    def get_schema(self, context: Context) -> Mapping[str, object]:
        schema = {
            "type": ["string", "null"] if self.optional else "string",
            "minLength": self.min,
            "maxLength": self.max,
        }

        if self.label:
            schema["title"] = self.label.render(**context)

        if self.default:
            schema["default"] = self.default

        re_val = self.regex_js or self.regex
        if re_val:
            schema["pattern"] = re_val

        return schema


def _strip_strings(v):
    return v.strip() if isinstance(v, str) else v


def _coerce_null(v):
    return v if v else None
