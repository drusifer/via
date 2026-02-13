# Sprint 6 - Watch Mode

**Author**: Cypher (PM)
**Date**: 2026-02-11
**Theme**: Watch Mode & Live Indexing
**Points**: 12

---

## Epic: Watch Mode (`via index -w`)

Enable `via` to run in the foreground, monitoring file changes and automatically re-indexing affected files. This eliminates the manual `via index .` step after editing code.

### Decisions (Drew, 2026-02-11)

| Decision | Answer |
|----------|--------|
| Debounce timing | 500ms, no configuration needed |
| File types | All supported files (`.py`, `.pyx`, `.pyi`, `.md`) |
| Relationship re-resolution | Yes, update/add/remove on re-index (2-pass OK) |
| Library | watchdog (cross-platform) |

---

### Story 1: Basic Watch Mode (P0, 5pts)

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

### Story 2: Watch Mode Feedback (P0, 2pts)

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

### Story 3: Watch Mode Respects Exclusions (P1, 2pts)

**As a developer**, I want watch mode to respect `.gitignore` and `--exclude` patterns, so it doesn't index generated files or virtual environments.

**Acceptance Criteria**:
- [ ] Watch mode ignores changes in directories matching `.gitignore` patterns
- [ ] Watch mode ignores changes matching `--exclude PATTERN` arguments
- [ ] Default exclusions apply: `.git/`, `__pycache__/`, `.venv/`, `node_modules/`
- [ ] Changes to excluded files produce no output and no re-indexing

---

### Story 4: Watch Mode Error Resilience (P1, 2pts)

**As a developer**, I want watch mode to handle errors gracefully without crashing, so I can leave it running during long coding sessions.

**Acceptance Criteria**:
- [ ] If a file has a syntax error, watch mode logs the error and continues watching
- [ ] If the database is locked (concurrent access), watch mode retries after a brief delay
- [ ] If a watched directory is deleted, watch mode logs a warning and continues
- [ ] Watch mode survives at least 1 hour of continuous operation without memory leaks or crashes
- [ ] Partial failures don't corrupt the index database

---

### Story 5: Force Re-index in Watch Mode (P2, 1pt)

**As a developer**, I want to trigger a full re-index while watch mode is running, without restarting it.

**Acceptance Criteria**:
- [ ] Pressing `Ctrl-L` (or sending SIGUSR1) in watch mode triggers a full re-index
- [ ] Full re-index uses `--force` logic (ignores mtime, re-parses everything)
- [ ] After re-index, normal incremental watching resumes
- [ ] Feedback: `Full re-index triggered... Done. (<N> files, <M> symbols)`

---

## Sprint 6 Summary

| Story | Points | Priority | Description |
|-------|--------|----------|-------------|
| Story 1 | 5 | P0 | Basic watch mode (watchdog → re-index) |
| Story 2 | 2 | P0 | Terminal feedback & debouncing |
| Story 3 | 2 | P1 | Exclusion pattern support |
| Story 4 | 2 | P1 | Error resilience & stability |
| Story 5 | 1 | P2 | Force re-index while watching |
| **Total** | **12** | | |

---

## Technical Context

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
