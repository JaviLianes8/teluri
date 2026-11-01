"""Hand-written subprocess contracts for stdin and complete JSON records."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _run(*args: str, data: bytes = b"", encoding: str = "utf-8:strict") -> tuple[int, str, str]:
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        "PYTHONIOENCODING": encoding,
    }
    result = subprocess.run(
        [sys.executable, "-m", "teluri", *args],
        input=data,
        capture_output=True,
        env=env,
        timeout=30,
        check=False,
    )
    return (
        result.returncode,
        result.stdout.decode("ascii").replace("\r\n", "\n"),
        result.stderr.decode("ascii").replace("\r\n", "\n"),
    )


@pytest.mark.parametrize("args", [(), ("--link",), ("--strict",)])
@pytest.mark.parametrize("bad", [b"\xffPRIVATE", b"tel:+1;note=\xff" + b"PRIVATE" * 10_000])
def test_malformed_stdin_preserves_valid_neighbors(args: tuple[str, ...], bad: bytes) -> None:
    reason = "param-value" if bad.startswith(b"tel:") else "scheme"
    assert _run(*args, data=b"tel:+1\n" + bad + b"\ntel:+2\n") == (
        1,
        "tel:+1\ntel:+2\n",
        f"invalid ({reason})\n",
    )


def test_stdin_retains_the_selected_encoding() -> None:
    assert _run("--link", data=b"tel:+1\xa0\n", encoding="cp1252:strict") == (0, "tel:+1\n", "")


@pytest.mark.parametrize("field,value", [("isub", "a%FF%3B%23"), ("ext", "23")])
def test_json_preserves_populated_optional_fields(field: str, value: str) -> None:
    text = f"tel:+1;{field}={value};note=%C3%A9"
    status, out, err = _run("--json", text)
    assert (status, err) == (0, "")
    assert json.loads(out) == {
        "uri": text,
        "number": "+1",
        "global": True,
        "e164": True,
        "ext": value if field == "ext" else None,
        "isub": value if field == "isub" else None,
        "phone_context": None,
        "params": {"note": "\u00e9"},
    }


@pytest.mark.parametrize("args", [(), ("--strict",)])
@pytest.mark.parametrize(
    "line,reason", [(b" tel:+1", "scheme"), (b"tel:+1 ", "number"), (b" \t ", "scheme")]
)
def test_stdin_preserves_invalid_whitespace(
    args: tuple[str, ...], line: bytes, reason: str
) -> None:
    assert _run(*args, data=line + b"\ntel:+2\n") == (1, "tel:+2\n", f"invalid ({reason})\n")


@pytest.mark.parametrize("line", [b" tel:+1", b"tel:+1 "])
def test_link_stdin_removes_surrounding_whitespace(line: bytes) -> None:
    assert _run("--link", data=line + b"\n") == (0, "tel:+1\n", "")


def test_link_stdin_rejects_whitespace_only_lines() -> None:
    assert _run("--link", data=b" \t \ntel:+2\n") == (1, "tel:+2\n", "invalid (scheme)\n")


@pytest.mark.parametrize("number", ["%252B1", "%2531", "%2523"])
def test_link_cli_rejects_nested_percent_escapes(number: str) -> None:
    assert _run("--link", "--context", "+1", "tel:" + number) == (1, "", "invalid (number)\n")
