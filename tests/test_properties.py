"""Seeded generated cases, distinct from external reference vectors."""

from __future__ import annotations

import random
import string

import pytest

from teluri import TelURIError, build, equivalent, parse, parse_link


@pytest.mark.parametrize("seed", [3966, 203, 20261101])
def test_hostile_text_has_typed_failures_or_stable_round_trips(seed: int) -> None:
    rng = random.Random(seed)
    alphabet = string.printable + "\x00\x1b\u00e9\u0661\ud800\U0001f642"
    for _ in range(5000):
        text = rng.choice(["", "tel:", "tel:+1;", "tel:1;phone-context="])
        text += "".join(rng.choices(alphabet, k=rng.randrange(90)))
        for parser in (parse, parse_link):
            try:
                uri = parser(text)
            except TelURIError as error:
                assert len(str(error)) < 100
            else:
                canonical = str(uri)
                again = parse(canonical, strict=True)
                assert again == uri and hash(again) == hash(uri)
                assert str(again) == canonical
                assert parse_link(uri.href) == uri


@pytest.mark.parametrize("seed", [3966, 203, 20261101])
def test_generated_values_round_trip_and_match_known_fields(seed: int) -> None:
    rng = random.Random(seed)
    alphabet = string.printable + "\x00\u00e9\U0001f642"
    for _ in range(1500):
        global_ = rng.choice([False, True])
        digits = "".join(rng.choices("0123456789" if global_ else "012abCF*#", k=12))
        number = ("+" if global_ else "") + digits
        context = None if global_ else rng.choice(["+1-23", "Example.COM."])
        ext = "".join(rng.choices("0123456789", k=4))
        value = "".join(rng.choices(alphabet, k=rng.randrange(1, 50)))
        built = build(number, ext=ext, phone_context=context, params={"X": value, "flag": None})
        uri = parse(built, strict=True)
        assert uri.number == number
        assert uri.ext == ext
        assert uri.phone_context == ("+123" if context == "+1-23" else context)
        assert dict(uri.params) == {"flag": None, "x": value}
        assert uri.is_global is global_
        assert uri.is_e164 is (global_ and not digits.startswith("0"))
        alternate = built.replace("tel:", "TEL:").replace(";flag;", ";FLAG;")
        assert equivalent(uri, alternate)
        assert parse_link(uri.href) == uri


def test_many_parameters_remain_distinct_and_canonical() -> None:
    names = [f"p{index:05d}" for index in range(20_000)]
    text = "tel:+1;" + ";".join(reversed(names))
    uri = parse(text)
    assert list(uri.params) == names
    assert str(uri) == "tel:+1;" + ";".join(names)
    assert parse(str(uri), strict=True) == uri
    with pytest.raises(TelURIError) as caught:
        parse(text + ";P00000")
    assert caught.value.reason == "duplicate-param"


def test_large_numbers_and_values_are_not_silently_truncated() -> None:
    number = "+" + "1" * 1_000_000
    uri = parse("tel:" + number + ";x=" + "%20" * 100_000)
    assert uri.number == number
    assert uri.params["x"] == " " * 100_000
    assert not uri.is_e164
    assert parse(str(uri)) == uri
