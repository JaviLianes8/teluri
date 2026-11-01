"""Compare live programs against a separately installed PyPI 0.2.0."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

PROGRAM = r"""
import json, random, string
from teluri import TelURIError, parse, parse_link, build
rng = random.Random(20261101)
output = []
for index in range(3000):
    number = "+" + "-".join(rng.choices(string.digits, k=rng.randrange(1, 20)))
    value = "".join(rng.choices(string.printable + "\u00e9", k=rng.randrange(1, 50)))
    built = build(number, params={"note": value, "flag": None})
    uri = parse(built)
    output.append([str(uri), uri.number, dict(uri.params), uri.is_e164, uri.href])
    hostile = rng.choice(["", "tel:", "tel:+1;x=", "tel:1;phone-context="])
    hostile += "".join(rng.choices(string.printable, k=rng.randrange(50)))
    for parser in [parse, parse_link]:
        try:
            output.append(str(parser(hostile)))
        except TelURIError as error:
            output.append(["error", error.reason])
print(json.dumps(output, ensure_ascii=True))
"""


def test_published_release_matches_for_unchanged_contracts() -> None:
    old_python = os.environ.get("TELURI_OLD_PYTHON")
    if not old_python:
        pytest.skip("set TELURI_OLD_PYTHON to an environment with PyPI 0.2.0")
    results = []
    for executable in (old_python, sys.executable):
        result = subprocess.run(
            [executable, "-I", "-c", PROGRAM],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        results.append(result.stdout)
    assert results[0] == results[1]
