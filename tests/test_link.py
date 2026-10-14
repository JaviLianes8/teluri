"""parse_link: tel: links as written in web pages and apps (a documented non-RFC dialect)."""

from __future__ import annotations

import pytest

from teluri import TelURIError, parse_link


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        # MDN <a> element page, fetched 2026-10-14 (see IMPROVEMENTS-round.md).
        ("tel:+49.157.0156", "tel:+491570156"),
        ("tel:+1(800)555-0123", "tel:+18005550123"),
        # Written by hand: spaces, encoded spaces and plus, surrounding whitespace.
        ("  tel:+1 201 555 0123 ", "tel:+12015550123"),
        ("tel:%2B1%20201%C2%A0555", "tel:+1201555"),
        ("Tel:+1;Ext=9", "tel:+1;ext=9"),
    ],
)
def test_links_with_a_global_number(href: str, expected: str) -> None:
    assert str(parse_link(href)) == expected


def test_local_link_takes_the_default_context() -> None:
    # Apple Phone Links reference example (no phone-context), fetched 2026-10-14.
    uri = parse_link("tel:1-408-555-5555", context="+1")
    assert str(uri) == "tel:14085555555;phone-context=+1"


def test_local_link_with_params_gets_the_context_appended() -> None:
    assert str(parse_link("tel:*31%23;x=1", context="example.com")) == (
        "tel:*31#;phone-context=example.com;x=1"
    )


def test_the_links_own_context_wins() -> None:
    uri = parse_link("tel:5;PHONE-CONTEXT=a.b", context="c.d")
    assert uri.phone_context == "a.b"


def test_a_global_link_ignores_the_default_context() -> None:
    assert parse_link("tel:+1", context="a.b").phone_context is None


@pytest.mark.parametrize(
    ("href", "kwargs", "reason"),
    [
        ("tel:555-0100", {}, "missing-context"),
        ("http:+1", {}, "scheme"),
        ("tel:+1%3B2", {}, "number"),
        ("tel:+1%252", {}, "number"),
        ("tel:+1%FF", {}, "number"),
        ("tel:   ", {}, "number"),
        ("tel:1", {"context": "bad context"}, "phone-context"),
        ("tel:+1;a=b c", {}, "param-value"),
    ],
)
def test_links_that_still_cannot_be_read(href: str, kwargs: dict[str, str], reason: str) -> None:
    with pytest.raises(TelURIError) as caught:
        parse_link(href, **kwargs)
    assert caught.value.reason == reason
