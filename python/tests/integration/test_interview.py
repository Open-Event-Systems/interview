import pytest
from blacksheep.testing import TestClient
from oes.interview.server.settings import Settings
from tests.integration.conftest import get_result, start_interview, update_interview


@pytest.mark.asyncio
async def test_interview_1(
    test_client: TestClient,
    settings: Settings,
):
    res = await start_interview(test_client, settings, "interview1")
    state = res["state"]
    assert res["content"] == {
        "schema": {
            "properties": {
                "field_0": {
                    "maxLength": 300,
                    "minLength": 0,
                    "title": "Name",
                    "type": "string",
                    "x-type": "text",
                    "nullable": False,
                }
            },
            "required": ["field_0"],
            "title": "Name",
            "type": "object",
        },
        "type": "question",
    }

    res = await update_interview(
        test_client,
        state,
        {
            "field_0": "Test",
        },
    )

    state = res["state"]
    assert res["complete"] is True

    result = await get_result(test_client, settings, state)
    assert result["data"] == {"name": "Test", "name2": "Test"}


@pytest.mark.asyncio
async def test_interview_2(
    test_client: TestClient,
    settings: Settings,
):
    res = await start_interview(
        test_client, settings, "interview2", data={"person": {}}
    )
    state = res["state"]

    res = await update_interview(
        test_client,
        state,
        {
            "field_0": "Test Name",
            "field_1": "1",
        },
    )

    state = res["state"]
    assert res["complete"] is True

    result = await get_result(test_client, settings, state)
    assert result["data"] == {
        "person": {
            "name": "Test Name",
        },
        "use_preferred_name": True,
    }


@pytest.mark.asyncio
async def test_interview_3(
    test_client: TestClient,
    settings: Settings,
):
    res = await start_interview(test_client, settings, "interview3")
    state = res["state"]

    res = await update_interview(
        test_client,
        state,
        {
            "field_0": "1999-01-01",
        },
    )

    state = res["state"]
    assert res["content"]["type"] == "question"

    res = await update_interview(
        test_client,
        state,
        {
            "field_0": "2",
        },
    )

    state = res["state"]
    assert res["complete"] is True

    result = await get_result(test_client, settings, state)
    assert result["data"] == {
        "birth_date": "1999-01-01",
        "level": "vip",
    }
