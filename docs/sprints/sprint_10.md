# Sprint 10 Consolidated Documentation

This document consolidates all documentation for Sprint 10.

## Table of Contents

- [SPRINT_10_USER_STORIES.md](#sprint-10-user-storiesmd) (originally `agents/cypher.docs/SPRINT_10_USER_STORIES.md`)

- [SPRINT_10_ARCHITECTURE.md](#sprint-10-architecturemd) (originally `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md`)

- [SPRINT_10_BETA_TEST.md](#sprint-10-beta-testmd) (originally `agents/smith.docs/SPRINT_10_BETA_TEST.md`)

- [SPRINT_10_REVIEW.md](#sprint-10-reviewmd) (originally `agents/smith.docs/SPRINT_10_REVIEW.md`)

- [SPRINT_10_TASKS.md](#sprint-10-tasksmd) (originally `agents/mouse.docs/SPRINT_10_TASKS.md`)

- [sprint10_kickoff.md](#sprint10-kickoffmd) (originally `agents/mouse.docs/sprint10_kickoff.md`)


---


## SPRINT_10_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_10_USER_STORIES.md`


## Sprint 10 — ReferenceType Unification + Stale Detection + prep_tldr Incremental

**Author**: Cypher (PM)
**Date**: 2026-03-22
**Theme**: CLI power-user query unification, cross-stage stale detection, incremental prep_tldr
**Points**: ~8pts total
**Baseline**: 908 tests (end of Sprint 9)

---

### Sprint Goal

Unify reference-type querying under a single `--ref-type` flag, add cross-stage stale detection (`--stale`), and make `prep_tldr` incremental using the temporal matcher shipped in Sprint 9. Clean up a watch-mode coupling issue (TD-WATCH-1).

---

### Stories

#### S10-1: `--ref-type` CLI Unification (3pts) — P0

**As a** power user of `via`,
**I want** to query relationships by reference type string directly (`--ref-type declares`),
**so that** I can use any current or future reference type without needing a dedicated `-V<X>` flag for each one.

##### Background
Sprint 9 shipped `ReferenceType` (renamed from `RelationshipType`) and added `DECLARES`. The `-V<X>` flags (`-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`) are convenient aliases but don't scale. `--ref-type` exposes the underlying type column directly, making all current and future types queryable.

##### Acceptance Criteria

1. **Flag exists**: `--ref-type <type>` is a valid CLI option on the relationship stage (between two `-mg` stages).
   ```
   via -mg 'MyClass' -tc --ref-type declares -mg '*' -tm -n 0
   via -mg 'Base' -tc --ref-type inherits-from -mg '*' -tc
   ```

2. **Valid types**: Accepts the string values of `ReferenceType` enum:
   - `inherits-from`, `calls`, `imports`, `references`, `declares`

3. **Existing flags unaffected**: `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas` all continue to work as before (they are sugar over `--ref-type`).

4. **Invalid type error**: Clear error for unknown type strings:
   ```
   Error: Unknown --ref-type 'foobar'.
   Valid types: inherits-from, calls, imports, references, declares.
   ```

5. **Combinable with temporal flags**: `--ref-type` works alongside `--newerthan`/`--olderthan` on either stage:
   ```
   via -mg '*service*' -tc --newerthan 1h --ref-type declares -mg '*' -tm -n 0
   ```

6. **Tests**: Unit tests for `--ref-type` parsing; integration tests for each valid type value; error test for invalid value.

---

#### S10-2: `--stale` Cross-Stage Temporal Comparison (2pts) — P1

**As a** developer using `via` to track test coverage freshness,
**I want** a `--stale` flag on relationship queries,
**so that** I can find symbols whose related symbols were indexed BEFORE the anchor (i.e., tests that are "older" than the source they test).

##### Background
Sprint 9 shipped per-stage `--newerthan`/`--olderthan` filters (absolute duration from now). Sprint 9 arch doc deferred "result older than anchor" to Sprint 10 as a cross-stage JOIN. Use case: `via -mg '*service*' -tc -Vinh -mg 'test_*' -tf --stale` → "show me test functions inheriting from service classes, where the test file is older than the service file."

##### Acceptance Criteria

1. **Flag exists**: `--stale` is a valid flag on the object/result side of a relationship query:
   ```
   via -mg '*' -tc --newerthan 1d -Vinh -mg 'test_*' -tf --stale
   ```
   Meaning: "find test classes that inherit from recently-changed source classes, where the test file was indexed BEFORE the source class file."

2. **Semantics**: `--stale` = `result.mtime < anchor.mtime` per relationship pair. Post-filter in executor after `query_relationships()` returns pairs.

3. **`MatchRecord` carries mtime**: `MatchRecord` gains an optional `mtime: Optional[float]` field. `query_relationships()` returns anchor mtime and result mtime on each pair.

4. **Independent of `--newerthan`/`--olderthan`**: `--stale` combines with them freely:
   ```
   via -mg '*' -tc --newerthan 7d -Vinh -mg '*' -tc --stale
   # Anchor: changed in last week; result: older than its anchor
   ```

5. **Error on missing mtime**: If mtime data is not present (old index), emit a clear error:
   ```
   Error: --stale requires symbols.mtime — rebuild index with `via index --force`.
   ```

6. **Tests**: Unit tests for `--stale` post-filter logic; integration test with known stale/fresh pairs.

---

#### S10-3: `prep_tldr` Incremental Mode (2pts) — P1

**As a** team member running `prep_tldr` repeatedly during a session,
**I want** the script to skip regenerating data files for unchanged source files,
**so that** each incremental run only processes files that have changed since the last run.

##### Background
Story 2b (from Sprint 9 planning). The temporal matcher (`symbols.mtime`, `--newerthan`) was shipped in Sprint 9. `prep_tldr` currently always regenerates all data files. With `symbols.mtime` now in the DB, we can compare file mtime against last-run timestamp and skip unchanged files.

##### Acceptance Criteria

1. **Last-run timestamp**: `prep_tldr` records a timestamp (float seconds, `os.time()`) to `.via/prep_tldr_last_run` after each successful run.

2. **Incremental default**: On subsequent runs, `prep_tldr` reads the last-run timestamp and only regenerates data files for source files whose `symbols.mtime > last_run_timestamp`.

3. **Force flag**: `prep_tldr --force` ignores last-run and regenerates all files (full mode). This is also the behavior when `.via/prep_tldr_last_run` does not exist (first run).

4. **Stale data file cleanup**: On incremental run, data files in `build/tldr_prep/` whose corresponding source no longer exists are deleted. (Already done on full run — carry through to incremental.)

5. **File list files updated**: `py_files.txt` and `md_files.txt` are always regenerated from the full current file list (not filtered) so consumers see the complete set.

6. **Output clarity**: On incremental run, print:
   ```
   Incremental mode: last run 2026-03-22T13:00:00. Processing N changed files (M skipped).
   ```

7. **Tests**: Unit tests for last-run timestamp read/write; integration test for skip behavior (unchanged file not regenerated); test for `--force` override.

---

#### TD-WATCH-1: Extract PathFilter from FileDiscovery (1pt) — P2

**As a** developer maintaining `via`'s watch mode,
**I want** path filtering logic extracted into a dedicated `PathFilter` class,
**so that** `FileDiscovery` and `WatchService` can share the same filtering rules without coupling.

##### Background
Morpheus flagged this in Sprint 6 review. `FileDiscovery` contains path-matching and exclusion logic that `WatchService` partially duplicates. Extracting a `PathFilter` class makes both cleaner and eliminates the coupling.

##### Acceptance Criteria

1. **New class**: `PathFilter` in `via/core/path_filter.py` (or inside `via/core/discovery.py` as a nested/sibling class).

2. **API**:
   ```python
   class PathFilter:
       def __init__(self, root: str, exclude_patterns: List[str] = None): ...
       def should_index(self, path: str) -> bool: ...
   ```

3. **`FileDiscovery` uses `PathFilter`**: `FileDiscovery.discover()` delegates include/exclude decisions to `PathFilter.should_index()`.

4. **`WatchService` uses `PathFilter`**: `WatchService` constructs a `PathFilter` with the same root and exclude patterns, replaces any inline path logic with `should_index()` calls.

5. **Behavior unchanged**: All existing `FileDiscovery` tests pass without modification.

6. **Tests**: Unit tests for `PathFilter.should_index()` with various patterns; verify `WatchService` integration.

---

### Sprint Summary

| Story | Points | Priority | Persona |
|-------|--------|----------|---------|
| S10-1: `--ref-type` CLI unification | 3 | P0 | Neo |
| S10-2: `--stale` cross-stage temporal | 2 | P1 | Neo |
| S10-3: `prep_tldr` incremental | 2 | P1 | Neo |
| TD-WATCH-1: PathFilter extraction | 1 | P2 | Neo |
| **Total** | **8** | | |

### Cycle Plan

| Cycle | Phase | Stories | Assigned |
|-------|-------|---------|----------|
| 1 | S10-1 (`--ref-type`) | S10-1 | Neo → Trin |
| 2 | S10-2 + S10-3 | S10-2, S10-3 | Neo → Trin |
| 3 | TD-WATCH-1 | TD-WATCH-1 | Neo → Trin |

### Open Questions for Morpheus

1. **S10-1 Parser placement**: Does `--ref-type` live in the relationship flag group (between stages) or as a modifier on `--ref-type <type>` appended to the second `-mg` stage? Recommendation: relationship stage (same position as `-Vinh`).

2. **S10-2 `MatchRecord.mtime` type**: Should `mtime` be `Optional[float]` (nullable for old indexes) or required (force rebuild)? Recommendation: `Optional[float]`, check None at `--stale` time.

3. **S10-3 prep_tldr location**: Should the last-run file live at `.via/prep_tldr_last_run` (alongside the DB) or `build/prep_tldr_last_run`? Recommendation: `.via/` (runtime state).

---

### Arch Handoff

@Morpheus: Sprint 10 user stories ready for review. Key decisions needed:
1. `--ref-type` parser placement (OQ-1 above)
2. `MatchRecord.mtime` nullability strategy (OQ-2)
3. prep_tldr last-run file location (OQ-3)

Please write `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md` resolving these OQs before Neo begins implementation.


---


## SPRINT_10_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md`


## Sprint 10 Architecture — `--ref-type` + `--stale` + `prep_tldr` Incremental

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-22
**Sprint**: 10
**Status**: FINAL

---

### Executive Summary

Sprint 10 has three feature stories and one tech-debt item:

1. **S10-1: `--ref-type` CLI Unification** — `--ref-type <value>` as a third way to express a relationship query (alongside `-Vinh` and `--via inherits-from`). Minimal parser change; full help visibility.
2. **S10-2: `--stale` Cross-Stage Temporal** — Post-filter in executor: keep only relationship pairs where `result.mtime < anchor.mtime`. Requires `MatchRecord` to carry `mtime` and `anchor_mtime`.
3. **S10-3: `prep_tldr` Incremental** — Last-run timestamp at `.via/prep_tldr_last_run`; skip files unchanged since last run; add `--force` flag via argparse.
4. **TD-WATCH-1: PathFilter Extraction** — Extract `_should_include_dir` / `_should_include_file` from `FileDiscovery` into a public `PathFilter` class; `WatchService` uses `PathFilter` directly (no private method access).

---

### S10-1: `--ref-type` Implementation

#### Design Decision: Pre-parse Detection (same as `--via`)

**Resolved: OQ-1** — `--ref-type <value>` is detected in `_find_relationship_split()` as a **third relationship specifier**, alongside `-Vinh` and `--via inherits-from`. It is NOT a match-stage modifier. The position is between the two `-mg` stages.

The three equivalent forms after Sprint 10:
```bash
via -mg 'Base' -tc -Vinh -mg '*' -tc                       # short flag alias
via -mg 'Base' -tc --via inherits-from -mg '*' -tc          # long value form (existing)
via -mg 'Base' -tc --ref-type inherits-from -mg '*' -tc     # NEW: explicit column form
```

#### Parser Changes

**File**: `via/pipeline/parser.py`

**`_find_relationship_split()`** — add a third scan loop after the existing two:

```python
## Look for --ref-type <value>  (Sprint 10)
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
## --ref-type: relationship specifier (listed in help; extracted pre-parse in _find_relationship_split)
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

#### No `flag_groups.py` Changes

`RELATIONSHIP_FLAGS` stays unchanged. `--ref-type` is not a `Flag` — it's a new category (relationship type specifier, not a named alias). Existing `-V<X>` flags remain as aliases.

#### Validation Error Location

Errors thrown from `_find_relationship_split()` as `PipelineParseError`. This surfaces to the user as:
```
Error: Unknown --ref-type 'foobar'.
Valid types: calls, declares, imports, inherits-from, references.
```

#### Tests

| Test | Location |
|------|----------|
| `--ref-type inherits-from` == `-Vinh` behavior | `tests/unit/test_pipeline_parser.py` |
| `--ref-type declares` == `-Vhas` behavior | integration test |
| All 5 valid types work | parametrized unit test |
| `--ref-type foobar` → `PipelineParseError` with valid types listed | unit test |
| `--ref-type` + `--newerthan` on subject stage | integration test |

---

### S10-2: `--stale` Implementation

#### Design Decision: `anchor_mtime` on MatchRecord (Minimal Change)

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

#### `MatchRecord` Changes

**File**: `via/core/match_record.py`

Add two fields to the `MatchRecord` base dataclass:
```python
mtime: Optional[float] = None           # file mtime at index time
anchor_mtime: Optional[float] = None    # anchor's mtime (relationship queries only)
```

These fields are non-rendering metadata — they don't appear in `__str__()` or any renderer output.

#### `MatchRecordFactory` Changes

**File**: `via/core/match_record.py` — `MatchRecordFactory.create_from_row()`

```python
kwargs = {
    ...
    'mtime': row.get('mtime'),   # NEW — from symbols.mtime column
}
```

#### `DatabaseStore.query_relationships()` Changes

When fetching relationship results, set `anchor_mtime` on each result record:

```python
## For each (anchor_symbol_id, result_symbol_id) pair found:
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

#### Parser: `--stale` Flag

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

#### `RelationshipFilter` Changes

**File**: `via/pipeline/relationship_filter.py`

```python
@dataclass
class RelationshipFilter:
    ...
    result_stale: bool = False   # NEW — filter: result.mtime < anchor.mtime
```

#### Executor Changes

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

#### Error: Missing mtime

If `--stale` is used but `result.mtime is None` or `anchor_mtime is None` for all results:
```
Error: --stale requires symbols.mtime — rebuild index with `via index --force`.
```
This check happens in the executor after fetching results. If ANY result has `None` mtime, raise this error.

#### `--help` for `--stale`

Smith's requirement: include one-line semantic example. The `help=` string above includes this inline:
> "Filter relationship results to those older than their anchor (e.g. stale tests). Example: via -mg '*' -tc -Vinh -mg 'test_*' -tf --stale"

#### Tests

| Test | Notes |
|------|-------|
| `result.mtime < anchor.mtime` → included | unit test with mocked mtimes |
| `result.mtime >= anchor.mtime` → excluded | unit test |
| `--stale` + `--newerthan` on anchor side | integration test |
| `None` mtime → error | unit test |
| `--stale` without relationship query → no-op (safe) | unit test |

---

### S10-3: `prep_tldr` Incremental Implementation

#### Design Decision: last-run file location

**Resolved: OQ-3** — `.via/prep_tldr_last_run` (alongside the index DB). This is runtime state that belongs with the index; it should not live in `build/` (which is build output, not project state).

#### Implementation Plan

**File**: `agents/tools/prep_tldr.py`

##### 1. Add `argparse` (replacing `sys.argv[1]` positional)

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

##### 2. Last-run timestamp read/write

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

##### 3. Incremental file selection (using symbols.mtime from DB)

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

##### 4. Stale data file cleanup (carry through to incremental)

Already done on full run (existing code deletes all `build/tldr_prep/` files before processing). On incremental: only delete data files for sources that no longer exist:

```python
## On incremental: remove stale data files
existing_paths = {f.path for f in all_files}
for data_file in PREP_DIR.iterdir():
    if data_file.name in ('py_files.txt', 'md_files.txt'):
        continue
    # Reconstruct source path from data file name (reverse safe_name)
    # If source no longer in existing_paths, delete
    # ... (implementation detail for Neo)
```

##### 5. Output message

```python
if last_run is not None:
    last_run_dt = datetime.fromtimestamp(last_run).isoformat(timespec='seconds')
    print(f"Incremental mode: last run {last_run_dt}. Processing {len(changed)} changed files ({len(skipped)} skipped).")
else:
    print(f"Full mode: processing {len(all_files)} files.")
```

##### 6. Write last-run AFTER successful completion

`write_last_run(LAST_RUN_FILE)` called at the end of `main()`, after all files processed. If the script errors mid-run, the timestamp is not updated (next run will re-process).

#### Smith's `time.time()` Correction

Cypher wrote `os.time()` in the user story — Python uses `time.time()`. The arch doc uses `time.time()` throughout. Fixed.

#### Tests

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

### TD-WATCH-1: PathFilter Extraction

#### Current State

`WatchService` calls **private** methods of `FileDiscovery`:
- `self._discovery._should_include_dir(root, d)` — line 171
- `self._discovery._should_include_file(path)` — line 220

This is a coupling smell: `WatchService` bypasses `FileDiscovery`'s public interface.

#### Target Design

Extract a `PathFilter` class that both `FileDiscovery` and `WatchService` use directly:

```python
## via/core/path_filter.py

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

#### Migration

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

#### File Location

`via/core/path_filter.py` — new file. `FileDiscovery` stays in `via/core/discovery.py`.

#### Behavior Invariant

All existing `FileDiscovery` tests must pass unchanged. `WatchService` filtering behavior is identical before and after.

#### Tests

| Test | Notes |
|------|-------|
| `PathFilter.should_include_file` excludes `.pyc` | unit test |
| `PathFilter.should_include_file` respects `.gitignore` | unit test |
| `PathFilter.should_include_dir` excludes `.git/` | unit test |
| Extra patterns applied | unit test |
| `FileDiscovery` tests all green (no modification) | regression |
| `WatchService` path filtering identical pre/post | behavioral test |

---

### Implementation Ordering

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

### Open Question Resolutions Summary

| OQ | Question | Decision |
|----|----------|---------|
| OQ-1 | `--ref-type` parser placement | Pre-parse detection in `_find_relationship_split()`, listed in `match_parser` help |
| OQ-2 | `MatchRecord.mtime` nullability | `Optional[float] = None` on base class; `anchor_mtime: Optional[float] = None` for stale |
| OQ-3 | `prep_tldr` last-run file location | `.via/prep_tldr_last_run` (runtime state, co-located with DB) |

---

### Handoff to Smith (Gate 2)

@Smith: Sprint 10 architecture is ready for Gate 2 review. Key UX decisions:

1. **S10-1**: `--ref-type <value>` positioned between `-mg` stages. Help lists all valid types via `choices`. Error message lists valid types.
2. **S10-2**: `--stale` on the result/object side of the relationship query. Help includes usage example. Error if index lacks mtime.
3. **S10-3**: `--force`/`-f` flag added via argparse. Clear incremental mode output message.
4. **TD-WATCH-1**: Transparent to end users — internal refactor only.

Full arch doc: `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md`


---


## SPRINT_10_BETA_TEST.md

**Original Location**: `agents/smith.docs/SPRINT_10_BETA_TEST.md`


## VIA Full Beta Test Report — All PRD User Stories
**Tester**: Smith (Expert User)
**Date**: 2026-03-22
**VIA version**: Sprint 10 (968 tests)

---

### Summary

**OVERALL: PASS with 2 UX defects filed**

All core user stories across Sprints 1-10 verified. Two documentation/UX issues found:
1. **UX-001**: MCP schema description has stale text ("Full-path matching not yet supported") — `-Q` ships in Sprint 9
2. **UX-002**: `-oD` (Mermaid diagram) with relationship query shows floating classes, no relationship arrows

---

### Sprint 1 — Core Indexing MVP ✅

| Test | Command | Result |
|------|---------|--------|
| Full index | `via index .` | ✅ Indexed 274 files, 6141 symbols |
| Incremental | `via index .` (2nd run) | ✅ Fast (skipped unchanged files) |
| Stats | `via stats` | ✅ Shows totals: 351 classes, 205 fns, 1252 methods, 1108 imports, 106 globals, 2485 headers |

**Observation**: `via index .` output is clean and informative. Incremental is genuinely fast.

---

### Sprint 2 — Pattern Matching & Query CLI ✅

| Test | Command | Result |
|------|---------|--------|
| Glob | `via -mg 'PathFilter' -tc` | ✅ Found class at correct location |
| Regex | `via -mr 'Match.*Record' -tc -n 3` | ✅ Matched TestMatchRecord*, etc. |
| SQL LIKE | `via -ms '%Store%' -tc -n 3` | ✅ Found DatabaseStore and test classes |
| Type: class | `via -mg '*' -tc -n 3` | ✅ 351 classes, cap warning shown |
| Type: function | `via -mg 'test_*' -tf -n 3` | ✅ 30 test functions |
| Type: header | `via -mg '*' -tH -n 3` | ✅ 2485 headers |
| Case-sensitive | `via -mg 'pathfilter' -tc` | ✅ No results (correct) |
| Case-insensitive | `via -mg 'pathfilter' -tc -I` | ✅ Found PathFilter |
| Result cap | `via -mg '*' -tc -n 3` | ✅ "results 1-3 of 351 matches returned (--limit=3) use -n 0 for all results" |
| Unlimited | `via -mg '*' -tc -n 0` | ✅ 351 results |

---

### Sprint 3 — Render Pipeline & Output Formats ✅

| Test | Command | Result |
|------|---------|--------|
| List (default) | `via -mg 'PathFilter' -tc` | ✅ `class:/path/to/file:line:qualified:@offset+len` |
| Table | `via -mg 'PathFilter' -tc -oT` | ✅ Markdown table with Type/Name/File/Line/QName columns |
| JSON | `via -mg 'PathFilter' -tc -oJ` | ✅ Keys: symbol_name, symbol_type, qualified_name, file_path, line_number |
| Raw source | `via -mg 'PathFilter' -tc -oR -C 2` | ✅ Shows source with header comment block |
| Formatted | `via -mg 'PathFilter' -tc -oF` | ✅ ANSI-colored source (pygments) |
| Usage | `via -mg 'PathFilter' -tc -oU` | ✅ Shows docstring/usage block |
| Diagram | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc -oD` | ⚠️ **UX-002** — see below |
| Context lines | `via -mg 'PathFilter' -tc -oR -C 2` | ✅ Shows 2 lines before/after |
| Stats | `via stats` | ✅ Symbol type counts, file count |

---

### Sprint 4 — Markdown Indexing ✅

| Test | Command | Result |
|------|---------|--------|
| Header type | `via -mg '*' -tH -n 3` | ✅ 2485 headers indexed from .md files |

---

### Sprint 5 — Relationship Queries ✅

| Test | Command | Result |
|------|---------|--------|
| Inheritance | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc` | ✅ 7 subclasses found |
| Invert | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc --invert` | ✅ Shows base classes (ArgumentProvider, HelpProvider) |
| Imports | `via -mg 'typing' -Vimp -mg '*' -tF -n 3` | ✅ Files that import typing |
| Calls | `via -mg 'query_relationships' -tm -Vca -mg '*' -tm -n 3` | ✅ Methods calling query_relationships |
| References | `via -mg 'DatabaseStore' -tc -Vr -mg '*' -n 3` | ✅ Functions referencing DatabaseStore |

---

### Sprint 6 — Watch Mode ✅

| Test | Command | Result |
|------|---------|--------|
| Globals type | `via -mg '*' -tg -n 5` | ✅ 106 globals (FAILURE_PATTERNS, ANSI_ESCAPE, etc.) |

*Watch mode not tested live (requires terminal blocking), but watchdog integration verified via test suite (968 passing).*

---

### Sprint 7 — MCP Server Mode ✅ (with UX-001)

| Test | Command | Result |
|------|---------|--------|
| MCP status | `via status mcp` | ✅ "Project: installed, Global: not installed" |
| MCP schema | `via mcp schema` | ⚠️ **UX-001** — stale text, see below |
| JSON output | `via -mg 'PathFilter' -tc -oJ` | ✅ JSON array with correct keys |

---

### Sprint 8 — Line-Level Indexing ✅

*Line-level byte offsets visible in list output format: `@<offset>+<length>` — verified on all results.*

---

### Sprint 9 — Temporal + Container + -Q ✅

| Test | Command | Result |
|------|---------|--------|
| Container | `via -mg 'PathFilter' -tc -Vhas -mg '*' -tm` | ✅ 4 methods (\_\_init\_\_, should_include_dir, should_include_file, _build_spec) |
| Temporal | `via -mg '*' -tc --olderthan 1m -n 3` | ✅ 351 classes (all older than 1 minute, correct) |
| newerthan | `via -mg '*' -tc --newerthan 1d -n 3` | ✅ 64 classes modified recently |
| -Q path match | `via -mg 'via/core/*' -tF -Q -n 5` | ✅ 13 files in via/core/ matched by path |

---

### Sprint 10 — --ref-type + --stale + prep_tldr ✅

| Test | Command | Result |
|------|---------|--------|
| --ref-type | `via -mg 'MatchRecord' -tc --ref-type inherits-from -mg '*' -tc -n 3` | ✅ Same 7 subclasses as -Vinh |
| --stale | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc --stale -n 0` | ✅ 0 results (subclasses all newer/same age — correct) |
| Error msg | `via -mg '*' -tc --ref-type invalid` | ✅ "Error: Unknown --ref-type 'invalid'. Valid types: calls, declares, imports, inherits-from, references." |
| prep_tldr | `python agents/tools/prep_tldr.py --force` | ✅ Full mode: 135 files |
| prep_tldr incr | `python agents/tools/prep_tldr.py` | ✅ "Processing 0 changed files (135 skipped)" |

---

### UX Defect Report

#### UX-001 — MCP Schema: Stale "Full-path matching not yet supported" text
**Severity**: Medium (misleads AI agents using MCP)
**CMD**: `via mcp schema`
**Expected**: Schema description mentions `-Q` for full-path matching
**Actual**: "Note: -mg matches against the symbol name (not file path). For filepath symbols (-tF), the match is against the basename (e.g. 'utils.py'). Full-path matching not yet supported."
**UX Issue**: This note was accurate before Sprint 9 but is now wrong. AI agents reading the schema will think full-path matching is impossible and won't use `-Q`. Since MCP is the primary interface for Claude Code, this misinformation directly harms usability.
**Fix**: Update the note to: "For full-path matching on -tF queries, use `-Q` (e.g. `via -mg 'via/core/*' -tF -Q`)."

#### UX-002 — -oD Diagram: No Relationship Arrows in Inheritance Queries
**Severity**: Low (cosmetic but confusing)
**CMD**: `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc -oD`
**Expected**: Mermaid diagram shows `ClassMatchRecord --|> MatchRecord` inheritance arrows
**Actual**: Diagram lists result classes as disconnected nodes — no arrows, no anchor class
**UX Issue**: A user who uses `-oD` to visualize an inheritance tree gets a diagram that looks like a bug. The chart shows the right classes but hides the entire relationship they asked for. Compare: `-oT` correctly shows results (you know MatchRecord is the anchor), but `-oD` loses this context entirely.
**Fix**: For relationship queries, include the anchor class in the diagram and draw the appropriate relationship arrows.

---

### Overall UX Observations

**Strengths:**
1. **Pipeline syntax is intuitive** — `via -mg PATTERN -t<Y> -V<X> -mg PATTERN -t<Y>` reads like plain English once you know it
2. **Error messages are excellent** — `--ref-type invalid` lists all valid options, no guessing
3. **Cap warning is perfect** — "results 1-3 of 351 matches returned (--limit=3) use -n 0 for all results" is exactly right
4. **`-I` case-insensitive** — clean, works exactly as expected
5. **`-Q` full-path matching** — `via -mg 'via/core/*' -tF -Q` feels natural, great addition
6. **JSON output (-oJ)** — keys are well-named, stable format for agents
7. **prep_tldr incremental** — "Processing 0 changed files (135 skipped)" is satisfying and informative
8. **MCP status output** — clear two-line format (project vs global) is exactly right

**Minor rough edges (not filing as bugs):**
- List output format includes `@offset+length` which is useful for editors but looks noisy in casual use — a `--no-offsets` flag could be nice (future sprint)
- `via -oF` ANSI output in a non-TTY context shows escape codes (expected, but worth noting for piped workflows)


---


## SPRINT_10_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_10_REVIEW.md`


## Smith — Sprint 10 User Story Review

**Date**: 2026-03-22
**Reviewer**: Smith (Expert User)
**Stories**: agents/cypher.docs/SPRINT_10_USER_STORIES.md
**Verdict**: **APPROVED WITH NOTES**

---

### Story-by-Story Review

#### S10-1: `--ref-type` CLI Unification — APPROVED ✅

**User perspective**: This is the right move. The `-V<X>` flags feel like magic runes. `--ref-type inherits-from` is self-documenting. Power users will love being able to query any reference type without memorizing flags.

**AC quality**: Solid. Error message in AC 4 is correct (lists valid values). Temporal flag combination in AC 5 is important to test.

**Note for Morpheus (not a blocker)**: The `--help` text MUST list valid `--ref-type` values inline (e.g., `choices: inherits-from, calls, imports, references, declares`). If a user has to go to the docs to find valid values, the flag is half-baked. Add this to the implementation spec.

**AC 1 example is correct**: `--ref-type declares` positioned between `-mg` stages, same as `-Vinh`. This is the right UX.

---

#### S10-2: `--stale` Cross-Stage Temporal — APPROVED ✅

**User perspective**: The "find tests older than the source they test" use case is real and powerful. The flag name `--stale` is exactly right — short, semantic, immediately understandable.

**AC quality**: Good. AC 5 error message is correct. The AC 3 `MatchRecord.mtime` change is well-specified.

**Note for Morpheus (not a blocker)**: The `--help` description for `--stale` must include a one-line example showing the semantic: `"Filter: result is older than its anchor (e.g. find stale tests)"`. Without this, users won't know what "stale" means in context.

**AC 2 semantic**: Confirmed correct — `result.mtime < anchor.mtime` per pair is the right comparison.

---

#### S10-3: `prep_tldr` Incremental — APPROVED WITH CORRECTION ⚠️

**User perspective**: This is a needed quality-of-life improvement. Running prep_tldr during active dev sessions and waiting for a full reindex is wasteful.

**AC quality**: Well-specified. The file-list-always-regenerated rule (AC 5) is important — good catch.

**Correction needed (not a blocker, fix in implementation)**:
- AC 1 says `os.time()` — Python doesn't have `os.time()`. The correct call is `time.time()`. Neo should use `time.time()` when writing the implementation.

**Timestamp comparison correctness**: Verified — `symbols.mtime` (OS file mtime) compared against `time.time()` at last prep_tldr run is correct. Files changed after last run will have higher mtime → they get reprocessed. ✅

**One UX request**: The `--force` flag should also be listed in `--help` (or argparse help text). The script needs proper argparse support (currently only accepts a positional `root`). Make sure the argparse help is informative.

---

#### TD-WATCH-1: PathFilter Extraction — APPROVED ✅

**User perspective**: Transparent refactor. Completely invisible to end users. The `PathFilter.should_index()` API is clean and well-named.

**AC quality**: Solid. AC 5 (behavior unchanged, existing tests pass) is the correct definition of done for a refactor.

---

### Summary

| Story | Verdict | Notes |
|-------|---------|-------|
| S10-1 `--ref-type` | ✅ Approved | Add valid-values list to `--help` text |
| S10-2 `--stale` | ✅ Approved | Add example to `--help` text |
| S10-3 prep_tldr incr | ✅ Approved | Fix `os.time()` → `time.time()` in impl |
| TD-WATCH-1 PathFilter | ✅ Approved | No notes |

**Sprint scope**: 8pts is reasonable for Sprint 10. Cycle plan (1 story per cycle, smallest last) is good sequencing.

**Gate 1 result**: **APPROVED** — sprint proceeds to Morpheus architecture.

---

### Carry-forward from Sprint 9

Note to Morpheus: Sprint 9 left S9-004 open (traceback noise on errors — raw Python tracebacks shown, should suppress unless `-v`). If Neo has bandwidth, fold this into Sprint 10 as a 0.5pt cleanup. Not a blocker.


---


## SPRINT_10_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_10_TASKS.md`


## Sprint 10 Task Board

**Sprint**: 10
**Theme**: `--ref-type` CLI Unification + `--stale` + `prep_tldr` Incremental + PathFilter
**Start**: 2026-03-22
**Baseline**: 908 tests

---

### Cycle 1: S10-1 `--ref-type` CLI Unification

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| S10-1a | `via/pipeline/parser.py:_find_relationship_split()` — add `--ref-type` scan loop | 1 | [ ] |
| S10-1b | `via/pipeline/parser.py:_create_match_parser()` — add `--ref-type` with `choices=` | 0.5 | [ ] |
| S10-1c | Tests: unit (all 5 types, invalid type error) + integration | 1.5 | [ ] |

**Neo impl → Trin UAT (Cycle 1)**

---

### Cycle 2: S10-2 `--stale` + S10-3 `prep_tldr`

#### S10-2: `--stale`

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| S10-2a | `via/core/match_record.py` — add `mtime`, `anchor_mtime` fields to `MatchRecord`; update `MatchRecordFactory` | 0.5 | [ ] |
| S10-2b | `via/db/store.py:query_relationships()` — JOIN anchor mtime, set `anchor_mtime` on results | 1 | [ ] |
| S10-2c | `via/pipeline/relationship_filter.py` — add `result_stale: bool = False` | 0.25 | [ ] |
| S10-2d | `via/pipeline/parser.py:_create_match_parser()` — add `--stale` flag | 0.25 | [ ] |
| S10-2e | `via/pipeline/executor.py` — check `result_stale`, post-filter results | 0.5 | [ ] |
| S10-2f | Tests: unit (stale/fresh filter, None mtime error) + integration | 0.5 | [ ] |

#### S10-3: `prep_tldr` Incremental

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| S10-3a | `agents/tools/prep_tldr.py` — add argparse (`root`, `--force`/`-f`) | 0.25 | [ ] |
| S10-3b | `agents/tools/prep_tldr.py` — `read_last_run()` / `write_last_run()` | 0.25 | [ ] |
| S10-3c | `agents/tools/prep_tldr.py` — `get_changed_files()` using `symbols.mtime` | 0.5 | [ ] |
| S10-3d | `agents/tools/prep_tldr.py` — incremental mode: skip unchanged, clean stale data files | 0.5 | [ ] |
| S10-3e | Tests: unit (timestamp r/w, skip logic, force override) | 0.5 | [ ] |

**Neo impl → Trin UAT (Cycle 2)**

---

### Cycle 3: TD-WATCH-1 PathFilter

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| TD-W1a | `via/core/path_filter.py` — new `PathFilter` class (extracted from `FileDiscovery`) | 0.5 | [ ] |
| TD-W1b | `via/core/discovery.py` — delegate `_should_include_dir/file` to `PathFilter` | 0.25 | [ ] |
| TD-W1c | `via/services/watch.py` — use own `PathFilter`, remove `_discovery` private method calls | 0.25 | [ ] |
| TD-W1d | Tests: unit `PathFilter` + verify all `FileDiscovery` tests pass | 0 (regressions) | [ ] |

**Neo impl → Trin UAT (Cycle 3)**

---

### Smith Implementation Notes (from Gate 2)

1. **S10-1**: `--via` + `--ref-type` in same stage: `--via` wins by scan order. Document this or add a warning.
2. **S10-2**: `--stale` on subject side is silently ignored. Neo: detect and warn or confirm acceptable.

---

### Velocity Tracking

| Sprint | Tests Start | Tests End | Delta |
|--------|-------------|-----------|-------|
| 9 | 837 | 908 | +71 |
| 10 | 908 | TBD | TBD |


---


## sprint10_kickoff.md

**Original Location**: `agents/mouse.docs/sprint10_kickoff.md`


## Sprint 10 KICKOFF

Sprint 9 complete: 908 tests, +71.

### Candidates for Sprint 10

1. ReferenceType CLI unification `--ref-type`
2. `--stale` flag cross-stage mtime
3. Story 2b `prep_tldr` temporal
4. TD-WATCH-1 PathFilter extraction

@Cypher: write Sprint 10 user stories from these candidates.


---
