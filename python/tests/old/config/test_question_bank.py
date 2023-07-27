from oes.interview_old.config.question_bank import QuestionBank
from oes.interview_old.parsing.location import Location
from oes.interview_old.serialization import converter


def test_get_questions_by_value():
    bank = converter.structure(
        {
            "questions": [
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
                {
                    "id": "q2",
                    "fields": [
                        {
                            "type": "number",
                            "set": "a.value_d",
                        }
                    ],
                },
            ]
        },
        QuestionBank,
    )

    res = list(bank.get_questions_providing_variable(Location.parse("a.b"), {}))
    assert res == [bank.get_question("q1")]

    res = list(bank.get_questions_providing_variable(Location.parse("a.c"), {}))
    assert res == [bank.get_question("q1")]

    res = list(bank.get_questions_providing_variable(Location.parse("a.value_d"), {}))
    assert res == [bank.get_question("q2")]


def test_get_questions_by_value_indexed():
    bank = converter.structure(
        {
            "questions": [
                {
                    "id": "q1",
                    "fields": [
                        {
                            "type": "text",
                            "set": "a[x].b",
                        },
                    ],
                },
            ]
        },
        QuestionBank,
    )

    res = list(
        bank.get_questions_providing_variable(Location.parse("a[0].b"), {"x": 0})
    )
    assert res == [bank.get_question("q1")]


def test_get_questions_by_value_indexed_nested():
    bank = converter.structure(
        {
            "questions": [
                {
                    "id": "q1",
                    "fields": [
                        {
                            "type": "text",
                            "set": "a[b[x]].b",
                        },
                    ],
                }
            ]
        },
        QuestionBank,
    )

    res = list(
        bank.get_questions_providing_variable(
            Location.parse("a[2].b"), {"b": [1, 2], "x": 1}
        )
    )
    assert res == [bank.get_question("q1")]
