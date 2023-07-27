"""Boolean field."""
from typing import Any, Literal, Optional

import attr
from attrs import frozen
from oes.interview_old.config.field import AskField, FieldBase
from oes.interview_old.parsing.location import Location
from oes.template import Template


@frozen
class BoolAskField(AskField):
    """Boolean :class:`AskField`."""

    type: Literal["bool"] = "bool"
    optional: bool = False
    default: Optional[bool] = None
    label: Optional[str] = None
    require_value: Optional[bool] = None
    require_value_message: Optional[str] = None


@frozen
class BoolField(FieldBase):
    """Boolean field."""

    type: Literal["bool"] = "bool"
    set: Optional[Location] = None
    optional: bool = False
    default: Optional[bool] = None
    label: Optional[Template] = None
    require_value: Optional[bool] = None
    require_value_message: Optional[str] = None

    def get_python_type(self) -> object:
        return bool

    def get_field_info(self) -> Any:
        return attr.ib(
            type=self.get_optional_type(),
            validator=[
                self.validate_required,
            ],
        )

    def get_ask_field(self, context: dict[str, Any]) -> AskField:
        return BoolAskField(
            type="bool",
            optional=self.optional,
            default=self.default,
            label=self.label.render(**context) if self.label else None,
            require_value=self.require_value,
            require_value_message=self.require_value_message,
        )
