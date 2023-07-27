"""Email field."""
from typing import Any, Literal, Optional

import attr
from attrs import frozen, validators
from attrs.converters import pipe
from email_validator import EmailNotValidError, validate_email
from oes.interview_old.config.field import AskField, FieldBase
from oes.interview_old.parsing.location import Location
from oes.template import Template
from publicsuffixlist import PublicSuffixList

_psl = PublicSuffixList()


@frozen
class EmailAskField(AskField):
    """:class:`AskField` for an email field."""

    type: Literal["email"] = "email"
    optional: bool = False
    default: Optional[str] = None
    label: Optional[str] = None
    require_value: Optional[str] = None
    require_value_message: Optional[str] = None


@frozen
class EmailField(FieldBase):
    """Email field."""

    type: Literal["email"] = "email"
    set: Optional[Location] = None
    optional: bool = False
    default: Optional[str] = None
    label: Optional[Template] = None
    require_value: Optional[str] = None
    require_value_message: Optional[str] = None

    def get_python_type(self) -> object:
        return str

    def get_ask_field(self, context: dict[str, Any]) -> EmailAskField:
        return EmailAskField(
            type=self.type,
            optional=self.optional,
            default=self.default,
            label=self.label.render(**context) if self.label else None,
            require_value=self.require_value,
            require_value_message=self.require_value_message,
        )

    def get_field_info(self) -> Any:
        return attr.ib(
            type=self.get_optional_type(),
            converter=pipe(_strip, _coerce_none),
            validator=[
                self.validate_required,
                validators.optional(
                    [
                        _validate_email,
                        _validate_email_domain,
                    ]
                ),
            ],
        )


def _strip(v: Optional[str]) -> Optional[str]:
    return v.strip() if isinstance(v, str) else v


def _coerce_none(v: Optional[str]) -> Optional[str]:
    return v if v else None


def _validate_email(i, a, v):
    try:
        validate_email(v, check_deliverability=False)
    except EmailNotValidError as e:
        raise ValueError(f"{a.name}: Invalid email: {v}") from e


def _validate_email_domain(i, a, v):
    """Validate that an email's domain exists.

    Warning:
        This is not a good idea and generally shouldn't be done, but some services
        (e.g. Square) perform this kind of validation and will reject requests
        involving emails with unknown public suffixes. By then, the user is already
        many steps past when they entered their email, and it would be bad UX to make
        them start over to correct it.
    """
    _, _, domain = v.rpartition("@")
    suffix = _psl.publicsuffix(domain, accept_unknown=False)
    if suffix is None:
        raise ValueError(f"{a.name}: Invalid email: {v}")
