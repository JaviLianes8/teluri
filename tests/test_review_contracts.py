"""Contracts closing the gaps found by the first independent review of 1.0.0."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from teluri import TelURI, TelURIError, build, equivalent, parse

BAD_EXTENSIONS = ["12a", "1*", "#", "A", "*#", "1-f", "%31"]


def _assert_ext_error(call: Callable[[], object]) -> None:
    with pytest.raises(TelURIError) as caught:
        call()
    assert caught.value.reason == "ext"


@pytest.mark.parametrize("value", BAD_EXTENSIONS)
def test_parse_refuses_an_extension_outside_digits_and_separators(value: str) -> None:
    _assert_ext_error(lambda: parse(f"tel:+1;ext={value}"))
    _assert_ext_error(lambda: parse(f"tel:1;ext={value};phone-context=+1"))


@pytest.mark.parametrize("value", BAD_EXTENSIONS)
def test_constructor_and_build_refuse_the_same_extensions(value: str) -> None:
    _assert_ext_error(lambda: TelURI("+1", ext=value))
    _assert_ext_error(lambda: build("+1", ext=value))


@pytest.mark.parametrize(("value", "digits"), [("1-2.(3)", "123"), ("0", "0")])
def test_digits_and_separators_remain_a_valid_extension(value: str, digits: str) -> None:
    assert parse(f"tel:+1;ext={value}").ext == digits
    assert TelURI("+1", ext=value).ext == digits
    assert build("+1", ext=value) == f"tel:+1;ext={digits}"


def _json(uri: str) -> object:
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    result = subprocess.run(
        [sys.executable, "-m", "teluri", "--json", uri],
        capture_output=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert (result.returncode, result.stderr) == (0, b"")
    return json.loads(result.stdout)


@pytest.mark.parametrize("number", ["+0123", "+1234567890123456"])
def test_json_tells_a_global_number_from_an_e164_number(number: str) -> None:
    assert _json(f"tel:{number}") == {
        "uri": f"tel:{number}",
        "number": number,
        "global": True,
        "e164": False,
        "ext": None,
        "isub": None,
        "phone_context": None,
        "params": {},
    }


@pytest.mark.parametrize(
    ("a", "b", "message"),
    [
        (5, "tel:+1", "a must be a str or TelURI"),
        ("tel:+1", 5, "b must be a str or TelURI"),
        (parse("tel:+1"), None, "b must be a str or TelURI"),
        (b"tel:+1", parse("tel:+1"), "a must be a str or TelURI"),
    ],
)
def test_equivalent_names_the_argument_of_the_wrong_type(
    a: object, b: object, message: str
) -> None:
    with pytest.raises(TypeError) as caught:
        equivalent(a, b)  # type: ignore[arg-type]
    assert caught.value.args == (message,)
    assert caught.value.__context__ is None
