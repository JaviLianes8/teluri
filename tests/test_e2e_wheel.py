"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with TELURI_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("TELURI_E2E") != "1", reason="set TELURI_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources, pickle
import teluri
from teluri import TelURIError, build, equivalent, parse, parse_link

assert "site-packages" in teluri.__file__, teluri.__file__
assert importlib.metadata.version("teluri") == teluri.__version__
assert importlib.resources.files("teluri").joinpath("py.typed").is_file()
uri = parse("TEL:863-1234;Tgrp=TG-1;phone-context=+1-914-555;note=caf%C3%A9")
assert str(uri) == "tel:8631234;phone-context=+1914555;note=caf%C3%A9;tgrp=TG-1"
assert uri.params["note"] == "caf\u00e9"
assert equivalent("tel:+1-201;EXT=1;a=X", "tel:+1201;a=x;ext=1")
assert pickle.loads(pickle.dumps(uri)) == uri
assert build("+1 (201) 555-0123", params={"x": "a;b"}) == "tel:+12015550123;x=a%3Bb"
link = parse_link("tel:*31%23", context="example.com")
assert link.href == "tel:*31%23;phone-context=example.com"
for bad, reason in [("tel:12", "missing-context"), ("tel:+1;b;a", "param-order")]:
    try:
        parse(bad, strict=True)
    except TelURIError as error:
        assert error.reason == reason
        assert pickle.loads(pickle.dumps(error)).reason == reason
    else:
        raise AssertionError(bad)
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("teluri-*.whl")

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"

    script = bindir / ("teluri.exe" if sys.platform == "win32" else "teluri")
    cli = _run(script, "tel:+1-2;Ext=3", "tel:12", cwd=work)
    assert cli.returncode == 1
    assert cli.stdout == "tel:+12;ext=3\n"
    assert cli.stderr == "invalid (missing-context): tel:12\n"


def test_distributions_ship_no_third_party_text(tmp_path: Path) -> None:
    built = _run(sys.executable, "-m", "build", "--outdir", tmp_path, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = tmp_path.glob("teluri-*.whl")
    (sdist,) = tmp_path.glob("teluri-*.tar.gz")
    wheel_names = zipfile.ZipFile(wheel).namelist()
    assert all(n.startswith(("teluri/", "teluri-")) for n in wheel_names), wheel_names
    with tarfile.open(sdist) as archive:
        names = [n.split("/", 1)[1] for n in archive.getnames() if "/" in n]
    assert "tests/upstream/MANIFEST.json" in names
    assert "tests/data/examples.json" in names
    assert not any(n.endswith("rfc3966.txt") for n in names), names
    assert not any(n.startswith((".github", "IMPROVEMENTS")) for n in names), names
