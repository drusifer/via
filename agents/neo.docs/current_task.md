# Neo Current Task

## Task: Sprint 9 Cycle 4 — Story 2a (Temporal Matcher)
**Status**: COMPLETE (100%)
**Date**: 2026-03-21

## What was done

### Story 2a: Temporal Matcher + Per-Symbol mtime

1. **`via/db/schema.py`**: `SCHEMA_VERSION = 5`. Added `mtime REAL` column to
   `CREATE_SYMBOLS_TABLE`. Added `idx_symbols_mtime` index.

2. **`via/db/store.py`**:
   - `initialize_schema()`: migration v5 — `ALTER TABLE symbols ADD COLUMN mtime REAL`
     (with PRAGMA table_info check to skip if column already exists on fresh DBs).
   - `insert_symbol()`: added `mtime: Optional[float] = None` param.
   - `match()`: added `newerthan_seconds`/`olderthan_seconds` params with SQL WHERE clauses.
   - `_match_with_regex()`: same temporal params, SQL WHERE clauses for regex path.
   - `query_relationships()`: added `result_newerthan_seconds`/`result_olderthan_seconds`.

3. **`via/core/duration.py`** (NEW): `parse_duration(value: str) -> float` — parses
   '30s', '5m', '2h', '1d', '1w' to seconds. Raises `ValueError` on bad format.

4. **`via/services/indexing.py`**: All 7 `insert_symbol()` calls updated with
   `mtime=file_info.mtime` (classes, methods, functions, imports, globals, filepath,
   filename, headers).

5. **`via/pipeline/parser.py`**: Added `parse_duration` import. Added `--newerthan`
   and `--olderthan` to `_create_match_parser()`. Result-side temporal parsed from
   object args and set on RelationshipFilter.

6. **`via/pipeline/relationship_filter.py`**: Added `result_newerthan_seconds` and
   `result_olderthan_seconds` Optional[float] fields.

7. **`via/pipeline/executor.py`**: Added `parse_duration` import. In
   `_execute_match_stage()`: parse temporal flags and pass to `db.match()`. In
   `_execute_relationship_query()`: pass result-side temporal to `query_relationships()`.

8. **`via/__main__.py`**: Added `--newerthan` and `--olderthan` to the help text
   Options section.

9. **Tests updated**: `test_line_index.py` (version 4→5 in two places).
   7 new `TestStory2a_TemporalMatcher` tests in UAT file.

## Test Results
- **908 passed, 1 xfailed** (was 901 baseline from Cycle 3)
- +7 net: 7 new Story 2a UAT tests

## Next
- Trin UAT on Story 2a
- Sprint 9 COMPLETE after UAT passes
