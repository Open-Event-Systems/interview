from typing import Optional

import attr
import pytest
from attrs import frozen
from cattrs import ClassValidationError
from cattrs.preconf.json import make_converter
from oes.interview.config2.response import create_response_parser
from oes.interview.config2.types import Parseable
from oes.interview.parsing.location import Location


@frozen
class CustomField(Parseable):
    field_info: object
    set: Optional[Location]


def test_create_response_parser():
    fields = [
        CustomField(
            attr.ib(type=int),
            set=Location.parse("val1"),
        ),
        CustomField(
            attr.ib(type=str),
            set=Location.parse("val2"),
        ),
    ]

    converter = make_converter()

    parser = create_response_parser(
        "my-test's_class 0",
        fields,
        converter,
    )

    response = {
        "field_0": 123,
        "field_1": "test",
    }

    parsed = parser(response)
    assert parsed == {
        Location.parse("val1"): 123,
        Location.parse("val2"): "test",
    }


def test_create_response_parser_error():
    fields = [
        CustomField(
            attr.ib(type=int),
            set=Location.parse("val1"),
        ),
        CustomField(
            attr.ib(type=str),
            set=Location.parse("val2"),
        ),
    ]

    converter = make_converter()

    parser = create_response_parser(
        "my-test's_class 0",
        fields,
        converter,
    )

    response = {
        "field_0": "test",
        "field_1": "test",
    }

    with pytest.raises(ClassValidationError):
        parser(response)
