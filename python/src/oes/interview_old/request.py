"""Request types."""
from datetime import datetime
from typing import Optional

from attrs import frozen
from oes.interview_old.state import InterviewState, get_validated_state


@frozen
class InterviewStateRequestBody:
    """Model for a request body containing a completed interview_old state."""

    state: str

    def get_validated_state(
        self,
        *,
        key: bytes,
        current_version: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> InterviewState:
        """Get the validated :class:`InterviewState`.

        See Also:
            :func:`oes.interview_old.state.get_validated_state`
        """
        return get_validated_state(
            self.state, key=key, current_version=current_version, now=now
        )
