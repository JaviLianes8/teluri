"""The error raised for a malformed tel: URI, with a machine-readable reason."""

from __future__ import annotations

from typing import Literal

Reason = Literal[
    "scheme",
    "number",
    "ext",
    "isub",
    "ext-and-isub",
    "phone-context",
    "missing-context",
    "global-context",
    "param-name",
    "param-value",
    "duplicate-param",
    "param-order",
]


class TelURIError(ValueError):
    """Raised when a tel: URI is malformed or cannot be built.

    `reason` names the rule that failed, from the closed set `Reason`.
    """

    reason: Reason

    def __init__(self, reason: Reason, message: str = "") -> None:
        super().__init__(reason, message)
        self.reason = reason
        self.message = message

    def __str__(self) -> str:
        return f"{self.reason}: {self.message}" if self.message else self.reason
