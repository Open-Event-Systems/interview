import pytest
from cattrs import ClassValidationError
from oes.interview_old.config.field import (
    build_class_from_fields,
    parse_response_values,
)
from oes.interview_old.config.fields.bool import BoolField


@pytest.mark.parametrize(
    "val, expected",
    [
        (None, None),
        (False, False),
        (True, True),
    ],
)
def test_parse_bool(val, expected):
    field = BoolField(
        type="bool",
        optional=True,
    )
    class_ = build_class_from_fields("test", [field])
    res = parse_response_values(class_, {"field_0": val})
    assert res == {"field_0": expected}


@pytest.mark.parametrize("val", [0, 1, None, "false", "true", "", []])
def test_parse_bool_invalid(val):
    field = BoolField(
        type="bool",
    )
    class_ = build_class_from_fields("test", [field])
    with pytest.raises(ClassValidationError):
        parse_response_values(class_, {"field_0": val})
