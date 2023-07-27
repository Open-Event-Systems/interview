"""State module."""
from __future__ import annotations

import uuid
import zlib
from collections.abc import Callable, Mapping, Set
from datetime import datetime, timedelta, timezone
from struct import Struct
from typing import Any, Optional

import orjson
from attr import Factory, evolve
from attrs import frozen
from cattrs.preconf.orjson import make_converter
from nacl.secret import SecretBox
from oes.template import Context
from typing_extensions import Self

DEFAULT_INTERVIEW_EXPIRATION = 1800
"""The default amount of time in seconds an interview state is valid."""

state_converter = make_converter()
"""Converter just for use with :class:`InterviewState`."""


class InvalidStateError(ValueError):
    """Raised when an interview state is not valid."""


@frozen
class InterviewState:
    """An interview_old state."""

    submission_id: str
    """Unique ID for this submission."""

    interview_id: str
    """The interview ID."""

    interview_version: str
    """The interview version."""

    expiration_date: datetime
    """When the interview expires."""

    target_url: str
    """The target URL."""

    complete: bool = False
    """Whether the state is complete."""

    context: Context = Factory(dict)
    """Context data."""

    answered_question_ids: Set[str] = frozenset()
    """Answered question IDs."""

    question_id: Optional[str] = None
    """The current question ID."""

    data: Context = Factory(dict)
    """Interview data."""

    @property
    def template_context(self) -> Context:
        """The context to use when evaluating templates."""
        return {**self.data, **self.context}

    @classmethod
    def create(
        cls,
        *,
        interview_id: str,
        interview_version: str,
        target_url: str,
        submission_id: Optional[str] = None,
        expiration_date: Optional[datetime] = None,
        context: Optional[Context] = None,
    ) -> Self:
        """Create a new :class:`InterviewState`."""
        return cls(
            interview_id=interview_id,
            interview_version=interview_version,
            target_url=target_url,
            submission_id=submission_id
            if submission_id is not None
            else uuid.uuid4().hex,
            expiration_date=expiration_date
            if expiration_date is not None
            else datetime.now(tz=timezone.utc)
            + timedelta(seconds=DEFAULT_INTERVIEW_EXPIRATION),
            context=context or {},
        )

    def encrypt(
        self, *, key: bytes, default: Optional[Callable[[Any], Any]] = None
    ) -> bytes:
        """Encrypt this state."""
        as_bytes = _encode_state(self, default=default)

        box = SecretBox(key)
        return box.encrypt(as_bytes)

    @classmethod
    def decrypt(cls, encrypted: bytes, *, key: bytes) -> InterviewState:
        """Decrypt an encrypted state.

        Warning:
            Does not check the expiration date or perform other validation.

        Args:
            encrypted: The encrypted state.
            key: The key.

        Returns:
            The decrypted :class:`InterviewState`.

        Raises:
            InvalidStateError: If decryption/verification fails.
        """

        try:
            box = SecretBox(key)
            decrypted = box.decrypt(encrypted)
            view = memoryview(decrypted)
            parsed = _decode_state(view)
        except Exception as e:
            raise InvalidStateError("Interview state is not valid") from e

        return parsed

    def get_is_expired(self, *, now: Optional[datetime] = None) -> bool:
        """Return whether the state is expired."""
        now = now if now is not None else datetime.now(tz=timezone.utc)
        return now >= self.expiration_date

    def get_is_current_version(self, /, current_version: str) -> bool:
        """Return whether the version is current/correct."""
        return self.interview_version == current_version

    def validate(
        self, *, current_version: Optional[str] = None, now: Optional[datetime] = None
    ):
        """Check that the state is valid.

        Warning:
            Only checks the version if provided.

        Args:
            current_version: The current interview_old version.
            now: The current ``datetime``.

        Raises:
            InvalidStateError: If the state is expired or the wrong version.
        """
        if self.get_is_expired(now=now) or (
            current_version is not None
            and not self.get_is_current_version(current_version)
        ):
            raise InvalidStateError("Interview state is not valid")

    def update_with_question(
        self,
        question_id: str,
    ) -> Self:
        """Return an updated instance with ``question_id`` set."""
        new_qs = self.answered_question_ids | {question_id}
        return evolve(self, question_id=question_id, answered_question_ids=new_qs)


_data = Struct("<i")


def _encode_state(
    state: InterviewState, default: Optional[Callable[[Any], Any]] = None
) -> bytes:
    as_dict: dict[str, Any] = state_converter.unstructure(state)
    data = as_dict.pop("data")
    return _encode_data(as_dict, compress=True, default=default) + _encode_data(
        {"data": data}, compress=False, default=default
    )


def _decode_state(data: memoryview) -> InterviewState:
    as_dict: dict[str, Any] = {}
    i = 0
    while i < len(data):
        ct, part = _decode_data(data[i:])
        as_dict.update(part)
        i += ct

    return state_converter.structure(as_dict, InterviewState)


def _encode_data(
    data: Mapping[str, Any],
    compress: bool = False,
    default: Optional[Callable[[Any], Any]] = None,
) -> bytes:
    json_bytes = orjson.dumps(data, default=default)

    if compress:
        compressed = zlib.compress(json_bytes)
        result = _data.pack(-len(compressed)) + compressed
    else:
        result = _data.pack(len(json_bytes)) + json_bytes

    return result


def _decode_data(data: memoryview) -> tuple[int, Mapping[str, Any]]:
    (size,) = _data.unpack_from(data)

    if size < 0:
        size = -size
        compressed = True
    else:
        compressed = False

    if len(data) < _data.size + size:
        raise ValueError("Invalid data")

    body = data[_data.size : _data.size + size]

    if compressed:
        decompressed = zlib.decompress(body)
        return _data.size + size, orjson.loads(decompressed)
    else:
        return _data.size + size, orjson.loads(body)
