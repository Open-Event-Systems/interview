from datetime import datetime, timedelta

import pytest
from attrs import evolve
from oes.hook import HttpHookConfig
from oes.interview_old.config.step import (
    Ask,
    Block,
    Eval,
    Exit,
    Hook,
    HookResult,
    Set,
    StepOrBlock,
    flatten_steps,
    http_func_ctx,
)
from oes.interview_old.response import ExitResult
from oes.interview_old.serialization import converter
from oes.interview_old.state import InterviewState


def hook_func(state: InterviewState):
    updated = evolve(state, data={"test": True})

    return updated, ExitResult("hook")


async def http_hook_func(state: InterviewState, config: HttpHookConfig):
    assert config.url == "http://localhost/hook"

    data = converter.unstructure(state)

    data["data"]["test"] = True

    result_dict = {"state": data, "result": {"type": "exit", "title": "Exit"}}

    obj = converter.structure(result_dict, HookResult)
    return obj.state, obj.result


def test_step_parse():
    step_list = [
        {"ask": "test"},
        {"set": "test", "value": "123"},
        {"block": [{"ask": "test2"}]},
        {"exit": "Exit", "message": "Exit message"},
        {"eval": [1, "2", "1 + 2"]},
    ]

    steps = converter.structure(step_list, list[StepOrBlock])
    assert isinstance(steps[0], Ask)
    assert isinstance(steps[1], Set)
    assert isinstance(steps[2], Block)
    assert isinstance(steps[3], Exit)
    assert isinstance(steps[4], Eval)


def test_flatten_blocks():
    step_list = [{"block": [{"block": [{"ask": "test"}]}]}]

    steps = converter.structure(step_list, list[StepOrBlock])
    flattened = flatten_steps(steps)
    assert len(flattened) == 1
    assert isinstance(flattened[0], Ask)


def test_flatten_blocks_when():
    step_list = [
        {
            "block": [{"block": [{"ask": "test", "when": "false"}], "when": "true"}],
            "when": [True],
        }
    ]

    steps = converter.structure(step_list, list[StepOrBlock])
    flattened = flatten_steps(steps)
    assert not flattened[0].when_matches()


def test_flatten_blocks_when_2():
    step_list = [{"block": [{"block": [{"ask": "test"}], "when": "true"}]}]

    steps = converter.structure(step_list, list[StepOrBlock])
    flattened = flatten_steps(steps)
    assert flattened[0].when_matches()


@pytest.mark.asyncio
async def test_hooks_1():
    step_list = [
        {
            "hook": {
                "python": "tests.config.test_step:hook_func",
            }
        }
    ]

    steps = converter.structure(step_list, list[StepOrBlock])
    assert isinstance(steps[0], Hook)

    state = InterviewState(
        submission_id="1",
        interview_id="hooks",
        interview_version="1",
        expiration_date=datetime.now().astimezone() + timedelta(hours=1),
        target_url="http://localhost",
    )

    expected_state = evolve(state, data={"test": True})

    res = await steps[0].handle(state)
    assert res == (expected_state, ExitResult("hook"))


@pytest.mark.asyncio
async def test_hooks_2():
    step_list = [
        {
            "hook": {
                "url": "http://localhost/hook",
            }
        }
    ]

    steps = converter.structure(step_list, list[StepOrBlock])
    assert isinstance(steps[0], Hook)

    state = InterviewState(
        submission_id="1",
        interview_id="hooks",
        interview_version="1",
        expiration_date=datetime.now().astimezone() + timedelta(hours=1),
        target_url="http://localhost",
    )

    expected_state = evolve(state, data={"test": True})

    token = http_func_ctx.set(http_hook_func)
    try:
        res = await steps[0].handle(state)
        assert res == (expected_state, ExitResult("Exit"))
    finally:
        http_func_ctx.reset(token)
