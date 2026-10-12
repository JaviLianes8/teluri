import pytest

from teluri import TelURI, TelURIError, build, parse


def test_parse_global_number_strips_visual_separators() -> None:
    uri = parse("tel:+1-201-555-0123")
    assert uri.number == "+12015550123"
    assert uri.is_global is True
    assert uri.ext is None
    assert uri.phone_context is None
    assert uri.params == {}


def test_parse_local_number_requires_phone_context() -> None:
    uri = parse("tel:7042;phone-context=example.com")
    assert uri.number == "7042"
    assert uri.is_global is False
    assert uri.phone_context == "example.com"


def test_parse_local_number_without_context_raises() -> None:
    with pytest.raises(TelURIError):
        parse("tel:863-1234")


def test_parse_reads_the_ext_parameter() -> None:
    uri = parse("tel:+1-201-555-0123;ext=1234")
    assert uri.number == "+12015550123"
    assert uri.ext == "1234"


def test_parse_normalizes_a_numeric_phone_context() -> None:
    uri = parse("tel:863-1234;phone-context=+1-914-555")
    assert uri.number == "8631234"
    assert uri.phone_context == "+1914555"


def test_parse_keeps_other_parameters_in_order() -> None:
    uri = parse("tel:+1-201-555-0123;ext=42;isub=12;tag")
    assert uri.ext == "42"
    assert uri.params == {"isub": "12", "tag": None}


def test_parse_rejects_a_global_number_with_a_phone_context() -> None:
    with pytest.raises(TelURIError):
        parse("tel:+12015550123;phone-context=example.com")


def test_parse_rejects_a_duplicate_parameter() -> None:
    with pytest.raises(TelURIError):
        parse("tel:+12015550123;ext=1;ext=2")


@pytest.mark.parametrize(
    "uri",
    [
        "sip:+12015550123",
        "tel:",
        "tel:;ext=1",
        "tel:+;ext=1",
        "tel:+1abc",
        "tel:+12015550123;=novalue",
        "tel:+12015550123;ext=",
        "tel:+12015550123;ext=12x",
    ],
)
def test_parse_rejects_malformed_input(uri: str) -> None:
    with pytest.raises(TelURIError):
        parse(uri)


def test_build_global_number() -> None:
    assert build("+1(201)555-0123") == "tel:+12015550123"


def test_build_normalizes_visual_separators() -> None:
    assert build("+1-201-555-0123", ext="1-2-3") == "tel:+12015550123;ext=123"


def test_build_local_number_needs_a_phone_context() -> None:
    with pytest.raises(TelURIError):
        build("7042")


def test_build_local_number_with_context() -> None:
    assert build("7042", phone_context="example.com") == "tel:7042;phone-context=example.com"


def test_build_rejects_a_global_number_with_a_context() -> None:
    with pytest.raises(TelURIError):
        build("+12015550123", phone_context="example.com")


def test_build_renders_extra_parameters() -> None:
    uri = build("+12015550123", params={"isub": "12", "tag": None})
    assert uri == "tel:+12015550123;isub=12;tag"


def test_build_rejects_a_reserved_parameter_name() -> None:
    with pytest.raises(TelURIError):
        build("+12015550123", params={"ext": "1"})


def test_round_trip_through_parse_and_build() -> None:
    uri = "tel:+12015550123;ext=1234;isub=99;tag"
    assert str(parse(uri)) == uri
    assert parse(str(parse(uri))) == parse(uri)


def test_str_rebuilds_a_local_number() -> None:
    model = TelURI("8631234", False, phone_context="+1914555")
    assert str(model) == "tel:8631234;phone-context=+1914555"
