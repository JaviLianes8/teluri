# teluri 1.0.0 certification report

Progress:
- [x] Check certification log and create `release/1.0.0` from main `e1887d0`
- [x] Check live PyPI: 0.2.0 is the published release
- [x] Baseline gates: 205 passed, 7 skipped; formatting, lint and strict types pass
- [x] Review stable API, add docstrings and harden errors and duplicate detection
- [x] Refresh RFC and documentation sources on 2026-11-01
- [x] Complete ground-truth and seeded property tests
- [x] Built-wheel e2e and upgrade from PyPI 0.2.0: 270 tests passed
- [x] Complete adversarial scaling and installed interpreter matrix
- [x] Complete mutation round: 24 of 24 killed
- [x] Final gates and distribution inspection
- [ ] Independent reviewer (item 16)
- [ ] Five QA lenses (item 19)
- [x] PR #3 opened from `release/1.0.0`; guard CLEAN
- [ ] Merge and publication reserved for the maintainer

## Baseline and API review

Main `e1887d0` reports version 0.2.0. https://pypi.org/pypi/teluri/json returned 0.2.0 on
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

## Interpreter matrix

The installed-wheel suite ran from the sdist with `src` omitted. Each distinct build
passed 267 tests, with only the three separately exercised e2e tests skipped:

| Interpreter | Result |
| --- | --- |
| CPython 3.10.22 | 267 passed, 3 skipped |
| CPython 3.11.18 | 267 passed, 3 skipped |
| CPython 3.12.16 | 267 passed, 3 skipped |
| CPython 3.13.18 | 267 passed, 3 skipped |
| CPython 3.14.6 | 267 passed, 3 skipped |
| CPython 3.14.10 free-threaded | 267 passed, 3 skipped |

At discovery only 3.14.6 existed. The launcher's other entries pointed to deleted
installations: 3.10.19/22, 3.11.5/14/17, 3.12.12/15, 3.13.2/16, 3.14.2/8 and
3.14.2t/8t could not run from those paths. Isolated interpreters supplied the remaining
supported minor versions and free-threaded coverage. No supported minor version was
left untested. Minor-version junctions resolve to the same downloaded builds.

## Adversarial scaling

Ten shapes ran at n=10,000, 4n and 16n, three measurements per size, median reported:
valid/invalid numbers, valid/invalid percent escapes, unique/late-duplicate parameters,
domain labels, link whitespace, builder values and isub octets. At 16n, elapsed time
was 7.1 to 23.4 times the n measurement, consistent with scanning plus sorting; the
largest measurement was 1.24 seconds (160,000 parameters). No quadratic growth or
unbounded diagnostics occurred. These are observations, not timing guarantees.

## Mutation round (item 18)

At code commit `03ad4f8`, each mutation was applied alone in an isolated source copy.
The 201 contract tests ran with `-x`, a 300-second per-test timeout and a 300-second
subprocess timeout; bytecode writes were disabled. All 24 mutants failed a behavioural
assertion, with zero survivors. The untouched baseline passed before and after.
The listed node is the first failing contract, not merely a collection or syntax error.

| Id | Deliberate bug | Caught by |
| --- | --- | --- |
| M01 | case-sensitive scheme | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M02 | drop parsed extension | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M03 | accept duplicate parameters | `tests/test_parse.py::test_malformed_input_names_the_rule[tel:+1;ext=1;EXT=2-duplicate-param]` |
| M04 | ignore strict order | `tests/test_parse.py::test_strict_mode_refuses_parameters_out_of_order[tel:1;phone-context=a.b;ext=2]` |
| M05 | allow hex in global numbers | `tests/test_parse.py::test_malformed_input_names_the_rule[tel:+1a-number]` |
| M06 | append extension digit | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M07 | ignore isub encoding | `tests/test_parse.py::test_malformed_input_names_the_rule[tel:+1;isub=a%zz-isub]` |
| M08 | skip value decoding | `tests/test_parse.py::test_other_parameters_are_named_in_lower_case_and_decoded` |
| M09 | ignore context in equality | `tests/test_model.py::test_different_uris_are_unequal[tel:1;phone-context=+12-tel:1;phone-context=+1]` |
| M10 | reject 15-digit E.164 shape | `tests/test_model.py::test_is_e164_checks_length_and_country_code[tel:+123456789012345-True]` |
| M11 | leave href hash unescaped | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M12 | misidentify mandatory parameters | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M13 | drop built extension | `tests/test_contract_api.py::test_guide_examples_run` |
| M14 | write raw parameter values | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M15 | case-sensitive local number equality | `tests/test_model.py::test_equality_follows_section_4` |
| M16 | wrong error base class | `tests/test_errors.py::test_is_a_value_error_with_reason_and_message` |
| M17 | omit error reason in str | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M18 | success status for invalid URI | `tests/test_cli.py::test_reports_each_invalid_uri_and_exits_one` |
| M19 | skip the character after a percent escape | `tests/test_safety.py::test_invalid_fields_never_enter_exception_messages[12]` |
| M20 | discard parameter values on lookup | `tests/test_contract_api.py::test_every_public_docstring_example_runs` |
| M21 | allow context on global number | `tests/test_parse.py::test_malformed_input_names_the_rule[tel:+1;phone-context=example.com-global-context]` |
| M22 | override existing link context | `tests/test_link.py::test_the_links_own_context_wins` |
| M23 | accept nonboolean strict | `tests/test_safety.py::test_strict_must_be_a_boolean[0]` |
| M24 | accept lone surrogate parameter | `tests/test_review.py::test_a_lone_surrogate_value_is_refused_up_front` |

## Independent stages

Items 16 and 19 have not been run for this release. No lens verdict or independent
reviewer pass is claimed. Item 17 merge and publication remain pending.

## Final gates

Each command ran separately and exited 0 on 2026-11-01:
`ruff format --check .`, `ruff check .`, `mypy --strict src`,
`mypy --strict src tests`, and `pytest` (270 passed, no skips, 36.76 seconds).
The test run enabled fetched references, the installed 0.2.0 comparison, wheel e2e
and PyPI upgrade. `pytest-timeout` enforces 300 seconds per test.
Tools: ruff 0.17.3, mypy 2.4.1, pytest 9.2.0, pytest-timeout 2.4.0,
build 1.6.1, twine 7.0.0, phonenumbers 9.0.42 and pypdf 6.21.4.
The release helper was syntax-checked without executing its publication path.

Final wheel SHA-256: `d6e39f385e8c9055e5f62876c71d69dfa52f7bdcb241d1847fb5eb0f25292ad7`.
Final sdist SHA-256: `83d5e0e85792623074c61c333c0f841a0a30a5df7d44d1760e4d74a2b9d5608d`.

## Scorecard

| Item | Result and evidence |
| --- | --- |
| 1 | PASS: seven stable exported names, signatures/defaults pinned; changes documented |
| 2 | PASS: exact `__all__`; no private imports in user documentation |
| 3 | PASS: 24 doctest statements across every export and public property; README/GUIDE executed |
| 4 | PASS: strict source and test typing, consumer inference and shipped `py.typed` |
| 5 | PASS: typed reasons, documented TypeError paths and input-free library diagnostics |
| 6 | PASS: 270 tests cover public behaviour, invalid inputs, CLI, source evidence and upgrade |
| 7 | PASS: twelve live-fetched sources, manifest, 245 reference implementation examples |
| 8 | PASS: clean wheel install, real CLI subprocesses and PyPI 0.2.0 upgrade |
| 9 | PASS: seeded properties, large inputs and ten scaling shapes |
| 10 | PASS: installed-wheel suites on all six listed interpreter builds |
| 11 | PASS: honest alternatives, absolute README links, guide and strict twine check |
| 12 | PASS: CHANGELOG 1.0.0 dated 2026-11-01 |
| 13 | PASS: 1.0.0, Production/Stable, MIT, Python classifiers, URLs, no runtime dependencies |
| 14 | PASS: both distribution member lists and metadata inspected |
| 15 | PASS: four standalone gates exit 0; strict types also include tests |
| 16 | PENDING: independent reviewer |
| 17 | PR #3 open, guard CLEAN; merge and publication pending |
| 18 | PASS: 24 of 24 mutations killed, table above |
| 19 | PENDING: five independent QA lenses |

PR: https://github.com/JaviLianes8/teluri/pull/3
