# teluri 1.0.0 certification report

Progress:
- [x] Check certification log and create `release/1.0.0` from main `e1887d0`
- [x] Check live PyPI: 0.2.0 is the published release
- [x] Baseline gates: 205 passed, 7 skipped; formatting, lint and strict types pass
- [x] Review stable API, add docstrings and harden errors and duplicate detection
- [x] Refresh RFC and documentation sources on 2026-11-01
- [ ] Complete ground-truth, property and adversarial verification
- [ ] Complete built-wheel e2e, PyPI upgrade and installed interpreter matrix
- [ ] Complete mutation round and final gates
- [ ] Independent reviewer (item 16)
- [ ] Five QA lenses (item 19)
- [ ] PR and guard; merge and publication reserved for the maintainer

## Baseline and API review

Main `e1887d0` reports version 0.2.0. The PyPI JSON endpoint returned 0.2.0 on
2026-11-01, and that distribution was installed in a separate environment.
Baseline `ruff format --check .`, `ruff check .` and `mypy --strict src tests`
each exited 0. Pytest passed 205 tests; two wheel tests and five unfetched-source
checks skipped. Seven exported names and their signatures are retained and pinned.
Every behaviour change is listed in CHANGELOG 1.0.0. Errors now omit supplied data;
duplicate detection uses a set; wrong-type handling and closed pipes are explicit.

## Ground truth

The five RFC texts in `tests/upstream/MANIFEST.json` were fetched live on 2026-11-01
and match their existing hashes. Erratum 203, Apple Phone Links, MDN's anchor
documentation, the IANA parameter registry, Python urllib.parse documentation and
the phonenumbers README were also fetched. The manifest records URLs, retrieval
dates, revisions, sizes, hashes and source terms. Copies stay outside the repository;
`TELURI_UPSTREAM` selects their directory and absent files cause clean test skips.
The existing 25 short RFC URI examples are checked against the downloaded texts.

## Independent stages

Items 16 and 19 have not been run for this release. No lens verdict or independent
reviewer pass is claimed. Item 17 merge and publication remain pending.
