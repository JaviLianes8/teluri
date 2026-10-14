# teluri

Strict, typed, zero-dependency parser, builder and comparator for `tel:` URIs
(RFC 3966), with a reader for the `tel:` links found in real web pages and apps.

## Install

```
pip install teluri
```

## Usage

### Parse

```python
from teluri import parse

uri = parse("tel:+1-201-555-0123;ext=1234")
print(uri.number)  # +12015550123
print(uri.is_global)  # True
print(uri.ext)  # 1234
print(uri.is_e164)  # True
print(uri)  # tel:+12015550123;ext=1234

local = parse("tel:863-1234;phone-context=+1-914-555")
print(local.number)  # 8631234
print(local.phone_context)  # +1914555
print(local.is_global)  # False
```

`parse` validates the whole RFC 3966 grammar and returns a frozen `TelURI`. Visual
separators (`-`, `.`, `(`, `)`) are removed from the number, the extension and a numeric
`phone-context`. Other parameters land in `params`, keyed by lower-case name, with
percent-decoded values and `None` for a parameter without a value. `str()` gives the
canonical form: `ext` or `isub` first, then `phone-context`, then the rest sorted by name,
as section 3 asks.

### Errors

```python
from teluri import TelURIError, parse

reasons = []
for bad in ["tel:863-1234", "tel:+1;ext=1;isub=2", "tel:+1;b;a"]:
    try:
        parse(bad, strict=True)
    except TelURIError as error:
        reasons.append(error.reason)
print(reasons)  # ['missing-context', 'ext-and-isub', 'param-order']
```

The ABNF accepts parameters in any order, so `parse` does too; `strict=True` also
enforces the order rule of section 3.

### Compare

```python
from teluri import equivalent, parse

print(equivalent("tel:+1-201-555-0123;EXT=1;a=X", "tel:+12015550123;a=x;ext=1"))  # True
print(
    equivalent("tel:7042;phone-context=Example.COM", "tel:7042;phone-context=example.com")
)  # True
print(equivalent("tel:+1234", "tel:1234;phone-context=+1"))  # False
print(len({parse("tel:+1;b;a"), parse("tel:+1;A;B")}))  # 1
```

`==`, `hash` and `equivalent` follow section 4: global and local numbers never match,
separators are ignored, a numeric context is compared digit by digit and a domain context
as a host name, parameters are compared by name in any order, and the comparison is
case-insensitive.

### Build

```python
from teluri import build

print(build("+1 (201) 555-0123", ext="1234"))  # tel:+12015550123;ext=1234
print(build("7042", phone_context="example.com"))  # tel:7042;phone-context=example.com
print(build("+1 201 555 0123", params={"note": "a;b c"}))  # tel:+12015550123;note=a%3Bb%20c
```

`build` takes human input: it removes spaces and separators from the numbers, encodes
parameter values, refuses `ext`, `isub` and `phone-context` inside `params`, and always
writes the canonical order. The result always parses back with `strict=True`.

### Links in the wild

```python
from teluri import parse_link

print(parse_link("tel:+1 201 555 0123"))  # tel:+12015550123
print(parse_link("tel:1-408-555-5555", context="+1"))  # tel:14085555555;phone-context=+1
print(parse_link("tel:*31%23", context="example.com").href)  # tel:*31%23;phone-context=example.com
```

Web pages and apps often write `tel:` links that RFC 3966 does not allow: spaces as in
printed numbers, percent-encoded numbers, and local numbers without a `phone-context`
(Apple's Phone Links reference shows `tel:1-408-555-5555`). `parse_link` decodes and
cleans the number, adds `context` to a local number that has none, then validates the
result as RFC 3966. In the other direction, `TelURI.href` writes `#` as `%23`: an HTML
URL parser would otherwise read it as the start of a fragment. Apple also documents that
its Phone app does not dial a link containing `*` or `#`.

### Command line

```
$ teluri "tel:+1-201-555-0123;Ext=9" "tel:863-1234"
tel:+12015550123;ext=9
invalid (missing-context): tel:863-1234
```

One URI per argument, or one per line on standard input. `--json` prints every field,
`--strict` enforces the parameter order, `--link` reads links as above and `--context`
gives local links their context. The exit status is 1 when any input is invalid.

## API

| Name | What it does |
| --- | --- |
| `parse(uri, *, strict=False)` | Parse and validate a `tel:` URI, return a `TelURI` |
| `parse_link(href, *, context=None)` | Read a real-world `tel:` link, return a `TelURI` |
| `build(number, *, ext, isub, phone_context, params)` | Canonical `tel:` URI from human input |
| `equivalent(a, b)` | Section 4 comparison of two URIs (strings or `TelURI`) |
| `TelURI` | Frozen, hashable result: `number`, `ext`, `isub`, `phone_context`, `params`, `is_global`, `is_e164`, `unknown_mandatory`, `href` |
| `TelURIError` | `ValueError` with a `reason` from `Reason` |
| `Reason` | The closed set of reasons, listed below |

`is_e164` checks the E.164 limits only: a global number of at most 15 digits whose
country code does not start with 0. `unknown_mandatory` lists `m-` parameters; section
5.4 says not to use a URI whose mandatory parameters you do not understand. `isub` is
kept in its encoded form because a subaddress may carry any octet.

### Reasons

- `scheme`: not a `tel:` URI
- `number`: the number is empty or has a character the grammar does not allow
- `ext`: the extension is empty or not made of digits and separators
- `isub`: the subaddress is empty or not `1*paramchar` (erratum 203)
- `ext-and-isub`: both are present, which section 5.3 forbids
- `phone-context`: the context is neither a global number prefix nor a domain name
- `missing-context`: a local number without `phone-context`
- `global-context`: a global number with `phone-context`
- `param-name`: a parameter name is empty, malformed, or reserved for a field
- `param-value`: a value is empty, malformed, badly percent-encoded or not UTF-8
- `duplicate-param`: a parameter appears twice (names compare case-insensitively)
- `param-order`: with `strict=True`, parameters are not in the section 3 order

## Why

RFC 3966 `tel:` URIs are their own grammar: global numbers with a leading `+`, local
numbers that must carry a `phone-context`, visual separators, `ext` and `isub`, and a
comparison rule that ignores separators, case and parameter order. The standard library
does not model any of it, general URI libraries stop at RFC 3986, and `phonenumbers` is a
number-validation database rather than a URI codec. teluri is a small, strict, typed one,
with the browser and phone dialect handled explicitly instead of by accident.

## Sources

RFC 3966 and its errata, the IANA tel URI parameter registry, RFC 4694, 4715, 4759 and
4904 for the registered parameters. Their examples are checked by the test suite; run
`python scripts/fetch_upstream.py` to fetch the texts and enable the tests that compare
against them.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
