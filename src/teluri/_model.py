"""The parsed, validated representation of a tel: URI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import unquote_to_bytes

from ._chars import RESERVED_PARAMETERS, encode_value
from ._errors import TelURIError
from ._grammar import descriptor, extension, global_digits, local_digits, pname, subaddress
from ._params import Params

_E164_MAX_DIGITS = 15


@dataclass(frozen=True, eq=False)
class TelURI:
    """A valid tel: URI (RFC 3966) with visual separators removed from its numbers.

    Constructing one validates every field: a number with a leading ``+`` is global and
    takes no ``phone_context``; any other number is local and requires one. ``params``
    holds the remaining parameters by lower-case name, with decoded values and ``None``
    for a parameter without a value. ``==`` and ``hash`` follow RFC 3966 section 4 and
    ``str()`` gives the canonical form.

    >>> from teluri import TelURI
    >>> str(TelURI("7042", phone_context="example.com"))
    'tel:7042;phone-context=example.com'
    """

    number: str
    ext: str | None = None
    isub: str | None = None
    phone_context: str | None = None
    params: Mapping[str, str | None] = field(default_factory=lambda: Params({}))

    def __post_init__(self) -> None:
        _check_types(self)
        number = self.number
        is_global = number.startswith("+")
        set_ = object.__setattr__
        set_(self, "number", global_digits(number) if is_global else local_digits(number))
        if self.ext is not None and self.isub is not None:
            raise TelURIError("ext-and-isub", "ext and isub cannot both be present")
        if self.ext is not None:
            set_(self, "ext", extension(self.ext))
        if self.isub is not None:
            set_(self, "isub", subaddress(self.isub))
        if self.phone_context is not None:
            if is_global:
                raise TelURIError("global-context", "a global number takes no phone-context")
            set_(self, "phone_context", descriptor(self.phone_context))
        elif not is_global:
            raise TelURIError("missing-context", "a local number needs phone-context")
        set_(self, "params", _checked(self.params))

    @property
    def is_global(self) -> bool:
        """True for global syntax, written with a leading ``+``.

        >>> from teluri import TelURI
        >>> TelURI("+1").is_global
        True
        """
        return self.number.startswith("+")

    @property
    def is_e164(self) -> bool:
        """True for 1 to 15 global digits not starting with 0; no allocation check.

        >>> from teluri import TelURI
        >>> TelURI("+0123").is_e164
        False
        """
        digits = self.number[1:]
        return self.is_global and len(digits) <= _E164_MAX_DIGITS and digits[0] != "0"

    @property
    def unknown_mandatory(self) -> tuple[str, ...]:
        """Names of ``m-`` parameters, sorted; callers must understand these before use.

        >>> from teluri import TelURI
        >>> TelURI("+1", params={"m-z": None}).unknown_mandatory
        ('m-z',)
        """
        return tuple(name for name in self.params if name.startswith("m-"))

    @property
    def href(self) -> str:
        """The URI form for an HTML ``href``, with ``#`` escaped; still HTML-escape it.

        >>> from teluri import TelURI
        >>> TelURI("*31#", phone_context="+1").href
        'tel:*31%23;phone-context=+1'
        """
        return str(self).replace("#", "%23")

    def __str__(self) -> str:
        out = ["tel:", self.number]
        if self.ext is not None:
            out.append(";ext=" + self.ext)
        if self.isub is not None:
            out.append(";isub=" + self.isub)
        if self.phone_context is not None:
            out.append(";phone-context=" + self.phone_context)
        for name, value in self.params.items():
            out.append(f";{name}" if value is None else f";{name}={encode_value(value)}")
        return "".join(out)

    def __repr__(self) -> str:
        return f"TelURI({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TelURI):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def _key(self) -> tuple[object, ...]:
        context = self.phone_context
        if context is not None and not context.startswith("+"):
            context = context.lower().removesuffix(".")
        return (
            self.number.lower(),
            self.ext,
            None if self.isub is None else unquote_to_bytes(self.isub).lower(),
            context,
            frozenset(
                (name, None if value is None else value.encode("utf-8").lower())
                for name, value in self.params.items()
            ),
        )


def _check_types(uri: TelURI) -> None:
    if not isinstance(uri.number, str):
        raise TypeError("number must be a str")
    object.__setattr__(uri, "number", str.__str__(uri.number))
    for name in ("ext", "isub", "phone_context"):
        value = getattr(uri, name)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{name} must be a str or None")
        if value is not None:
            object.__setattr__(uri, name, str.__str__(value))
    if not isinstance(uri.params, Mapping) or not all(isinstance(k, str) for k in uri.params):
        raise TypeError("params must be a mapping with str keys")


def _checked(params: Mapping[str, str | None]) -> Params:
    items: dict[str, str | None] = {}
    for raw, value in params.items():
        name = pname(str.__str__(raw))
        if name in RESERVED_PARAMETERS:
            raise TelURIError("param-name", "reserved parameters have their own fields")
        if name in items:
            raise TelURIError("duplicate-param", "a parameter appears twice")
        if isinstance(value, str):
            value = str.__str__(value)
        if value is not None and (not isinstance(value, str) or not value or _unencodable(value)):
            raise TelURIError("param-value", "parameters need non-empty text values or None")
        items[name] = value
    return Params(dict(sorted(items.items())))


def _unencodable(text: str) -> bool:
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:  # a lone surrogate cannot be written in a URI
        return True
    return False
