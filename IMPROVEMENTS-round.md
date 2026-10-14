# teluri improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: RFC 3966 and parameter RFC examples, errata, manifest
- [x] Error reasons: `TelURIError.reason` from a closed set, picklable
- [x] Full RFC 3966 grammar: digits, domain names, `isub`, `pvalue`, ext and isub exclusive
- [x] Canonical form: section 3 parameter order, lower-case names, encoded values
- [x] Comparison per section 4: `==`, `hash` and `equivalent`
- [x] Safe builder: spaces and separators stripped, values percent-encoded, order fixed
- [x] Link dialect: `parse_link` for real-world `href` values, `href` for HTML
- [x] E.164 length check and unknown mandatory parameters
- [x] Command line: canonical form or JSON per URI, link mode
- [x] Contracts: RFC examples, README examples, typing, installed wheel
- [x] Docs and packaging: README, CHANGELOG, metadata, sdist contents
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Mutation run: removing guarded logic makes the suite fail
- [x] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` gives `parse`, `build`, a frozen `TelURI` and `TelURIError`. Checked against the
sources below:

- `isub` is kept as an ordinary parameter: it is not validated, and `ext` together with
  `isub` is accepted although section 5.3 allows at most one of them.
- Parameter values are never checked against `pvalue`: `tel:+1;a=b c`, `tel:+1;a=%zz`
  and `tel:+1;a=` all parse.
- Domain names in `phone-context` are checked only by character set, so `-x-.`, `..` and
  a numeric top label are accepted.
- `str()` writes parameters in input order, so `tel:+1;b;a` is not written in the order
  that section 3 requires (isub or ext, then phone-context, then the rest sorted).
- Equality is plain field comparison: case, parameter order and percent-encoding make two
  equivalent URIs unequal, and `TelURI` is not hashable because `params` is a dict.
- `build` copies parameter values verbatim, so a value with `;` or a space produces a
  broken URI. Names are not lower-cased, order is not fixed.
- Errors carry prose only; callers cannot branch on the cause.
- Real links (`tel:+1 201 555 0123`, `tel:555-0100` with no context, `%23` for `#`) have
  no supported path, and nothing helps write an `href` that keeps a `#`.
- `phone-context` given as a number is accepted with any length; E.164 limits are not
  available to the caller.

## Sources (fetched 2026-10-14)

- RFC 3966, https://www.rfc-editor.org/rfc/rfc3966.txt (sha256
  38d9aeec48d7f07120bd603f70b2da478218ffd3356eb362a651a31d0ff816bd): ABNF (3), parameter
  order (3), comparison (4), numbers and context (5.1), isub (5.2), ext (5.3), mandatory
  `m-` parameters (5.4), examples (6, 8).
- RFC 3966 errata, https://www.rfc-editor.org/errata/rfc3966: 202 (verified, wording in
  5.1.5), 203 (verified: `isub` takes `1*paramchar`, not `1*uric`), 702 (held, fax and
  modem schemes), 4376 (held, the optional `[ visual-separator ]` alternatives).
- IANA tel URI parameters, https://www.iana.org/assignments/tel-uri-parameters/ (RFC 5341
  registry): isub, isub-encoding, ext, phone-context, enumdi, npdi, rn, rn-context, cic,
  cic-context, tgrp, trunk-context, premium-rate, verstat.
- RFC 4694 (npdi, rn, cic), RFC 4715 (isub-encoding), RFC 4759 (enumdi), RFC 4904 (tgrp,
  trunk-context), all from https://www.rfc-editor.org/rfc/: examples used as fixtures.
- E.164 length: the ITU text is behind a login; the 15 digit limit (country code plus
  national number) is taken from https://en.wikipedia.org/wiki/E.164, which cites it.
- Dialects: Apple Phone Links reference,
  https://developer.apple.com/library/archive/featuredarticles/iPhoneURLScheme_Reference/PhoneLinks/PhoneLinks.html
  (links such as `tel:1-408-555-5555` with no context; the Phone app refuses `*` and
  `#`), MDN `<a>` element, https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a
  (`tel:+49.157.0156`, `tel:+1(800)555-0123`).

## Ranked improvements

1. Closed set of error reasons on `TelURIError` (`reason`, `Literal` type, picklable).
2. Full grammar: ASCII digits only, at least one digit in a global number and one hex,
   `*` or `#` in a local one, RFC 1034 style domain names, `pname`, `pvalue` with valid
   percent-encoding, `isub` per erratum 203, `ext` and `isub` mutually exclusive, no
   duplicate names, empty values refused.
3. Canonical `str()`: section 3 order, lower-case names, values re-encoded. `strict=True`
   additionally refuses input that breaks the order rule.
4. Comparison per section 4: global or local, digits without separators, numeric context
   digit by digit and domain context as a host name, parameters by name in any order,
   case-insensitive. `==`, `hash` and `equivalent(a, b)` agree.
5. Safe builder: strips spaces and visual separators from human input, percent-encodes
   values, refuses reserved names in `params`, writes canonical order.
6. Link dialect, documented as non-RFC: `parse_link` accepts spaces, `%20`, `%23`, a
   missing context filled from a default; `TelURI.href` writes `#` as `%23` so browsers do
   not treat it as a fragment.
7. `is_e164` (global, 1 to 15 digits, no leading zero) and `unknown_mandatory` (`m-`
   parameters a caller must refuse per section 5.4).
8. Command line `teluri`: canonical form or JSON per URI, from arguments or stdin, exit 1
   with the reason, `--link` and `--context` for the dialect.
9. Contracts: RFC examples extracted by script into `tests/data`, checked against the
   fetched text (skipped while absent), README examples run, typing pinned with mypy,
   installed wheel driven end to end.
10. Docs and packaging: README with API table and reasons, CHANGELOG `0.2.0`, keywords,
    classifiers, sdist limited to sources and tests.

Deferred: parameter-specific grammars from RFC 4694 and 4904 (`rn`, `cic`, `tgrp`) are
validated only as generic `pvalue`; the `isub-encoding` semantics are left to callers.

## Results

- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src tests` and `pytest`
  (212 tests with the installed wheel end to end and the fetched RFC texts) exit 0.
- Mutation run: 58 hand-written mutants on the first pass, 6 survived. Four guarded code
  that other checks already covered (a `+` test, two empty-value tests, a `%` test in the
  link reader; removed), two exposed missing assertions (the error `args`, the `params`
  hash; added). The second pass, after the review fixes, ran 62 mutants including the new
  code: two survived (type checks whose fallback was a less helpful `TypeError`) and are now
  pinned by their messages. The suite was green before and after each run.
- Review: ASCII-only command line output, the link context checked as one descriptor, lone
  surrogates refused, `--strict` with `--link` refused, `TypeError` for wrong types, values
  and `isub` compared on decoded octets with ASCII case folding, and the README and
  CHANGELOG wording on the normalised form were fixed with tests in `tests/test_review.py`.
