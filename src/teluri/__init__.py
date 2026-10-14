"""Parse, build and compare tel: URIs per RFC 3966, zero dependencies and fully typed."""

from __future__ import annotations

from ._build import build
from ._errors import Reason, TelURIError
from ._link import parse_link
from ._model import TelURI
from ._parse import equivalent, parse

__version__ = "0.2.0"

__all__ = ["Reason", "TelURI", "TelURIError", "build", "equivalent", "parse", "parse_link"]
