# Trin Context - Working Memory

## Session: 2026-03-21 — Query Documentation UAT + Doc Fix

### Query UAT Results (initial)
- Created `tests/uat/test_documented_queries_uat.py` — 47 pass, 5 xfail
- Full suite: 884 pass, 0 fail
- 5 doc inconsistencies found, written to `agents/trin.docs/QUERY_DOC_REVIEW_2026_03_21.md`
- Fixed `-th` → `-tH` typo in all persona SKILL.md files (oracle, morpheus, cypher, bob)

### Doc Fixes Applied (per Drew feedback)
- `schema.py` Ex02: replaced path-glob function search with valid name-glob example
- `schema.py` Ex05: updated to basename pattern (`*service*`); added note that `-mg` matches basename not full path
- `schema.py` Ex09: changed class-anchor to method-anchor for calls query; added note about class-level bug
- `schema.py` description: added notes about `-mg` matching symbol names (not paths) and `-Vr` scope limitation
- `trin.docs/SKILL.md`: fixed subclass query direction (Base on LEFT, `*` on RIGHT)
- `trin.docs/SKILL.md`: fixed "Who references Symbol?" row (Symbol on LEFT)
- `tests/uat/test_documented_queries_uat.py`: replaced 3 xfail test classes with passing tests; 2 real-bug xfails remain
- Suite: 884 → 894 pass, 5 → 2 xfail

### Remaining xfails (real bugs, not doc issues)
1. Class-level `-Vca` anchor returns empty (bug: calls stored from methods, not classes) — sprint 9 backlog
2. `-th` (lowercase) is invalid flag — confirmed impl limitation, docs already fixed to `-tH`

### Bob Protocol Update
- Bob updated all persona SKILL.md files: EXIT section is now "HARD GATE"
- Rationale: state must be saved before switching to survive context overflow/restart
- Updated: neo, trin, morpheus, oracle, mouse, cypher SKILL.md + bob-protocol/SKILL.md
- Added State Management Protocol to cypher (was missing entirely)

## Current Sprint: Sprint 8 (Line Number Index) — SIGNED OFF

### Test Suite Health (2026-03-21)
- **Full suite**: 834 pass, 0 fail
- **Sprint 8 UAT**: 7/7 pass (tests/uat/test_sprint8_uat.py)
- **Sprint 7 UAT**: 10/10 pass (unchanged)
- **No regressions**

### Key Finding: pytest tmp_path naming
- pytest names temp dirs after the test function, e.g. `test_top_func_not_in_class_sli0/`
- Assertions like `assert "top_func" not in r.stdout` false-fail because the string appears in the FILE PATH in delimiters
- Fix: assert against `"def top_func"` (with keyword prefix) to distinguish path from content

### Key Finding: -oF skips filepath symbols
- FormattedRenderer skips symbols that don't support -oF; filepath/filename types are skipped silently
- UAT for -oF must use class/function/method symbols, not filepath/filename
- stderr: `"1 record(s) skipped (don't support -oF): filepath(1)"`

### Key Finding: force re-index and parse errors
- If new file content is invalid Python (SyntaxError), the parser sets `parse_error`
- `_store_file_with_error` is called, NOT `_store_parsed_file` — line_offsets are never updated
- UAT86 fix: use valid Python content when testing force re-index

## Current Sprint: Sprint 6 (Watch Mode) — SIGNED OFF

### Test Suite Health (2026-03-19)
- **Full suite**: 709 pass, 0 fail (83% coverage)
- **Sprint 6 UAT**: 17/17 pass
- **Sprint 5 UAT**: 25/25 pass (unchanged)
- **No regressions**

### Key Finding: SQLite + Threading
- `DatabaseStore.connect()` must use `check_same_thread=False`
- WatchService uses `threading.Timer` for debounce — DB ops run in timer thread
- Without this, all timer-thread DB writes silently fail (exception caught, 0 symbols logged)
- **Diagnostic pattern**: if output says "(0 symbols)" but no error in stderr, suspect thread safety
- **Test pattern**: `test_watch_thread_safety.py` — call target method from `threading.Timer`, assert DB state

### Key Finding: Symbols table not CASCADE-linked to files
- `symbols.file_path` is a plain TEXT column, no FK to `files`
- Deleting a file record does NOT delete its symbols
- Must call `delete_symbols_by_file(path)` before/alongside `delete_file_by_path(path)`

### Test Philosophy
- Oracle First: Consult Oracle for expected behaviors
- Fast Feedback: Use `make` skill for all test runs (not raw Bash)
- Incremental: Test small components in isolation
- Quality Gates: No regressions allowed

### Test Files Added (Sprint 6)
- `tests/unit/test_watch_service.py` — 27 unit tests (Neo wrote)
- `tests/unit/test_watch_thread_safety.py` — 1 diagnostic unit test (Trin wrote)
- `tests/integration/test_cli_watch.py` — 3 CLI integration tests (Neo wrote)
- `tests/uat/test_sprint6_uat.py` — 17 UAT scenario tests (Trin wrote)

## Sprint 16 — SIGNED OFF (2026-04-08)

### Verification Result
- Status: PASS
- Targeted verification baseline: 176 passing tests
- Summary: `agents/trin.docs/SPRINT_16_UAT_Summary_2026-04-08T19:00.md`

### Coverage
- S16-1 OR-query `--slice` pagination fixed and regression-covered
- S16-2 `-ts` string constants extracted/indexed/queryable in Python and JavaScript
- S16-3 `coverage import` creates `covered-by` relationships from `coverage.xml`
- S16-4 `--canned` expands to normal via argv without a separate execution path

### QA Notes
- Sprint 15 slice regression coverage stayed green
- `make test` bootstrap was not usable in the restricted environment; verification used targeted local pytest runs instead

## Sprint 17 — SIGNED OFF (2026-04-08)

### Verification Result
- Status: PASS
- Targeted verification baseline: 138 passing tests
- Summary: `agents/trin.docs/SPRINT_17_UAT_Summary_2026-04-08T20:45.md`

### Coverage
- S17-1 `link` symbol extraction/querying
- S17-2 `http-calls` relationship for JS/TS outbound HTTP sites
- S17-3 `--contains` body filtering while preserving symbol output

## Sprint 18 — SIGNED OFF (2026-04-08)

### Verification Result
- Status: PASS
- Targeted verification baseline: 96 passing tests
- Summary: `agents/trin.docs/SPRINT_18_UAT_Summary_2026-04-08T21:14.md`

### Coverage
- S18-1 polymorphic JS parser top-level handler refactor
- Sprint 11, 14, 16, and 17 JS parser regressions stayed green

## Sprint 19 — SIGNED OFF (2026-04-08)

### Verification Result
- Status: PASS
- Targeted verification baseline: 30 passing tests
- Summary: `agents/trin.docs/SPRINT_19_UAT_Summary_2026-04-08T21:37.md`

### Coverage
- Sprint 19 builder execution path
- Existing web query and web relationship query behavior stayed green

## Sprint 20 — SIGNED OFF (2026-04-08)

### Verification Result
- Status: PASS
- Targeted verification baseline: 50 passing tests
- Summary: `agents/trin.docs/SPRINT_20_UAT_Summary_2026-04-08T21:58.md`

### Coverage
- Sprint 20 parser/builder shared seam parity
- Existing pipeline parser behavior
- Existing Sprint 19 builder behavior

## Sprint 22 Cycle 1 UAT — PASSED (2026-04-12)

### Verification Result
- Status: PASS
- Targeted verification baseline: 85 passing tests
- Summary: `agents/trin.docs/SPRINT_22_CYCLE_1_UAT_Summary_2026-04-12T17:18.md`

### Coverage
- Structured `PipelineParseError` fields.
- MCP `output_type: "error"` shape for expected parser errors.
- MCP internal error shape preserves `output_type: "error"` and logs details.
- Valid empty MCP result remains normal `output_type: "json"` with empty result.
- CLI parse errors print a recovery `Hint:` when available.
- Parser and existing MCP output/schema regressions stayed green.

## Sprint 22 Cycle 2 UAT — PASSED (2026-04-12)

### Verification Result
- Status: PASS
- Targeted verification baseline: 70 passing tests
- Summary: `agents/trin.docs/SPRINT_22_CYCLE_2_UAT_Summary_2026-04-12T17:22.md`

### Coverage
- Repeated match flags rejected in result stage.
- Mixed match flags rejected in result stage.
- Repeated matchers rejected in relationship filter stage.
- One matcher on result stage plus one matcher on filter stage remains valid.
- Invalid regex rejected in result and filter stages.
- Valid regex with no matches remains a valid parsed query.
- Multi-type OR (`-tf -tm -tc`) remains valid.
- Existing relationship CLI regressions stayed green.

## Sprint 22 Cycle 3 UAT — PASSED (2026-04-12)

### Verification Result
- Status: PASS
- Targeted verification baseline: 42 passing tests
- Forbidden old-wording scan: no matches
- Summary: `agents/trin.docs/SPRINT_22_CYCLE_3_UAT_Summary_2026-04-12T17:30.md`

### Coverage
- CLI help teaches result-stage-first syntax.
- MCP schema teaches result-stage/filter-stage syntax and regex example.
- One-matcher-per-stage docs are present.
- `agents/PROJECT.md` removed "Find all symbols in a file."
- User guide uses container filters and avoids inverse `declares` wording.

## Sprint 23 Cycle 1 UAT — PASSED (2026-04-12)

### Verification Result
- Status: PASS
- Targeted verification baseline: 9 passing tests
- Summary: `agents/trin.docs/SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18:21.md`

### Coverage
- Supported Sprint 23 canned shortcuts are registered.
- Deferred `callees` and `declared-in-file` shortcuts are not runnable built-ins.
- `callers`, `methods-calling`, and `inheritors` match explicit expanded queries.
- `--show-expanded` prints a copyable command and does not execute.
- Missing canned args remain actionable.
- Sprint 16 canned-query regression stayed green.

### QA Note
- Shortcut tests verify current runtime behavior. The docs/runtime relationship-orientation mismatch remains a Morpheus follow-up risk, not a Cycle 1 QA failure.

## Sprint 23 Cycle 2 UAT — PASSED (2026-04-12)

## Sprint 24 Cycle 2 UAT — PASSED (2026-04-13)

### Verification Result
- Status: PASS
- Full suite baseline: 1313 passed, 1 skipped, 4 warnings.
- Summary: `agents/trin.docs/SPRINT_24_CYCLE_2_UAT_Summary_2026-04-13T10:28.md`

### Coverage
- Parser preserves multiple relationship filters in order.
- Executor applies later positive relationship filters to the prior result set.
- Executor applies later negative relationship filters to exclude prior results.
- Existing single-filter relationship behavior remains covered by the full suite.

### Verification Result
- Status: PASS
- Targeted verification baseline: 30 passing tests
- Summary: `agents/trin.docs/SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18:27.md`

### Coverage
- CLI help common-task examples.
- MCP schema common-task examples.
- `--show-expanded` help discoverability.
- Uppercase `-tH` guidance and invalid lowercase `-th` schema guidance.
- Unsupported shortcut names absent from help/schema.
- Help length budget preserved: 121 lines vs 137-line maximum.

### QA Note
- Examples are runtime-correct and task-first. Smith should review final wording for HCI density and clarity.

## Sprint 23 Cycle 3 UAT — PASSED (2026-04-12)

### Verification Result
- Status: PASS
- Targeted verification baseline: 28 passing tests
- Summary: `agents/trin.docs/SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18:32.md`

### Coverage
- Unsupported diagram fallback preserves matching JSON result rows.
- Empty diagram fallback returns empty JSON with a note.
- Valid class diagram output remains `output_type: "diagram"`.
- Existing MCP output wrapper and structured error behavior stayed green.

### QA Note
- A parallel Makefile test run hit coverage SQLite combine state after tests passed. Rerunning `tests/unit/test_sprint23_c3.py` alone passed cleanly.
