"""No raised error carries the caller's input in a chained cause or context."""

from __future__ import annotations

import ast
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import get_args

import pytest

from teluri import Reason, TelURI, TelURIError, build, parse, parse_link

SRC = Path(__file__).resolve().parents[1] / "src" / "teluri"
SECRET = "hidden" + "-value-77"
# Every octet percent-encoded, so a failed UTF-8 decode would hold the secret.
SECRET_PCT = "".join(f"%{octet:02X}" for octet in SECRET.encode()) + "%FF"


class _Private:
    def __repr__(self) -> str:
        return SECRET * 100

    def __str__(self) -> str:
        return SECRET * 100


VALUE_ERRORS: dict[str, Callable[[], object]] = {
    "scheme": lambda: parse(SECRET + ":+1"),
    "link-scheme": lambda: parse_link(SECRET),
    "number": lambda: parse("tel:+1" + SECRET),
    "local-number": lambda: TelURI("1" + SECRET, phone_context="example.com"),
    "ext": lambda: parse("tel:+1;ext=" + SECRET),
    "isub": lambda: parse("tel:+1;isub=" + SECRET + "%"),
    "ext-and-isub": lambda: TelURI("+1", ext="1", isub=SECRET),
    "phone-context": lambda: parse("tel:1;phone-context=" + SECRET + "!"),
    "missing-context": lambda: parse("tel:1;x=" + SECRET),
    "global-context": lambda: parse("tel:+1;phone-context=" + SECRET),
    "param-name": lambda: parse("tel:+1;" + SECRET + "!=1"),
    "param-value-escape": lambda: parse("tel:+1;x=" + SECRET + "%"),
    "param-value-utf8": lambda: parse("tel:+1;x=" + SECRET_PCT),
    "param-value-surrogate": lambda: TelURI("+1", params={"x": SECRET + "\ud800"}),
    "reserved-param": lambda: TelURI("+1", params={"ext": SECRET}),
    "duplicate-param": lambda: parse("tel:+1;x=" + SECRET + ";x=1"),
    "duplicate-model-param": lambda: TelURI("+1", params={"X": SECRET, "x": "1"}),
    "param-order": lambda: parse("tel:+1;z=" + SECRET + ";a=1", strict=True),
    "link-number-utf8": lambda: parse_link("tel:" + SECRET_PCT),
    "link-separator": lambda: parse_link("tel:+1" + SECRET + "%3B"),
    "link-context": lambda: parse_link("tel:1", context=SECRET + "!"),
    "build": lambda: build("+1 " + SECRET),
}

TYPE_ERRORS: dict[str, Callable[[], object]] = {
    "parse-uri": lambda: parse(_Private()),  # type: ignore[arg-type]
    "parse-strict": lambda: parse("tel:+1", strict=_Private()),  # type: ignore[arg-type]
    "link-href": lambda: parse_link(_Private()),  # type: ignore[arg-type]
    "link-context": lambda: parse_link("tel:1", context=_Private()),  # type: ignore[arg-type]
    "build-number": lambda: build(_Private()),  # type: ignore[arg-type]
    "build-ext": lambda: build("+1", ext=_Private()),  # type: ignore[arg-type]
    "build-isub": lambda: build("+1", isub=_Private()),  # type: ignore[arg-type]
    "build-context": lambda: build("1", phone_context=_Private()),  # type: ignore[arg-type]
    "build-params": lambda: build("+1", params=_Private()),  # type: ignore[arg-type]
    "number": lambda: TelURI(_Private()),  # type: ignore[arg-type]
    "ext": lambda: TelURI("+1", ext=_Private()),  # type: ignore[arg-type]
    "isub": lambda: TelURI("+1", isub=_Private()),  # type: ignore[arg-type]
    "phone-context": lambda: TelURI("1", phone_context=_Private()),  # type: ignore[arg-type]
    "params": lambda: TelURI("+1", params=_Private()),  # type: ignore[arg-type]
    "params-key": lambda: TelURI("+1", params={_Private(): "1"}),  # type: ignore[dict-item]
}


def assert_unchained(error: BaseException) -> None:
    """The error stands alone, and nothing a traceback prints holds the secret."""
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not error.__suppress_context__
    formatted = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert SECRET not in formatted


@pytest.mark.parametrize("call", VALUE_ERRORS.values(), ids=VALUE_ERRORS.keys())
def test_syntax_errors_carry_no_chained_input(call: Callable[[], object]) -> None:
    with pytest.raises(TelURIError) as caught:
        call()
    assert_unchained(caught.value)


@pytest.mark.parametrize("call", TYPE_ERRORS.values(), ids=TYPE_ERRORS.keys())
def test_type_errors_carry_no_chained_input(call: Callable[[], object]) -> None:
    with pytest.raises(TypeError) as caught:
        call()
    assert_unchained(caught.value)


def test_every_syntax_reason_is_covered() -> None:
    reasons: set[str] = set()
    for call in VALUE_ERRORS.values():
        with pytest.raises(TelURIError) as caught:
            call()
        reasons.add(caught.value.reason)
    assert reasons == set(get_args(Reason))


def _raises(path: Path) -> list[tuple[ast.Raise, bool]]:
    """Every raise in a module, flagged when it sits inside an except handler."""
    found: list[tuple[ast.Raise, bool]] = []

    def visit(node: ast.AST, in_handler: bool) -> None:
        if isinstance(node, ast.Raise):
            found.append((node, in_handler))
        for child in ast.iter_child_nodes(node):
            visit(child, in_handler or isinstance(node, ast.ExceptHandler))

    visit(ast.parse(path.read_text(encoding="utf-8")), False)
    return found


@pytest.mark.parametrize("path", sorted(SRC.glob("*.py")), ids=lambda path: path.name)
def test_no_source_raise_can_chain_an_error(path: Path) -> None:
    # A chained error keeps the failed input in reach of tracebacks and loggers, so the
    # library neither writes `raise ... from` nor raises a new error inside a handler.
    for node, in_handler in _raises(path):
        assert node.cause is None, f"{path.name}:{node.lineno} chains with from"
        assert not (in_handler and node.exc is not None), f"{path.name}:{node.lineno}"
