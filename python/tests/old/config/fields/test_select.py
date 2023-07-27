import pytest
from cattrs import BaseValidationError
from oes.interview_old.config.fields.select import Option, SelectField
from oes.interview_old.config.question import Question
from oes.interview_old.parsing.location import Location
from oes.template import Template

question1 = Question(
    id="q1",
    fields=(
        SelectField(
            type="select",
            set=Location.parse("select"),
            options=[
                Option(label=Template("A"), value="a"),
                Option(label=Template("B"), value="b"),
            ],
        ),
    ),
)

question2 = Question(
    id="q2",
    fields=(
        SelectField(
            type="select",
            set=Location.parse("select"),
            max=2,
            options=[
                Option(label=Template("A"), value="a"),
                Option(label=Template("B"), value="b"),
            ],
        ),
    ),
)

question3 = Question(
    id="q3",
    fields=(
        SelectField(
            type="select",
            set=Location.parse("select"),
            min=0,
            max=1,
            options=[
                Option(label=Template("A"), value="a"),
                Option(label=Template("B"), value="b"),
            ],
        ),
    ),
)

question4 = Question(
    id="q4",
    fields=(
        SelectField(
            type="select",
            set=Location.parse("select"),
            min=0,
            max=2,
            options=[
                Option(label=Template("A"), value="a"),
                Option(label=Template("B"), value="b"),
            ],
        ),
    ),
)


def test_select_ask_field():
    fields = question1.get_ask_fields({})
    assert fields["field_0"].options == ("A", "B")


def test_select_schema_multi():
    fields = question1.get_ask_fields({})
    assert fields["field_0"].options == ("A", "B")
    assert fields["field_0"].min == 1
    assert fields["field_0"].max == 1


def test_select_parses():
    res = question1.parse_response_fields({"field_0": 0})
    assert res == {Location.parse("select"): "a"}


def test_select_parses_error():
    with pytest.raises(BaseValidationError):
        question1.parse_response_fields({"field_0": [2]})


def test_select_parse_multi():
    res = question2.parse_response_fields({"field_0": [0, 1]})
    assert res == {Location.parse("select"): ["a", "b"]}


def test_select_parse_optional():
    res = question3.parse_response_fields({"field_0": None})
    assert res == {Location.parse("select"): None}

    res = question3.parse_response_fields({"field_0": None})
    assert res == {Location.parse("select"): None}


def test_select_parse_multi_optional():
    res = question4.parse_response_fields({"field_0": []})
    assert res == {Location.parse("select"): []}

    res = question4.parse_response_fields({"field_0": []})
    assert res == {Location.parse("select"): []}
