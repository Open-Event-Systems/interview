from contextvars import Context
from datetime import datetime, timedelta, timezone

import pytest
from attr import evolve
from cattrs import BaseValidationError
from oes.interview_old.config.interview import InterviewConfig, interviews_context
from oes.interview_old.config.question_bank import QuestionBank, question_bank_context
from oes.interview_old.config.step import StepResultStatus
from oes.interview_old.parsing.location import Location
from oes.interview_old.parsing.template import default_jinja2_env
from oes.interview_old.process import (
    InvalidStateError,
    advance_interview_state,
    get_question_for_variable,
    get_questions_for_variable,
    recursive_get_ask_for_variable,
)
from oes.interview_old.response import AskResult, ExitResult
from oes.interview_old.serialization import converter
from oes.interview_old.state import InterviewState
from oes.template import jinja2_env_context


def empty_context(func):
    def wrapper(*a, **kw):
        context = Context()
        return context.run(func, *a, **kw)

    return wrapper


@pytest.fixture
def question_bank() -> QuestionBank:
    bank = converter.structure(
        {
            "questions": [
                {
                    "id": "q1",
                    "title": "q1",
                    "fields": [
                        {"type": "text", "set": "a"},
                        {"type": "text", "set": "b"},
                    ],
                    "when": "test_value is true",
                },
                {
                    "id": "q1-2",
                    "title": "q1-2",
                    "fields": [
                        {"type": "text", "set": "a"},
                    ],
                },
                {
                    "id": "q2",
                    "title": "q2",
                    "fields": [
                        {"type": "text", "set": "c"},
                    ],
                },
                {
                    "id": "q3",
                    "title": "q3",
                    "description": "Depends on {{ c }}",
                    "fields": [
                        {"type": "text", "set": "d"},
                    ],
                },
                {
                    "id": "q4",
                    "title": "q4",
                    "description": "Depends on d via when",
                    "fields": [
                        {"type": "text", "set": "e"},
                    ],
                    "when": "d",
                },
                {
                    "id": "q5",
                    "title": "q5",
                    "description": "Array index",
                    "fields": [
                        {"type": "text", "set": "f[x]"},
                    ],
                },
                {
                    "id": "q6",
                    "title": "q6",
                    "description": "Sets y",
                    "fields": [
                        {"type": "text", "set": "y"},
                    ],
                },
                {
                    "id": "q7",
                    "title": "q7",
                    "description": "Sets g[y]",
                    "fields": [
                        {"type": "text", "set": "g[y]"},
                    ],
                },
                {
                    "id": "q8",
                    "title": "q8",
                    "description": "Sets h[g[y]]",
                    "fields": [
                        {"type": "text", "set": "h[g[y]]"},
                    ],
                },
            ],
        },
        QuestionBank,
    )

    return bank


@pytest.fixture
def state() -> InterviewState:
    return InterviewState(
        submission_id="1",
        interview_id="interview1",
        interview_version="1",
        expiration_date=datetime.now(tz=timezone.utc) + timedelta(seconds=30),
        target_url="",
        data={
            "test_value": True,
        },
    )


def test_get_questions_for_variable_single(
    question_bank: QuestionBank, state: InterviewState
):
    questions = list(
        get_questions_for_variable(state, question_bank, Location.parse("c"))
    )
    assert questions == [question_bank.get_question("q2")]


def test_get_questions_for_variable(question_bank: QuestionBank, state: InterviewState):
    questions = sorted(
        get_questions_for_variable(state, question_bank, Location.parse("a")),
        key=lambda q: q.id,
    )
    assert questions == [
        question_bank.get_question("q1"),
        question_bank.get_question("q1-2"),
    ]


def test_get_question_for_variable(question_bank: QuestionBank, state: InterviewState):
    question = get_question_for_variable(state, question_bank, Location.parse("a"))
    assert question == question_bank.get_question("q1")


def test_get_question_for_variable_skip_answered(
    question_bank: QuestionBank, state: InterviewState
):
    state = evolve(state, answered_question_ids=frozenset({"q1"}))
    question = get_question_for_variable(state, question_bank, Location.parse("a"))
    assert question == question_bank.get_question("q1-2")


def test_get_question_for_variable_check_when(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["test_value"] = False
    question = get_question_for_variable(state, question_bank, Location.parse("a"))
    assert question == question_bank.get_question("q1-2")


def test_recursive_get_ask_for_variable_found(
    question_bank: QuestionBank, state: InterviewState
):
    _, res = recursive_get_ask_for_variable(state, question_bank, Location.parse("a"))
    assert res.fields == question_bank.get_question("q1").get_ask_fields(
        state.template_context
    )


def test_recursive_get_ask_for_variable(
    question_bank: QuestionBank, state: InterviewState
):
    _, res = recursive_get_ask_for_variable(state, question_bank, Location.parse("d"))
    assert res.fields == question_bank.get_question("q2").get_ask_fields(
        state.template_context
    )


def test_recursive_get_ask_for_variable_defined(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["c"] = "x"
    _, res = recursive_get_ask_for_variable(state, question_bank, Location.parse("d"))
    assert res.fields == question_bank.get_question("q3").get_ask_fields(
        state.template_context
    )


def test_recursive_get_ask_for_variable_multi(
    question_bank: QuestionBank, state: InterviewState
):
    _, res = recursive_get_ask_for_variable(state, question_bank, Location.parse("e"))
    assert res.title == "q2"


def test_recursive_get_ask_for_variable_multi_2(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["c"] = "x"
    _, res = recursive_get_ask_for_variable(state, question_bank, Location.parse("e"))
    assert res.title == "q3"


def test_recursive_get_ask_for_variable_multi_3(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["d"] = "x"
    _, res = recursive_get_ask_for_variable(state, question_bank, Location.parse("e"))
    assert res.title == "q4"


def test_get_questions_for_variable_indexed(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["x"] = 0
    questions = list(
        get_questions_for_variable(state, question_bank, Location.parse("f[0]"))
    )
    assert questions == [question_bank.get_question("q5")]


def test_get_questions_for_variable_indexed_not_found(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["x"] = 1
    questions = list(
        get_questions_for_variable(state, question_bank, Location.parse("f[0]"))
    )
    assert questions == []


def test_recursive_get_ask_for_variable_indexed(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["g"] = []
    _, res = recursive_get_ask_for_variable(
        state, question_bank, Location.parse("h[3]")
    )
    assert res.title == "q6"


def test_recursive_get_ask_for_variable_indexed_2(
    question_bank: QuestionBank, state: InterviewState
):
    state.data["y"] = 1
    state.data["g"] = []
    _, res = recursive_get_ask_for_variable(
        state, question_bank, Location.parse("h[3]")
    )
    assert res.title == "q7"


@pytest.mark.asyncio
@empty_context
async def test_interview_1():
    jinja2_env_context.set(default_jinja2_env)
    interviews = converter.structure(
        {
            "interviews": [
                {
                    "id": "int1",
                    "questions": [
                        {"id": "q1", "fields": [{"type": "text", "set": "a"}]},
                        {"id": "q2", "fields": [{"type": "text", "set": "b"}]},
                    ],
                    "steps": [
                        {"ask": "q1"},
                        {"eval": ["a", "b"]},
                    ],
                }
            ]
        },
        InterviewConfig,
    )

    interviews_context.set(interviews)
    interview = interviews.get_interview("int1")
    question_bank_context.set(interview.question_bank)
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        submission_id="1",
        expiration_date=datetime.now(tz=timezone.utc) + timedelta(seconds=30),
        target_url="",
    )

    state, res = await advance_interview_state(state, interview.question_bank, None)
    assert isinstance(res, AskResult)
    assert state.question_id == "q1"
    state, res = await advance_interview_state(
        state, interview.question_bank, {"field_0": "a"}
    )
    assert isinstance(res, AskResult)
    assert state.data == {"a": "a"}

    # note: q2 gets added here before it is actually answered
    assert state.answered_question_ids == {"q1", "q2"}
    assert state.question_id == "q2"

    state, res = await advance_interview_state(
        state, interview.question_bank, {"field_0": "b"}
    )
    assert res is StepResultStatus.completed
    assert state.complete
    assert state.question_id is None
    assert state.data == {"a": "a", "b": "b"}


@pytest.mark.asyncio
@empty_context
async def test_interview_2():
    jinja2_env_context.set(default_jinja2_env)
    interviews = converter.structure(
        {
            "interviews": [
                {
                    "id": "int1",
                    "questions": [
                        {"id": "q1", "fields": [{"type": "text", "set": "a"}]},
                        {"id": "q2", "fields": [{"type": "text", "set": "b"}]},
                    ],
                    "steps": [
                        {"set": "a", "value": "'a'"},
                        {"set": "a", "value": "'x'"},
                        {"eval": ["a", "b"]},
                        {
                            "set": "a",
                            "value": "'x'",
                            "always": True,
                            "when": "a != 'x'",
                        },
                    ],
                }
            ],
        },
        InterviewConfig,
    )

    interviews_context.set(interviews)
    interview = interviews.get_interview("int1")
    question_bank_context.set(interview.question_bank)
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        submission_id="1",
        expiration_date=datetime.now(tz=timezone.utc) + timedelta(seconds=30),
        target_url="",
    )

    # skips q1 since the value is already set
    state, res = await advance_interview_state(state, interview.question_bank, None)
    assert isinstance(res, AskResult)
    assert state.question_id == "q2"

    # Should not re-set this since it is already defined
    assert state.data["a"] == "a"

    # Invalid response
    with pytest.raises(BaseValidationError):
        await advance_interview_state(
            state,
            interview.question_bank,
            {"field_0": None},
        )

    state, res = await advance_interview_state(
        state, interview.question_bank, {"field_0": "b"}
    )

    # Should be re-set since always is set
    assert state.data["a"] == "x"
    assert state.complete
    assert state.question_id is None
    assert res is StepResultStatus.completed

    # Can't continue after finished
    with pytest.raises(InvalidStateError):
        await advance_interview_state(state, interview.question_bank, {"field_0": "b"})


@pytest.mark.asyncio
@empty_context
async def test_interview_3():
    jinja2_env_context.set(default_jinja2_env)
    interviews = converter.structure(
        {"interviews": [{"id": "int1", "questions": [], "steps": [{"exit": "test"}]}]},
        InterviewConfig,
    )

    interviews_context.set(interviews)
    interview = interviews.get_interview("int1")
    question_bank_context.set(interview.question_bank)
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        submission_id="1",
        expiration_date=datetime.now(tz=timezone.utc) + timedelta(seconds=30),
        target_url="",
    )

    state, res = await advance_interview_state(state, interview.question_bank, None)
    assert isinstance(res, ExitResult)
