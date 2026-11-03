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
Reason.__doc__ = """The closed set of syntax error reasons, for static type checking.

>>> from typing import get_args
>>> from teluri import Reason
>>> "missing-context" in get_args(Reason)
True
"""


class TelURIError(ValueError):
    """Raised when a tel: URI is malformed or cannot be built.

    `reason` names the rule that failed, from the closed set `Reason`.
    Library-generated messages contain no input. A caller-supplied message is kept as is.

    >>> from teluri import TelURIError
    >>> error = TelURIError("ext", "expected digits")
    >>> (error.reason, str(error))
    ('ext', 'ext: expected digits')
    """

    reason: Reason

    def __init__(self, reason: Reason, message: str = "") -> None:
        super().__init__(reason, message)
        self.reason = reason
        self.message = message

    def __str__(self) -> str:
        return f"{self.reason}: {self.message}" if self.message else self.reason
