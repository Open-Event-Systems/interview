import pytest
from cattrs import ClassValidationError
from oes.interview_old.config.field import (
    build_class_from_fields,
    parse_response_values,
)
from oes.interview_old.config.fields.email import EmailField
from oes.interview_old.parsing.location import Location


@pytest.mark.parametrize(
    "val, expected",
    [
        ("test@example.com", "test@example.com"),
        ("test@example.co.uk", "test@example.co.uk"),
        ("test+plus@example.com", "test+plus@example.com"),
        (None, None),
        ("", None),
        (" test@example.com ", "test@example.com"),
    ],
)
def test_parse(val, expected):
    field = EmailField(type="email", set=Location.parse("email"), optional=True)
    class_ = build_class_from_fields("test", [field])
    res = parse_response_values(class_, {"field_0": val})
    assert res == {"field_0": expected}


@pytest.mark.parametrize(
    "val",
    [
        "",
        None,
        "1",
        1,
        True,
        "invalid",
        "invalid@invalid",
        "in valid@example.com",
        "invalid@example.con",
    ],
)
def test_parse_invalid(val):
    field = EmailField(
        type="email",
        set=Location.parse("email"),
    )
    class_ = build_class_from_fields("test", [field])
    with pytest.raises(ClassValidationError):
        parse_response_values(class_, {"field_0": val})
