import pytest
from cattrs import ClassValidationError
from cattrs.preconf.json import make_converter
from oes.interview.input.field_types.text import TextField
from oes.interview.input.response import create_response_parser
from oes.interview.variables.locator import parse_locator
from oes.template import Template

field1 = TextField(
    set=parse_locator("value"),
    label=Template("{{ name }}"),
    default="default",
    min=2,
    max=4,
    regex="[a-f]+",
    regex_js="^[a-f]+$",
)

field2 = TextField(
    set=parse_locator("value"),
    label=Template("{{ name }}"),
    default="default",
    optional=True,
    min=2,
    max=4,
    regex="[a-f]+",
    regex_js="^[a-f]+$",
)

converter = make_converter()


def test_text_field_schema():
    schema = field1.get_schema({"name": "name"})

    assert schema == {
        "type": "string",
        "x-type": "text",
        "minLength": 2,
        "maxLength": 4,
        "pattern": "^[a-f]+$",
        "default": "default",
        "title": "name",
    }


def test_text_field_schema_optional():
    schema = field2.get_schema({"name": "name"})

    assert schema == {
        "type": ["string", "null"],
        "x-type": "text",
        "minLength": 2,
        "maxLength": 4,
        "pattern": "^[a-f]+$",
        "default": "default",
        "title": "name",
    }


@pytest.mark.parametrize(
    "val, expected",
    (
        ("ab", "ab"),
        ("abcd", "abcd"),
        (" abcd ", "abcd"),
        (None, None),
        ("", None),
        (" ", None),
    ),
)
def test_text_field_parse(val, expected):
    parser = create_response_parser("test", [field2], converter)

    result = parser({"field_0": val})
    assert result == {parse_locator("value"): expected}


@pytest.mark.parametrize(
    "val",
    (
        None,
        "",
        "  ",
        "asdf",
        123,
        True,
        ["ab"],
    ),
)
def test_text_field_parse_error(val):
    parser = create_response_parser("test", [field1], converter)

    with pytest.raises(ClassValidationError):
        parser({"field_0": val})
