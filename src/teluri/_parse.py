"""Parse a tel: URI (RFC 3966) into a validated :class:`TelURI`."""

from __future__ import annotations

from ._errors import Reason, TelURIError
from ._grammar import pname, pvalue
from ._model import TelURI

_FIELDS: dict[str, Reason] = {"ext": "ext", "isub": "isub", "phone-context": "phone-context"}


def parse(uri: str, *, strict: bool = False) -> TelURI:
    """Parse a tel: URI, raising :class:`TelURIError` with a reason if it is malformed.

    Parameters may come in any order, as the ABNF allows. With ``strict=True`` the order
    rule of section 3 is enforced too: ext or isub first, then phone-context, then the
    other parameters in lexicographic order.
    """
    scheme, colon, rest = uri.partition(":")
    if not colon or scheme.lower() != "tel":
        raise TelURIError("scheme", f"not a tel: URI: {uri!r}")
    number, *segments = rest.split(";")
    if not number:
        raise TelURIError("number", "the telephone number is empty")

    fields: dict[str, str] = {}
    params: dict[str, str | None] = {}
    order: list[str] = []
    for segment in segments:
        raw_name, equals, raw_value = segment.partition("=")
        name = pname(raw_name)
        if name in order:
            raise TelURIError("duplicate-param", f"{name!r} appears twice")
        order.append(name)
        if name in _FIELDS:
            if not raw_value:
                raise TelURIError(_FIELDS[name], f"{name} needs a value")
            fields[name] = raw_value
        elif equals:
            params[name] = pvalue(raw_value)
        else:
            params[name] = None

    result = TelURI(
        number,
        ext=fields.get("ext"),
        isub=fields.get("isub"),
        phone_context=fields.get("phone-context"),
        params=params,
    )
    if strict and order != _canonical_order(order):
        raise TelURIError("param-order", f"parameters out of order: {';'.join(order)}")
    return result


def _canonical_order(names: list[str]) -> list[str]:
    first = [name for name in ("ext", "isub", "phone-context") if name in names]
    return first + sorted(name for name in names if name not in _FIELDS)


def equivalent(a: str | TelURI, b: str | TelURI) -> bool:
    """True when two tel: URIs are equivalent under RFC 3966 section 4.

    Strings are parsed first, so a malformed one raises :class:`TelURIError`.
    """
    left = a if isinstance(a, TelURI) else parse(a)
    right = b if isinstance(b, TelURI) else parse(b)
    return left == right
