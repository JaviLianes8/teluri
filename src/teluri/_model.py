"""The parsed representation of a tel: URI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ._build import build


@dataclass(frozen=True)
class TelURI:
    """A parsed tel: URI with its numeric parts already normalized.

    ``params`` holds every parameter other than ``ext`` and ``phone-context``,
    in order, with ``None`` for a value-less parameter.
    """

    number: str
    is_global: bool
    ext: str | None = None
    phone_context: str | None = None
    params: Mapping[str, str | None] = field(default_factory=dict)

    def __str__(self) -> str:
        return build(
            self.number,
            ext=self.ext,
            phone_context=self.phone_context,
            params=self.params,
        )
