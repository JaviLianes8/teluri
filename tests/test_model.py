"""TelURI: validation on construction, canonical str, section 4 equality, properties."""

from __future__ import annotations

import dataclasses
import pickle

import pytest

from teluri import TelURI, TelURIError, equivalent, parse


def test_construction_normalizes_like_parse() -> None:
    assert TelURI("863-1234", phone_context="+1-914-555") == parse(
        "tel:8631234;phone-context=+1914555"
    )


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"number": "12"}, "missing-context"),
        ({"number": "+1", "phone_context": "a.b"}, "global-context"),
        ({"number": "+1", "ext": "1", "isub": "2"}, "ext-and-isub"),
        ({"number": "+1", "params": {"EXT": "1"}}, "param-name"),
        ({"number": "+1", "params": {"isub": "1"}}, "param-name"),
        ({"number": "+1", "params": {"a": "1", "A": "2"}}, "duplicate-param"),
        ({"number": "+1", "params": {"a": ""}}, "param-value"),
        ({"number": "+1", "params": {"a": 1}}, "param-value"),
    ],
)
def test_construction_refuses_invalid_fields(kwargs: dict[str, object], reason: str) -> None:
    with pytest.raises(TelURIError) as caught:
        TelURI(**kwargs)  # type: ignore[arg-type]
    assert caught.value.reason == reason


def test_str_writes_the_section_3_order() -> None:
    uri = parse("tel:1;z=1;phone-context=a.b;Ab;isub=x")
    assert str(uri) == "tel:1;isub=x;phone-context=a.b;ab;z=1"


def test_str_encodes_values_that_need_it() -> None:
    uri = TelURI("+1", params={"note": "a b;c=d%\u00e9", "keep": "[x]/:&+$-_.!~*'()"})
    assert str(uri) == "tel:+1;keep=[x]/:&+$-_.!~*'();note=a%20b%3Bc%3Dd%25%C3%A9"
    assert parse(str(uri)) == uri
    assert parse(str(uri)).params["note"] == "a b;c=d%\u00e9"


def test_repr_shows_the_canonical_form() -> None:
    assert repr(parse("tel:+1-2")) == "TelURI('tel:+12')"


def test_equality_follows_section_4() -> None:
    assert parse("tel:+1-201-555-0123;Ext=1;A=X;b") == parse("tel:+12015550123;b;a=x;ext=1")
    assert parse("tel:7a;phone-context=Example.COM.") == parse("tel:7A;phone-context=example.com")
    assert parse("tel:1;phone-context=+1-914") == parse("tel:1;phone-context=+1914")
    assert parse("tel:+1;isub=%41b%2f") == parse("tel:+1;isub=aB%2F")
    assert parse("tel:+1;x=caf%C3%89") == parse("tel:+1;x=CAF%C3%A9")


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("tel:+1234", "tel:1234;phone-context=+1"),
        ("tel:+1;a", "tel:+1"),
        ("tel:+1;a", "tel:+1;a=1"),
        ("tel:+1;ext=1", "tel:+1;ext=2"),
        ("tel:+1;ext=1", "tel:+1;isub=1"),
        ("tel:1;phone-context=+12", "tel:1;phone-context=+1"),
        ("tel:1;phone-context=a.b", "tel:1;phone-context=b.a"),
        ("tel:+1;isub=%2F", "tel:+1;isub=/"),
    ],
)
def test_different_uris_are_unequal(left: str, right: str) -> None:
    assert parse(left) != parse(right)
    assert not equivalent(left, right)


def test_hash_agrees_with_equality() -> None:
    uris = {parse("tel:+1;B=x;a"), parse("tel:+1;a;b=X"), parse("tel:+2")}
    assert len(uris) == 2


def test_equivalent_accepts_strings_and_models() -> None:
    assert equivalent("tel:+1-2", parse("TEL:+12"))
    with pytest.raises(TelURIError):
        equivalent("tel:+1", "tel:x")


def test_comparison_with_other_types_is_not_equal() -> None:
    assert parse("tel:+1") != "tel:+1"


def test_the_model_is_immutable_and_picklable() -> None:
    uri = parse("tel:1;phone-context=a.b;x=1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        uri.number = "2"  # type: ignore[misc]
    with pytest.raises(TypeError):
        uri.params["x"] = "2"  # type: ignore[index]
    copy = pickle.loads(pickle.dumps(uri))
    assert copy == uri
    assert str(copy) == str(uri)


def test_replace_revalidates() -> None:
    uri = parse("tel:+1;ext=1")
    assert str(dataclasses.replace(uri, ext="2-3")) == "tel:+1;ext=23"
    with pytest.raises(TelURIError):
        dataclasses.replace(uri, isub="9")


@pytest.mark.parametrize(
    ("uri", "expected"),
    [
        ("tel:+1", True),
        ("tel:+123456789012345", True),
        ("tel:+1234567890123456", False),
        ("tel:+0123", False),
        ("tel:123;phone-context=+1", False),
    ],
)
def test_is_e164_checks_length_and_country_code(uri: str, expected: bool) -> None:
    assert parse(uri).is_e164 is expected


def test_unknown_mandatory_lists_m_parameters() -> None:
    assert parse("tel:+1;m-b=1;a;M-a").unknown_mandatory == ("m-a", "m-b")
    assert parse("tel:+1;ma;x-m").unknown_mandatory == ()


def test_href_escapes_the_hash_only() -> None:
    uri = parse("tel:*31#;phone-context=+1;x=a%23")
    assert uri.href == "tel:*31%23;phone-context=+1;x=a%23"
    assert str(uri) == "tel:*31#;phone-context=+1;x=a%23"


def test_params_mapping_behaves_like_a_mapping() -> None:
    params = parse("tel:+1;b=2;a").params
    assert list(params) == ["a", "b"]
    assert len(params) == 2
    assert params == {"a": None, "b": "2"}
    assert params.__eq__(["a"]) is NotImplemented
    assert repr(params) == "Params({'a': None, 'b': '2'})"
    assert hash(params) == hash(frozenset({("a", None), ("b", "2")}))
