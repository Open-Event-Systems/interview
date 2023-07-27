"""Date field."""
from datetime import date
from typing import Any, Literal, Optional, Union

import attr
from attrs import frozen, validators
from oes.interview_old.config.field import AskField, FieldBase
from oes.interview_old.parsing.location import Location
from oes.template import Template


@frozen
class DateAskField(AskField):
    """An :class:`AskField` for a date."""

    type: Literal["date"] = "date"
    optional: bool = False
    default: Any = None
    label: Optional[str] = None
    min: Optional[date] = None
    max: Optional[date] = None
    require_value: Optional[date] = None
    require_value_message: Optional[str] = None


@frozen
class DateField(FieldBase):
    """A date field."""

    type: Literal["date"] = "date"
    set: Optional[Location] = None
    optional: bool = False

    default: Optional[Union[date, Literal["today"]]] = None
    """A default value, or ``"today"`` to use the current date."""

    label: Optional[Template] = None

    require_value: Optional[date] = None
    require_value_message: Optional[str] = None

    min: Optional[Union[date, Literal["today"]]] = None
    """A minimum value, or ``"today"`` to use the current date."""

    max: Optional[Union[date, Literal["today"]]] = None
    """A maximum value, or ``"today"`` to use the current date."""

    def get_python_type(self) -> object:
        return date

    def _get_date(self, val: Optional[Union[date, Literal["today"]]]) -> Optional[date]:
        if val is None:
            return None
        elif val == "today":
            return date.today()
        else:
            return val

    def _validate_min(self, i, a, v):
        min_ = self._get_date(self.min)
        if min_ is not None and v < min_:
            raise ValueError(f"{a.name}: must be on or after {min_}")

    def _validate_max(self, i, a, v):
        max_ = self._get_date(self.max)
        if max_ is not None and v > max_:
            raise ValueError(f"{a.name}: must be on or before {max_}")

    def get_field_info(self) -> Any:
        return attr.ib(
            type=self.get_optional_type(),
            validator=[
                self.validate_required,
                validators.optional(
                    [
                        validators.instance_of(date),
                        self._validate_min,
                        self._validate_max,
                    ]
                ),
            ],
        )

    def get_ask_field(self, context: dict[str, Any]) -> AskField:
        return DateAskField(
            type="date",
            optional=self.optional,
            default=self._get_date(self.default),
            label=self.label.render(**context) if self.label else None,
            min=self._get_date(self.min),
            max=self._get_date(self.max),
            require_value=self.require_value,
            require_value_message=self.require_value_message,
        )
