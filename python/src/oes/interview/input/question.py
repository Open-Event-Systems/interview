"""Question module."""
from collections.abc import Mapping, Sequence
from typing import Optional, Union

from attrs import field, frozen
from oes.interview.input.types import Context, Field, Whenable, validate_identifier
from oes.template import Template, ValueOrEvaluable


@frozen
class Question(Whenable):
    """A question object."""

    id: str = field(validator=validate_identifier)
    """The question ID."""

    title: Optional[Template] = None
    """The question title."""

    description: Optional[Template] = None
    """The question description."""

    fields: Sequence[Field] = ()
    """Fields in the question."""

    when: Union[ValueOrEvaluable, Sequence[ValueOrEvaluable]] = ()
    """``when`` conditions"""


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
        schema["title"] = title.render(context)

    if description:
        schema["description"] = description.render(context)

    return schema
