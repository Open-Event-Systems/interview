"""Question tests."""
import copy

import pytest
from cattrs import BaseValidationError
from oes.interview_old.config.field import (
    build_class_from_fields,
    parse_response_values,
)
from oes.interview_old.config.fields.number import NumberField
from oes.interview_old.config.fields.text import TextField
from oes.interview_old.config.question import Question
from oes.interview_old.parsing.location import Location
from oes.interview_old.serialization import converter

text1 = TextField(
    type="text",
    min=2,
    max=4,
    set=Location.parse("text1"),
)


def test_question_template():
    q = converter.structure(
        {
            "id": "q1",
            "title": "Title {{ title }}",
            "description": "Description {{ description }}",
        },
        Question,
    )

    context = {
        "title": "Test",
        "description": "desc",
    }

    assert q.title.render(**context) == "Title Test"
    assert q.description.render(**context) == "Description desc"


def test_question_copy():
    q = converter.structure(
        {
            "id": "q1",
            "title": "Title {{ title }}",
            "description": "Description {{ description }}",
        },
        Question,
    )
    q2 = copy.deepcopy(q)
    assert q2.title == q.title


def test_build_class():
    class_ = build_class_from_fields("test1", [text1])

    valid = {
        "field_0": "test",
    }

    res1 = parse_response_values(class_, valid)
    assert res1 == {"field_0": "test"}


def test_build_class_validation():
    class_ = build_class_from_fields("test1", [text1])

    with pytest.raises(BaseValidationError):
        parse_response_values(class_, {"text1": "x"})

    with pytest.raises(BaseValidationError):
        parse_response_values(class_, {"text1": "12345"})


def test_provides():
    q1 = converter.structure(
        {
            "id": "q1",
            "fields": [
                {
                    "type": "text",
                    "set": "a.b",
                },
                {
                    "type": "number",
                    "set": "a.c",
                },
            ],
        },
        Question,
    )

    q2 = converter.structure(
        {
            "id": "q2",
            "fields": [
                {
                    "type": "number",
                    "set": "a.d",
                }
            ],
        },
        Question,
    )

    assert sorted(str(p) for p in q1.provides) == ["a.b", "a.c"]
    assert sorted(str(p) for p in q2.provides) == ["a.d"]


def test_parse_fields():
    q = converter.structure(
        {
            "id": "q1",
            "fields": [
                {
                    "type": "text",
                    "set": "a.b",
                },
                {
                    "type": "number",
                    "set": "a.c",
                },
            ],
        },
        Question,
    )

    assert isinstance(q.fields[0], TextField)
    assert isinstance(q.fields[1], NumberField)


def test_parse_fields_error():
    with pytest.raises(BaseValidationError):
        converter.structure(
            {
                "id": "q1",
                "fields": [
                    {
                        "type": "text",
                        "set": "a.b",
                    },
                    {
                        "type": "-unknown-",
                        "set": "a.c",
                    },
                ],
            },
            Question,
        )


def test_parse_response():
    q = converter.structure(
        {
            "id": "q1",
            "fields": [
                {"type": "text", "set": "a"},
                {
                    "type": "text",
                    "set": "b",
                },
            ],
        },
        Question,
    )

    parsed = q.parse_response(
        {
            "field_0": "a",
            "field_1": "b",
        },
    )

    assert parsed == {
        Location.parse("a"): "a",
        Location.parse("b"): "b",
    }


def test_parse_response_button():
    q = converter.structure(
        {
            "id": "q1",
            "fields": [{"type": "text", "set": "a"}],
            "buttons": [
                {
                    "label": "Button1",
                    "value": 1,
                },
                {
                    "label": "Button2",
                    "value": 2,
                },
            ],
            "buttons_set": "b",
        },
        Question,
    )

    parsed = q.parse_response(
        {
            "field_0": "a",
        },
        1,
    )

    assert parsed == {Location.parse("a"): "a", Location.parse("b"): 2}


def test_parse_response_error():
    q = converter.structure(
        {"id": "q1", "fields": [{"type": "text", "set": "a"}]}, Question
    )

    with pytest.raises(BaseValidationError):
        q.parse_response(
            {
                "field_0": "",
            },
        )


def test_parse_response_error_button_missing():
    q = converter.structure(
        {
            "id": "q1",
            "fields": [{"type": "text", "set": "a"}],
            "buttons": [{"label": "Button1", "value": 1}],
            "buttons_set": "b",
        },
        Question,
    )

    with pytest.raises(ValueError):
        q.parse_response(
            {
                "field_0": "a",
            },
        )


def test_parse_response_error_button_value():
    q = converter.structure(
        {
            "id": "q1",
            "fields": [{"type": "text", "set": "a"}],
            "buttons": [{"label": "Button1", "value": 1}],
            "buttons_set": "b",
        },
        Question,
    )

    with pytest.raises(ValueError):
        q.parse_response(
            {
                "field_0": "a",
            },
            2,
        )
