# teluri 1.0.0 certification report

Progress:
- [x] Check certification log and create `release/1.0.0` from main `e1887d0`
- [x] Check live PyPI: 0.2.0 is the published release
- [x] Baseline gates: 205 passed, 7 skipped; formatting, lint and strict types pass
- [x] Review stable API, add docstrings and harden errors and duplicate detection
- [x] Refresh RFC and documentation sources on 2026-11-01
- [x] Complete ground-truth and seeded property tests
- [x] Built-wheel e2e and upgrade from PyPI 0.2.0: 270 tests passed
- [ ] Complete adversarial scaling and installed interpreter matrix
- [ ] Complete mutation round and final gates
- [ ] Independent reviewer (item 16)
- [ ] Five QA lenses (item 19)
- [ ] PR and guard; merge and publication reserved for the maintainer

## Baseline and API review

Main `e1887d0` reports version 0.2.0. The PyPI JSON endpoint returned 0.2.0 on
2026-11-01, and that distribution was installed in a separate environment. All its
Python modules match main byte for byte after normalizing line endings.
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
Character-set tests derive their sets from fetched RFC 3966 ABNF and check code
points 0 through 511. IANA's registered names, Apple and MDN links and verified
erratum 203 are checked against their downloads. ITU-T E.164 (February 2026),
section A.3.1.1, supplies the 15-digit boundary via PDF text extraction.
The phonenumbers 9.0.42 implementation ran on all 245 region example numbers,
comparing RFC 3966 output, global digits and extensions in both directions.

## Properties and compatibility

Three seeds (3966, 203, 20261101) exercise 15,000 hostile strings through both
parsers and 4,500 generated builder cases with exact field assertions, strict
round trips, link serialization and equality. Large cases include 20,000 parameters,
a million-digit number, and 100,000 percent-encoded spaces. Input-free error
contracts exercise every validation family with large sensitive markers.
A separate live PyPI 0.2.0 process matches 3,000 generated build/parse results and
6,000 hostile-parser outcomes; the intentional changes have their own upgrade probes.

## Wheel and upgrade

The wheel and sdist build successfully. `twine check --strict` passes on both.
Their member lists are inspected: source, `py.typed`, license and metadata in the
wheel; source, tests, manifest, fetch script and user docs in the sdist. Neither
contains downloaded source text, caches, scratch files or certification reports.
Two throwaway venvs exercise a clean wheel install and an actual 0.2.0 install
upgraded in place. Both run an isolated API consumer and the installed command,
including JSON stdin, invalid inputs, strict/link modes, help, usage and closed pipes.
Old pickles load after upgrade and new pickles load after reinstalling 0.2.0.
The full run passed 270 tests with all source checks and e2e enabled.

## Independent stages

Items 16 and 19 have not been run for this release. No lens verdict or independent
reviewer pass is claimed. Item 17 merge and publication remain pending.
