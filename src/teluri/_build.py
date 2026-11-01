"""Build a canonical tel: URI from human-written parts."""

from __future__ import annotations

from collections.abc import Mapping

from ._model import TelURI


def build(
    number: str,
    *,
    ext: str | None = None,
    isub: str | None = None,
    phone_context: str | None = None,
    params: Mapping[str, str | None] | None = None,
) -> str:
    """Build a canonical tel: URI, raising :class:`TelURIError` for invalid parts.

    Spaces and visual separators are removed from the number, the extension and a numeric
    phone-context, so printed forms such as ``+1 (201) 555-0123`` are accepted. A number
    with a leading ``+`` is global; any other needs ``phone_context``. ``isub`` is taken
    in its encoded form. ``params`` values are plain text and are percent-encoded.

    >>> from teluri import build
    >>> build("+1 (201)", params={"note": "a;b"})
    'tel:+1201;note=a%3Bb'
    """
    context = phone_context
    if context is not None and _unspaced(context).startswith("+"):
        context = _unspaced(context)
    uri = TelURI(
        _unspaced(number),
        ext=None if ext is None else _unspaced(ext),
        isub=isub,
        phone_context=context,
        params={} if params is None else params,
    )
    return str(uri)


def _unspaced(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("number, ext and phone_context must be strings when supplied")
    return "".join(char for char in str.__str__(text) if not char.isspace())
