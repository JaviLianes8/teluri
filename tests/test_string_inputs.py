"""Hand-written contracts for string subclasses at public input boundaries."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from teluri import TelURI, TelURIError, build, equivalent, parse, parse_link


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


class ReindexedText(str):
    def __getitem__(self, key: object) -> str:
        return "tel:+9"


class ReindexedDigits(str):
    def __getitem__(self, key: object) -> str:
        return "99"


class DigitIteratorText(str):
    def __iter__(self) -> Iterator[str]:
        return iter("1")


class FalsyDigits(DigitIteratorText):
    def __bool__(self) -> bool:
        return False


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


@pytest.mark.parametrize("strict", [False, True])
def test_parser_preserves_number_when_subclass_overrides_partition(strict: bool) -> None:
    uri = parse(AlteredText("tel:+1"), strict=strict)
    assert uri.number == "+1"
    assert str(uri) == "tel:+1"


def test_link_parser_uses_the_underlying_string_and_context() -> None:
    assert str(parse_link(AlteredText(" tel:12 "), context=AlteredText("example.com"))) == (
        "tel:12;phone-context=example.com"
    )


@pytest.mark.parametrize("strict", [False, True])
def test_parser_preserves_number_when_subclass_overrides_indexing(strict: bool) -> None:
    uri = parse(ReindexedText("tel:+1"), strict=strict)
    assert uri.number == "+1"
    assert str(uri) == "tel:+1"


def test_equivalence_uses_underlying_text_when_indexing_is_overridden() -> None:
    uri = ReindexedText("tel:+1")
    for other in ("tel:+1", TelURI("+1")):
        assert equivalent(uri, other)
        assert equivalent(other, uri)
    assert not equivalent(uri, "tel:+9")
    assert not equivalent("tel:+9", uri)


def test_constructor_preserves_number_when_subclass_overrides_indexing() -> None:
    uri = TelURI(ReindexedDigits("12"), phone_context="+1")
    assert uri.number == "12"
    assert str(uri) == "tel:12;phone-context=+1"


def test_constructor_preserves_extension_when_subclass_overrides_indexing() -> None:
    uri = TelURI("+1", ext=ReindexedDigits("23"))
    assert uri.ext == "23"
    assert str(uri) == "tel:+1;ext=23"


@pytest.mark.parametrize("number", ["1x", "1;ext=9"])
def test_constructor_rejects_invalid_number_hidden_by_subclass_iteration(number: str) -> None:
    with pytest.raises(TelURIError) as caught:
        TelURI(DigitIteratorText(number), phone_context="+1")
    assert caught.value.reason == "number"


@pytest.mark.parametrize("extension", ["x", "1x"])
def test_constructor_rejects_invalid_extension_hidden_by_subclass_iteration(extension: str) -> None:
    with pytest.raises(TelURIError) as caught:
        TelURI("+1", ext=DigitIteratorText(extension))
    assert caught.value.reason == "ext"


@pytest.mark.parametrize("extension", ["x", "1x"])
def test_constructor_rejects_invalid_false_valued_extension(extension: str) -> None:
    with pytest.raises(TelURIError) as caught:
        TelURI("+1", ext=FalsyDigits(extension))
    assert caught.value.reason == "ext"


def test_constructor_preserves_false_valued_extension_and_context() -> None:
    uri = TelURI("12", ext=FalsyDigits("23"), phone_context=FalsyDigits("Example.com"))
    assert type(uri.ext) is str and type(uri.phone_context) is str
    assert (uri.ext, uri.phone_context) == ("23", "Example.com")
    assert str(uri) == "tel:12;ext=23;phone-context=Example.com"


def test_constructor_preserves_false_valued_subaddress() -> None:
    uri = TelURI("+1", isub=FalsyDigits("a%FF"))
    assert type(uri.isub) is str
    assert uri.isub == "a%FF"
    assert str(uri) == "tel:+1;isub=a%FF"


def test_subclass_parameter_names_cannot_hide_reserved_fields() -> None:
    with pytest.raises(TelURIError) as caught:
        TelURI("+1", params={AlteredText("ext"): "9"})
    assert caught.value.reason == "param-name"
