"""Input-free diagnostics and deliberate wrong-type contracts."""

from __future__ import annotations

import errno
import io
from collections.abc import Callable

import pytest

from teluri import TelURI, TelURIError, build, parse, parse_link
from teluri._cli import main


@pytest.mark.parametrize("size", [12, 100_000])
def test_invalid_fields_never_enter_exception_messages(size: int) -> None:
    secret = "sensitive-credential" * size
    calls: list[Callable[[], object]] = [
        lambda: parse(secret),
        lambda: parse("tel:+1" + secret),
        lambda: parse("tel:1" * size),
        lambda: parse("tel:+1;ext=" + secret),
        lambda: parse("tel:+1;isub=" + secret + "%FF%"),
        lambda: parse("tel:1;phone-context=" + secret + "!"),
        lambda: parse("tel:+1;" + secret + "="),
        lambda: parse("tel:+1;" + secret + ";" + secret),
        lambda: parse("tel:+1;z;" + secret, strict=True),
        lambda: parse("tel:+1;x=" + secret + "%FF"),
        lambda: parse_link(secret),
        lambda: parse_link("tel:" + secret + "%FF"),
        lambda: parse_link("tel:" + secret + "%3Bext=1"),
        lambda: TelURI("1" * size),
        lambda: TelURI("+1", params={secret: "\ud800"}),
    ]
    for call in calls:
        with pytest.raises(TelURIError) as caught:
            call()
        assert "sensitive" not in str(caught.value)
        assert len(str(caught.value)) < 100
        assert secret not in repr(caught.value.args)


@pytest.mark.parametrize("value", [None, 1, False, b"+1", [], {}, object()])
def test_builder_rejects_non_text_number(value: object) -> None:
    with pytest.raises(TypeError):
        build(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [1, False, b"+1", [], {}])
def test_optional_text_fields_reject_wrong_types(value: object) -> None:
    with pytest.raises(TypeError):
        build("+1", ext=value)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build("1", phone_context=value)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        parse_link("tel:+1", context=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [False, [], "", 0])
def test_builder_rejects_false_valued_non_mappings(value: object) -> None:
    with pytest.raises(TypeError):
        build("+1", params=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [0, 1, None, "yes", []])
def test_strict_must_be_a_boolean(value: object) -> None:
    with pytest.raises(TypeError, match="strict must be a bool"):
        parse("tel:+1", strict=value)  # type: ignore[arg-type]


def test_type_names_are_not_echoed() -> None:
    value = type("sensitive" * 1000, (), {})()
    with pytest.raises(TypeError) as caught:
        parse(value)
    assert str(caught.value) == "uri must be a str"


def test_cli_omits_input_and_unknown_arguments() -> None:
    secret = "sensitive" * 100_000
    for args, status in [(["tel:" + secret], 1), (["--" + secret], 2)]:
        out, err = io.StringIO(), io.StringIO()
        assert main(args, io.StringIO(), out, err) == status
        assert not out.getvalue()
        assert "sensitive" not in err.getvalue()
        assert len(err.getvalue()) < 300


def test_cli_handles_a_closed_output_pipe() -> None:
    class ClosedPipe(io.StringIO):
        def write(self, text: str) -> int:
            raise BrokenPipeError

    assert main(["tel:+1"], io.StringIO(), ClosedPipe(), io.StringIO()) == 1


def test_cli_does_not_hide_unrelated_os_errors() -> None:
    class FullDisk(io.StringIO):
        def write(self, text: str) -> int:
            raise OSError(errno.ENOSPC, "disk full")

    with pytest.raises(OSError) as caught:
        main(["tel:+1"], io.StringIO(), FullDisk(), io.StringIO())
    assert caught.value.errno == errno.ENOSPC
