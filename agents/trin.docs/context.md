# Trin Context - Working Memory

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
