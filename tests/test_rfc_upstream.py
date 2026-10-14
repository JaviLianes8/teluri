"""The committed examples are exactly the tel: URIs printed in the fetched RFC texts.

Skips until `python scripts/fetch_upstream.py` has fetched the files in the manifest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from conftest import read_upstream

DATA = json.loads((Path(__file__).parent / "data" / "examples.json").read_text("utf-8"))
MANIFEST = json.loads(
    (Path(__file__).parent / "upstream" / "MANIFEST.json").read_text(encoding="utf-8")
)
PAGE_LINE = re.compile(r"^(RFC \d{4} |[A-Z][a-z]+(, | & | et al\.).*\[Page )")


def _uris_in(text: str) -> list[str]:
    lines = [line for line in text.replace("\f", "").splitlines() if not PAGE_LINE.match(line)]
    # Join a URI that the RFC wraps right after a parameter separator.
    body = re.sub(r";\n\s+", ";", "\n".join(lines))
    found: list[str] = []
    for match in re.finditer(r"tel:[^\s<>\"']+", body):
        uri = match.group(0).rstrip(":,.")  # sentence punctuation after the URI
        if uri.endswith(")") and "(" not in uri:
            uri = uri[:-1]
        if re.match(r"tel:[+0-9A-Fa-f*#]", uri) and uri not in found:
            found.append(uri)
    return found


@pytest.mark.parametrize("rfc", sorted(DATA["uris"]))
def test_the_examples_match_the_rfc_text(rfc: str) -> None:
    text = read_upstream(f"{rfc}.txt").decode("ascii")
    assert _uris_in(text) == DATA["uris"][rfc]


def test_the_manifest_and_the_examples_name_the_same_texts() -> None:
    for rfc, source in DATA["sources"].items():
        assert MANIFEST[f"{rfc}.txt"]["sha256"] == source["sha256"]
        assert MANIFEST[f"{rfc}.txt"]["url"] == source["url"]
