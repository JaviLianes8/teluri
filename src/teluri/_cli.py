"""Command line: print the canonical form of each tel: URI, exit 1 if any is invalid."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from collections.abc import Iterable, Sequence
from typing import TextIO

from ._errors import TelURIError
from ._link import parse_link
from ._model import TelURI
from ._parse import parse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="teluri",
        description="Validate tel: URIs (RFC 3966) and print their canonical form. "
        "Reads one URI per line from standard input when none are given.",
    )
    parser.add_argument("uris", nargs="*", metavar="URI")
    parser.add_argument("--json", action="store_true", help="print one JSON object per URI")
    parser.add_argument("--strict", action="store_true", help="enforce the parameter order")
    parser.add_argument(
        "--link", action="store_true", help="read links as browsers do (spaces, %%23)"
    )
    parser.add_argument(
        "--context", metavar="DESCRIPTOR", help="phone-context for local links without one"
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the command line and return its exit status (0 ok, 1 invalid, 2 usage)."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            args = _parser().parse_args(argv)
            if args.context is not None and not args.link:
                _parser().error("--context needs --link")
    except SystemExit as stop:
        return int(stop.code or 0)
    uris: Iterable[str] = args.uris or _lines(stdin or sys.stdin)
    status = 0
    for uri in uris:
        try:
            if args.link:
                parsed = parse_link(uri, context=args.context)
            else:
                parsed = parse(uri, strict=args.strict)
        except TelURIError as error:
            err.write(f"invalid ({error.reason}): {_shown(uri)}\n")
            status = 1
            continue
        out.write((json.dumps(_fields(parsed), ensure_ascii=False) if args.json else str(parsed)))
        out.write("\n")
    return status


def _fields(uri: TelURI) -> dict[str, object]:
    return {
        "uri": str(uri),
        "number": uri.number,
        "global": uri.is_global,
        "e164": uri.is_e164,
        "ext": uri.ext,
        "isub": uri.isub,
        "phone_context": uri.phone_context,
        "params": dict(uri.params),
    }


def _lines(stream: TextIO) -> Iterable[str]:
    for line in stream:
        text = line.rstrip("\r\n")
        if text:
            yield text


def _shown(uri: str) -> str:
    """The input as safe to print: control and other unprintable characters escaped."""
    return "".join(c if c.isprintable() else repr(c)[1:-1] for c in uri)
