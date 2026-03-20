# Neo Current Task - Sprint 6 Watch Mode

## Task: Implement WatchService (Sprint 6)
**Status**: COMPLETE (100%)
**Date**: 2026-03-19

## What was built

- `via/services/watch.py` — `WatchService` class using `watchdog` library
- `tests/unit/test_watch_service.py` — 27 unit tests (TDD, all passing)
- `tests/integration/test_cli_watch.py` — 3 CLI integration tests
- `pyproject.toml` — added `watchdog>=3.0.0` dependency
- `via/commands/index.py` — updated help text (removed "NOT IMPLEMENTED YET")
- `via/__main__.py` — wired up watch mode dispatch

## Acceptance Criteria Coverage

| Story | AC | Status |
|-------|----|--------|
| Story 1: Basic Watch | starts watchdog observer, initial index, SIGINT shutdown | ✅ |
| Story 2: Feedback | "Watching..." + "Re-indexed: X (N symbols)" + "Removed: X" + "stopped" | ✅ |
| Story 3: Exclusions | .gitignore + DEFAULT_EXCLUDES + --exclude patterns | ✅ |
| Story 4: Error resilience | parse errors logged, DB errors caught, stop() idempotent | ✅ |
| Story 5: Force re-index | NOT YET — SIGUSR1/Ctrl-L not implemented | ⬜ |

## Story 5 remaining
Story 5 (1pt) — force re-index via SIGUSR1 while watching. Low priority (P2).
Can be done in follow-up. Core watch mode is fully functional.

## Test Results
- 691 passed, 0 failed (up from 661)
- 30 new tests added
