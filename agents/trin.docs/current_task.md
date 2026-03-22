# Trin Current Task

## Task: Sprint 9 Cycle 4 UAT — Story 2a (Temporal Matcher)
**Status**: COMPLETE — UAT PASSED
**Date**: 2026-03-21

## Review Results

### Story 2a: Temporal Matcher ✅

**`via/db/schema.py`**: `SCHEMA_VERSION = 5`, `mtime REAL` in CREATE_SYMBOLS_TABLE,
`idx_symbols_mtime` index added to CREATE_INDEXES. ✅

**`via/db/store.py`**:
- Migration v5: PRAGMA table_info(symbols) check before ALTER TABLE — no duplicate column error on fresh DBs ✅
- `insert_symbol()`: `mtime: Optional[float] = None` param, stored in INSERT ✅
- `match()`: `newerthan_seconds`/`olderthan_seconds` → `mtime > (now - N)` / `mtime < (now - N)` WHERE clauses ✅
- `_match_with_regex()`: same temporal params applied before Python-side regex filter ✅
- `query_relationships()`: `result_newerthan_seconds`/`result_olderthan_seconds` applied to `select_from.mtime` ✅

**`via/core/duration.py`**: `parse_duration` — regex `^(\d+)([smhdw])$`, dict of multipliers,
raises `ValueError` with clear message on bad input ✅

**`via/services/indexing.py`**: All 7 `insert_symbol()` calls pass `mtime=file_info.mtime`
(classes, methods, functions, imports, globals, filename, filepath, headers) ✅

**`via/pipeline/parser.py`**: `--newerthan`/`--olderthan` in `_create_match_parser()`,
result-side temporal parsed from object args, `parse_duration` called at parse time ✅

**`via/pipeline/relationship_filter.py`**: `result_newerthan_seconds`, `result_olderthan_seconds`
Optional[float] fields with correct defaults ✅

**`via/pipeline/executor.py`**: temporal flags parsed in `_execute_match_stage()`,
passed to `db.match()`; result-side from `rel.result_*` passed to `query_relationships()` ✅

**`via/__main__.py`**: `--newerthan`/`--olderthan` in help text Options section ✅

## Test Results
- **908 passed, 1 xfailed** (was 901 baseline from Cycle 3)
- +7 net: 7 new Story 2a UAT tests

## Notes
- `test_olderthan_filters_out_recent_symbols` is mildly timing-sensitive (assumes indexing was < 1h ago). Passes reliably in test runs since fixture is indexed in the same session.
- `--newerthan` on first run (no prior index): all symbols have mtime set from fresh index = all qualify as "new". Correct behavior per spec.
- No mtime on external module symbols (inserted as '<external>' with no file stat). mtime=NULL for module symbols. Temporal filter on module symbols returns nothing — acceptable edge case.
