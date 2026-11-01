"""Stable public signatures, examples, metadata and value semantics."""

from __future__ import annotations

import copy
import doctest
import inspect
import re
import typing
from pathlib import Path

import pytest

import teluri
from teluri import TelURI, TelURIError, build, parse


@pytest.mark.parametrize(
    ("name", "parameters"),
    [
        ("parse", "uri,*,strict=False"),
        ("parse_link", "href,*,context=None"),
        ("equivalent", "a,b"),
        ("build", "number,*,ext=None,isub=None,phone_context=None,params=None"),
        ("TelURI", "number,ext=None,isub=None,phone_context=None,params=<factory>"),
        ("TelURIError", "reason,message="),
    ],
)
def test_signatures_are_stable(name: str, parameters: str) -> None:
    signature = inspect.signature(getattr(teluri, name))
    parts = []
    keyword = False
    for param in signature.parameters.values():
        if param.kind == param.KEYWORD_ONLY and not keyword:
            parts.append("*")
            keyword = True
        parts.append(param.name + (f"={param.default}" if param.default != param.empty else ""))
    assert ",".join(parts) == parameters


def test_only_declared_public_names_exist() -> None:
    assert {name for name in vars(teluri) if not name.startswith("_")} == set(teluri.__all__)
    assert len(teluri.__all__) == len(set(teluri.__all__))
    assert TelURI.__module__ == TelURIError.__module__ == "teluri"


def test_every_public_docstring_example_runs() -> None:
    names = [(name, getattr(teluri, name)) for name in teluri.__all__]
    names += [
        (name, getattr(TelURI, name))
        for name in ("is_global", "is_e164", "unknown_mandatory", "href")
    ]
    runner = doctest.DocTestRunner()
    for name, value in names:
        doc = inspect.getdoc(value)
        assert doc and ">>>" in doc, name
        runner.run(doctest.DocTestParser().get_doctest(doc, {}, name, None, 0))
    assert runner.summarize().failed == 0
    assert runner.tries == 24


def test_public_type_hints_resolve_without_any() -> None:
    for value in (TelURI, TelURIError, teluri.parse, teluri.parse_link, build, teluri.equivalent):
        hints = typing.get_type_hints(value)
        assert hints
        assert all("Any" not in str(hint) for hint in hints.values())


def test_model_snapshots_mapping_and_supports_copy() -> None:
    values: dict[str, str | None] = {"X": "old"}
    uri = TelURI("+1", params=values)
    values["X"] = "new"
    assert dict(uri.params) == {"x": "old"}
    assert copy.copy(uri) == copy.deepcopy(uri) == uri
    assert hash(copy.deepcopy(uri)) == hash(uri)
    with pytest.raises(KeyError):
        _ = uri.params["missing"]


def test_documentation_links_are_absolute() -> None:
    root = Path(__file__).resolve().parents[1]
    for name in ("README.md", "GUIDE.md"):
        doc = (root / name).read_text(encoding="utf-8")
        assert all(link.startswith("https://") for link in re.findall(r"\]\(([^)]+)\)", doc))
        assert "from teluri._" not in doc


def test_guide_examples_run() -> None:
    import contextlib
    import io

    root = Path(__file__).resolve().parents[1]
    guide = (root / "GUIDE.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", guide, re.DOTALL)
    assert len(blocks) == 2
    for block in blocks:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exec(compile(block, "GUIDE.md", "exec"), {})
        assert stream.getvalue().splitlines() == re.findall(r"print\(.*\)  # (.+)", block)


def test_metadata_is_ready_for_release() -> None:
    root = Path(__file__).resolve().parents[1]
    metadata = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert teluri.__version__ == "1.0.0"
    assert 'requires-python = ">=3.10"' in metadata
    assert "dependencies = []" in metadata
    assert 'license = "MIT"' in metadata
    assert "Development Status :: 5 - Production/Stable" in metadata
    for key in ("Homepage", "Source", "Issues", "Changelog"):
        assert re.search(rf'^{key} = "https://', metadata, re.MULTILINE)


def test_builder_defaults_match_direct_construction() -> None:
    assert build("+1") == str(TelURI("+1")) == str(parse("tel:+1"))
