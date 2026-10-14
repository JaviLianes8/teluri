"""Character classes and percent-encoding from the RFC 3966 grammar."""

from __future__ import annotations

from urllib.parse import quote

VISUAL_SEPARATORS = "-.()"
_SEPARATOR_TABLE = {ord(char): None for char in VISUAL_SEPARATORS}

ALPHA = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = frozenset("0123456789")
ALPHANUM = ALPHA | DIGITS
HEXDIG = DIGITS | frozenset("ABCDEFabcdef")
LOCAL_DIGITS = HEXDIG | frozenset("*#")
PNAME_CHARS = ALPHANUM | frozenset("-")
MARK = frozenset("-_.!~*'()")
UNRESERVED = ALPHANUM | MARK
# paramchar minus pct-encoded: the characters a value may carry unencoded.
PARAMCHAR = UNRESERVED | frozenset("[]/:&+$")
_SAFE = "".join(sorted(PARAMCHAR - ALPHANUM))

# Names with their own field on TelURI; they never appear in `params`.
RESERVED_PARAMETERS = frozenset({"ext", "isub", "phone-context"})


def strip_separators(value: str) -> str:
    """Drop the visual separators (-, ., (, )) that only aid readability."""
    return value.translate(_SEPARATOR_TABLE)


def only(value: str, allowed: frozenset[str]) -> bool:
    """True when every character of `value` is in `allowed` (ASCII sets only)."""
    return all(char in allowed for char in value)


def encode_value(text: str) -> str:
    """Percent-encode `text` (UTF-8) so that it is a valid `pvalue`."""
    return quote(text, safe=_SAFE)


def valid_pct(value: str, allowed: frozenset[str]) -> bool:
    """True when `value` is made of `allowed` characters and well-formed %HH escapes."""
    index = 0
    while index < len(value):
        char = value[index]
        if char == "%":
            escape = value[index + 1 : index + 3]
            if len(escape) != 2 or not only(escape, HEXDIG):
                return False
            index += 3
            continue
        if char not in allowed:
            return False
        index += 1
    return True
