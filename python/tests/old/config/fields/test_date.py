from datetime import date
from unittest.mock import patch

import pytest
from cattrs import ClassValidationError
from oes.interview_old.config.field import (
    build_class_from_fields,
    parse_response_values,
)
from oes.interview_old.config.fields.date import DateAskField, DateField


@pytest.mark.parametrize(
    "val, expected",
    [
        (None, None),
        ("2020-01-01", date(2020, 1, 1)),
        ("2020-12-31", date(2020, 12, 31)),
    ],
)
def test_date_parse(val, expected):
    field = DateField(
        type="date",
        optional=True,
        min=date(2020, 1, 1),
        max=date(2020, 12, 31),
    )
    class_ = build_class_from_fields("test", [field])
    res = parse_response_values(class_, {"field_0": val})
    assert res == {"field_0": expected}


def test_date_today():
    field = DateField(
        type="date",
        min="today",
        max="today",
        default="today",
    )
    today = date.today()

    ask_field = field.get_ask_field({})
    assert isinstance(ask_field, DateAskField)
    assert ask_field.min == today
    assert ask_field.max == today
    assert ask_field.default == today


@pytest.mark.parametrize(
    "val, min, max",
    [
        (None, None, None),
        (date(2021, 1, 1), None, date(2020, 12, 31)),
        (date(2021, 12, 31), None, date(2020, 1, 1)),
        (date(2020, 7, 3), "today", date(2020, 12, 31)),
        (date(2020, 7, 5), date(2020, 1, 1), "today"),
    ],
)
@patch("oes.interview_old.config.fields.date.date")
def test_date_invalid(mock_date, val, min, max):
    mock_date.today.return_value = date(2020, 7, 4)
    field = DateField(
        type="date",
        min=min,
        max=max,
    )
    class_ = build_class_from_fields("test", [field])
    with pytest.raises(ClassValidationError):
        parse_response_values(class_, {"field_0": val})
