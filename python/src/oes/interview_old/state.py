"""Interview state."""
from __future__ import annotations

import base64
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

from attrs import evolve, frozen
from cattrs.preconf.orjson import make_converter
from nacl.secret import SecretBox

if TYPE_CHECKING:
    from oes.interview_old.config.interview import Interview

DEFAULT_INTERVIEW_EXPIRATION = 1800
"""The default amount of time in seconds an interview_old state is valid."""

state_converter = make_converter()
"""Converter just for use with :class:`InterviewState`."""


class InvalidStateError(ValueError):
    """Raised when an interview_old state is not valid."""


@frozen
class InterviewState:
    """An interview_old state."""

    submission_id: str
    """Unique ID for this submission."""

    interview_id: str
    """The interview_old ID."""

    interview_version: str
    """The interview_old version."""

    expiration_date: datetime
    """When the interview_old expires."""

    target_url: str
    """The target URL."""

    complete: bool = False
    """Whether the state is complete."""

    context: dict[str, Any] = {}
    """Context data."""

    answered_question_ids: frozenset[str] = frozenset()
    """Answered question IDs."""

    question_id: Optional[str] = None
    """The current question ID."""

    data: dict[str, Any] = {}
    """Interview data."""

    @property
    def interview(self) -> Interview:
        """The associated :class:`Interview`."""
        # so code using just the state doesn't have to also import this module
        from oes.interview_old.config.interview import interviews_context

        config = interviews_context.get()
        interview = config.get_interview(self.interview_id) if config else None
        if not interview:
            raise LookupError(f"Interview not found: {self.interview_id}")
        return interview

    @property
    def template_context(self) -> dict[str, Any]:
        """The context dict to use when evaluating templates."""
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
        context: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> InterviewState:
        """Create a new :class:`InterviewState`."""
        return cls(
            interview_id=interview_id,
            interview_version=interview_version,
            target_url=target_url,
            submission_id=submission_id
            if submission_id is not None
            else str(uuid.uuid4()),
            expiration_date=expiration_date
            if expiration_date is not None
            else datetime.now(tz=timezone.utc)
            + timedelta(seconds=DEFAULT_INTERVIEW_EXPIRATION),
            context=context or {},
            data=data or {},
        )

    def encrypt(
        self, *, key: bytes, default: Optional[Callable[[Any], Any]] = None
    ) -> str:
        """Encrypt this state."""
        json_bytes = state_converter.dumps(self, default=default)

        box = SecretBox(key)
        enc_bytes = box.encrypt(json_bytes)
        return base64.urlsafe_b64encode(enc_bytes).decode()

    @classmethod
    def decrypt(cls, encrypted: str, *, key: bytes) -> InterviewState:
        """Decrypt an encrypted state.

        Warning:
            Does not check the expiration date or perform other validation.

        Args:
            encrypted: The base64 encoded encrypted state.
            key: The key.

        Returns:
            The :class:`InterviewState`.

        Raises:
            InvalidStateError: If decryption/verification fails.
        """

        try:
            enc_bytes = base64.urlsafe_b64decode(encrypted)

            box = SecretBox(key)
            decrypted = box.decrypt(enc_bytes)
            parsed = state_converter.loads(decrypted, cls)
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

    def update_with_question(self, question_id: str) -> InterviewState:
        """Return a new state with the given question ID as the current question."""
        new_qs = self.answered_question_ids | {question_id}
        return evolve(
            self,
            question_id=question_id,
            answered_question_ids=new_qs,
        )


def get_validated_state(
    state: str,
    *,
    key: bytes,
    current_version: Optional[str] = None,
    now: Optional[datetime] = None,
) -> InterviewState:
    """Get the validated :class:`InterviewState`.

    Decrypts, verifies, and validates the state.

    Args:
        state: The encrypted state string.
        key: The encryption key.
        current_version: The current interview_old version.
        now: The current time.

    Returns:
        The validated state.

    Raises:
        InvalidStateError: If the state is not valid.
    """
    verified_state = InterviewState.decrypt(state, key=key)
    verified_state.validate(current_version=current_version, now=now)

    return verified_state
