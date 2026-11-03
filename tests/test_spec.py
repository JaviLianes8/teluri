"""Contracts derived from sources fetched on 2026-11-01; see the hash manifest."""

from __future__ import annotations

import html
import io
import re
import string
import xml.etree.ElementTree as ET

import pytest
from conftest import read_upstream

from teluri import TelURIError, build, parse, parse_link


def _rule(text: str, name: str) -> str:
    match = re.search(rf"^   {name}\s*=\s*(.*(?:\n {{20,}}.*)*)", text, re.MULTILINE)
    assert match, name
    return match.group(1)


def _literals(rule: str) -> set[str]:
    return set(re.findall(r'"([^"]+)"', rule))


def test_numeric_character_sets_come_from_the_fetched_grammar() -> None:
    text = read_upstream("rfc3966.txt").decode("ascii")
    visual = _literals(_rule(text, "visual-separator"))
    assert "DIGIT" in _rule(text, "global-number-digits")
    assert "HEXDIG" in _rule(text, "local-number-digits")
    local_extra = _literals(_rule(text, "phonedigit-hex"))
    for code in range(512):
        char = chr(code)
        if char == ";":  # a delimiter can start a valid flag parameter
            continue
        for prefix, context, allowed in [
            ("+", "", set(string.digits) | visual),
            ("", ";phone-context=example.com", set(string.hexdigits) | local_extra | visual),
        ]:
            candidate = f"tel:{prefix}1{char}2{context}"
            if char in allowed:
                assert (
                    parse(candidate).number == prefix + "1" + ("" if char in visual else char) + "2"
                )
            else:
                with pytest.raises(TelURIError):
                    parse(candidate)


def test_parameter_characters_match_the_fetched_abnf() -> None:
    text = read_upstream("rfc3966.txt").decode("ascii")
    allowed = set(string.ascii_letters + string.digits)
    allowed |= _literals(_rule(text, "mark")) | _literals(_rule(text, "param-unreserved"))
    for code in range(512):
        char = chr(code)
        # Semicolon is structural, so it is tested as a delimiter elsewhere.
        if char == ";":
            continue
        candidate = "tel:+1;x=a" + char + "b"
        if char in allowed:
            assert parse(candidate).params["x"] == "a" + char + "b"
        else:
            with pytest.raises(TelURIError):
                parse(candidate)


def test_verified_erratum_changes_isub_to_paramchar() -> None:
    text = html.unescape(read_upstream("errata203.html").decode())
    assert "Verified" in text and '";isub=" 1*paramchar' in text
    for char in "?@=;":
        with pytest.raises(TelURIError):
            parse("tel:+1;isub=" + char)
        assert parse(f"tel:+1;isub=%{ord(char):02X}").isub == f"%{ord(char):02X}"


def test_iana_parameter_names_are_preserved() -> None:
    root = ET.fromstring(read_upstream("iana.xml"))
    namespace = {"i": "http://www.iana.org/assignments"}
    names = [node.text for node in root.findall(".//i:record/i:parameter", namespace)]
    assert len(names) >= 10
    for name in names:
        assert name
        if name not in {"ext", "isub", "phone-context"}:
            assert parse(build("+1", params={name: "example"})).params[name] == "example"


def test_apple_and_mdn_link_examples_are_read_from_the_downloads() -> None:
    apple = html.unescape(read_upstream("apple.html").decode())
    mdn = html.unescape(read_upstream("mdn.html").decode())
    assert "tel:1-408-555-5555" in apple
    assert str(parse_link("tel:1-408-555-5555", context="+1")) == (
        "tel:14085555555;phone-context=+1"
    )
    for uri in ("tel:+49.157.0156", "tel:+1(800)555-0123"):
        assert uri in mdn
        assert parse_link(uri) == parse(uri)


def test_reference_number_formatter_agrees_on_real_region_examples() -> None:
    reference = pytest.importorskip("phonenumbers")
    count = 0
    for region in sorted(reference.SUPPORTED_REGIONS):
        number = reference.example_number(region)
        if number is None:
            continue
        number.extension = "1234"
        uri = reference.format_number(number, reference.PhoneNumberFormat.RFC3966)
        digits = reference.format_number(number, reference.PhoneNumberFormat.E164)
        parsed = parse(uri, strict=True)
        assert parsed.number == digits
        assert parsed.ext == "1234"
        assert str(parsed) == build(digits, ext="1234")
        assert reference.parse(str(parsed), None) == number
        count += 1
    assert count >= 200


def test_length_limit_is_derived_from_the_current_itu_text() -> None:
    pdf = pytest.importorskip("pypdf")
    reader = pdf.PdfReader(io.BytesIO(read_upstream("e164.pdf")))
    text = " ".join(" ".join(page.extract_text() for page in reader.pages).split())
    match = re.search(r"A\.3\.1\.1.*?maximum length of (\d+) digits", text)
    assert match
    limit = int(match.group(1))
    assert parse("tel:+" + "1" * limit).is_e164
    assert not parse("tel:+" + "1" * (limit + 1)).is_e164
