# Sprint 9 Architecture — ReferenceType + Temporal Matcher

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-21
**Sprint**: 9
**Status**: DRAFT — for Drew review

---

## Executive Summary

Two architectural topics for Sprint 9:

1. **ReferenceType / `-Vhas`**: The DB already has `reference_type` column in `symbol_references`. The right Sprint 9 move is to rename `RelationshipType` → `ReferenceType` (aligns with the DB), add `DECLARES`, and map `-Vhas` to it. CLI unification under `--ref-type` deferred to Sprint 10.

2. **Temporal Matcher**: Add `mtime REAL` to the `symbols` table (schema migration). Watch events already call `reindex_file()`, which replaces symbols — new symbols get fresh mtime; other symbols untouched. CLI operators: `--newerthan <duration>` and `--olderthan <duration>` as pipeline-level filter flags.

---

## Part 1: ReferenceType Architecture

### Key Insight: The DB Already Has This

The `symbol_references` table already has:
```sql
reference_type TEXT NOT NULL
```

Current stored values: `'inherits-from'`, `'calls'`, `'imports'`, `'references'`

The Python enum `RelationshipType` wraps this column. The naming mismatch (`RelationshipType` in Python vs `reference_type` in DB) is the actual problem Drew is pointing at. Fixing it aligns the codebase.

### Sprint 9: Rename `RelationshipType` → `ReferenceType`

**File changes:**
- `via/core/relationship_types.py` — rename class, update TLDR docstring
- All imports updated project-wide (Grep: `from via.core.relationship_types import RelationshipType`)

The enum values themselves are unchanged. This is a **pure rename** — no behavior change, no DB migration needed.

```python
# BEFORE
class RelationshipType(Enum):
    INHERITS_FROM = 'inherits-from'
    CALLS = 'calls'
    IMPORTS = 'imports'
    REFERENCES = 'references'

# AFTER
class ReferenceType(Enum):
    INHERITS_FROM = 'inherits-from'
    CALLS = 'calls'
    IMPORTS = 'imports'
    REFERENCES = 'references'
    DECLARES = 'declares'        # NEW — Sprint 9
```

The module file can be renamed to `reference_types.py` or kept as `relationship_types.py` with an alias. **Keep the file name as-is for Sprint 9 to minimize churn**; rename the class only.

### Sprint 9: Add `DECLARES` and `-Vhas`

```python
# relationship_types.py (updated)
class ReferenceType(Enum):
    ...
    DECLARES = 'declares'        # structural containment

_SHORT_FLAGS = {
    ...
    ReferenceType.DECLARES: 'has',
}
```

```python
# flag_groups.py (updated)
RELATIONSHIP_FLAGS: List[Flag] = [
    ...
    Flag(FlagGroup.RELATIONSHIP, 'has', 'via-has', 'relationship_type', 'declares', 'Container membership'),
]
```

No other infrastructure changes needed — `query_relationships()` already dispatches on the `reference_type` column value string.

### Sprint 9: `_store_declares_relationships()` in IndexingService

No parser changes. Uses existing `file_path` and `parent_name` data.

```python
def _store_declares_relationships(self, file_info: FileInfo, symbols: List[Symbol]) -> None:
    """Store DECLARES relationships for all symbols in a file.

    Three kinds:
      1. file → every symbol in that file (file_path → symbol)
      2. class → its methods and inner classes (parent_name → symbol)
      3. function → its nested functions (parent_name → symbol, where parent is a function)
    """
    # Each symbol is declared by its file
    # Each method/inner-class/nested-function is declared by its parent
```

The `to_symbol_id` is the symbol being declared; `from_symbol_id` is the container (file symbol or class/function symbol).

**Note**: This requires `file_path` symbols to be indexed before their contained symbols — already the case in the current indexing order.

**OQ-1 resolved**: Nested function→function declarations are in scope. Same mechanism — `parent_name` already holds the containing function name.

### Container Type Validation for `-Vhas`

Valid stage 1 container types (for `-Vhas` anchor):
- `-tF` (filepath) — a file symbol, declares all symbols in the file
- `-tN` (filename) — same file, matched by basename
- `-tc` (class) — declares its methods, inner classes
- `-tf` (function) — declares nested functions

**Not valid as containers**: `-tm`, `-ti`, `-tg`, `-tH` — these don't declare children.

Error message format (per project standard):
```
Error: -Vhas requires a container type as stage 1 anchor.
Received: '-tm' (method) — methods are not containers.
Valid containers: -tF (filepath), -tN (filename), -tc (class), -tf (function).
```

### Sprint 10: CLI Unification under `--ref-type`

**Deferred.** The vision: `via -mg 'X' --ref-type declares -mg '*'` as a power-user alternative to `-Vhas`. This makes the `reference_type` column directly queryable by string value without needing a dedicated `-V<X>` flag for every type. Existing `-V<X>` flags become aliases.

This is clean but is a new CLI surface area. Sprint 10 scope.

---

## Part 2: Temporal Matcher Architecture

### Schema Migration (SCHEMA_VERSION 4 → 5)

Add `mtime REAL` to the `symbols` table:

```sql
ALTER TABLE symbols ADD COLUMN mtime REAL;
```

Migration script in `DatabaseStore.initialize_schema()` / `_run_migrations()`:
- Version 5 migration: `ALTER TABLE symbols ADD COLUMN mtime REAL`
- Existing rows: `NULL` mtime (treated as "never indexed" — will appear in `olderthan` queries)

Add index for temporal queries:
```sql
CREATE INDEX IF NOT EXISTS idx_symbols_mtime ON symbols(mtime);
```

### How `symbols.mtime` Gets Set

**On first index**: `mtime` set from the file's `os.stat().st_mtime` at index time (same value as `files.mtime` for that file). All symbols for a file share the same mtime — the file's last-modified time.

**On watch event**: `WatchService` calls `reindex_file()`. This deletes and re-inserts symbols for the changed file. New symbols get the file's current `st_mtime`. Symbols from other files are untouched — their `mtime` reflects when their file last changed.

**On full reindex (`--force`)**: All symbols are deleted and re-inserted. Each gets fresh `mtime` from its current file.

**Invariant**: `symbols.mtime` always reflects the `mtime` of the file that declared the symbol at the time it was last indexed.

### Duration Format

Human-friendly duration strings:

| Input | Seconds | Meaning |
|-------|---------|---------|
| `30s` | 30 | 30 seconds |
| `5m` | 300 | 5 minutes |
| `2h` | 7200 | 2 hours |
| `1d` | 86400 | 1 day |
| `1w` | 604800 | 1 week |

Parser: `re.match(r'^(\d+)([smhdw])$', duration)`. Reject anything else with a clear error.

**Duration format: human-friendly strings only at the CLI** (Drew confirmed "both" — the library API additionally accepts raw float seconds directly). No ISO 8601 durations.

### CLI Flags — Per-Stage (Drew confirmed, 2026-03-21)

`--newerthan` and `--olderthan` are **per-stage modifiers**, not global flags. They apply to the specific pipeline stage they are attached to, enabling queries like:

```bash
# Find tests for classes I changed in the last hour
via -mg '*' -tc --newerthan 1h -Vinh -mg 'test_*' -tf

# Find functions in recently-changed service files
via -mg '*service*' -tF --newerthan 2h -Vhas -tf -n 0

# Find tests that are older than 1 day
via -mg 'test_*' -tf --olderthan 1d
```

The flags:
```
--newerthan <duration>    Filter: symbols whose file mtime is less than <duration> ago
--olderthan <duration>    Filter: symbols whose file mtime is more than <duration> ago
```

SQL WHERE clauses:
```sql
-- newerthan 2h: symbols from files changed in last 2 hours
WHERE symbols.mtime > (strftime('%s','now') - 7200)

-- olderthan 1d: symbols from files unchanged for more than 1 day
WHERE symbols.mtime < (strftime('%s','now') - 86400)
```

**mtime is never NULL** (Drew confirmed: we can just rebuild the index; no backward compat needed).

### Parser Integration

Add to `_create_match_parser()` in `via/pipeline/parser.py`:
```python
parser.add_argument('--newerthan', dest='newerthan', default=None, metavar='DURATION',
                    help='Filter: symbols newer than duration (e.g. 1h, 2d)')
parser.add_argument('--olderthan', dest='olderthan', default=None, metavar='DURATION',
                    help='Filter: symbols older than duration (e.g. 1h, 2d)')
```

Since these are added to the shared `match_parser`, they are parsed on **both sides** of a relationship query. For a relationship query `<subject_args> -Vinh <object_args>`:
- `parsed_args.newerthan` — temporal filter for **anchor** (subject, stage 1)
- `object_parsed.newerthan` / `object_parsed.olderthan` — temporal filter for **result** (object, stage 2)

The object-side temporal must be passed through `RelationshipFilter`:
```python
@dataclass
class RelationshipFilter:
    relationship_type: ReferenceType   # renamed from RelationshipType
    object_pattern: str
    object_match_syntax: str = 'glob'
    object_types: List[str] = field(default_factory=list)
    invert: bool = False
    result_newerthan_seconds: Optional[float] = None   # NEW
    result_olderthan_seconds: Optional[float] = None   # NEW
```

And in `_parse_match_stage()`, after merging output/format flags:
```python
if object_parsed.newerthan:
    parsed_args.relationship.result_newerthan_seconds = parse_duration(object_parsed.newerthan)
if object_parsed.olderthan:
    parsed_args.relationship.result_olderthan_seconds = parse_duration(object_parsed.olderthan)
```

Subject-side temporal is parsed from `parsed_args.newerthan`/`parsed_args.olderthan` and passed to `db.match()` as seconds.

### Executor Integration

In `_execute_match_stage()`:
```python
newerthan_seconds = parse_duration(args.newerthan) if args.newerthan else None
olderthan_seconds = parse_duration(args.olderthan) if args.olderthan else None
results = self.db.match(..., newerthan_seconds=newerthan_seconds, olderthan_seconds=olderthan_seconds)
```

In `_execute_relationship_query()`, pass result-side temporal to `db.query_relationships()`:
```python
return self.db.query_relationships(
    ...,
    result_newerthan_seconds=rel.result_newerthan_seconds,
    result_olderthan_seconds=rel.result_olderthan_seconds,
)
```

### Cross-Stage Mtime Comparison — Sprint 10

Drew's second example: *"what tests are older than the class they are testing"* — this requires comparing `test.mtime < class.mtime` per relationship pair. This is a **cross-stage temporal JOIN**, not a simple filter.

Design (Sprint 10):
- Add `mtime: Optional[float]` to `MatchRecord`
- `query_relationships()` returns pairs with anchor mtime and result mtime
- New flag `--stale` means "result is older than its anchor" — post-filter in executor

**Sprint 9 delivers**: independent per-stage temporal filters. Cross-stage comparison deferred to Sprint 10.

### Python Library API

```python
# New method on DatabaseStore:
def query_symbols_changed_since(self, seconds: float) -> List[MatchRecord]:
    """Return all symbols whose mtime > (now - seconds)."""

def query_symbols_changed_before(self, seconds: float) -> List[MatchRecord]:
    """Return all symbols whose mtime < (now - seconds)."""

# Or as parameters on existing match():
def match(self, ..., newerthan_seconds: Optional[float] = None,
          olderthan_seconds: Optional[float] = None) -> Iterator[MatchRecord]:
```

**Recommendation**: Add `newerthan_seconds` and `olderthan_seconds` as optional parameters to the existing `match()` method. Avoids a new method call pattern; library consumers pass the pre-parsed float directly.

### Duration Parsing Module

New utility: `via/core/duration.py`

```python
def parse_duration(value: str) -> float:
    """Parse a human-friendly duration string to seconds.

    Args:
        value: Duration string like '1h', '30m', '2d', '1w'

    Returns:
        Number of seconds as float

    Raises:
        ValueError: with message "Invalid duration '<value>'.
                    Use format: 30s, 5m, 2h, 1d, 1w."
    """
```

---

## Implementation Ordering (Critical)

TD-REVIEW items affect the files Story 1 and Story 2a will touch. Do these first:

```
Phase 1 (TD-REVIEW — before any Sprint 9 features):
  1. TD-REVIEW-2: Add DatabaseStore.get_symbol_id() — Story 1 needs this
  2. TD-REVIEW-5: Merge _store_call + _store_ref methods — Story 1 adds a third sibling
  3. TD-REVIEW-3: Simplify delete_file_completely (trust CASCADE)
  4. TD-REVIEW-4: Extract _upsert_raw_file()
  5. TD-REVIEW-1: Move column widths to TableRenderer

Phase 2 (Story 3+4+5 — no dependencies):
  - Story 3: Expand -Vr reference tracking (parser change only)
  - Story 4: Fix class anchor bug for -Vca (executor change)
  - Story 5: -Q full-path matching (store.py + executor change)

Phase 3 (Story 1 — depends on TD-REVIEW-2, TD-REVIEW-5):
  - Rename RelationshipType → ReferenceType
  - Add DECLARES, -Vhas, _store_declares_relationships()

Phase 4 (Story 2a — schema migration, independent of Story 1):
  - Schema migration: symbols.mtime column
  - Update IndexingService to set mtime on insert
  - Update WatchService reindex_file path
  - Add --newerthan / --olderthan CLI flags
  - Add duration.py parser
  - Add library API parameters to match()
```

---

## Drew's Answers (2026-03-21) — All Resolved

| Question | Answer |
|----------|--------|
| Rename `RelationshipType` → `ReferenceType`? | ✅ Agreed |
| Per-stage vs. global modifiers? | ✅ Per-stage — enables "classes changed in last hour → find their tests" |
| Duration format? | ✅ Human-friendly strings (`1h`, `2d`) at CLI; library also accepts raw float seconds |
| Library API: add to `match()` params? | ✅ Agreed |
| `mtime NULL` semantics? | ✅ Never null — no backward compat needed; rebuild index to get mtime |

**Architecture is fully resolved. Ready for Neo implementation.**



