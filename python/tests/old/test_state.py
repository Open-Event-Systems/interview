from datetime import datetime, timedelta, timezone

import pytest
from oes.interview_old.state import InterviewState


def test_state_encrypt_decrypt():
    now = datetime.now(tz=timezone.utc)
    state = InterviewState(
        submission_id="1",
        interview_id="test",
        interview_version="1",
        expiration_date=now + timedelta(seconds=15),
        target_url="http://test.com",
    )

    enc = state.encrypt(key=b"00000000000000000000000000000000")
    dec = InterviewState.decrypt(enc, key=b"00000000000000000000000000000000")
    assert dec == state
    assert not dec.get_is_expired(now=now)


def test_state_encrypt_decrypt_error():
    state = InterviewState(
        submission_id="1",
        interview_id="test",
        interview_version="1",
        expiration_date=datetime.now(tz=timezone.utc) + timedelta(seconds=15),
        target_url="http://test.com",
    )

    enc = state.encrypt(key=b"00000000000000000000000000000000")
    with pytest.raises(ValueError):
        InterviewState.decrypt(enc, key=b"00000000000000000000000000000001")


def test_state_expiration_date():
    now = datetime.now(tz=timezone.utc)
    state = InterviewState(
        submission_id="1",
        interview_id="test",
        interview_version="1",
        expiration_date=now - timedelta(seconds=5),
        target_url="http://test.com",
    )
    assert state.get_is_expired(now=now)


def test_state_dumps_default():
    obj = object()

    def default(v):
        if v is obj:
            return "test"

    now = datetime.now(tz=timezone.utc)
    state = InterviewState(
        submission_id="1",
        interview_id="test",
        interview_version="1",
        expiration_date=now - timedelta(seconds=5),
        target_url="http://test.com",
        data={"obj": obj},
    )

    enc = state.encrypt(key=b"\0" * 32, default=default)
    dec = InterviewState.decrypt(enc, key=b"\0" * 32)
    assert dec.data == {"obj": "test"}
