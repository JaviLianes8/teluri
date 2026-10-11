"""Normalize the numeric parts of a tel: URI, stripping visual separators."""

from __future__ import annotations

from ._chars import DECIMAL_DIGITS, DOMAIN_CHARS, LOCAL_DIGITS, strip_separators
from ._errors import TelURIError


def normalize_number(raw: str, *, is_global: bool) -> str:
    """Return the number without visual separators, validated for its kind."""
    if is_global:
        digits = strip_separators(raw[1:])
        if not digits or not _all_in(digits, DECIMAL_DIGITS):
            raise TelURIError(f"invalid global number: {raw!r}")
        return "+" + digits
    digits = strip_separators(raw)
    if not digits or not _all_in(digits, LOCAL_DIGITS):
        raise TelURIError(f"invalid local number: {raw!r}")
    return digits


def normalize_ext(value: str) -> str:
    """Return the extension digits without visual separators."""
    digits = strip_separators(value)
    if not digits or not _all_in(digits, DECIMAL_DIGITS):
        raise TelURIError(f"invalid ext: {value!r}")
    return digits


def normalize_context(value: str) -> str:
    """Return a phone-context: a global number (separators stripped) or a domain."""
    if not value:
        raise TelURIError("phone-context must not be empty")
    if value.startswith("+"):
        return normalize_number(value, is_global=True)
    if not _all_in(value, DOMAIN_CHARS):
        raise TelURIError(f"invalid phone-context domain: {value!r}")
    return value


def _all_in(value: str, allowed: frozenset[str]) -> bool:
    return all(char in allowed for char in value)
