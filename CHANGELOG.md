# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release: parse and build tel: URIs per RFC 3966.
- `parse` reads global numbers (leading `+`) and local numbers with a
  `phone-context`, strips visual separators, and keeps other parameters verbatim.
- `build` composes a tel: URI from a number, optional `ext`, optional
  `phone-context` and extra parameters, normalizing visual separators.
- `TelURI` is a frozen, typed result whose `str()` round-trips through `build`.
- `TelURIError` signals malformed input.
