"""External-consumer programs run before and after upgrading PyPI 0.2.0."""

from __future__ import annotations

BEFORE_UPGRADE = r"""
import pickle
from pathlib import Path
import teluri
from teluri import TelURIError, build, parse, parse_link
assert teluri.__version__ == "0.2.0"
uri = parse("tel:+1-2;x=X")
error = TelURIError("ext", "custom")
Path("old.pickle").write_bytes(pickle.dumps((uri, error)))
assert uri.__class__.__module__ == "teluri._model"
assert error.__class__.__module__ == "teluri._errors"
assert parse("tel:+1", strict=1).number == "+1"
assert build(["+1"]) == "tel:+1"
assert build("+1", params=[]) == "tel:+1"
try:
    parse_link("tel:+1", context=123)
except AttributeError:
    pass
else:
    raise AssertionError("old context behavior differs")
try:
    parse("private-value")
except TelURIError as caught:
    assert "private-value" in str(caught)
try:
    parse(type("private-type", (), {})())
except TypeError as caught:
    assert "private-type" in str(caught)
assert hasattr(teluri, "annotations")
"""

AFTER_UPGRADE = r"""
import pickle
from pathlib import Path
import teluri
from teluri import TelURIError, build, parse, parse_link
assert teluri.__version__ == "1.0.0"
uri, error = pickle.loads(Path("old.pickle").read_bytes())
assert str(uri) == "tel:+12;x=X"
assert (error.reason, error.message, error.args) == ("ext", "custom", ("ext", "custom"))
assert uri.__class__.__module__ == error.__class__.__module__ == "teluri"
Path("new.pickle").write_bytes(pickle.dumps((uri, error)))
for call in [lambda: parse("tel:+1", strict=1), lambda: build(["+1"]),
             lambda: build("+1", params=[]), lambda: parse_link("tel:+1", context=123)]:
    try:
        call()
    except TypeError:
        pass
    else:
        raise AssertionError("wrong type accepted")
try:
    parse("private-value")
except TelURIError as caught:
    assert str(caught) == "scheme: expected a tel: URI"
try:
    parse(type("private-type", (), {})())
except TypeError as caught:
    assert str(caught) == "uri must be a str"
assert not hasattr(teluri, "annotations")
"""
