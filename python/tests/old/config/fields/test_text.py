import pytest
from cattrs import BaseValidationError
from oes.interview_old.config.field import (
    build_class_from_fields,
    parse_response_values,
)
from oes.interview_old.config.fields.text import TextField
from oes.interview_old.parsing.location import Location


def test_strip_strings():
    field = TextField(type="text", set=Location.parse("text"))

    class_ = build_class_from_fields("test", [field])
    res = parse_response_values(class_, {"field_0": "white space\t"})
    assert res == {"field_0": "white space"}


def test_coerce_none():
    field = TextField(
        type="text",
        set=Location.parse("text"),
        optional=True,
    )
    class_ = build_class_from_fields("test", [field])
    res = parse_response_values(class_, {"field_0": ""})
    assert res == {"field_0": None}


def test_coerce_white_space_none():
    field = TextField(
        type="text",
        set=Location.parse("text"),
        optional=True,
    )
    class_ = build_class_from_fields("test", [field])
    res = parse_response_values(class_, {"field_0": "  "})
    assert res == {"field_0": None}


def test_validate_regex():
    field = TextField(
        type="text",
        set=Location.parse("regextest"),
        regex=r"^[a-d]+$",
        regex_js="^a+$",
    )

    class_ = build_class_from_fields("test", [field])
    res = parse_response_values(class_, {"field_0": "abcd"})
    assert res == {"field_0": "abcd"}


def test_validate_regex_invalid():
    field = TextField(
        type="text",
        set=Location.parse("regextest"),
        regex=r"^[a-d]+$",
        regex_js="^a+$",
    )

    class_ = build_class_from_fields("test", [field])

    with pytest.raises(BaseValidationError):
        parse_response_values(class_, {"field_0": "abce"})


def test_parse_path():
    field = TextField.parse(
        {
            "type": "text",
            "set": "a.b[c]",
        }
    )

    assert isinstance(field.set, Location)
    assert str(field.set) == "a.b[c]"
