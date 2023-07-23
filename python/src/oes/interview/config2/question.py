"""Question module."""
from collections.abc import Mapping, Sequence
from typing import Optional

from attrs import field, frozen
from oes.interview.config2.types import Context, Field, Whenable
from oes.interview.config.field import AbstractField
from oes.interview.parsing.types import validate_identifier
from oes.template import Template


@frozen
class Question(Whenable):
    """A question object."""

    id: str = field(validator=validate_identifier)
    """The question ID."""

    title: Optional[Template] = None
    """The question title."""

    description: Optional[Template] = None
    """The question description."""

    fields: Sequence[AbstractField] = ()
    """Fields in the question."""


def get_question_schema(
    title: Optional[Template],
    description: Optional[Template],
    fields: Mapping[str, Field],
    context: Context,
) -> Mapping[str, object]:
    """Create an OpenAPI schema for a question.

    Args:
        title: The question title.
        description: The question description.
        fields: The fields.
        context: The context to use to render templates.
    """
    schema = {
        "type": "object",
        "properties": {nm: field.get_schema(context) for nm, field in fields.items()},
        "required": [nm for nm, field in fields.items() if not field.optional],
    }

    if title:
        schema["title"] = title.render(**context)

    if description:
        schema["description"] = description.render(**context)

    return schema
