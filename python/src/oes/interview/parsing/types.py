"""Base parsing types."""
from __future__ import annotations

import re
from abc import abstractmethod
from typing import Any

from attrs import Attribute
from oes.template import Condition, evaluate
from typing_extensions import Protocol

IDENTIFIER_PATTERN = r"^(?![0-9_-])[a-zA-Z0-9_-]+(?<!-)$"
"""Valid identifiers pattern.

Identifiers are alphanumeric including "-" and "_", must start with a letter,
and must not end with a "-".
"""


def validate_identifier(instance: object, attribute: Attribute, value: object):
    """Raise :class:`ValueError` if the string is not a valid identifier."""
    if not isinstance(value, str) or not re.match(IDENTIFIER_PATTERN, value, re.I):
        raise ValueError(f"Invalid identifier: {value}")


class Whenable(Protocol):
    """Type with a ``when`` condition."""

    @property
    @abstractmethod
    def when(self) -> Condition:
        """The ``when`` condition."""
        ...

    def when_matches(self, **context: Any) -> bool:
        """Check if the condition matches."""
        return bool(evaluate(self.when, context))
