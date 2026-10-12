"""Character classes shared by the parser and the builder (RFC 3966)."""

from __future__ import annotations

VISUAL_SEPARATORS = "-.()"
_SEPARATOR_TABLE = {ord(char): None for char in VISUAL_SEPARATORS}

DECIMAL_DIGITS = frozenset("0123456789")
LOCAL_DIGITS = frozenset("0123456789ABCDEFabcdef*#")
DOMAIN_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.")
PNAME_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")

RESERVED_PARAMETERS = frozenset({"ext", "phone-context"})


def strip_separators(value: str) -> str:
    """Drop the RFC 3966 visual separators (-, ., (, )) used for readability."""
    return value.translate(_SEPARATOR_TABLE)
