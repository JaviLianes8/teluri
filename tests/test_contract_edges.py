"""Hand-written boundary contracts for contexts, links and equality dispatch."""

from __future__ import annotations

from urllib.parse import urlsplit

import pytest

from teluri import TelURI, TelURIError, build, parse, parse_link


@pytest.mark.parametrize("context", ["A" * 64 + ".com", ".".join(["Ab" * 31] * 5) + "."])
def test_domain_contexts_have_no_dns_length_limits(context: str) -> None:
    text = "tel:1;phone-context=" + context
    assert build("1", phone_context=context) == text
    for uri in (
        parse(text),
        TelURI("1", phone_context=context),
        parse_link(text),
        parse_link("tel:1", context=context),
    ):
        assert uri.phone_context == context
        assert str(uri) == text


def test_href_escapes_every_hash_and_round_trips_without_a_fragment() -> None:
    uri = TelURI("##1#", phone_context="+1")
    assert uri.href == "tel:%23%231%23;phone-context=+1"
    assert urlsplit(uri.href).fragment == ""
    assert parse_link(uri.href) == uri


def test_equality_returns_not_implemented_for_foreign_operands() -> None:
    uri = TelURI("+1")
    assert uri.__eq__(object()) is NotImplemented
    assert uri.__eq__("tel:+1") is NotImplemented


def test_equality_allows_the_reflected_comparison() -> None:
    uri = TelURI("+1")
    seen: list[object] = []

    class Reflected:
        def __eq__(self, other: object) -> bool:
            seen.append(other)
            return True

    assert uri == Reflected()
    assert seen == [uri]


@pytest.mark.parametrize("number", ["%252B1", "%2531", "%2523"])
def test_link_number_is_not_percent_decoded_twice(number: str) -> None:
    with pytest.raises(TelURIError) as caught:
        parse_link("tel:" + number, context="+1")
    assert caught.value.reason == "number"


@pytest.mark.parametrize("number,expected", [("%2B1", "+1"), ("%31", "1"), ("%23", "#")])
def test_link_number_accepts_a_single_percent_escape(number: str, expected: str) -> None:
    assert parse_link("tel:" + number, context="+1").number == expected
