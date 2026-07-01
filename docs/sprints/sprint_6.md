# Sprint 6 Consolidated Documentation

This document consolidates all documentation for Sprint 6.

## Table of Contents

- [SPRINT_6_BACKLOG.md](#sprint-6-backlogmd) (originally `agents/cypher.docs/SPRINT_6_BACKLOG.md`)

- [SPRINT_6_BACKLOG_20260124190429.md](#sprint-6-backlog-20260124190429md) (originally `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124190429.md`)

- [SPRINT_6_BACKLOG_20260124201814.md](#sprint-6-backlog-20260124201814md) (originally `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124201814.md`)

- [SPRINT_6_BACKLOG_20260124201845.md](#sprint-6-backlog-20260124201845md) (originally `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124201845.md`)

- [SPRINT_6_BACKLOG_20260124202018.md](#sprint-6-backlog-20260124202018md) (originally `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124202018.md`)

- [SPRINT_6_USER_STORIES.md](#sprint-6-user-storiesmd) (originally `agents/cypher.docs/SPRINT_6_USER_STORIES.md`)

- [SPRINT_6_REVIEW.md](#sprint-6-reviewmd) (originally `agents/morpheus.docs/SPRINT_6_REVIEW.md`)

- [project_sprint6_lessons.md](#project-sprint6-lessonsmd) (originally `memory/project_sprint6_lessons.md`)


---


## SPRINT_6_BACKLOG.md

**Original Location**: `agents/cypher.docs/SPRINT_6_BACKLOG.md`


## Sprint 6 - Backlog

**Author**: Cypher (PM)
**Date**: 2026-01-24

### User Stories

#### 1. Implement Correct `UsageRenderer` Functionality [COMPLETE]
*   **User Story**: As a developer, I want to quickly see the 'usage' aka docstring/javadoc/manpage etc. for the matched symbols.

*   **Acceptance Criteria**:
    *   The existing `UsageRenderer` is refactored to find and display usages of a symbol.
    *   When a user runs `via -mg 'my_symbol' -t<X> -oU`, the output shows a the rendered docstring for the symbol
    *   The output should be clearly formatted, showing the file, line number, and the line of code containing the symbol definition.


---


## SPRINT_6_BACKLOG_20260124190429.md

**Original Location**: `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124190429.md`


## Sprint 6 - Backlog\n\n**Author**: Cypher (PM)\n**Date**: 2026-01-24\n\n## User Stories\n\n### 1. Implement Correct `UsageRenderer` Functionality\n\n*   **User Story**: As a developer, I want to find all usages of a symbol so that I can understand its impact and dependencies throughout the codebase.\n\n*   **Acceptance Criteria**:\n    *   The existing `UsageRenderer` is refactored to find and display usages of a symbol.\n    *   When a user runs `via -mg 'my_symbol' -t<X> -oU`, the output shows a list of files and line numbers where `my_symbol` is used.\n    *   The implementation should be efficient, using `ripgrep` or a similar fast search tool.\n    *   The output should be clearly formatted, showing the file, line number, and the line of code containing the usage.


---


## SPRINT_6_BACKLOG_20260124201814.md

**Original Location**: `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124201814.md`


## Sprint 6 - Backlog

**Author**: Cypher (PM)
**Date**: 2026-01-24

### User Stories

#### 1. Implement Correct `UsageRenderer` Functionality
*   **User Story**: As a developer, I want to quickly see the 'usage' aka docstring/javadoc/manpage etc. for the matched symbols.

*   **Acceptance Criteria**:
    *   The existing `UsageRenderer` is refactored to find and display usages of a symbol.
    *   When a user runs `via -mg 'my_symbol' -t<X> -oU`, the output shows a list of files and line numbers where `my_symbol` is used.
    *   The implementation should be efficient, using `ripgrep` or a similar fast search tool.
    *   The output should be clearly formatted, showing the file, line number, and the line of code containing the usage.


---


## SPRINT_6_BACKLOG_20260124201845.md

**Original Location**: `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124201845.md`


## Sprint 6 - Backlog

**Author**: Cypher (PM)
**Date**: 2026-01-24

### User Stories

#### 1. Implement Correct `UsageRenderer` Functionality
*   **User Story**: As a developer, I want to quickly see the 'usage' aka docstring/javadoc/manpage etc. for the matched symbols.

*   **Acceptance Criteria**:
    *   The existing `UsageRenderer` is refactored to find and display usages of a symbol.
    *   When a user runs `via -mg 'my_symbol' -t<X> -oU`, the output shows a the rendered docstring for the symbol
    *   The output should be clearly formatted, showing the file, line number, and the line of code containing the usage.


---


## SPRINT_6_BACKLOG_20260124202018.md

**Original Location**: `.history/agents/cypher.docs/SPRINT_6_BACKLOG_20260124202018.md`


## Sprint 6 - Backlog

**Author**: Cypher (PM)
**Date**: 2026-01-24

### User Stories

#### 1. Implement Correct `UsageRenderer` Functionality
*   **User Story**: As a developer, I want to quickly see the 'usage' aka docstring/javadoc/manpage etc. for the matched symbols.

*   **Acceptance Criteria**:
    *   The existing `UsageRenderer` is refactored to find and display usages of a symbol.
    *   When a user runs `via -mg 'my_symbol' -t<X> -oU`, the output shows a the rendered docstring for the symbol
    *   The output should be clearly formatted, showing the file, line number, and the line of code containing the symbol definition.


---


## SPRINT_6_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_6_USER_STORIES.md`


## Sprint 6 - Watch Mode

**Author**: Cypher (PM)
**Date**: 2026-02-11
**Theme**: Watch Mode & Live Indexing
**Points**: 12

---

### Epic: Watch Mode (`via index -w`)

Enable `via` to run in the foreground, monitoring file changes and automatically re-indexing affected files. This eliminates the manual `via index .` step after editing code.

#### Decisions (Drew, 2026-02-11)

| Decision | Answer |
|----------|--------|
| Debounce timing | 500ms, no configuration needed |
| File types | All supported files (`.py`, `.pyx`, `.pyi`, `.md`) |
| Relationship re-resolution | Yes, update/add/remove on re-index (2-pass OK) |
| Library | watchdog (cross-platform) |

---

#### Story 1: Basic Watch Mode (P0, 5pts)

**As a developer**, I want to run `via index -w` and have it automatically re-index files when I save changes, so my queries always reflect the latest code.

**Acceptance Criteria**:
- [ ] `via index -w .` starts in the foreground and blocks the terminal
- [ ] On startup, performs a full incremental index (same as `via index .`)
- [ ] After initial index, watches for file changes using `watchdog` library
- [ ] When a supported file (`.py`, `.pyx`, `.pyi`, `.md`) is modified, only that file is re-indexed
- [ ] When a new supported file is created, it is indexed automatically
- [ ] When a supported file is deleted, its symbols are removed from the database
- [ ] On re-index, relationships are updated (add/remove) using 2-pass resolution
- [ ] Ctrl-C (SIGINT) gracefully stops the watcher and exits cleanly
- [ ] Non-parseable files (e.g., `.txt`, `.json`) are tracked as metadata only (existing behavior)

**Notes**:
- Architecture decision (Morpheus): foreground-only, no daemon/PID complexity
- Use existing `IndexingService` and `_should_index_file()` mtime logic
- `watchdog` is the specified library per `VIA_INDEX_SPEC.md`

---

#### Story 2: Watch Mode Feedback (P0, 2pts)

**As a developer**, I want to see clear feedback in the terminal when watch mode detects and processes changes, so I know the index is up to date.

**Acceptance Criteria**:
- [ ] On startup, prints: `Watching <dir> for changes... (Ctrl-C to stop)`
- [ ] On file change, prints: `Re-indexed: <filepath> (<N> symbols)`
- [ ] On file create, prints: `Indexed: <filepath> (<N> symbols)`
- [ ] On file delete, prints: `Removed: <filepath>`
- [ ] On Ctrl-C, prints: `Watch mode stopped.`
- [ ] Respects verbosity flags: `-v` shows more detail, default is terse
- [ ] No output spam: debounce rapid saves (500ms cooldown per file)

---

#### Story 3: Watch Mode Respects Exclusions (P1, 2pts)

**As a developer**, I want watch mode to respect `.gitignore` and `--exclude` patterns, so it doesn't index generated files or virtual environments.

**Acceptance Criteria**:
- [ ] Watch mode ignores changes in directories matching `.gitignore` patterns
- [ ] Watch mode ignores changes matching `--exclude PATTERN` arguments
- [ ] Default exclusions apply: `.git/`, `__pycache__/`, `.venv/`, `node_modules/`
- [ ] Changes to excluded files produce no output and no re-indexing

---

#### Story 4: Watch Mode Error Resilience (P1, 2pts)

**As a developer**, I want watch mode to handle errors gracefully without crashing, so I can leave it running during long coding sessions.

**Acceptance Criteria**:
- [ ] If a file has a syntax error, watch mode logs the error and continues watching
- [ ] If the database is locked (concurrent access), watch mode retries after a brief delay
- [ ] If a watched directory is deleted, watch mode logs a warning and continues
- [ ] Watch mode survives at least 1 hour of continuous operation without memory leaks or crashes
- [ ] Partial failures don't corrupt the index database

---

#### Story 5: Force Re-index in Watch Mode (P2, 1pt)

**As a developer**, I want to trigger a full re-index while watch mode is running, without restarting it.

**Acceptance Criteria**:
- [ ] Pressing `Ctrl-L` (or sending SIGUSR1) in watch mode triggers a full re-index
- [ ] Full re-index uses `--force` logic (ignores mtime, re-parses everything)
- [ ] After re-index, normal incremental watching resumes
- [ ] Feedback: `Full re-index triggered... Done. (<N> files, <M> symbols)`

---

### Sprint 6 Summary

| Story | Points | Priority | Description |
|-------|--------|----------|-------------|
| Story 1 | 5 | P0 | Basic watch mode (watchdog → re-index) |
| Story 2 | 2 | P0 | Terminal feedback & debouncing |
| Story 3 | 2 | P1 | Exclusion pattern support |
| Story 4 | 2 | P1 | Error resilience & stability |
| Story 5 | 1 | P2 | Force re-index while watching |
| **Total** | **12** | | |

---

### Technical Context

**What already exists**:
- `-w` / `--watch` flag is parsed by argparse (currently errors with "not implemented")
- `IndexingService` supports incremental indexing via mtime checks
- `FileDiscovery` handles `.gitignore` and exclusion patterns
- `ParserRegistry` is plugin-based with extension mapping

**What needs to be built**:
- `WatchService` class in `via/services/watch.py`
- `watchdog` event handler wired to `IndexingService`
- Debounce logic (500ms), SIGINT handling, symbol cleanup on delete
- Relationship re-resolution on file change

**Architecture**: Per Morpheus's decision - foreground only, no daemon complexity.


---


## SPRINT_6_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_6_REVIEW.md`


## Sprint 6 Architecture Review — Watch Mode

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-19
**Status**: SIGNED OFF with tech debt items recorded

---

### Verdict: APPROVED

Sprint 6 ships a correct, well-tested Watch Mode. Architecture is sound. Two bugs were caught by Trin's UAT and fixed before sign-off. Tech debt items below are non-blocking.

---

### What's Good

| Area | Assessment |
|------|-----------|
| Observer pattern | `_ViaEventHandler` delegates cleanly to `WatchService` — no business logic in the event handler |
| Debounce | `threading.Lock` + `threading.Timer` pattern is correct and minimal |
| SIGINT | Save/restore original handler, `threading.Event`-driven loop — textbook |
| Error resilience | Exceptions in `_execute` are caught; watcher survives parse errors |
| TDD | 30 unit + integration tests. 17 UAT scenarios. Both bugs caught pre-ship |
| Thread safety fix | `check_same_thread=False` in `DatabaseStore.connect()` is the right call |

---

### Tech Debt (Non-Blocking)

#### TD-1: No transaction in `_reindex_file` (MEDIUM)

`WatchService._reindex_file` calls `indexing_service._index_file()` directly, bypassing the `begin_transaction / commit_transaction` wrapper used by `IndexingService.index()`.

**Risk**: If the process is killed mid-reindex, the DB can be left in partial state — old symbols deleted, new ones only partially inserted.

**Fix (Sprint 7 or 8)**: Either:
- Expose a `IndexingService.reindex_file(file_info)` method that wraps `_index_file` in a transaction, OR
- Add `begin_transaction / commit_transaction` around the `_index_file` call in `_reindex_file`

#### TD-2: `WatchService` takes redundant `db_store` parameter (LOW)

`db_store` is already accessible via `indexing_service.db_store`. Passing it separately creates a potential for divergence.

**Fix**: Remove `db_store` parameter. Access via `self.indexing_service.db_store` internally.

#### TD-3: Lazy imports inside methods (LOW)

```python
## In _reindex_file:
from via.core.discovery import DiscoveredFile

## In __init__:
import pathspec
```

Move both to module-level imports. Lazy imports mask dependencies.

#### TD-4: `_discovery._should_include_file` is a private call (LOW)

`WatchService._is_watched_file` calls `self._discovery._should_include_file(path)` — accessing a private method of `FileDiscovery`. Should be public API.

**Fix**: Add `FileDiscovery.should_include(path: str) -> bool` public method.

#### TD-5: `IOBase` imported but unused (TRIVIAL)

```python
from io import IOBase  # line 17 — never used
```

Remove.

---

### Bug Post-Mortem

#### Bug 1: SQLite `check_same_thread=True` (CRITICAL — FIXED)

**Root Cause**: `threading.Timer` callbacks run in a thread different from the one that created the DB connection. SQLite's default `check_same_thread=True` raises a `ProgrammingError` which was silently caught, resulting in no-op reindexes ("Re-indexed: X (0 symbols)").

**Lesson**: Any service using `threading.Timer` or `ThreadPoolExecutor` for DB work must have `check_same_thread=False`. This should be documented in DatabaseStore.

**Fix applied**: `sqlite3.connect(self.db_path, check_same_thread=False)`

#### Bug 2: Missing `delete_symbols_by_file` in `_remove_file` (MEDIUM — FIXED)

**Root Cause**: `symbols` table has no `FOREIGN KEY` to `files` (by design — denormalized). `delete_file_by_path` deletes the `files` row but leaves orphaned symbols.

**Lesson**: Any code deleting a file from the index must call the deletion triad: `delete_relationships_for_file` → `delete_symbols_by_file` → `delete_file_by_path`. This pattern should be a single `delete_file_completely(path)` method on DatabaseStore.

**Fix applied**: Added `self.db_store.delete_symbols_by_file(path)` to `_remove_file`.

---

### Architectural Recommendation for TD-2 + Bug 2

Add a `DatabaseStore.delete_file_completely(path)` method that encapsulates the deletion triad. This eliminates the risk of callers forgetting one of the three steps:

```python
def delete_file_completely(self, path: str) -> None:
    """Remove file, its symbols, and its relationships from the index."""
    self.delete_relationships_for_file(path)
    self.delete_symbols_by_file(path)
    self.delete_file_by_path(path)
```

And similarly, expose `IndexingService.reindex_file(path)` as a public method to replace the `_index_file` private call in WatchService.

---

### Sprint 6 Final State

| Metric | Value |
|--------|-------|
| Tests added | 48 (27 unit + 1 diagnostic + 3 integration + 17 UAT) |
| Total tests | 709 |
| Coverage | 83% |
| Bugs found in UAT | 2 |
| Bugs fixed before ship | 2 |
| Regressions | 0 |


---


## project_sprint6_lessons.md

**Original Location**: `memory/project_sprint6_lessons.md`


---
name: Sprint 6 lessons learned
description: Key bugs and architectural lessons from Sprint 6 Watch Mode implementation
type: project
---

Two bugs found in UAT (both fixed before ship):

**Bug 1: SQLite + threading = check_same_thread=False**
`DatabaseStore.connect()` now uses `check_same_thread=False`. Required because `WatchService` runs DB ops in `threading.Timer` threads. Without it: silent failures, "0 symbols" output, nothing actually committed.

**Bug 2: Symbols table not CASCADE-linked to files**
`symbols.file_path` is a plain TEXT column. Deleting a file record does NOT cascade. Must call `delete_symbols_by_file()` + `delete_file_by_path()`. TD item: add `DatabaseStore.delete_file_completely()`.

**Why:** These are non-obvious gotchas that could recur in Sprint 7/8.

**How to apply:** When writing any new service that uses DB from a non-main thread, verify `check_same_thread=False` is set. When deleting files from index, always use the deletion triad.


---
