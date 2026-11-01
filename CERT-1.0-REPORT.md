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
- [x] Fix all nine QA round 1 findings; six surviving mutations now fail contracts
- [x] Fix all four QA round 2 findings; four more surviving mutations now fail contracts
- [x] Fix all three QA round 3 findings; strict parsing and constructor mutations now fail contracts
- [x] Fix QA round 4 finding E14; false-valued optional string mutation now fails contracts
- [x] Fix QA round 5 findings E15 and E16; number and private type-error mutations now fail contracts
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

## QA lenses: round 1

Reviewed base: `5eea1002049efd3bdf980a8f869621fc18b3dac0`, on 2026-11-01.
Fix commit: `30f74964781bc1a216a9345f642b4859b0136b87`. All nine findings accepted.

| Finding | Change and detecting contract |
| --- | --- |
| C-001 | Normalize string subclasses before validation and storage, including keys/values; `test_string_inputs.py` covers injected delimiters, false lengths, overridden operations and strict round trips. |
| C-002 | Preserve stdin encoding and replace malformed bytes with invalid URI characters; `test_malformed_stdin_preserves_valid_neighbors` checks bounded diagnostics and continued output in all three modes. |
| D-001 | Ship `requirements-dev.txt` and `scripts/check.ps1`; clarify contributor instructions and assert both archive members. |
| E01 / M18 | `test_domain_contexts_have_no_dns_length_limits` preserves labels over 63 characters and domains over 253 through construction, build and both parsers. |
| E02 / M30 | `test_href_escapes_every_hash_and_round_trips_without_a_fragment` asserts the complete href, no URL fragment and link round trip. |
| E03 / M40 | `test_equality_returns_not_implemented_for_foreign_operands` and `test_equality_allows_the_reflected_comparison` pin both dispatch contracts. |
| E04 / M51 | `test_link_number_is_not_percent_decoded_twice` and `test_link_cli_rejects_nested_percent_escapes` reject nested escapes; single escapes remain accepted. |
| E05 / M56 | `test_json_preserves_populated_optional_fields` checks complete subprocess JSON with encoded isub and, separately, a populated extension. |
| E06 / M60 | `test_stdin_preserves_invalid_whitespace` covers default/strict modes; link tests pin surrounding-space cleanup and rejection of whitespace-only records. |

Before implementation changes, the new contracts had 22 failures and 29 passes;
the archive check also failed on the two missing files. All 52 focused checks now pass.
The six exact lens-e mutations each fail behavioural assertions in an isolated copy;
all 51 new contracts pass before injection and after restoring the sources.
Each required gate exits 0: formatting, lint, strict source types and pytest (321 passed,
zero skips, 37.81 seconds). Strict source/test typing also passes on CPython 3.14.6.
The rebuilt sdist's documented `pip install -r requirements-dev.txt` and
`scripts/check.ps1` both pass in a fresh environment (321 tests, zero skips).
Wheel and sdist pass `twine check --strict`. Behaviour changes are in CHANGELOG 1.0.0.
Lenses c, d and e require independent re-verification; no replacement PASS verdict is
claimed. Items 16, 19 and the maintainer's merge/publication remain pending.

## QA lenses: round 2

Reviewed base: `1df80a39651f42a7254afecfb7703c3c8f67a562`, on 2026-11-01.
Fix commit: `b44fd7fc66061203d02009dd804411d8860643ac`. All four findings accepted.
These are contract gaps: the existing implementation handles the reported inputs
correctly. Runtime code and the public API are unchanged. CHANGELOG 1.0.0 records
the added coverage.

| Finding | Change and detecting contract |
| --- | --- |
| E07 / N03 | `test_parser_preserves_number_when_subclass_overrides_indexing` preserves the underlying number in default and strict modes; `test_equivalence_uses_underlying_text_when_indexing_is_overridden` covers both operand positions and string/model comparisons. |
| E08 / N11 | `test_constructor_rejects_invalid_number_hidden_by_subclass_iteration` rejects invalid underlying local numbers, including an injected delimiter, with reason `number` even when iteration yields valid digits. |
| E09 / N13 | `test_constructor_rejects_invalid_extension_hidden_by_subclass_iteration` rejects invalid underlying extensions with reason `ext` even when iteration yields valid digits. |
| E10 / N24 | `test_malformed_stdin_preserves_valid_neighbors` now covers `utf-8:strict`, `utf-8:ignore` and `utf-8:surrogateescape` in default, link and strict modes. Malformed schemes, numbers and parameter values fail with exact bounded diagnostics while valid lines before and after them remain intact. |

Each exact mutation from the review was replayed alone in an isolated source copy.
Before the additions, all four mutants passed the complete 321-test suite with zero
skips, reproducing the findings. With the strengthened contracts, N03, N11, N13 and
N24 produce respectively 3, 2, 2 and 6 behavioural assertion failures, with no
collection errors or skips. All 79 focused contracts pass on the unmodified source
both before injection and after byte-for-byte restoration.

Each required gate exits 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src` and `pytest` (349 passed, zero skips, 76.64 seconds).
Strict source/test typing also passes on CPython 3.14.6. The full suite enables
the recorded source references, installed 0.2.0 comparison, wheel installation,
CLI subprocess checks and PyPI upgrade. Every test has a 300-second timeout.
The four findings require independent lens-e re-verification; no replacement PASS
verdict is claimed. Items 16, 19 and merge/publication remain pending.

## QA lenses: round 3

Reviewed base: `bcc0a784c39b0931eadf962de376298480f6e612`, on 2026-11-01.
Fix commit: `72ce5d63ff003c4defabf4a5d85c302e4cbaeb97`. All three findings accepted.
These are contract gaps: the existing implementation preserves the underlying text
for each reported input. Runtime behaviour and the public API are unchanged.
CHANGELOG 1.0.0 records the added coverage.

| Finding | Change and detecting contract |
| --- | --- |
| E11 / S03 | `test_parser_preserves_number_when_subclass_overrides_partition` covers default and strict parsing with an overridden `partition`, asserting the underlying `+1` number and canonical `tel:+1` URI. |
| E12 / S04 | `test_constructor_preserves_number_when_subclass_overrides_indexing` asserts the underlying local number `12` and complete canonical URI when indexing returns substituted digits. |
| E13 / S06 | `test_constructor_preserves_extension_when_subclass_overrides_indexing` asserts the underlying extension `23` and complete canonical URI when indexing returns substituted digits. |

Each exact mutation was replayed alone in an isolated source copy. All three passed
the original 26 string-input contracts. With the strengthened contracts, S03, S04
and S06 each fail the corresponding value assertion above: substituted values are
`+9`, `99` and `99`, respectively. There are no collection errors or skips.
All 30 strengthened string-input contracts pass before injection and after restoring
the source bytes, which were compared with the unchanged repository sources.

Each required gate exits 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src` and `pytest` (353 passed, zero skips).
Strict source/test typing also passes on CPython 3.14.6. The full suite enables
the recorded source references, installed 0.2.0 comparison, wheel installation,
CLI subprocess checks and PyPI upgrade. Every test has a 300-second timeout.
The three findings require independent lens-e re-verification; no replacement PASS
verdict is claimed. Items 16, 19 and merge/publication remain pending.

## QA lenses: round 4

Reviewed base: `43b38cd5fc34849a7b1a219a3684171329e39782`, on 2026-11-01.
Fix commit: `15b830ed05d48615d9f9ff48f05d9a49bc933d6f`. Finding E14 accepted.
This is a contract gap: the existing implementation normalizes false-valued string
subclasses before validation. Runtime behaviour and the public API are unchanged.
CHANGELOG 1.0.0 records the added coverage.

| Finding | Change and detecting contract |
| --- | --- |
| E14 / R09 | `test_constructor_rejects_invalid_false_valued_extension` requires `TelURIError` with reason `ext` for underlying `x` and `1x` when `__bool__` returns false and iteration yields `1`. `test_constructor_preserves_false_valued_extension_and_context` and `test_constructor_preserves_false_valued_subaddress` assert plain-string storage, original values and complete canonical URIs for valid false-valued optional fields. |

The exact R09 mutation was replayed in an isolated source copy. It passed all 353
original tests with zero skips, reproducing the survivor. With the new contracts,
R09 causes four behavioural failures: two invalid extensions are accepted, a context
retains its subclass, and a valid subaddress is rejected. There are no collection
errors or skips. All 34 strengthened string-input contracts pass before injection
and after byte-for-byte source restoration against the unchanged repository source.

Each required gate exits 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src` and `pytest` (357 passed, zero skips).
Strict source/test typing also passes on CPython 3.14.6. The full suite enables
the recorded source references, installed 0.2.0 comparison, wheel installation,
CLI subprocess checks and PyPI upgrade. Every test has a 300-second timeout.
E14 requires independent lens-e re-verification; no replacement PASS verdict is
claimed. Items 16, 19 and merge/publication remain pending.

## QA lenses: round 5

Reviewed base: `12a236e35350696d7ac41b55d51b9ce2ac9da544`, on 2026-11-01.
Fix commit: `4402ebc15f449e0161e0f9c96b0ac19f8be28a87`. Both findings accepted.
These are contract gaps: the existing implementation rejects invalid underlying
number text and omits optional-field input from type errors. Runtime behaviour and
the public API are unchanged. CHANGELOG 1.0.0 records the added coverage.

| Finding | Change and detecting contract |
| --- | --- |
| E15 / N01 | `test_constructor_rejects_invalid_false_valued_number` requires `TelURIError` with reason `number` for underlying `1x` and `1;ext=9` when truth testing returns false and iteration yields `1`. `test_constructor_preserves_false_valued_number` asserts plain-string storage, normalized digits and the complete canonical URI for valid inputs. |
| E16 / N10 | `test_constructor_optional_type_errors_do_not_expose_input` requires `TypeError` for private objects supplied as `ext`, `isub` and `phone_context`. Small and large representations must be absent from exception text, repr and args, with each diagnostic shorter than 100 characters. |

Both exact mutations were replayed separately in an isolated source copy. Each
passed the original 357-test suite with zero skips, reproducing the two survivors.
With the strengthened contracts, N01 produces two behavioural assertion failures
and N10 produces six. There are no collection errors or skips. All 71 focused
contracts pass before injection and after byte-for-byte restoration of the source.
Evidence is retained under `scratch/teluri-cert/fix-r5-verify` outside the repository.

Each required gate exits 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src` and `pytest` (367 passed, zero skips).
Strict source/test typing also passes on CPython 3.14.6. The full suite enables
the recorded source references, installed 0.2.0 comparison, wheel installation,
CLI subprocess checks and PyPI upgrade. Every test has a 300-second timeout.
E15 and E16 require independent lens-e re-verification; no replacement PASS verdict
is claimed. Items 16, 19 and merge/publication remain pending.

## Initial certification gates

Each command ran separately and exited 0 on 2026-11-01:
`ruff format --check .`, `ruff check .`, `mypy --strict src`,
`mypy --strict src tests`, and `pytest` (270 passed, no skips, 36.76 seconds).
The test run enabled fetched references, the installed 0.2.0 comparison, wheel e2e
and PyPI upgrade. `pytest-timeout` enforces 300 seconds per test.
Tools: ruff 0.17.3, mypy 2.4.1, pytest 9.2.0, pytest-timeout 2.4.0,
build 1.6.1, twine 7.0.0, phonenumbers 9.0.42 and pypdf 6.21.4.
The release helper was syntax-checked without executing its publication path.

Initial wheel SHA-256: `d6e39f385e8c9055e5f62876c71d69dfa52f7bdcb241d1847fb5eb0f25292ad7`.
Initial sdist SHA-256: `83d5e0e85792623074c61c333c0f841a0a30a5df7d44d1760e4d74a2b9d5608d`.

## Scorecard

| Item | Result and evidence |
| --- | --- |
| 1 | PASS: seven stable exported names, signatures/defaults pinned; changes documented |
| 2 | PASS: exact `__all__`; no private imports in user documentation |
| 3 | PASS: 24 doctest statements across every export and public property; README/GUIDE executed |
| 4 | PASS: strict source and test typing, consumer inference and shipped `py.typed` |
| 5 | PASS: typed reasons, documented TypeError paths and input-free library diagnostics |
| 6 | PASS: 367 tests cover public behaviour, invalid inputs, CLI, source evidence and upgrade |
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
| 18 | PASS: 24 initial mutations killed; all sixteen lens-e survivors now caught, QA tables above |
| 19 | PENDING: nine round 1, four round 2, three round 3, one round 4 and two round 5 findings fixed; independent lens re-verification required |

PR: https://github.com/JaviLianes8/teluri/pull/3
