"""Validators for the pieces of the RFC 3966 grammar, each raising a precise reason."""

from __future__ import annotations

from urllib.parse import unquote

from ._chars import (
    ALPHA,
    ALPHANUM,
    DIGITS,
    LOCAL_DIGITS,
    PARAMCHAR,
    PNAME_CHARS,
    VISUAL_SEPARATORS,
    only,
    strip_separators,
    valid_pct,
)
from ._errors import Reason, TelURIError

_GLOBAL = DIGITS | frozenset(VISUAL_SEPARATORS)
_LOCAL = LOCAL_DIGITS | frozenset(VISUAL_SEPARATORS)


def global_digits(raw: str, reason: Reason = "number") -> str:
    """`global-number-digits`: digits and separators after the `+` the caller has seen."""
    body = raw[1:]
    if not only(body, _GLOBAL) or not strip_separators(body):
        raise TelURIError(reason, f"not a global number: {raw!r}")
    return "+" + strip_separators(body)


def local_digits(raw: str) -> str:
    """`local-number-digits`: hex digits, `*` and `#` with separators, at least one of them."""
    if not only(raw, _LOCAL) or not strip_separators(raw):
        raise TelURIError("number", f"not a local number: {raw!r}")
    return strip_separators(raw)


def is_domainname(value: str) -> bool:
    """`domainname`: dot-separated labels, a top label starting with a letter, optional root dot."""
    labels = value[:-1].split(".") if value.endswith(".") else value.split(".")
    if not all(_is_label(label) for label in labels):
        return False
    return labels[-1][0] in ALPHA


def descriptor(value: str, reason: Reason = "phone-context") -> str:
    """A context `descriptor`: a global number prefix (separators dropped) or a domain name."""
    if value.startswith("+"):
        return global_digits(value, reason)
    if not is_domainname(value):
        raise TelURIError(reason, f"not a domain name or global number: {value!r}")
    return value


def extension(value: str) -> str:
    """`ext`: digits and separators; at least one digit, since an empty extension names nothing."""
    digits = strip_separators(value)
    if not only(value, _GLOBAL) or not digits:
        raise TelURIError("ext", f"not an extension: {value!r}")
    return digits


def subaddress(value: str) -> str:
    """`isub` per erratum 203: `1*paramchar`, kept in its encoded form (any octet may occur)."""
    if not value or not valid_pct(value, PARAMCHAR):
        raise TelURIError("isub", f"not an ISDN subaddress: {value!r}")
    return value


def pname(name: str) -> str:
    """`pname`, lower-cased: names compare case-insensitively and SHOULD be lower case."""
    if not name or not only(name, PNAME_CHARS):
        raise TelURIError("param-name", f"not a parameter name: {name!r}")
    return name.lower()


def pvalue(value: str) -> str:
    """`pvalue`, percent-decoded as UTF-8 (an empty one is refused by the model)."""
    if not valid_pct(value, PARAMCHAR):
        raise TelURIError("param-value", f"not a parameter value: {value!r}")
    try:
        return unquote(value, errors="strict")
    except UnicodeDecodeError:
        raise TelURIError("param-value", f"not UTF-8 once decoded: {value!r}") from None


def _is_label(label: str) -> bool:
    if not label or not only(label, ALPHANUM | frozenset("-")):
        return False
    return label[0] != "-" and label[-1] != "-"
