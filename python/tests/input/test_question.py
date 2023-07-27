from oes.interview.input.field_types.text import TextField
from oes.interview.input.question import get_question_schema
from oes.template import Template


def test_get_question_schema():
    schema = get_question_schema(
        Template("title"),
        Template("description"),
        fields={
            "field_0": TextField(min=2, max=10),
        },
        context={},
    )

    assert schema == {
        "type": "object",
        "title": "title",
        "description": "description",
        "properties": {
            "field_0": {
                "type": "string",
                "minLength": 2,
                "maxLength": 10,
                "x-type": "text",
            }
        },
        "required": ["field_0"],
    }
