"""A read-only, hashable, picklable mapping for the extra parameters of a tel: URI."""

from __future__ import annotations

from collections.abc import Iterator, Mapping


class Params(Mapping[str, "str | None"]):
    """Parameters other than ext, isub and phone-context, keyed by lower-case name."""

    __slots__ = ("_items",)

    def __init__(self, items: Mapping[str, str | None]) -> None:
        self._items = dict(items)

    def __getitem__(self, name: str) -> str | None:
        return self._items[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __hash__(self) -> int:
        return hash(frozenset(self._items.items()))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Mapping):
            return dict(self._items) == dict(other)
        return NotImplemented

    def __repr__(self) -> str:
        return f"Params({self._items!r})"

    def __reduce__(self) -> tuple[type[Params], tuple[dict[str, str | None]]]:
        return (Params, (self._items,))
