"""Hand-written contracts for string subclasses at public input boundaries."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from teluri import TelURI, TelURIError, build, parse, parse_link


class ShortText(str):
    def __len__(self) -> int:
        return 1


class LongText(str):
    def __len__(self) -> int:
        return 100


class AlteredText(ShortText):
    def __str__(self) -> str:
        return "different"

    def __iter__(self) -> Iterator[str]:
        return iter("9")

    def lower(self) -> str:
        return "different"

    def partition(self, sep: str) -> tuple[str, str, str]:
        return "tel", ":", "+9"

    def strip(self, chars: str | None = None) -> str:
        return "tel:+9"


@pytest.mark.parametrize("text_type", [ShortText, LongText, AlteredText])
@pytest.mark.parametrize("value", ["a;ext=9", "a\nSECRET", "a%", ""])
def test_subclass_subaddresses_validate_the_complete_text(text_type: type[str], value: str) -> None:
    for constructor in (TelURI, build):
        with pytest.raises(TelURIError) as caught:
            constructor("+1", isub=text_type(value))
        assert caught.value.reason == "isub"


@pytest.mark.parametrize("text_type", [ShortText, LongText, AlteredText])
def test_subclass_subaddresses_are_stored_as_plain_strings(text_type: type[str]) -> None:
    uri = TelURI("+1", isub=text_type("a%FF"))
    assert type(uri.isub) is str
    assert uri.isub == "a%FF"
    assert build("+1", isub=text_type("a%FF")) == "tel:+1;isub=a%FF"
    assert parse(str(uri), strict=True) == uri


def test_constructor_normalizes_all_string_fields_and_mapping_entries() -> None:
    uri = TelURI(
        AlteredText("12"),
        ext=AlteredText("3"),
        phone_context=AlteredText("Example.com"),
        params={AlteredText("NOTE"): AlteredText("a;b")},
    )
    assert str(uri) == "tel:12;ext=3;phone-context=Example.com;note=a%3Bb"
    assert all(type(value) is str for value in (uri.number, uri.ext, uri.phone_context))
    assert all(type(key) is str and type(value) is str for key, value in uri.params.items())
    assert parse(str(uri), strict=True) == uri


def test_builder_normalizes_strings_before_removing_whitespace() -> None:
    result = build(AlteredText("1 2"), ext=AlteredText("3 4"), phone_context=AlteredText("+5 6"))
    assert result == "tel:12;ext=34;phone-context=+56"


def test_parsers_use_the_underlying_string_and_context() -> None:
    assert str(parse(AlteredText("tel:+1"))) == "tel:+1"
    assert str(parse_link(AlteredText(" tel:12 "), context=AlteredText("example.com"))) == (
        "tel:12;phone-context=example.com"
    )


def test_subclass_parameter_names_cannot_hide_reserved_fields() -> None:
    with pytest.raises(TelURIError) as caught:
        TelURI("+1", params={AlteredText("ext"): "9"})
    assert caught.value.reason == "param-name"
