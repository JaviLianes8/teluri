# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- `TelURIError.reason` from the closed set `Reason`; errors survive pickling.
- Full RFC 3966 grammar: ASCII digits only, domain names per the ABNF, `pvalue` and
  percent-encoding checks, `isub` per erratum 203, `ext` and `isub` mutually exclusive.
- `parse(..., strict=True)` enforces the section 3 parameter order.
- `equivalent(a, b)`, and `==` and `hash` on `TelURI`, follow the section 4 rules.
- `TelURI.isub`, `is_e164`, `unknown_mandatory` and `href`.
- `parse_link` reads real-world `tel:` links (spaces, encoded numbers, missing context).
- `build` accepts `isub`, strips spaces from printed numbers and encodes values.
- `teluri` command line with `--json`, `--strict`, `--link` and `--context`.

### Changed

- `str(TelURI)` writes the canonical form: section 3 order, lower-case parameter names.
- `TelURI(number, ext, isub, phone_context, params)`: `is_global` is now derived from the
  number, every field is validated on construction (wrong types raise `TypeError`), and
  `params` is read-only and hashable.
- `params` values are percent-decoded; `isub` has its own field.
- `build` percent-encodes `params` values, so callers that passed encoded values must now
  pass plain text.
- `TelURIError(reason, message)` replaces the single message argument.

## [0.1.0]

- First release: parse and build tel: URIs per RFC 3966.
- `parse` reads global numbers (leading `+`) and local numbers with a
  `phone-context`, strips visual separators, and keeps other parameters verbatim.
- `build` composes a tel: URI from a number, optional `ext`, optional
  `phone-context` and extra parameters, normalizing visual separators.
- `TelURI` is a frozen, typed result whose `str()` round-trips through `build`.
- `TelURIError` signals malformed input.
