# teluri guide

## Stable surface

Import only from `teluri`. `__all__` contains `Reason`, `TelURI`, `TelURIError`,
`build`, `equivalent`, `parse` and `parse_link`. `__version__` is the release version.
Parameter names, positional arguments, keyword-only arguments and defaults are stable:

```python
from teluri import TelURI, build, equivalent, parse, parse_link

uri = TelURI("7042", phone_context="example.com", params={"m-service": "desk"})
print(uri.unknown_mandatory)  # ('m-service',)
print(build("+1 201", ext="3"))  # tel:+1201;ext=3
print(equivalent(parse("tel:+1-201"), "TEL:+1201"))  # True
print(parse_link("tel:7042", context="example.com"))  # tel:7042;phone-context=example.com
```

`TelURI(number, ext=None, isub=None, phone_context=None, params=<empty mapping>)`
validates on construction. It snapshots the mapping, normalizes the number, extension
and numeric context, and stores generic parameter names in sorted lower case. Its public
fields are frozen; changing a source mapping later does not change the URI. The mapping
interface is read-only. Private attributes are outside the immutability contract.
`dataclasses.replace` validates again. Copying and pickling preserve values.

`parse(uri, *, strict=False)` accepts parameters in any order. `strict=True` also
requires `ext` or `isub` first, then `phone-context`, then generic parameters sorted
by lower-case name. Duplicate names are always invalid.

`build(number, *, ext=None, isub=None, phone_context=None, params=None)` removes
Unicode whitespace from numbers, extensions and numeric contexts. It percent-encodes
plain-text generic parameter values as UTF-8. Pass `isub` already percent-encoded.
Reserved names in `params` are rejected; use the corresponding fields instead.

`parse_link(href, *, context=None)` strips surrounding whitespace, decodes the number
as UTF-8 and removes its Unicode whitespace. A local number without a context uses
the supplied context. An existing context wins; a global number ignores the default.
Any supplied default is still validated. Encoded semicolons cannot inject parameters.
Parameter syntax is the same as `parse`; parameter order remains permissive.

`equivalent(a, b)` accepts strings or `TelURI` objects. Invalid strings raise the same
errors as `parse`. `==` and `hash` use the same identity: separator-free numbers,
case-insensitive ASCII octets, the same parameter names and values, and context identity.
A domain's final root dot is ignored. Local and global numbers are never equivalent.
A local context is an identifier, not a prefix to concatenate with a local number.

## Syntax policies and limits

The basis is [RFC 3966](https://www.rfc-editor.org/rfc/rfc3966.html), sections 3 to 5,
with [verified erratum 203](https://www.rfc-editor.org/errata/eid203) for `isub`.
The following are deliberate library policies, also present in 0.2.0:

- Generic parameter values must decode as UTF-8. An `isub` can contain any encoded
  octet and retains its encoded spelling. Empty values are invalid; `None` means a flag.
- An extension must contain a digit, even though the RFC's ABNF also permits a string
  of separators. Global syntax accepts any positive digit count, including a leading 0.
- Parameter values follow the ABNF character set, including literal `+`. Comparison
  folds decoded ASCII bytes, including reserved characters represented by percent escapes.
- Domain contexts follow the RFC's label syntax without DNS resolution or length limits.
- Registered parameters such as `rn`, `cic`, `tgrp` and `isub-encoding` receive generic
  syntax validation only. Their parameter-specific semantics belong to the caller.
- `unknown_mandatory` reports every `m-` name in sorted order. The caller decides which
  it understands before using the URI. The parser does not dial or contact anything.
- `is_e164` is only a shape check: global, 1 to 15 digits, nonzero first digit. It does
  not validate assigned country codes, number lengths by country, or reachability.
- `href` escapes `#` for URL use, but does not HTML-escape `&` or quotes. Use an HTML
  serializer when putting it into markup. Not every device can dial every valid URI.

There is no fixed input length cap. Work is linear in input length plus parameter
sorting, O(p log p); memory is proportional to input and output size. Applications
receiving untrusted traffic should choose limits appropriate to their own workload.

## Errors

Malformed text raises `TelURIError`, a `ValueError`. `.reason` is one of the twelve
`Literal` strings in `Reason`; see the complete list in the
[README](https://github.com/JaviLianes8/teluri/blob/main/README.md#reasons).
`.message` provides a short description; `.args` is `(reason, message)`.
Library-generated diagnostics never include input. The wording is not a stable parser
interface: branch on `.reason`. Directly creating an exception preserves a caller's
message without redacting it. `Reason` is a typing alias, not a runtime validator.

```python
from teluri import TelURIError, parse

try:
    parse("tel:7042")
except TelURIError as error:
    print(error.reason)  # missing-context
```

Wrong argument types raise `TypeError`: URI text, number and optional string fields,
the boolean `strict`, the default link context, and mapping keys. Invalid generic
parameter values, including non-strings, raise `TelURIError` with `param-value`.
`None` is accepted only where shown in the signatures.
String subclasses are accepted using their underlying text, without invoking overridden
string operations. Validation and stored fields use plain strings, including parameter
names and values.

## Command line

Both `teluri` and `python -m teluri` accept one URI per argument, or one URI per stdin
line when there are no arguments. Empty lines are skipped. Each valid URI produces a
canonical line on stdout; each invalid URI produces `invalid (reason)` on stderr.
`--json` emits one ASCII JSON object per valid URI with `uri`, `number`, `global`,
`e164`, `ext`, `isub`, `phone_context` and `params`. `--strict`, `--link` and
`--context` match the API options. `--context` requires `--link`; `--link` and
`--strict` cannot be combined. Use `--` before URIs beginning with `-`.

Exit codes: 0 for success or help, 1 if any URI is invalid or an output pipe closes,
2 for invalid command-line usage. Inputs are processed independently and in order.
Diagnostics are ASCII, bounded per input, and omit the supplied data.
Stdin uses its configured encoding. Malformed byte sequences become replacement
characters, which fail URI validation on that line; valid neighboring lines still run.
Only line endings are removed in the default and `--strict` modes. `--link` removes
surrounding whitespace, but a whitespace-only line is invalid in every mode.

## Upgrading from 0.2.0

Install with `pip install --upgrade teluri`. The exported signatures, valid URI results,
and error reasons remain unchanged. Invalid-type handling is stricter, diagnostics no
longer echo data, and pipe failures exit quietly. Import classes from `teluri`; their
public module identity now also controls new pickles. Existing 0.2.0 pickles remain
readable. See every change in the
[1.0.0 changelog](https://github.com/JaviLianes8/teluri/blob/main/CHANGELOG.md).

## Reproducing checks

Install `.[dev]`, then run `ruff format --check .`, `ruff check .`,
`mypy --strict src tests` and `pytest --basetemp=<your-scratch-directory>`.
Tests use a 300-second per-test timeout. Set `TELURI_UPSTREAM` to a local scratch
directory and run `python scripts/fetch_upstream.py` to enable fetched-source checks.
Sources are hash-checked against the manifest and are never distributed.
Set `TELURI_E2E=1` for wheel builds and clean-environment tests, and `TELURI_PYPI=1`
to include installing and upgrading the published 0.2.0 release. Set `TEMP` and `TMP`
to your scratch directory so build and venv tools use it too. The optional reference
checks use `phonenumbers` and `pypdf`, installed separately, and otherwise skip cleanly.
`TELURI_OLD_PYTHON` can point to a separate environment containing PyPI 0.2.0 to run
the seeded compatibility comparison without rebuilding the distributions.
