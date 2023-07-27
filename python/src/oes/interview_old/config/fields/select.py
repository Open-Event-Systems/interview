"""Select field."""
from collections.abc import Sequence
from enum import Enum
from typing import Any, List, Literal, Optional, Union

import attr
from attrs import frozen, validators
from oes.interview_old.config.field import AskField, FieldBase
from oes.interview_old.parsing.location import Location
from oes.template import Template


@frozen
class Option:
    """A :class:`SelectField` option."""

    value: Any
    label: Optional[Template] = None


class SelectComponentType(str, Enum):
    dropdown = "dropdown"
    checkbox = "checkbox"
    radio = "radio"


@frozen
class SelectAskField(AskField):
    """AskField for a select field."""

    type: Literal["select"] = "select"
    optional: bool = False
    default: Optional[Union[int, Sequence[int]]] = None
    label: Optional[str] = None

    require_value: Optional[Union[int, Sequence[int]]] = None
    require_value_message: Optional[str] = None

    component: SelectComponentType = SelectComponentType.dropdown
    """The select component type."""

    min: int = 1
    """The minimum number of items."""

    max: int = 1
    """The maximum number of items."""

    options: Sequence[str] = ()
    """The list of options."""

    input_mode: Optional[str] = None
    """The HTML input mode for this field."""

    autocomplete: Optional[str] = None
    """The autocomplete type for this field's input."""


@frozen
class SelectField(FieldBase):
    """Select field."""

    type: Literal["select"] = "select"
    set: Optional[Location] = None
    optional: bool = False
    default: Optional[Union[int, Sequence[int]]] = None
    label: Optional[Template] = None

    require_value: Optional[Union[int, Sequence[int]]] = None
    require_value_message: Optional[str] = None

    min: int = 1
    """The minimum number of items."""

    max: int = 1
    """The maximum number of items."""

    component: SelectComponentType = SelectComponentType.dropdown
    """The select component type."""

    input_mode: Optional[str] = None
    """The HTML input mode for this field."""

    autocomplete: Optional[str] = None
    """The autocomplete type for this field's input."""

    options: list[Option] = []
    """The options."""

    def get_ask_field(self, context: dict[str, Any]) -> SelectAskField:
        return SelectAskField(
            type=self.type,
            optional=self.optional,
            default=self.default,
            label=self.label.render(**context) if self.label else None,
            min=self.min,
            max=self.max,
            component=self.component,
            input_mode=self.input_mode,
            autocomplete=self.autocomplete,
            options=tuple(
                opt.label.render(**context) if opt.label else str(opt.value)
                for opt in self.options
            ),
            require_value=self.require_value,
            require_value_message=self.require_value_message,
        )

    def get_python_type(self) -> object:
        if self.max == 1:
            if self.min == 0:
                return Optional[int]
            else:
                return int
        else:
            return List[int]

    def _validate_size(self, instance, attribute, value):
        if self.max == 1 and value is None and self.min == 1:
            raise ValueError(f"{attribute.name}: A value is required")

        if self.max > 1 and len(value) < self.min:
            raise ValueError(f"{attribute.name}: At least {self.min} items required")

        if self.max > 1 and len(value) > self.max:
            raise ValueError(f"{attribute.name}: At most {self.max} items required")

    def _validate_required_value(self, i, a, v):
        # values/shape should already have been validated
        if self.require_value is not None and v is not None:
            expected = (
                self._transform_option_list(sorted(self.require_value))
                if isinstance(self.require_value, (list, tuple, set, frozenset))
                else self._transform_single_option(self.require_value)
            )
            given = v
            if expected != given:
                raise ValueError(
                    f"{a.name}: {self.require_value_message or 'Required'}"
                )

    def get_field_info(self) -> Any:
        return attr.ib(
            type=self.get_python_type(),
            converter=self.transform_options,
            validator=[
                validators.optional(
                    [
                        self._validate_size,
                        self._validate_required_value,
                    ]
                )
            ],
        )

    def option_to_value(self, option: Any) -> Any:
        """Get an option value by its index."""
        if not isinstance(option, int):
            raise ValueError(f"Not a valid option: {option}")

        try:
            option_entry = self.options[option]
        except IndexError:
            raise ValueError(f"Not a valid option: {option}")

        return option_entry.value

    def _transform_single_option(self, value: Any) -> Any:
        if value is None:
            return None
        else:
            return self.option_to_value(value)

    def _transform_option_list(self, value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            # sort values for consistent comparison
            transformed = [self.option_to_value(v) for v in sorted(value)]
            number_set = set(value)
            if len(number_set) != len(transformed):
                raise ValueError("Duplicate values not allowed")

            return transformed
        else:
            raise ValueError("Not a list")

    def transform_options(self, value: Any) -> Any:
        if self.max == 1:
            return self._transform_single_option(value)
        else:
            return self._transform_option_list(value)
