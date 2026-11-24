# Code Review — VIA Codebase
**Morpheus (Tech Lead)**
**Date**: 2026-03-21
**Scope**: Full production code (`via/`) — architecture-level smells and refactoring prescriptions

---

## Executive Summary

The codebase is well-structured and clean overall. The pipeline/renderer/parser layers are solid.
The main issues cluster in three areas:
1. **Layering violations** — DB layer knows about rendering (column widths)
2. **Direct DB access from service layer** — bypasses the `DatabaseStore` abstraction
3. **Structural duplication** — 3 nearly-identical file-storage methods, 2 identical relationship methods

Pylint score post-cleanup: **9.46/10**. Target: 9.7+ with the refactors below.

---

## CRITICAL: Layering Violations

### SMELL-1: `DatabaseStore._get_match_metadata()` computes render column widths
**File**: `via/db/store.py:553–595`
**Smell**: Data Clumps + SRP violation — the DB layer runs an aggregation query to compute
`max_symbol_name`, `max_qualified_name`, `max_file_path` widths — pure rendering concerns.
This fires an *extra aggregation SQL query* on every single `match()` call.

```python
# store.py:586-594 — DB returning rendering metadata
return {
    'total_matches': row[0],
    'column_widths': {
        'symbol_name': row[1] or 0,
        'qualified_name': row[2] or 0,
        ...
    }
}
```

**Impact**: Every query pays the cost of a second COUNT+MAX aggregation, even when output is
`-oR` (raw) where column widths are irrelevant.

**Prescription**: Move column width computation into `TableRenderer`. It already collects
all records — it can compute widths during a first pass or stream with lazy max-tracking.
Remove `_get_match_metadata()` entirely. `total_matches` can be a separate `count()` call
made lazily only when the limit warning is needed (in `executor._execute_render_stage`).

---

### SMELL-2: `_store_call_relationships` / `_store_reference_relationships` reach into `db_store.conn` directly
**File**: `via/services/indexing.py:478, 501`
**Smell**: Feature Envy + abstraction bypass — the service layer directly executes SQL
against the raw SQLite connection, bypassing `DatabaseStore` entirely.

```python
# indexing.py:478 — service accessing DB internals
cursor = self.db_store.conn.execute(
    """SELECT id FROM symbols WHERE symbol_name = ? ...""",
    (call.caller_name, caller_type, file_info.path, parent_name, parent_name)
)
```

**Prescription**: Add `DatabaseStore.get_symbol_id(name, symbol_type, file_path, parent_name)`
returning `Optional[int]`. IndexingService calls that. DB layer owns all SQL.

---

## HIGH: Dead Code / DB Doing Extra Work

### SMELL-3: `delete_file_completely` manually deletes symbol_references — FK CASCADE already handles it
**File**: `via/db/store.py:357–384`

The schema already defines `ON DELETE CASCADE` on `symbol_references(from_symbol_id)` and
`symbol_references(to_symbol_id)`. The manual deletion of relationships in
`delete_file_completely` is dead work:

```python
# store.py:371-376 — unnecessary manual delete
cursor.execute(
    """DELETE FROM symbol_references
       WHERE from_symbol_id IN (SELECT id FROM symbols WHERE file_path = ?)
          OR to_symbol_id   IN (SELECT id FROM symbols WHERE file_path = ?)""",
    (path, path),
)
```

Just deleting from `symbols` will cascade automatically. Then delete from `files`.

**Prescription**: Simplify to:
```python
cursor.execute("DELETE FROM symbols WHERE file_path = ?", (path,))
cursor.execute("DELETE FROM files WHERE path = ?", (rel_path,))
```

---

### SMELL-4: `delete_relationships_for_file` is entirely redundant with FK CASCADE
**File**: `via/db/store.py:1089–1127`

Same issue. This method loads all symbol IDs for a file and manually deletes their
relationships. The CASCADE handles this when symbols are deleted.

**Check usage**: Grep callers. If only called before `delete_symbols_by_file`, it's
dead weight. If `delete_symbols_by_file` is used without `delete_file_completely`, the
method may be needed — but the fix is still to rely on CASCADE.

---

### SMELL-5: `initialize_schema` duplicates DDL inline instead of using schema.py constants
**File**: `via/db/store.py:100–112`

`initialize_schema()` re-defines CREATE TABLE for `metadata` and `schema_migrations` inline,
even though these exact DDL strings exist in `ALL_TABLES` (schema.py).

**Prescription**: Import and use `CREATE_METADATA_TABLE`, `CREATE_SCHEMA_MIGRATIONS_TABLE`
from schema.py instead of inline strings.

---

## MEDIUM: Structural Duplication

### SMELL-6: Three near-identical "upsert raw file" methods
**File**: `via/services/indexing.py:560–616`

`_store_unparsed_file`, `_store_oversized_file`, and `_store_file_with_error` all share
the exact same skeleton:
```python
existing = self.db_store.get_file_by_path(file_info.path)
if existing:
    self.db_store.update_file(file_id=existing['id'], size_bytes=..., mtime=..., <flag>=...)
else:
    self.db_store.insert_file(path=..., size_bytes=..., mtime=..., <flag>=...)
```

They differ only in which boolean flag is set (`parsed=False`, `oversized=True`).

**Prescription**: Extract:
```python
def _upsert_raw_file(self, file_info: DiscoveredFile, *, parsed: bool = False, oversized: bool = False) -> None:
```
Then all three collapse to one-liners calling `_upsert_raw_file`.

---

### SMELL-7: `_store_call_relationships` and `_store_reference_relationships` are near-identical
**File**: `via/services/indexing.py:472–516`

Both methods:
1. Iterate over a list of entity objects
2. Look up a caller/referencer symbol by name+type+path+parent
3. Call `insert_pending_relationship(source_id, target_name, rel_type)`

The only difference is the attribute names (`call.caller_name` vs `ref.referencer_name`,
`call.callee_name` vs `ref.referenced_name`) and the `rel_type` string.

**Prescription**: Extract:
```python
def _store_pending_relationships(
    self, file_info, entities, source_name_attr, source_type_attr,
    source_parent_attr, target_name_attr, rel_type
) -> None:
```
Or better — add `source_symbol_name`, `source_symbol_type`, `target_symbol_name` as
attributes on `CallEntity`/`ReferenceEntity` so the loop is uniform.

---

### SMELL-8: `_match_with_regex` duplicates the SELECT query from `match()`
**File**: `via/db/store.py:696–780` vs `via/db/store.py:662–679`

Both methods build an identical 8-column SELECT from `symbols`. The WHERE clause building
is also partially duplicated (type filter).

**Prescription**: Extract `_build_symbols_select(where_clause: str, limit: Optional[int]) -> str`
returning the query string. Both methods call it.

---

## MEDIUM: Executor Issues

### SMELL-9: `_execute_render_stage` is a Long Method (77 lines)
**File**: `via/pipeline/executor.py:357–434`

Does too much: type conversion, option building, result filtering, rendering, and
limit/skip warnings.

**Prescription**: Extract:
- `_build_render_options(args) -> dict` (lines 376–383)
- `_warn_limit(limit, total, rendered_count)` (lines 411–417)

The inline closure `filter_supported()` using list-as-mutable-cell (`rendered_count = [0]`,
`total_matches_ref = [None]`) is a Python 2 workaround — use `nonlocal` instead (Python 3).

---

### SMELL-10: `RENDER_TYPE_FLAGS` dict is incomplete
**File**: `via/pipeline/executor.py:35–42`

Missing entries for `RAW`, `FORMATTED`, `JSON`. The fallback to `render_type.value`
silently hides the gap. Either complete the dict or put it on `RenderType` enum as a property.

---

## LOW: Minor Issues

### SMELL-11: `_calculate_qualified_name` has a hardcoded magic prefix
**File**: `via/services/indexing.py:33–55`

```python
if module.startswith('src.'):
    module = module[4:]
```

Silently strips `src.` prefix — this assumption may not hold for all projects.
Should be configurable or removed. At minimum, document the assumption.

### SMELL-12: Inconsistent transaction management in `delete_file_completely`
**File**: `via/db/store.py:368–384`

`delete_file_completely` uses `cursor.execute("BEGIN")` / `cursor.execute("COMMIT")` directly
instead of calling `self.begin_transaction()` / `self.commit_transaction()`. Inconsistent with
the rest of the class. If the class's transaction methods were used, the manual BEGIN/COMMIT
would also integrate properly with the `_in_transaction` flag.

### SMELL-13: `_execute_stats_stage` is a stub with dual suppression annotations
**File**: `via/pipeline/executor.py:436`

```python
def _execute_stats_stage(self, stage: PipelineStage):  # noqa: ARG002  pylint: disable=unused-argument
```
Both `# noqa: ARG002` (ruff) and `pylint: disable=unused-argument` suppress the same warning.
Use just one (pylint disable is already configured project-wide for this pattern).
When `stats` is implemented, remove both.

### SMELL-14: Missing blank line between `_calculate_qualified_name` and `@dataclass`
**File**: `via/services/indexing.py:55–56`

PEP-8: blank line required between top-level definitions. Minor but a ruff target.

---

## Refactoring Priority Order

| Priority | Smell | Effort | Value |
|----------|-------|--------|-------|
| P1 | SMELL-1: Remove `_get_match_metadata()`, move to renderer | Medium | High (perf + SRP) |
| P1 | SMELL-2: Add `get_symbol_id()` to `DatabaseStore`, remove `.conn` access | Small | High (abstraction) |
| P2 | SMELL-3+4: Simplify `delete_file_completely`, remove `delete_relationships_for_file` | Small | Medium |
| P2 | SMELL-6: Merge 3 file-storage methods into `_upsert_raw_file` | Small | Medium |
| P2 | SMELL-7: Merge call+ref relationship methods | Small | Medium |
| P3 | SMELL-8: Extract `_build_symbols_select` | Small | Low |
| P3 | SMELL-9: Extract helpers from `_execute_render_stage` | Small | Low |
| P3 | SMELL-5: Use schema.py constants in `initialize_schema` | Tiny | Low |
| P3 | SMELL-10: Complete `RENDER_TYPE_FLAGS` | Tiny | Low |

---

## What's Clean (Don't Touch)

- Renderer hierarchy — ABC + factory pattern, well-factored
- Pipeline architecture (parser/types/executor split)
- SymbolType / MatchOp enums — clean value objects
- MatchRecord hierarchy + MatchRecordFactory
- Schema design (`symbols` denormalized, FK cascades on `symbol_references`)
- WatchService event handling
- `delete_file_completely` semantics (wrapping atomic delete)

---

## Backlog Items Created

- **TD-REVIEW-1**: Remove `_get_match_metadata()`, push column width to TableRenderer
- **TD-REVIEW-2**: Add `DatabaseStore.get_symbol_id()`, remove `.conn` access in IndexingService
- **TD-REVIEW-3**: Simplify `delete_file_completely` (trust FK CASCADE), audit `delete_relationships_for_file`
- **TD-REVIEW-4**: Extract `_upsert_raw_file()`, merge 3 file-storage methods
- **TD-REVIEW-5**: Merge `_store_call_relationships` + `_store_reference_relationships`
