# Sprint 8 Task Breakdown — Line Number Index

**Scrum Master**: Mouse
**Date**: 2026-03-20
**Sprint Points**: 6 (2 user stories)
**Architecture**: `agents/morpheus.docs/SPRINT_8_ARCHITECTURE.md` ✅ APPROVED
**Stories**: `agents/cypher.docs/SPRINT_8_USER_STORIES.md` ✅ READY

---

## Sprint Goal

Ship `-mL` line slice queries — developers and AI agents can extract specific lines or
line ranges from any matched file or symbol using the pre-built index, with O(1) byte
seeks instead of file scanning.

---

## Phase Summary

| Phase | Name | Owner | Gates | Pts |
|-------|------|-------|-------|-----|
| P1 | DB Schema + Line Indexing | Neo | line_offsets table populated, unit tests pass | Story 1 |
| P2 | Pipeline Integration | Neo | `via -mg 'f.py' -tF -mL 1:5 -oR` works end-to-end | Story 2 |
| P3 | UAT | Trin | All UAT pass, make test green | 6pts done |

---

## Phase 1 — DB Schema + Line Indexing (Story 1)

**Goal**: New `line_offsets` table in schema; every indexed file's line byte offsets
are stored and updated on re-index. No pipeline changes yet.

### Tasks

- [ ] **P1-1** Add `CREATE_LINE_OFFSETS_TABLE` DDL to `via/db/schema.py`:
  ```sql
  CREATE TABLE line_offsets (
      file_id     INTEGER NOT NULL,
      line_number INTEGER NOT NULL,
      byte_offset INTEGER NOT NULL,
      byte_length INTEGER NOT NULL,
      PRIMARY KEY (file_id, line_number),
      FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
  );
  ```
  Add `"CREATE INDEX IF NOT EXISTS idx_line_offsets_file ON line_offsets(file_id);"` to `CREATE_INDEXES`.
  Add to `ALL_TABLES`. Bump `SCHEMA_VERSION = 3 → 4`.

- [ ] **P1-2** Add schema migration in `DatabaseStore.initialize_schema()`:
  - If `current_version < 4`: execute `CREATE_LINE_OFFSETS_TABLE` + index DDL, update version

- [ ] **P1-3** Add `DatabaseStore.upsert_line_offsets(file_id, offsets)`:
  - Atomic: DELETE existing rows for file_id, then `executemany` INSERT
  - Use existing `transaction()` context manager

- [ ] **P1-4** Add `DatabaseStore.get_line_byte_range(file_path, abs_start, abs_end) -> tuple[int, int]`:
  - Returns `(byte_offset, byte_length)` for lines abs_start..abs_end inclusive (1-based)
  - Single SQL query (JOIN files, MIN/MAX aggregate)
  - Returns `(0, 0)` if not found

- [ ] **P1-5** Add `IndexingService._index_line_offsets(file_id, content: bytes)`:
  - `content.splitlines(keepends=True)` → enumerate byte offsets
  - Call `db_store.upsert_line_offsets(file_id, offsets)`

- [ ] **P1-6** Wire `_index_line_offsets()` into `IndexingService._index_file()`:
  - Called immediately after symbol indexing (same `content` bytes already in memory)
  - Only for `parsed=True` files (same gate as symbol indexing)

- [ ] **P1-7** Unit tests (`tests/unit/test_line_index.py`):
  - Schema: `line_offsets` table exists after `initialize_schema()`
  - Migration: existing DB at version 3 migrates to 4 cleanly
  - `upsert_line_offsets` idempotent (re-index same file → same data, no duplicates)
  - `get_line_byte_range` returns correct byte range for known content
  - `get_line_byte_range` returns `(0, 0)` for unknown file/lines
  - Line offsets match actual file content when read at returned byte offset

- [ ] **P1-8** FK cascade test: deleting a file record cascades to `line_offsets`

**Gate**: `line_offsets` table populated after `via index .`. All P1 unit tests pass. Existing 794 tests unbroken.

---

## Phase 2 — Pipeline Integration (Story 2)

**Goal**: `-mL SLICE` modifier wired into the pipeline. Matched records have their
`byte_offset`/`byte_length` updated before rendering. No renderer changes.

### Tasks

- [ ] **P2-1** Add `parse_line_slice(s: str) -> tuple[int | None, int | None]` to `via/core/utils.py`:
  - `'5:10'` → `(5, 10)`, `'1:'` → `(1, None)`, `':5'` → `(None, 5)`, `'7'` → `(7, 7)`
  - Negative values parsed but treated as "end of symbol" (resolved in executor)
  - Raises `ValueError` on invalid input

- [ ] **P2-2** Add `-mL` / `--match-lines` argument to `PipelineParser._create_match_parser()`:
  - `dest='line_slice'`, `default=None`, `metavar='SLICE'`
  - **Not** in `MATCH_FLAGS` mutex group — optional modifier alongside `-mg/-tF`

- [ ] **P2-3** Add `PipelineExecutor._apply_line_slice(records, args)` method:
  - For each record: resolve `(rel_start, rel_end)` to absolute file lines using `record.line_number`
  - Call `self.db.get_line_byte_range(record.file_path, abs_start, abs_end)`
  - Update `record.byte_offset`, `record.byte_length`, `record.line_number` in place
  - Yield updated record (skip if `new_length == 0`)

- [ ] **P2-4** Wire `_apply_line_slice()` into `PipelineExecutor.execute()`:
  - After all MATCH stages complete and `result_iter` is ready
  - Only if `getattr(last_match_stage.args, 'line_slice', None)` is truthy

- [ ] **P2-5** Unit tests (extend `tests/unit/test_line_index.py`):
  - `parse_line_slice`: all slice forms (`5:10`, `1:`, `:5`, `7`, `-10:`)
  - `parse_line_slice` raises on garbage input
  - `_apply_line_slice` updates byte_offset/byte_length correctly
  - Open-ended slice `1:` covers to symbol end
  - Slice out-of-bounds → record skipped (byte_length=0)

- [ ] **P2-6** Integration smoke test (`tests/integration/test_cli_line_slice.py`):
  - `via -mg '*.py' -tF -mL 1:3 -oR` → returns first 3 lines of matched files
  - `via -mg 'MyClass' -tc -mL 1:5 -oR` → first 5 lines of class
  - `via -mg 'store.py' -tF -mL 2:2 -oR` → single line
  - Combined with `-oF` (syntax highlight): works with correct lines

**Gate**: All P2 tests pass. `via -mg 'store.py' -tF -mL 1:5 -oR` extracts correct first 5 lines. Existing 794+ tests unbroken.

---

## Phase 3 — UAT (Trin)

**Goal**: End-to-end acceptance tests covering all Story 2 acceptance criteria.

### Tasks

- [ ] **P3-1** UAT test file: `tests/uat/test_sprint8_uat.py`

- [ ] **P3-2** UAT cases:
  - `TestUAT81_FileLineExtraction`: `via -mg '*.py' -tF -mL 1:3 -oR` returns correct content
  - `TestUAT82_SymbolLineExtraction`: `via -mg 'MyClass' -tc -mL 1:5 -oR` correct first 5 lines of class
  - `TestUAT83_OpenSlice`: `via -mg 'file.py' -tF -mL 3: -oR` returns line 3 to end
  - `TestUAT84_SingleLine`: `-mL 1:1` returns exactly one line
  - `TestUAT85_LineNumbersMatch`: output line numbers match actual file line numbers
  - `TestUAT86_IncrementalUpdate`: modify a file, re-index, `-mL` returns updated content
  - `TestUAT87_FormattedOutput`: `-mL` works with `-oF` (syntax highlighting)

- [ ] **P3-3** Regression: `make test` — all 794+ tests pass, 0 failures

**Gate**: All UAT cases pass. Sprint 8 = SHIPPED.

---

## Dependency Chain

```
P1 (DB Schema + Line Indexing)
  └─ P2 (Pipeline) depends on P1 complete
  └─ P3 (UAT) depends on P1 + P2 complete
```

**P1 is unblocked** — start immediately.
**P2 can start after P1-4 done** (needs `get_line_byte_range()` in store).

---

## Task Count

| Phase | Tasks | Testable After |
|-------|-------|----------------|
| P1 | 8 | P1 complete |
| P2 | 6 | P2 complete |
| P3 | 3 | P3 = done |
| **Total** | **17** | |

---

## OQs Status (from Morpheus arch)

| # | Question | Status |
|---|----------|--------|
| OQ-1 | Relative vs absolute slice? | Implement as **relative** (Morpheus rec) — confirm with Drew |
| OQ-2 | Which files? | `parsed=True` only (Morpheus rec) — proceed |
| OQ-3 | Negative indices? | **Defer** to TD-S8-1 — proceed without |
