"""Build a tel: URI string from its parts (RFC 3966)."""

from __future__ import annotations

from collections.abc import Mapping

from ._chars import PNAME_CHARS, RESERVED_PARAMETERS
from ._errors import TelURIError
from ._normalize import normalize_context, normalize_ext, normalize_number


def build(
    number: str,
    *,
    ext: str | None = None,
    phone_context: str | None = None,
    params: Mapping[str, str | None] | None = None,
) -> str:
    """Build a tel: URI, normalizing visual separators in the numeric parts.

    A number starting with ``+`` is global. Any other number is local and
    requires ``phone_context``. A global number rejects ``phone_context``.
    """
    if not number:
        raise TelURIError("number must not be empty")
    is_global = number.startswith("+")
    if is_global and phone_context is not None:
        raise TelURIError("a global number must not carry a phone-context")
    if not is_global and phone_context is None:
        raise TelURIError("a local number requires a phone-context")

    out = ["tel:", normalize_number(number, is_global=is_global)]
    if ext is not None:
        out.append(";ext=" + normalize_ext(ext))
    if phone_context is not None:
        out.append(";phone-context=" + normalize_context(phone_context))
    if params:
        out.extend(_render_params(params))
    return "".join(out)


def _render_params(params: Mapping[str, str | None]) -> list[str]:
    rendered = []
    for name, value in params.items():
        if not name or not all(char in PNAME_CHARS for char in name):
            raise TelURIError(f"invalid parameter name: {name!r}")
        if name.lower() in RESERVED_PARAMETERS:
            raise TelURIError(f"use the dedicated argument for {name!r}")
        rendered.append(f";{name}" if value is None else f";{name}={value}")
    return rendered
