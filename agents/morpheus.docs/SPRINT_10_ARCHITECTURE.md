# Sprint 10 Architecture — `--ref-type` + `--stale` + `prep_tldr` Incremental

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-22
**Sprint**: 10
**Status**: FINAL

---

## Executive Summary

Sprint 10 has three feature stories and one tech-debt item:

1. **S10-1: `--ref-type` CLI Unification** — `--ref-type <value>` as a third way to express a relationship query (alongside `-Vinh` and `--via inherits-from`). Minimal parser change; full help visibility.
2. **S10-2: `--stale` Cross-Stage Temporal** — Post-filter in executor: keep only relationship pairs where `result.mtime < anchor.mtime`. Requires `MatchRecord` to carry `mtime` and `anchor_mtime`.
3. **S10-3: `prep_tldr` Incremental** — Last-run timestamp at `.via/prep_tldr_last_run`; skip files unchanged since last run; add `--force` flag via argparse.
4. **TD-WATCH-1: PathFilter Extraction** — Extract `_should_include_dir` / `_should_include_file` from `FileDiscovery` into a public `PathFilter` class; `WatchService` uses `PathFilter` directly (no private method access).

---

## S10-1: `--ref-type` Implementation

### Design Decision: Pre-parse Detection (same as `--via`)

**Resolved: OQ-1** — `--ref-type <value>` is detected in `_find_relationship_split()` as a **third relationship specifier**, alongside `-Vinh` and `--via inherits-from`. It is NOT a match-stage modifier. The position is between the two `-mg` stages.

The three equivalent forms after Sprint 10:
```bash
via -mg 'Base' -tc -Vinh -mg '*' -tc                       # short flag alias
via -mg 'Base' -tc --via inherits-from -mg '*' -tc          # long value form (existing)
via -mg 'Base' -tc --ref-type inherits-from -mg '*' -tc     # NEW: explicit column form
```

### Parser Changes

**File**: `via/pipeline/parser.py`

**`_find_relationship_split()`** — add a third scan loop after the existing two:

```python
# Look for --ref-type <value>  (Sprint 10)
for i, arg in enumerate(args):
    if arg == '--ref-type' and i + 1 < len(args):
        next_arg = args[i + 1]
        if next_arg in value_map:
            rel_type = value_map[next_arg]
            subject_args = args[:i]
            object_args, invert = self._extract_invert_flag(args[i + 2:])
            return (subject_args, rel_type, object_args, invert)
        else:
            valid = ', '.join(sorted(value_map.keys()))
            raise PipelineParseError(
                f"Error: Unknown --ref-type '{next_arg}'.\n"
                f"Valid types: {valid}."
            )
```

**`_create_match_parser()`** — add `--ref-type` for **help visibility only**:

```python
# --ref-type: relationship specifier (listed in help; extracted pre-parse in _find_relationship_split)
valid_types = sorted(RelationshipType.get_value_map().keys())
parser.add_argument(
    '--ref-type',
    dest='ref_type',
    default=None,
    choices=valid_types,
    metavar='{' + ','.join(valid_types) + '}',
    help='Relationship type (alternative to -Vinh, -Vca, etc.): inherits-from, calls, imports, references, declares',
)
```

Adding it to `match_parser` with `choices` means:
- `via -mg '*' -tc --ref-type --help` shows valid choices inline
- `via -mg '*' -tc --ref-type foobar` (without a relationship context) gives a clear argparse error listing valid values
- `parsed_args.ref_type` is set but **ignored** by the executor (it was already consumed by `_find_relationship_split`)

This satisfies Smith's requirement: valid values listed in `--help`.

### No `flag_groups.py` Changes

`RELATIONSHIP_FLAGS` stays unchanged. `--ref-type` is not a `Flag` — it's a new category (relationship type specifier, not a named alias). Existing `-V<X>` flags remain as aliases.

### Validation Error Location

Errors thrown from `_find_relationship_split()` as `PipelineParseError`. This surfaces to the user as:
```
Error: Unknown --ref-type 'foobar'.
Valid types: calls, declares, imports, inherits-from, references.
```

### Tests

| Test | Location |
|------|----------|
| `--ref-type inherits-from` == `-Vinh` behavior | `tests/unit/test_pipeline_parser.py` |
| `--ref-type declares` == `-Vhas` behavior | integration test |
| All 5 valid types work | parametrized unit test |
| `--ref-type foobar` → `PipelineParseError` with valid types listed | unit test |
| `--ref-type` + `--newerthan` on subject stage | integration test |

---

## S10-2: `--stale` Implementation

### Design Decision: `anchor_mtime` on MatchRecord (Minimal Change)

**Resolved: OQ-2** — Do NOT introduce a new `RelationshipMatch` dataclass. Instead, add two fields to `MatchRecord`:

```python
@dataclass
class MatchRecord(ABC, ArgumentProvider, HelpProvider):
    ...
    # Temporal fields (set by DatabaseStore for mtime-aware queries)
    mtime: Optional[float] = None           # this symbol's file mtime
    anchor_mtime: Optional[float] = None    # anchor's mtime (set for relationship results only)
```

`anchor_mtime` is set by `DatabaseStore.query_relationships()` on each result record. The `--stale` post-filter in the executor is then:

```python
if args.stale:
    results = [r for r in results if r.anchor_mtime is not None and r.mtime is not None
               and r.mtime < r.anchor_mtime]
```

**Why not `RelationshipMatch`?** Introducing a new return type from `query_relationships()` would require changes in the executor's dispatch logic, the MCP layer, and potentially all renderers. Adding two nullable fields to `MatchRecord` is a clean additive change with no ripple effects.

### `MatchRecord` Changes

**File**: `via/core/match_record.py`

Add two fields to the `MatchRecord` base dataclass:
```python
mtime: Optional[float] = None           # file mtime at index time
anchor_mtime: Optional[float] = None    # anchor's mtime (relationship queries only)
```

These fields are non-rendering metadata — they don't appear in `__str__()` or any renderer output.

### `MatchRecordFactory` Changes

**File**: `via/core/match_record.py` — `MatchRecordFactory.create_from_row()`

```python
kwargs = {
    ...
    'mtime': row.get('mtime'),   # NEW — from symbols.mtime column
}
```

### `DatabaseStore.query_relationships()` Changes

When fetching relationship results, set `anchor_mtime` on each result record:

```python
# For each (anchor_symbol_id, result_symbol_id) pair found:
result_record.anchor_mtime = anchor_record.mtime  # or fetched separately
```

The SQL query must SELECT `mtime` from both anchor and result sides. This requires a JOIN or two separate lookups. Given that `query_relationships()` already fetches result symbols, the simplest approach is a single query that SELECTs `s_result.mtime AS result_mtime, s_anchor.mtime AS anchor_mtime`:

```sql
SELECT s_result.*, s_anchor.mtime AS anchor_mtime
FROM symbol_references sr
JOIN symbols s_result ON sr.to_symbol_id = s_result.id
JOIN symbols s_anchor ON sr.from_symbol_id = s_anchor.id
WHERE sr.reference_type = ?
  AND s_anchor.symbol_name GLOB ?
  ...
```

Then the factory sets both `mtime = row['mtime']` and `anchor_mtime = row['anchor_mtime']`.

### Parser: `--stale` Flag

**File**: `via/pipeline/parser.py` — `_create_match_parser()`

```python
parser.add_argument(
    '--stale',
    dest='stale',
    action='store_true',
    default=False,
    help='Filter relationship results to those older than their anchor (e.g. stale tests). '
         'Example: via -mg "*" -tc -Vinh -mg "test_*" -tf --stale',
)
```

`--stale` goes on the **object/result side** of the relationship query (parsed from `object_args`). The executor checks `object_parsed.stale` and sets `result_stale=True` on `RelationshipFilter`.

### `RelationshipFilter` Changes

**File**: `via/pipeline/relationship_filter.py`

```python
@dataclass
class RelationshipFilter:
    ...
    result_stale: bool = False   # NEW — filter: result.mtime < anchor.mtime
```

### Executor Changes

**File**: `via/pipeline/executor.py` — `_execute_relationship_query()`

```python
if rel.result_stale:
    results = [r for r in results
               if r.anchor_mtime is not None and r.mtime is not None
               and r.mtime < r.anchor_mtime]
```

And in `_parse_match_stage()`:
```python
parsed_args.relationship = RelationshipFilter(
    ...
    result_stale=getattr(object_parsed, 'stale', False),  # NEW
)
```

### Error: Missing mtime

If `--stale` is used but `result.mtime is None` or `anchor_mtime is None` for all results:
```
Error: --stale requires symbols.mtime — rebuild index with `via index --force`.
```
This check happens in the executor after fetching results. If ANY result has `None` mtime, raise this error.

### `--help` for `--stale`

Smith's requirement: include one-line semantic example. The `help=` string above includes this inline:
> "Filter relationship results to those older than their anchor (e.g. stale tests). Example: via -mg '*' -tc -Vinh -mg 'test_*' -tf --stale"

### Tests

| Test | Notes |
|------|-------|
| `result.mtime < anchor.mtime` → included | unit test with mocked mtimes |
| `result.mtime >= anchor.mtime` → excluded | unit test |
| `--stale` + `--newerthan` on anchor side | integration test |
| `None` mtime → error | unit test |
| `--stale` without relationship query → no-op (safe) | unit test |

---

## S10-3: `prep_tldr` Incremental Implementation

### Design Decision: last-run file location

**Resolved: OQ-3** — `.via/prep_tldr_last_run` (alongside the index DB). This is runtime state that belongs with the index; it should not live in `build/` (which is build output, not project state).

### Implementation Plan

**File**: `agents/tools/prep_tldr.py`

#### 1. Add `argparse` (replacing `sys.argv[1]` positional)

```python
import argparse
import time

def parse_args():
    parser = argparse.ArgumentParser(
        description='Prepare per-file TLDR data for Oracle sub-agents.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('root', nargs='?', default=None,
                        help='Project root directory (default: auto-detect from script location)')
    parser.add_argument('--force', '-f', action='store_true', default=False,
                        help='Regenerate all files, ignoring last-run timestamp')
    return parser.parse_args()
```

#### 2. Last-run timestamp read/write

```python
LAST_RUN_FILE = root / '.via' / 'prep_tldr_last_run'

def read_last_run(last_run_path: Path) -> Optional[float]:
    """Read last-run timestamp. Returns None if not present."""
    try:
        return float(last_run_path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None

def write_last_run(last_run_path: Path) -> None:
    """Write current time as last-run timestamp."""
    last_run_path.write_text(str(time.time()))
```

#### 3. Incremental file selection (using symbols.mtime from DB)

```python
def get_changed_files(conn, all_files, last_run: float) -> tuple[list, list]:
    """Return (changed_files, skipped_files) based on symbols.mtime."""
    changed, skipped = [], []
    for f in all_files:
        # Query mtime from DB for this file's symbols
        cur = conn.execute(
            "SELECT MAX(mtime) FROM symbols WHERE file_path = ?", (f.path,)
        )
        row = cur.fetchone()
        file_mtime = row[0] if row and row[0] is not None else 0.0
        if file_mtime > last_run:
            changed.append(f)
        else:
            skipped.append(f)
    return changed, skipped
```

Note: This queries `MAX(mtime)` per file (all symbols in a file share the same mtime, but MAX is safe). If a file has no symbols (no parseable content), its mtime won't be in the symbols table — treat as changed (reprocess to pick up any new content).

#### 4. Stale data file cleanup (carry through to incremental)

Already done on full run (existing code deletes all `build/tldr_prep/` files before processing). On incremental: only delete data files for sources that no longer exist:

```python
# On incremental: remove stale data files
existing_paths = {f.path for f in all_files}
for data_file in PREP_DIR.iterdir():
    if data_file.name in ('py_files.txt', 'md_files.txt'):
        continue
    # Reconstruct source path from data file name (reverse safe_name)
    # If source no longer in existing_paths, delete
    # ... (implementation detail for Neo)
```

#### 5. Output message

```python
if last_run is not None:
    last_run_dt = datetime.fromtimestamp(last_run).isoformat(timespec='seconds')
    print(f"Incremental mode: last run {last_run_dt}. Processing {len(changed)} changed files ({len(skipped)} skipped).")
else:
    print(f"Full mode: processing {len(all_files)} files.")
```

#### 6. Write last-run AFTER successful completion

`write_last_run(LAST_RUN_FILE)` called at the end of `main()`, after all files processed. If the script errors mid-run, the timestamp is not updated (next run will re-process).

### Smith's `time.time()` Correction

Cypher wrote `os.time()` in the user story — Python uses `time.time()`. The arch doc uses `time.time()` throughout. Fixed.

### Tests

| Test | Notes |
|------|-------|
| `read_last_run` returns None on missing file | unit test |
| `read_last_run` parses float correctly | unit test |
| `write_last_run` creates file with valid float | unit test |
| Unchanged file (mtime <= last_run) is skipped | integration test |
| Changed file (mtime > last_run) is reprocessed | integration test |
| `--force` ignores last_run, processes all | integration test |
| Stale data file (source deleted) is removed | integration test |

---

## TD-WATCH-1: PathFilter Extraction

### Current State

`WatchService` calls **private** methods of `FileDiscovery`:
- `self._discovery._should_include_dir(root, d)` — line 171
- `self._discovery._should_include_file(path)` — line 220

This is a coupling smell: `WatchService` bypasses `FileDiscovery`'s public interface.

### Target Design

Extract a `PathFilter` class that both `FileDiscovery` and `WatchService` use directly:

```python
# via/core/path_filter.py

class PathFilter:
    """Path inclusion/exclusion filter using gitignore spec and default excludes."""

    def __init__(self, root_dir: str, respect_gitignore: bool = True,
                 extra_patterns: Optional[List[str]] = None) -> None:
        self.root_dir = os.path.abspath(root_dir)
        self._spec = self._build_spec(respect_gitignore, extra_patterns or [])

    def should_include_dir(self, parent_path: str, dirname: str) -> bool:
        """Return True if directory should be walked."""
        dir_path = os.path.join(parent_path, dirname)
        rel_path = os.path.relpath(dir_path, self.root_dir)
        return not self._spec.match_file(rel_path + '/')

    def should_include_file(self, file_path: str) -> bool:
        """Return True if file should be indexed."""
        rel_path = os.path.relpath(file_path, self.root_dir)
        return not self._spec.match_file(rel_path)

    def _build_spec(self, respect_gitignore: bool, extra_patterns: List[str]) -> pathspec.PathSpec:
        # (same logic as FileDiscovery._build_gitignore_spec() today)
        ...
```

### Migration

**`FileDiscovery`**: Replace `_build_gitignore_spec()`, `_should_include_dir()`, `_should_include_file()` with delegation to `PathFilter`:

```python
class FileDiscovery:
    def __init__(self, root_dir, ...):
        ...
        self._filter = PathFilter(root_dir, respect_gitignore)
        # Keep self.gitignore_spec for backward compat? No — it was private.
        # Remove: self.gitignore_spec = self._build_gitignore_spec()

    # Keep as public API (no leading underscore)
    def should_include_dir(self, parent, dirname):
        return self._filter.should_include_dir(parent, dirname)

    def should_include_file(self, path):
        return self._filter.should_include_file(path)
```

**`WatchService`**: Replace `self._discovery._should_include_dir/file` with its own `PathFilter`:

```python
class WatchService:
    def __init__(self, ..., exclude_patterns=None, ...):
        ...
        extra = exclude_patterns or []
        self._filter = PathFilter(root_dir, extra_patterns=extra)
        # Remove self._discovery (used only for path filtering)
        # Remove self._extra_spec (merged into PathFilter)
```

### File Location

`via/core/path_filter.py` — new file. `FileDiscovery` stays in `via/core/discovery.py`.

### Behavior Invariant

All existing `FileDiscovery` tests must pass unchanged. `WatchService` filtering behavior is identical before and after.

### Tests

| Test | Notes |
|------|-------|
| `PathFilter.should_include_file` excludes `.pyc` | unit test |
| `PathFilter.should_include_file` respects `.gitignore` | unit test |
| `PathFilter.should_include_dir` excludes `.git/` | unit test |
| Extra patterns applied | unit test |
| `FileDiscovery` tests all green (no modification) | regression |
| `WatchService` path filtering identical pre/post | behavioral test |

---

## Implementation Ordering

```
Cycle 1: S10-1 (--ref-type)
  - via/pipeline/parser.py: _find_relationship_split + match_parser --ref-type
  - Tests: unit + integration

Cycle 2: S10-2 (--stale) + S10-3 (prep_tldr incremental)
  - S10-2: via/core/match_record.py + via/db/store.py + via/pipeline/relationship_filter.py + executor.py
  - S10-3: agents/tools/prep_tldr.py (argparse + timestamp logic)
  - Tests for both

Cycle 3: TD-WATCH-1 (PathFilter)
  - via/core/path_filter.py (new)
  - via/core/discovery.py (delegate to PathFilter)
  - via/services/watch.py (use PathFilter directly)
  - Tests: all existing + new
```

---

## Open Question Resolutions Summary

| OQ | Question | Decision |
|----|----------|---------|
| OQ-1 | `--ref-type` parser placement | Pre-parse detection in `_find_relationship_split()`, listed in `match_parser` help |
| OQ-2 | `MatchRecord.mtime` nullability | `Optional[float] = None` on base class; `anchor_mtime: Optional[float] = None` for stale |
| OQ-3 | `prep_tldr` last-run file location | `.via/prep_tldr_last_run` (runtime state, co-located with DB) |

---

## Handoff to Smith (Gate 2)

@Smith: Sprint 10 architecture is ready for Gate 2 review. Key UX decisions:

1. **S10-1**: `--ref-type <value>` positioned between `-mg` stages. Help lists all valid types via `choices`. Error message lists valid types.
2. **S10-2**: `--stale` on the result/object side of the relationship query. Help includes usage example. Error if index lacks mtime.
3. **S10-3**: `--force`/`-f` flag added via argparse. Clear incremental mode output message.
4. **TD-WATCH-1**: Transparent to end users — internal refactor only.

Full arch doc: `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md`
