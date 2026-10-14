"""TelURIError: a ValueError with a reason from a closed set, printable and picklable."""

from __future__ import annotations

import pickle
import typing

from teluri import Reason, TelURIError


def test_is_a_value_error_with_reason_and_message() -> None:
    error = TelURIError("ext", "bad")
    assert isinstance(error, ValueError)
    assert (error.reason, error.message, str(error)) == ("ext", "bad", "ext: bad")
    assert str(TelURIError("scheme")) == "scheme"


def test_survives_pickling() -> None:
    copy = pickle.loads(pickle.dumps(TelURIError("param-order", "b;a")))
    assert (copy.reason, copy.message) == ("param-order", "b;a")
    assert copy.args == ("param-order", "b;a")


def test_the_reason_set_is_closed_and_unique() -> None:
    reasons = typing.get_args(Reason)
    assert len(reasons) == len(set(reasons)) == 12
