# Sprint 10 — ReferenceType Unification + Stale Detection + prep_tldr Incremental

**Author**: Cypher (PM)
**Date**: 2026-03-22
**Theme**: CLI power-user query unification, cross-stage stale detection, incremental prep_tldr
**Points**: ~8pts total
**Baseline**: 908 tests (end of Sprint 9)

---

## Sprint Goal

Unify reference-type querying under a single `--ref-type` flag, add cross-stage stale detection (`--stale`), and make `prep_tldr` incremental using the temporal matcher shipped in Sprint 9. Clean up a watch-mode coupling issue (TD-WATCH-1).

---

## Stories

### S10-1: `--ref-type` CLI Unification (3pts) — P0

**As a** power user of `via`,
**I want** to query relationships by reference type string directly (`--ref-type declares`),
**so that** I can use any current or future reference type without needing a dedicated `-V<X>` flag for each one.

#### Background
Sprint 9 shipped `ReferenceType` (renamed from `RelationshipType`) and added `DECLARES`. The `-V<X>` flags (`-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`) are convenient aliases but don't scale. `--ref-type` exposes the underlying type column directly, making all current and future types queryable.

#### Acceptance Criteria

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

### S10-2: `--stale` Cross-Stage Temporal Comparison (2pts) — P1

**As a** developer using `via` to track test coverage freshness,
**I want** a `--stale` flag on relationship queries,
**so that** I can find symbols whose related symbols were indexed BEFORE the anchor (i.e., tests that are "older" than the source they test).

#### Background
Sprint 9 shipped per-stage `--newerthan`/`--olderthan` filters (absolute duration from now). Sprint 9 arch doc deferred "result older than anchor" to Sprint 10 as a cross-stage JOIN. Use case: `via -mg '*service*' -tc -Vinh -mg 'test_*' -tf --stale` → "show me test functions inheriting from service classes, where the test file is older than the service file."

#### Acceptance Criteria

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

### S10-3: `prep_tldr` Incremental Mode (2pts) — P1

**As a** team member running `prep_tldr` repeatedly during a session,
**I want** the script to skip regenerating data files for unchanged source files,
**so that** each incremental run only processes files that have changed since the last run.

#### Background
Story 2b (from Sprint 9 planning). The temporal matcher (`symbols.mtime`, `--newerthan`) was shipped in Sprint 9. `prep_tldr` currently always regenerates all data files. With `symbols.mtime` now in the DB, we can compare file mtime against last-run timestamp and skip unchanged files.

#### Acceptance Criteria

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

### TD-WATCH-1: Extract PathFilter from FileDiscovery (1pt) — P2

**As a** developer maintaining `via`'s watch mode,
**I want** path filtering logic extracted into a dedicated `PathFilter` class,
**so that** `FileDiscovery` and `WatchService` can share the same filtering rules without coupling.

#### Background
Morpheus flagged this in Sprint 6 review. `FileDiscovery` contains path-matching and exclusion logic that `WatchService` partially duplicates. Extracting a `PathFilter` class makes both cleaner and eliminates the coupling.

#### Acceptance Criteria

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

## Sprint Summary

| Story | Points | Priority | Persona |
|-------|--------|----------|---------|
| S10-1: `--ref-type` CLI unification | 3 | P0 | Neo |
| S10-2: `--stale` cross-stage temporal | 2 | P1 | Neo |
| S10-3: `prep_tldr` incremental | 2 | P1 | Neo |
| TD-WATCH-1: PathFilter extraction | 1 | P2 | Neo |
| **Total** | **8** | | |

## Cycle Plan

| Cycle | Phase | Stories | Assigned |
|-------|-------|---------|----------|
| 1 | S10-1 (`--ref-type`) | S10-1 | Neo → Trin |
| 2 | S10-2 + S10-3 | S10-2, S10-3 | Neo → Trin |
| 3 | TD-WATCH-1 | TD-WATCH-1 | Neo → Trin |

## Open Questions for Morpheus

1. **S10-1 Parser placement**: Does `--ref-type` live in the relationship flag group (between stages) or as a modifier on `--ref-type <type>` appended to the second `-mg` stage? Recommendation: relationship stage (same position as `-Vinh`).

2. **S10-2 `MatchRecord.mtime` type**: Should `mtime` be `Optional[float]` (nullable for old indexes) or required (force rebuild)? Recommendation: `Optional[float]`, check None at `--stale` time.

3. **S10-3 prep_tldr location**: Should the last-run file live at `.via/prep_tldr_last_run` (alongside the DB) or `build/prep_tldr_last_run`? Recommendation: `.via/` (runtime state).

---

## Arch Handoff

@Morpheus: Sprint 10 user stories ready for review. Key decisions needed:
1. `--ref-type` parser placement (OQ-1 above)
2. `MatchRecord.mtime` nullability strategy (OQ-2)
3. prep_tldr last-run file location (OQ-3)

Please write `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md` resolving these OQs before Neo begins implementation.
