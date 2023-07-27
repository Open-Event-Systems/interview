import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from unittest.mock import create_autospec, patch

import pytest
import pytest_asyncio
import typed_settings as ts
from blacksheep import Content, Response
from blacksheep.testing import TestClient
from loguru import logger
from oes.interview_old.response import (
    AskResult,
    CompleteInterviewStateResponse,
    ExitResult,
    IncompleteInterviewStateResponse,
    InterviewStateResponse,
    create_state_response,
)
from oes.interview_old.serialization import converter
from oes.interview_old.server.app import app
from oes.interview_old.server.settings import Settings
from oes.interview_old.state import InterviewState, get_validated_state


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client():
    with patch("oes.interview_old.server.app.load_settings") as load_settings:
        settings = create_autospec(Settings)
        settings.config_file = Path("tests/test_data/interviews.yml")
        settings.encryption_key = ts.Secret(b"0" * 32)
        load_settings.return_value = settings

        app.show_error_details = True

        async def print_exceptions(self, request, exc):
            logger.opt(exception=exc).exception(str(exc))
            return Response(500)

        app.exception_handler(Exception)(print_exceptions)

        await app.start()
        yield TestClient(app)
        await app.stop()


def get_initial_state(interview_id: str) -> InterviewStateResponse:
    settings: Settings = app.service_provider[Settings]

    state = InterviewState.create(
        interview_id=interview_id,
        interview_version="1",
        target_url="/complete",
        submission_id="1",
        expiration_date=datetime.now(tz=timezone.utc) + timedelta(seconds=30),
    )

    response = create_state_response(
        state,
        key=settings.encryption_key.get_secret_value(),
        update_url="/update",
    )

    return response


async def update_state(
    client: TestClient,
    state: InterviewStateResponse,
    responses: Optional[dict[str, Any]] = None,
    button: Optional[int] = None,
) -> InterviewStateResponse:
    if not isinstance(state, IncompleteInterviewStateResponse):
        raise TypeError(f"State is already complete: {state}")

    data = {"state": state.state, "responses": responses or {}, "button": button}

    res = await client.post(
        "/update",
        content=Content(
            b"application/json",
            data=json.dumps(data).encode(),
        ),
    )
    assert res.status == 200
    res_json = await res.json()
    return converter.structure(res_json, InterviewStateResponse)


@pytest.mark.asyncio
async def test_interview_1(client: TestClient):
    settings: Settings = app.service_provider[Settings]

    # State should start off with an incomplete interview_old response, with no content
    state = get_initial_state("test1")
    assert isinstance(state, IncompleteInterviewStateResponse)
    assert not state.content

    # First update should give an ask for first name/last name
    state = await update_state(client, state)
    assert isinstance(state, IncompleteInterviewStateResponse)
    assert bool(state.content)

    # Next update should accept the responses and complete the state
    state = await update_state(
        client, state, {"field_0": "fname", "field_1": " lname "}
    )
    assert isinstance(state, CompleteInterviewStateResponse)
    assert state.complete
    assert state.target_url == "/complete"

    state_inst = get_validated_state(
        state.state, key=settings.encryption_key.get_secret_value()
    )
    assert state_inst.data == {"first_name": "fname", "last_name": "lname"}


@pytest.mark.asyncio
async def test_interview_2(client: TestClient):
    state = get_initial_state("test2")

    # First update should ask for optional text
    state = await update_state(client, state)
    assert isinstance(state, IncompleteInterviewStateResponse)
    assert bool(state.content)
    assert isinstance(state.content, AskResult)

    # Next update should exit if no text was provided
    exit_state = await update_state(client, state, {"field_0": " "})
    assert isinstance(exit_state, IncompleteInterviewStateResponse)
    assert isinstance(exit_state.content, ExitResult)
    assert exit_state.content.title == "Required"

    # Resubmit with text, should provide a complete state
    state = await update_state(client, state, {"field_0": "test"})
    assert isinstance(state, CompleteInterviewStateResponse)
