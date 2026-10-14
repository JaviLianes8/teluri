"""parse: the RFC 3966 grammar, accepted forms and the reason for each rejection."""

from __future__ import annotations

import pytest

from teluri import TelURIError, parse


def test_global_number_drops_visual_separators() -> None:
    uri = parse("tel:+1-201-555-0123")
    assert uri.number == "+12015550123"
    assert uri.is_global
    assert (uri.ext, uri.isub, uri.phone_context, dict(uri.params)) == (None, None, None, {})


def test_scheme_is_case_insensitive() -> None:
    assert str(parse("TEL:+1")) == "tel:+1"


def test_local_number_keeps_hex_star_and_hash() -> None:
    uri = parse("tel:*3.1#a-F;phone-context=example.com")
    assert uri.number == "*31#aF"
    assert not uri.is_global


def test_ext_isub_and_context_get_their_own_fields() -> None:
    uri = parse("tel:863-1234;phone-context=+1-914-555;ext=1-2")
    assert (uri.ext, uri.phone_context) == ("12", "+1914555")
    assert parse("tel:+1;isub=a%2Fb").isub == "a%2Fb"


def test_other_parameters_are_named_in_lower_case_and_decoded() -> None:
    uri = parse("tel:+1;Tag;Foo=caf%C3%A9+x")
    assert dict(uri.params) == {"foo": "caf\u00e9+x", "tag": None}


def test_domain_context_with_root_dot_and_digits_in_labels() -> None:
    assert parse("tel:1;phone-context=a-1.9b.Example.").phone_context == "a-1.9b.Example."


@pytest.mark.parametrize(
    ("uri", "reason"),
    [
        ("sip:+1", "scheme"),
        ("tel", "scheme"),
        ("tel:", "number"),
        ("tel:;ext=1", "number"),
        ("tel:+", "number"),
        ("tel:+-.", "number"),
        ("tel:+1a", "number"),
        ("tel:+1 2", "number"),
        ("tel:+\u0661", "number"),
        ("tel:--;phone-context=a.b", "number"),
        ("tel:12g;phone-context=a.b", "number"),
        ("tel:+1?x=y", "number"),
        ("tel:863-1234", "missing-context"),
        ("tel:+1;phone-context=example.com", "global-context"),
        ("tel:1;phone-context=", "phone-context"),
        ("tel:1;phone-context", "phone-context"),
        ("tel:1;phone-context=+", "phone-context"),
        ("tel:1;phone-context=-a.com", "phone-context"),
        ("tel:1;phone-context=a-.com", "phone-context"),
        ("tel:1;phone-context=a..com", "phone-context"),
        ("tel:1;phone-context=example.9", "phone-context"),
        ("tel:1;phone-context=.", "phone-context"),
        ("tel:1;phone-context=ex_ample.com", "phone-context"),
        ("tel:+1;ext", "ext"),
        ("tel:+1;ext=", "ext"),
        ("tel:+1;ext=-", "ext"),
        ("tel:+1;ext=12x", "ext"),
        ("tel:+1;ext=+1", "ext"),
        ("tel:+1;isub", "isub"),
        ("tel:+1;isub=a%zz", "isub"),
        ("tel:+1;isub=a%2", "isub"),
        ("tel:+1;isub=a b", "isub"),
        ("tel:+1;isub=a?", "isub"),
        ("tel:+1;ext=1;isub=2", "ext-and-isub"),
        ("tel:+1;", "param-name"),
        ("tel:+1;=x", "param-name"),
        ("tel:+1;a_b", "param-name"),
        ("tel:+1;a=", "param-value"),
        ("tel:+1;a=b c", "param-value"),
        ("tel:+1;a=%zz", "param-value"),
        ("tel:+1;a=%FF", "param-value"),
        ("tel:+1;a=x=y", "param-value"),
        ("tel:+1;a=#", "param-value"),
        ("tel:+1;ext=1;EXT=2", "duplicate-param"),
        ("tel:+1;a;A=1", "duplicate-param"),
        ("tel:1;phone-context=a.b;phone-context=a.b", "duplicate-param"),
    ],
)
def test_malformed_input_names_the_rule(uri: str, reason: str) -> None:
    with pytest.raises(TelURIError) as caught:
        parse(uri)
    assert caught.value.reason == reason


def test_any_parameter_order_is_accepted_by_default() -> None:
    assert str(parse("tel:1;z;phone-context=a.b;ext=2;b=1")) == (
        "tel:1;ext=2;phone-context=a.b;b=1;z"
    )


@pytest.mark.parametrize(
    "uri",
    [
        "tel:1;phone-context=a.b;ext=2",
        "tel:+1;b;a",
        "tel:1;a;phone-context=a.b",
        "tel:+1;isub=1;ext=2",
    ],
)
def test_strict_mode_refuses_parameters_out_of_order(uri: str) -> None:
    with pytest.raises(TelURIError) as caught:
        parse(uri, strict=True)
    assert caught.value.reason in {"param-order", "ext-and-isub"}


def test_strict_mode_accepts_the_section_3_order() -> None:
    uri = "tel:1;isub=9;phone-context=a.b;a;b=1;m-x"
    assert str(parse(uri, strict=True)) == uri


def test_strict_order_failure_has_its_own_reason() -> None:
    with pytest.raises(TelURIError) as caught:
        parse("tel:+1;b;a", strict=True)
    assert caught.value.reason == "param-order"
