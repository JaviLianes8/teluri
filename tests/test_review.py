"""Regression tests for the findings of the independent review of the 0.2.0 round."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from teluri import TelURI, TelURIError, build, parse, parse_link
from teluri._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def test_json_output_is_ascii_so_any_console_can_print_it() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "teluri", "--json", "tel:+1;a=%E4%B8%AD", "tel:+2"],
        capture_output=True,
        cwd=SRC,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "cp1252", "SYSTEMROOT": ""},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.decode("ascii").splitlines()
    assert [json.loads(line)["params"] for line in lines] == [{"a": "\u4e2d"}, {}]


def test_invalid_non_ascii_input_is_reported_escaped() -> None:
    err = io.StringIO()
    assert main(["tel:\u4e2d"], io.StringIO(), io.StringIO(), err) == 1
    assert err.getvalue() == "invalid (number): tel:\\u4e2d\n"


@pytest.mark.parametrize("context", ["example.com;ext=5", "example.com;foo=bar", "+1;x", ""])
def test_the_link_context_is_one_descriptor(context: str) -> None:
    with pytest.raises(TelURIError) as caught:
        parse_link("tel:123", context=context)
    assert caught.value.reason == "phone-context"


def test_the_command_line_refuses_an_injected_context() -> None:
    err = io.StringIO()
    status = main(
        ["--link", "--context", "x.com;ext=9", "tel:123"], io.StringIO(), io.StringIO(), err
    )
    assert status == 1
    assert err.getvalue().startswith("invalid (phone-context)")


def test_a_lone_surrogate_value_is_refused_up_front() -> None:
    with pytest.raises(TelURIError) as caught:
        TelURI("+1", params={"a": "\ud800"})
    assert caught.value.reason == "param-value"
    with pytest.raises(TelURIError):
        build("+1", params={"a": "x\udfff"})


def test_strict_and_link_cannot_be_combined() -> None:
    err = io.StringIO()
    assert main(["--strict", "--link", "tel:+1;b;a"], io.StringIO(), io.StringIO(), err) == 2
    assert "cannot be used with --link" in err.getvalue()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"number": 123},
        {"number": "+1", "ext": 5},
        {"number": "+1", "isub": b"1"},
        {"number": "1", "phone_context": 1},
        {"number": "+1", "params": [("a", "b")]},
        {"number": "+1", "params": {1: "b"}},
    ],
)
def test_wrong_types_raise_type_error(kwargs: dict[str, object]) -> None:
    with pytest.raises(TypeError):
        TelURI(**kwargs)  # type: ignore[arg-type]


def test_parsers_refuse_non_text() -> None:
    with pytest.raises(TypeError):
        parse(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        parse_link(b"tel:+1")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("tel:+1;a=%C3%9F", "tel:+1;a=ss"),
        ("tel:+1;a=%E2%84%AA", "tel:+1;a=k"),
        ("tel:+1;a=%C3%A9", "tel:+1;a=%C3%89"),
        ("tel:+1;isub=%C3%A9", "tel:+1;isub=%C3%89"),
    ],
)
def test_values_compare_ascii_case_insensitively_only(left: str, right: str) -> None:
    assert parse(left) != parse(right)


def test_params_and_isub_follow_the_same_escape_rule() -> None:
    assert parse("tel:+1;a=%2F") == parse("tel:+1;a=/")
    assert parse("tel:+1;isub=%2F") == parse("tel:+1;isub=/")
    assert parse("tel:+1;isub=%41") == parse("tel:+1;isub=a")
    assert hash(parse("tel:+1;isub=%2f")) == hash(parse("tel:+1;isub=/"))
