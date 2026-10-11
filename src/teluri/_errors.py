"""Error type raised when a tel: URI is malformed or cannot be built."""

from __future__ import annotations


class TelURIError(ValueError):
    """A tel: URI does not conform to RFC 3966."""
