"""Parse, build and compare tel: URIs per RFC 3966, zero dependencies and fully typed."""

from __future__ import annotations

from typing import get_type_hints as _get_type_hints

from ._build import build
from ._errors import Reason, TelURIError
from ._link import parse_link
from ._model import TelURI
from ._parse import equivalent, parse

__version__ = "1.0.0"

TelURI.__annotations__ = _get_type_hints(TelURI)
TelURI.__module__ = __name__
TelURIError.__module__ = __name__

del annotations

__all__ = ["Reason", "TelURI", "TelURIError", "build", "equivalent", "parse", "parse_link"]
