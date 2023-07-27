import pytest
from cattrs.preconf.json import make_converter
from oes.interview.input.field_types.text import TextField
from oes.interview.input.question import Question
from oes.interview.input.question_bank import QuestionBank, get_questions_providing_var
from oes.interview.variables.locator import parse_locator


@pytest.fixture
def question_bank() -> QuestionBank:
    bank = QuestionBank(converter=make_converter())

    qs = [
        Question(
            id="q1",
            fields=(
                TextField(
                    set=parse_locator("person.name"),
                ),
            ),
        ),
        Question(
            id="q2",
            fields=(
                TextField(
                    set=parse_locator("person.preferred_name"),
                ),
                TextField(
                    set=parse_locator("person.name"),
                ),
            ),
        ),
        Question(
            id="q3",
            fields=(
                TextField(
                    set=parse_locator("person[attr]"),
                ),
            ),
        ),
    ]

    for q in qs:
        bank[q.id] = q

    return bank


def test_question_bank(question_bank: QuestionBank):
    assert len(question_bank) == 3
    assert question_bank["q1"].id == "q1"
    assert question_bank["q2"].id == "q2"
    assert "q1" in question_bank
    assert "missing" not in question_bank


def test_get_questions_for_var_1(question_bank: QuestionBank):
    qs = question_bank.values()
    filtered = get_questions_providing_var(
        qs,
        parse_locator("person.name"),
        {},
    )

    ids = [q.id for q in filtered]
    assert ids == ["q1", "q2"]


def test_get_questions_for_var_2(question_bank: QuestionBank):
    qs = question_bank.values()
    filtered = get_questions_providing_var(
        qs,
        parse_locator("person.preferred_name"),
        {"attr": "name"},
    )

    ids = [q.id for q in filtered]
    assert ids == ["q2"]


def test_get_questions_for_var_parametrized(question_bank: QuestionBank):
    qs = question_bank.values()
    filtered = get_questions_providing_var(
        qs,
        parse_locator("person.name"),
        {"attr": "name"},
    )

    ids = [q.id for q in filtered]
    assert ids == ["q1", "q2", "q3"]
