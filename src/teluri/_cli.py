"""Command line: print the canonical form of each tel: URI, exit 1 if any is invalid."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from collections.abc import Iterable, Sequence
from typing import NoReturn, TextIO

from ._errors import TelURIError
from ._link import parse_link
from ._model import TelURI
from ._parse import parse


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        # argparse's default message includes arbitrary user input.
        super().error("invalid command-line arguments; use --help")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
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
    try:
        status = _main(argv, stdin, stdout, stderr)
        (stdout or sys.stdout).flush()
        (stderr or sys.stderr).flush()
        return status
    except BrokenPipeError:
        # Prevent a second flush of a closed pipe during interpreter shutdown.
        if stdout is None:
            sys.stdout = io.StringIO()
        if stderr is None:
            sys.stderr = io.StringIO()
        return 1


def _main(
    argv: Sequence[str] | None,
    stdin: TextIO | None,
    stdout: TextIO | None,
    stderr: TextIO | None,
) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            args = _parser().parse_args(argv)
            if args.context is not None and not args.link:
                err.write("teluri: error: --context needs --link\n")
                return 2
            if args.strict and args.link:
                err.write("teluri: error: --strict cannot be used with --link\n")
                return 2
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
            err.write(f"invalid ({error.reason})\n")
            status = 1
            continue
        out.write(json.dumps(_fields(parsed)) if args.json else str(parsed))
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
