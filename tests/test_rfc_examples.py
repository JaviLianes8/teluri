"""Every tel: URI printed in RFC 3966 and the parameter RFCs parses, strictly, and round-trips.

The URIs in tests/data/examples.json were extracted by script from the RFC texts named in
tests/upstream/MANIFEST.json. The canonical forms below are written by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from teluri import parse

DATA = json.loads((Path(__file__).parent / "data" / "examples.json").read_text("utf-8"))
ALL = [uri for uris in DATA["uris"].values() for uri in uris]


@pytest.mark.parametrize("uri", ALL)
def test_every_rfc_example_parses_strictly_and_round_trips(uri: str) -> None:
    parsed = parse(uri, strict=True)
    assert parse(str(parsed), strict=True) == parsed
    assert str(parse(str(parsed))) == str(parsed)


def test_the_extraction_found_the_examples() -> None:
    assert len(ALL) == 25
    assert "tel:7042;phone-context=example.com" in DATA["uris"]["rfc3966"]


@pytest.mark.parametrize(
    ("uri", "canonical"),
    [
        ("tel:+1-201-555-0123", "tel:+12015550123"),
        ("tel:863-1234;phone-context=+1-914-555", "tel:8631234;phone-context=+1914555"),
        ("tel:+1-202-533-1234;npdi;rn=+1-202-544-0000", "tel:+12025331234;npdi;rn=+1-202-544-0000"),
        (
            "tel:5550100;phone-context=+1-630;tgrp=TG-1;trunk-context=example.com",
            "tel:5550100;phone-context=+1630;tgrp=TG-1;trunk-context=example.com",
        ),
    ],
)
def test_canonical_forms_of_rfc_examples(uri: str, canonical: str) -> None:
    assert str(parse(uri)) == canonical


def test_section_4_comparison_of_rfc_examples() -> None:
    assert parse("tel:+1-201-555-0123") == parse("tel:+12015550123")
    assert parse("tel:863-1234;phone-context=+1-914-555") != parse("tel:+1-914-555-863-1234")


def test_the_registered_parameters_from_the_rfcs_are_kept() -> None:
    uri = parse("tel:+17005554141;isub=12345;isub-encoding=nsap-ia5")
    assert uri.isub == "12345"
    assert dict(uri.params) == {"isub-encoding": "nsap-ia5"}
    assert dict(parse("tel:+441632960038;enumdi").params) == {"enumdi": None}
