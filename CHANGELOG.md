# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-01

### Stable

- The seven exported names, their signatures and defaults: `Reason`, `TelURI`,
  `TelURIError`, `build`, `equivalent`, `parse` and `parse_link`.
- Validated immutable URI fields, canonical serialization, RFC 3966 comparison,
  the explicit link dialect, typed error reasons and command-line modes.
- Python 3.10 through 3.14; no runtime dependencies; `py.typed` included.

### Changed

- Library errors and CLI diagnostics no longer echo input, parameter names or values.
  CLI usage errors also omit arbitrary arguments. Error reasons remain unchanged;
  caller-created `TelURIError(reason, message)` still preserves its message and args.
- `parse` requires a boolean `strict`; `parse_link` rejects a non-string context with
  `TypeError` rather than leaking `AttributeError`. `build` checks strings before
  stripping whitespace and rejects false-valued non-mappings in `params`.
- Wrong-type diagnostics use fixed descriptions rather than user-controlled type names.
- CLI output failures caused by a closed pipe return 1 without a traceback.
- String subclasses are normalized to plain strings before validation and storage,
  including mapping keys and values, so overridden operations cannot bypass validation.
- CLI stdin decoding keeps its configured encoding and replaces malformed bytes with
  characters that fail URI validation. Invalid lines receive bounded diagnostics and
  valid neighboring lines are processed, even with strict input decoding configured.
- Duplicate parameter detection uses a set rather than scanning an ever-growing list.
- `TelURI` and `TelURIError` identify their public module as `teluri`; old pickles still
  load, and new pickles also load in 0.2.0. The accidental `annotations` attribute is removed.
- The release helper checks version availability and a clean working tree, preserves
  any existing `dist` directory and stops if a quality or build check fails.

### Added

- Runnable public docstrings, a guide with explicit grammar policies, strict consumer
  typing checks, seeded properties, refreshed source checks and wheel upgrade tests.
- Source distributions include the development requirements and check script referenced
  by their contributor instructions.
- Contracts for long domain contexts, multiple href hashes, reflected equality,
  single-pass link decoding, populated CLI JSON fields and stdin whitespace handling.
- Contracts for string subclasses that override indexing or hide invalid numbers and
  extensions through iteration, and malformed stdin under `ignore` and
  `surrogateescape` decoding policies while preserving valid neighboring lines.
- Contracts preserving underlying numbers in strict parsing with overridden partitioning,
  and constructor numbers and extensions with overridden indexing, including canonical URIs.
- Contracts rejecting invalid false-valued extension subclasses whose iteration hides
  their text, and preserving valid false-valued extensions, subaddresses and contexts.
- Contracts rejecting invalid false-valued number subclasses and preserving valid ones,
  plus bounded constructor type errors that omit private optional-field input.

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
