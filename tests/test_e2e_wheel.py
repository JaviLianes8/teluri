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
from test_upgrade import AFTER_UPGRADE, BEFORE_UPGRADE

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
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False, timeout=180
    )


@pytest.fixture(scope="module")
def distributions(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dist = tmp_path_factory.mktemp("dist")
    built = _run(sys.executable, "-m", "build", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    return dist


@pytest.mark.parametrize("upgrade", [False, True])
def test_installed_wheel_end_to_end(tmp_path: Path, distributions: Path, upgrade: bool) -> None:
    if upgrade and os.environ.get("TELURI_PYPI") != "1":
        pytest.skip("set TELURI_PYPI=1 to install the published release")
    dist = distributions
    (wheel,) = dist.glob("teluri-*.whl")

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    if upgrade:
        old = _run(python, "-m", "pip", "install", "-q", "teluri==0.2.0")
        assert old.returncode == 0, old.stderr
        before = _run(python, "-I", "-c", BEFORE_UPGRADE, cwd=work)
        assert before.returncode == 0, before.stderr
        consumer = _run(python, "-I", "-c", PROGRAM, cwd=work)
        assert consumer.returncode == 0, consumer.stderr
    installed = _run(python, "-m", "pip", "install", "-q", "--upgrade", wheel)
    assert installed.returncode == 0, installed.stderr
    if upgrade:
        after = _run(python, "-I", "-c", AFTER_UPGRADE, cwd=work)
        assert after.returncode == 0, after.stderr
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"

    script = bindir / ("teluri.exe" if sys.platform == "win32" else "teluri")
    cli = _run(script, "tel:+1-2;Ext=3", "tel:12", cwd=work)
    assert cli.returncode == 1
    assert cli.stdout == "tel:+12;ext=3\n"
    assert cli.stderr == "invalid (missing-context)\n"
    module = _run(python, "-I", "-m", "teluri", "--link", "--context", "+1", "tel:12 3", cwd=work)
    assert (module.returncode, module.stdout, module.stderr) == (
        0,
        "tel:123;phone-context=+1\n",
        "",
    )
    strict = _run(script, "--strict", "tel:+1;b;a", cwd=work)
    assert (strict.returncode, strict.stdout, strict.stderr) == (1, "", "invalid (param-order)\n")
    help_ = _run(script, "--help", cwd=work)
    assert help_.returncode == 0 and "usage: teluri" in help_.stdout
    invalid = _run(script, "--unknown-private-value", cwd=work)
    assert invalid.returncode == 2 and "private" not in invalid.stderr
    stdin = subprocess.run(
        [str(script), "--json"],
        input="\ntel:+1;ext=2\ntel:1\n",
        capture_output=True,
        text=True,
        cwd=work,
        timeout=30,
        check=False,
    )
    assert stdin.returncode == 1
    import json

    assert json.loads(stdin.stdout) == {
        "uri": "tel:+1;ext=2",
        "number": "+1",
        "global": True,
        "e164": True,
        "ext": "2",
        "isub": None,
        "phone_context": None,
        "params": {},
    }
    assert stdin.stderr == "invalid (missing-context)\n"
    with subprocess.Popen(
        [str(python), "-I", "-m", "teluri"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=work,
    ) as process:
        assert process.stdout is not None and process.stdin is not None
        process.stdout.close()
        process.stdin.write("tel:+1\n")
        process.stdin.close()
        assert process.wait(timeout=30) == 1
        assert process.stderr is not None and process.stderr.read() == ""
    if upgrade:
        # New public-module pickles also load in the previous published version.
        old = _run(python, "-m", "pip", "install", "-q", "teluri==0.2.0")
        assert old.returncode == 0, old.stderr
        check = "import pickle; from pathlib import Path; "
        check += "assert str(pickle.loads(Path('new.pickle').read_bytes())[0]) == 'tel:+12;x=X'"
        assert _run(python, "-I", "-c", check, cwd=work).returncode == 0


def test_distributions_ship_no_third_party_text(distributions: Path) -> None:
    (wheel,) = distributions.glob("teluri-*.whl")
    (sdist,) = distributions.glob("teluri-*.tar.gz")
    wheel_names = zipfile.ZipFile(wheel).namelist()
    assert all(n.startswith(("teluri/", "teluri-")) for n in wheel_names), wheel_names
    with tarfile.open(sdist) as archive:
        names = [n.split("/", 1)[1] for n in archive.getnames() if "/" in n]
    assert "tests/upstream/MANIFEST.json" in names
    assert "tests/data/examples.json" in names
    assert not any(n.endswith("rfc3966.txt") for n in names), names
    assert not any(n.startswith((".github", "IMPROVEMENTS")) for n in names), names
    assert "teluri/py.typed" in wheel_names
    assert any(n.endswith("/licenses/LICENSE") for n in wheel_names)
    assert {
        "LICENSE",
        "README.md",
        "GUIDE.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "requirements-dev.txt",
        "scripts/check.ps1",
    } <= set(names)
    assert not any("__pycache__" in n or n.endswith(".pyc") for n in names + wheel_names)
    assert not any("CERT-" in n or ".venv" in n for n in names + wheel_names)
    for name in names:
        if name.startswith("tests/upstream/"):
            assert name == "tests/upstream/MANIFEST.json"
