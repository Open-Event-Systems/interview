import os
from datetime import datetime, timedelta, timezone

import pytest
from oes.interview.state.state import InterviewState, InvalidStateError


def test_encrypt_decrypt():
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        target_url="http://localhost",
        submission_id="s1",
        expiration_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        context={
            "test": True,
        },
    )

    key = os.urandom(32)

    enc = state.encrypt(key=key)
    assert isinstance(enc, bytes)

    dec = state.decrypt(enc, key=key)
    assert dec == state


def test_encrypt_decrypt_invalid_key():
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        target_url="http://localhost",
        submission_id="s1",
        expiration_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        context={
            "test": True,
        },
    )

    key = os.urandom(32)

    enc = state.encrypt(key=key)

    key2 = bytearray(key)
    key2[16] = (key[16] + 1) % 256

    with pytest.raises(InvalidStateError):
        state.decrypt(enc, key=key2)


def test_encrypt_decrypt_invalid_state_1():
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        target_url="http://localhost",
        submission_id="s1",
        expiration_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        context={
            "test": True,
        },
    )

    key = os.urandom(32)

    enc = bytearray(state.encrypt(key=key))

    enc[128] = (enc[128] + 1) % 256

    with pytest.raises(InvalidStateError):
        state.decrypt(enc, key=key)


def test_encrypt_decrypt_invalid_state_2():
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        target_url="http://localhost",
        submission_id="s1",
        expiration_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        context={
            "test": True,
        },
    )

    key = os.urandom(32)

    enc = state.encrypt(key=key) + b"\x01\x00\x00\x00\x00"

    with pytest.raises(InvalidStateError):
        state.decrypt(enc, key=key)


def test_state_expiration():
    state = InterviewState.create(
        interview_id="int1",
        interview_version="1",
        target_url="http://localhost",
        submission_id="s1",
        expiration_date=datetime.now(tz=timezone.utc) - timedelta(minutes=1),
        context={
            "test": True,
        },
    )

    assert state.get_is_expired()
