"""build: human input in, canonical tel: URI out, invalid parts refused with a reason."""

from __future__ import annotations

import pytest

from teluri import TelURIError, build, parse


def test_printed_number_with_spaces_and_separators() -> None:
    assert build("+1 (201) 555-0123") == "tel:+12015550123"
    assert build("+44\u00a020\t7946") == "tel:+44207946"


def test_extension_and_numeric_context_lose_spaces() -> None:
    assert build("+1 201", ext="12 34") == "tel:+1201;ext=1234"
    assert build("863 1234", phone_context="+1 914 555") == "tel:8631234;phone-context=+1914555"


def test_domain_context_is_not_rewritten() -> None:
    assert build("7042", phone_context="example.com") == "tel:7042;phone-context=example.com"
    with pytest.raises(TelURIError) as caught:
        build("7042", phone_context="exa mple.com")
    assert caught.value.reason == "phone-context"


def test_isub_is_taken_encoded() -> None:
    assert build("+1", isub="a%2Fb") == "tel:+1;isub=a%2Fb"
    with pytest.raises(TelURIError) as caught:
        build("+1", isub="a b")
    assert caught.value.reason == "isub"


def test_params_are_sorted_lower_cased_and_encoded() -> None:
    uri = build("+1", ext="2", params={"Tgrp": "TG 1", "npdi": None, "rn": "+1-202"})
    assert uri == "tel:+1;ext=2;npdi;rn=+1-202;tgrp=TG%201"
    assert parse(uri, strict=True).params["tgrp"] == "TG 1"


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"number": ""}, "number"),
        ({"number": "   "}, "number"),
        ({"number": "7042"}, "missing-context"),
        ({"number": "+1", "phone_context": "a.b"}, "global-context"),
        ({"number": "+1", "ext": "x"}, "ext"),
        ({"number": "+1", "ext": "1", "isub": "1"}, "ext-and-isub"),
        ({"number": "+1", "params": {"phone-context": "a.b"}}, "param-name"),
        ({"number": "+1", "params": {"a b": "1"}}, "param-name"),
    ],
)
def test_invalid_parts_are_refused(kwargs: dict[str, object], reason: str) -> None:
    with pytest.raises(TelURIError) as caught:
        build(**kwargs)  # type: ignore[arg-type]
    assert caught.value.reason == reason


def test_output_always_parses_back_strictly() -> None:
    uri = build("12", phone_context="+1", params={"z": "a;b", "a": None})
    assert str(parse(uri, strict=True)) == uri
