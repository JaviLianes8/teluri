"""Read tel: links as browsers and phones accept them, which RFC 3966 does not."""

from __future__ import annotations

from urllib.parse import unquote

from ._errors import TelURIError
from ._grammar import descriptor
from ._model import TelURI
from ._parse import parse


def parse_link(href: str, *, context: str | None = None) -> TelURI:
    """Parse a tel: link from a web page or an app, then validate it as RFC 3966.

    Links in the wild write spaces (``tel:+1 201 555 0123``), percent-encode the number
    (``%20``, ``%2B``, ``%23``) and leave local numbers without a phone-context. This
    reader decodes the number, drops whitespace, and gives a local number ``context``
    when the link has none. Everything after the number is read as strict RFC 3966.
    """
    if not isinstance(href, str):
        raise TypeError(f"href must be a str, not {type(href).__name__}")
    if context is not None:
        descriptor(context)  # one descriptor, so it cannot smuggle in other parameters
    text = href.strip()
    scheme, colon, rest = text.partition(":")
    if not colon or scheme.lower() != "tel":
        raise TelURIError("scheme", f"not a tel: link: {href!r}")
    number, semicolon, tail = rest.partition(";")
    try:
        decoded = unquote(number, errors="strict")
    except UnicodeDecodeError:
        raise TelURIError("number", f"not UTF-8 once decoded: {number!r}") from None
    cleaned = "".join(char for char in decoded if not char.isspace())
    if ";" in cleaned:  # an encoded separator must not start a parameter
        raise TelURIError("number", f"not a telephone number: {number!r}")
    names = [segment.partition("=")[0].lower() for segment in tail.split(";")]
    if context is not None and not cleaned.startswith("+") and "phone-context" not in names:
        tail = f"{tail};phone-context={context}" if semicolon else f"phone-context={context}"
        semicolon = ";"
    return parse(f"tel:{cleaned}{semicolon}{tail}")
