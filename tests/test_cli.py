"""The teluri command line: canonical form or JSON, exit status, link mode."""

from __future__ import annotations

import io
import json

from teluri._cli import main


def _run(*argv: str, stdin: str = "") -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    status = main(list(argv), io.StringIO(stdin), out, err)
    return status, out.getvalue(), err.getvalue()


def test_prints_the_canonical_form() -> None:
    assert _run("tel:+1-201-555-0123;Ext=9") == (0, "tel:+12015550123;ext=9\n", "")


def test_reports_each_invalid_uri_and_exits_one() -> None:
    status, out, err = _run("tel:12", "tel:+1")
    assert (status, out) == (1, "tel:+1\n")
    assert err == "invalid (missing-context): tel:12\n"


def test_escapes_unprintable_input_in_errors() -> None:
    assert _run("tel:+1\x1b")[2] == "invalid (number): tel:+1\\x1b\n"


def test_json_output_lists_every_field() -> None:
    status, out, _ = _run("--json", "tel:1;phone-context=+44;a=%C3%A9")
    assert status == 0
    assert json.loads(out) == {
        "uri": "tel:1;phone-context=+44;a=%C3%A9",
        "number": "1",
        "global": False,
        "e164": False,
        "ext": None,
        "isub": None,
        "phone_context": "+44",
        "params": {"a": "\u00e9"},
    }


def test_reads_standard_input_and_skips_blank_lines() -> None:
    assert _run(stdin="tel:+1\n\ntel:+2\r\n") == (0, "tel:+1\ntel:+2\n", "")


def test_strict_flag_enforces_the_order() -> None:
    assert _run("--strict", "tel:+1;b;a")[0] == 1
    assert _run("tel:+1;b;a")[0] == 0


def test_link_mode_with_a_context() -> None:
    assert _run("--link", "--context", "+1", "tel:408 555")[1] == "tel:408555;phone-context=+1\n"
    assert _run("--link", "tel:+1 2")[1] == "tel:+12\n"


def test_context_without_link_is_a_usage_error() -> None:
    status, _, err = _run("--context", "+1", "tel:1")
    assert status == 2
    assert "--context needs --link" in err


def test_help_exits_zero() -> None:
    status, out, _ = _run("--help")
    assert status == 0
    assert "usage: teluri" in out
