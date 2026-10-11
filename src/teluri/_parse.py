"""Parse a tel: URI into a :class:`TelURI` (RFC 3966)."""

from __future__ import annotations

from ._chars import PNAME_CHARS
from ._errors import TelURIError
from ._model import TelURI
from ._normalize import normalize_context, normalize_ext, normalize_number


def parse(uri: str) -> TelURI:
    """Parse a tel: URI, normalizing visual separators in the numeric parts.

    A global number starts with ``+``. A local number carries a
    ``phone-context`` parameter, as RFC 3966 requires; a local number without
    one raises :class:`TelURIError`.
    """
    scheme, sep, rest = uri.partition(":")
    if sep != ":" or scheme.lower() != "tel":
        raise TelURIError(f"not a tel: URI: {uri!r}")
    if not rest:
        raise TelURIError("empty telephone subscriber")

    raw_number, *segments = rest.split(";")
    if not raw_number:
        raise TelURIError("empty telephone number")
    is_global = raw_number.startswith("+")
    number = normalize_number(raw_number, is_global=is_global)

    ext: str | None = None
    phone_context: str | None = None
    params: dict[str, str | None] = {}
    for segment in segments:
        name, eq, value = segment.partition("=")
        if not name or not all(char in PNAME_CHARS for char in name):
            raise TelURIError(f"invalid parameter: {segment!r}")
        key = name.lower()
        if key == "ext":
            ext = _unique(ext, "ext", eq, normalize_ext(value))
        elif key == "phone-context":
            phone_context = _unique(phone_context, "phone-context", eq, normalize_context(value))
        elif name in params:
            raise TelURIError(f"duplicate parameter: {name!r}")
        else:
            params[name] = value if eq else None

    if is_global and phone_context is not None:
        raise TelURIError("a global number must not carry a phone-context")
    if not is_global and phone_context is None:
        raise TelURIError("a local number requires a phone-context")

    return TelURI(number, is_global, ext, phone_context, params)


def _unique(current: str | None, name: str, eq: str, value: str) -> str:
    if current is not None:
        raise TelURIError(f"duplicate parameter: {name!r}")
    if not eq:
        raise TelURIError(f"{name} needs a value")
    return value
