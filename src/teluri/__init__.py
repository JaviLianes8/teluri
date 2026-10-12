"""Parse and build tel: URIs per RFC 3966, zero dependencies and fully typed."""

from __future__ import annotations

from ._build import build
from ._errors import TelURIError
from ._model import TelURI
from ._parse import parse

__version__ = "0.1.0"

__all__ = ["TelURI", "TelURIError", "build", "parse"]
