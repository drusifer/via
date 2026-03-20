# Trin Context - Working Memory

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
