"""Validators for the pieces of the RFC 3966 grammar, each raising a precise reason."""

from __future__ import annotations

from ._chars import (
    ALPHA,
    ALPHANUM,
    DIGITS,
    LOCAL_DIGITS,
    PARAMCHAR,
    PNAME_CHARS,
    VISUAL_SEPARATORS,
    decode_pct,
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
        raise TelURIError(reason, "expected a global number")
    return "+" + strip_separators(body)


def local_digits(raw: str) -> str:
    """`local-number-digits`: hex digits, `*` and `#` with separators, at least one of them."""
    if not only(raw, _LOCAL) or not strip_separators(raw):
        raise TelURIError("number", "expected a local number")
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
        raise TelURIError(reason, "expected a domain name or global number")
    return value


def extension(value: str) -> str:
    """`ext`: digits and separators; at least one digit, since an empty extension names nothing."""
    digits = strip_separators(value)
    if not only(value, _GLOBAL) or not digits:
        raise TelURIError("ext", "expected an extension with at least one digit")
    return digits


def subaddress(value: str) -> str:
    """`isub` per erratum 203: `1*paramchar`, kept in its encoded form (any octet may occur)."""
    if not value or not valid_pct(value, PARAMCHAR):
        raise TelURIError("isub", "expected an encoded ISDN subaddress")
    return value


def pname(name: str) -> str:
    """`pname`, lower-cased: names compare case-insensitively and SHOULD be lower case."""
    if not name or not only(name, PNAME_CHARS):
        raise TelURIError("param-name", "expected a parameter name")
    return name.lower()


def pvalue(value: str) -> str:
    """`pvalue`, percent-decoded as UTF-8 (an empty one is refused by the model)."""
    if not valid_pct(value, PARAMCHAR):
        raise TelURIError("param-value", "expected an encoded parameter value")
    decoded = decode_pct(value)
    if decoded is None:
        raise TelURIError("param-value", "parameter value must decode as UTF-8")
    return decoded


def _is_label(label: str) -> bool:
    if not label or not only(label, ALPHANUM | frozenset("-")):
        return False
    return label[0] != "-" and label[-1] != "-"
