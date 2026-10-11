# teluri

Parse and build tel: URIs per RFC 3966, zero dependencies and fully typed.

## Install

```
pip install teluri
```

## Usage

```python
from teluri import parse, build

uri = parse("tel:+1-201-555-0123;ext=1234")
uri.number         # "+12015550123"  (visual separators stripped)
uri.is_global      # True
uri.ext            # "1234"
uri.phone_context  # None
uri.params         # {}

# Local numbers carry a phone-context, as RFC 3966 requires.
local = parse("tel:863-1234;phone-context=+1-914-555")
local.number        # "8631234"
local.is_global     # False
local.phone_context # "+1914555"

build("+1 (201) 555-0123".replace(" ", ""), ext="1234")
# "tel:+12015550123;ext=1234"

build("7042", phone_context="example.com")
# "tel:7042;phone-context=example.com"
```

`parse` returns a frozen `TelURI`. Its `number`, `ext` and numeric `phone-context`
have their visual separators (`-`, `.`, `(`, `)`) stripped. Any parameter other than
`ext` and `phone-context` is preserved verbatim, in order, in `params`, with `None`
for a value-less one. `str(tel_uri)` rebuilds the URI. Malformed input, and a local
number missing its `phone-context`, raise `TelURIError`.

## Why

RFC 3966 `tel:` URIs are their own grammar: a global number (leading `+`), a local
number that needs a `phone-context`, visual separators for readability, and
parameters such as `;ext=` and `;phone-context=`. The standard library does not model
them: `urllib.parse.urlparse` mis-splits a bare `tel:` URI (a long-standing documented
bug) and knows nothing of its parameters. General URI libraries such as `uritools`
stop at RFC 3986 and do not understand `tel:` semantics, and `phonenumbers` is a large
number-validation port, not a URI codec. Other ecosystems ship a small dedicated
codec (Perl's `URI::tel`, Elixir's `ex_rfc3966`); this is a clean, typed, zero-dependency
one for Python.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
