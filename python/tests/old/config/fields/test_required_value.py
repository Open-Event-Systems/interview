from datetime import date

import pytest
from cattrs import ClassValidationError
from oes.interview_old.config.field import (
    build_class_from_fields,
    parse_response_values,
)
from oes.interview_old.config.fields.bool import BoolField
from oes.interview_old.config.fields.date import DateField
from oes.interview_old.config.fields.email import EmailField
from oes.interview_old.config.fields.number import NumberField
from oes.interview_old.config.fields.select import Option, SelectField
from oes.interview_old.config.fields.text import TextField


@pytest.mark.parametrize(
    "cls, required, value",
    [
        (BoolField, True, True),
        (BoolField, True, False),
        (BoolField, False, True),
        (BoolField, False, False),
        (DateField, date(2020, 7, 4), date(2020, 7, 4)),
        (DateField, date(2020, 7, 4), date(2020, 7, 5)),
        (EmailField, "test@example.com", "test@example.com"),
        (EmailField, "test@example.com", "test@example.net"),
        (NumberField, 12.5, 12.5),
        (NumberField, 12.5, 12.6),
        (TextField, "test", "test"),
        (TextField, "test", "test2"),
    ],
)
def test_required_value(cls, required, value):
    field = cls(require_value=required)
    class_ = build_class_from_fields("test", [field])

    if value == required:
        res = parse_response_values(class_, {"field_0": value})
        assert res == {"field_0": required}
    else:
        with pytest.raises(ClassValidationError):
            parse_response_values(class_, {"field_0": value})


@pytest.mark.parametrize(
    "min, max, required, expected, value, match",
    [
        (1, 1, 0, "a", 0, True),
        (1, 1, 0, "a", 1, False),
        (0, 1, 1, None, None, True),
        (0, 1, 1, "b", 0, False),
        (0, 2, [0, 1], ["a", "b"], [0, 1], True),
        (0, 2, [0, 1], ["a", "b"], [1], False),
        (0, 2, [0, 1], ["a", "b"], [1, 0], True),
    ],
)
def test_required_value_select(min, max, required, expected, value, match):
    field = SelectField(
        require_value=required, min=min, max=max, options=[Option("a"), Option("b")]
    )
    class_ = build_class_from_fields("test", [field])

    if match:
        res = parse_response_values(class_, {"field_0": value})
        assert res == {"field_0": expected}
    else:
        with pytest.raises(ClassValidationError):
            parse_response_values(class_, {"field_0": value})
