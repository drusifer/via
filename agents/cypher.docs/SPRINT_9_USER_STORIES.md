# Sprint 9 - Container Queries + Temporal Matching + Tech Debt Phase 1

**Author**: Cypher (PM)
**Date**: 2026-03-20 (updated 2026-03-21 with Drew feedback)
**Theme**: ReferenceType architecture, `-Vhas`, temporal matching with per-symbol timestamps, tech debt phase 1
**Points**: ~16–18 (see sprint summary — scope grew significantly from Drew's OQ answers)

---

## ⚠️ Architectural Pivot: ReferenceType (Drew, 2026-03-21)

Drew confirmed OQ-9: **+1 for ReferenceType as a filter on `-Vr` to capture all relationship queries based on references.**

This is a significant design direction. The current model has a flat `-V<X>` flag per relationship type (`-Vinh`, `-Vca`, `-Vimp`, `-Vr`). Drew's direction is to introduce a **`ReferenceType`** concept where `-Vr` becomes a unified reference query operator and `ReferenceType` acts as a sub-filter/type qualifier.

**Implication for Story 1**: The design of `-Vhas` / `DECLARES` is now in flux. Options:
- Keep `-Vhas` as syntactic sugar over `-Vr DECLARES` (new unified model)
- Or keep flat model and defer ReferenceType to a future sprint

**⚠️ Morpheus must spec the ReferenceType API before Story 1 implementation begins.** This is now a hard blocker on Story 1.

Questions for Morpheus to resolve:
1. Does `-Vr <ReferenceType>` replace all `-V<X>` flags, or are they kept as aliases?
2. What is the CLI syntax for the type sub-filter? (`-Vr declares`, `--ref-type declares`, etc.)
3. Does `ReferenceType` live in its own enum or as a property on `RelationshipType`?
4. How does `-Vhas` relate to `-Vr` in the new model?

---

## Design Decision: `-Vhas` backed by `DECLARES` relationship (Drew, 2026-03-21)

**Summary of discussion:**

The `-Vhas` implementation should be backed by a proper `DECLARES` relationship
type — not a file-path JOIN and not re-using `-Vr` (REFERENCES).

### Why not `-Vr`?

`-Vr` (REFERENCES) is a **usage** relationship: it tracks `ast.Name` nodes with
`Load` context inside function/method bodies only. It does NOT capture:
- Class base class declarations (`class Child(Base):`)
- Decorator names, type annotations, module-level usage
- Anything outside a function/method body

`DECLARES` is a **structural containment** relationship — entirely distinct.

### What `DECLARES` means

| Source (container) | declares | Target (member) |
|-------------------|----------|-----------------|
| `filepath` | declares | `class`, `function`, `global`, `import` |
| `class` | declares | `method`, inner `class`, class-level `global` |
| `function` | declares | nested `function` |

This is multi-level: file→symbol, class→method, function→nested function.

### Key implementation insight

**No new parsing needed.** The data already exists:
- Every symbol has `file_path` (which file declares it)
- Every method/inner-class has `parent_name` (which class declares it)

`_store_declares_relationships()` in `IndexingService` would simply materialize
these into `symbol_references` rows at index time — no AST changes required.

### Scope change to Story 1

`-Vhas` is now properly specified as:
> `-Vhas` is syntactic sugar over a `DECLARES` relationship query

The flag `-Vhas` / `--via-has` should be added to `flag_groups.py` and mapped
to `RelationshipType.DECLARES` (new). The query infrastructure stays the same.

**Morpheus design inputs updated** (see Story 1 section below).

---

## Epic: Has-A Relationship (`-Vhas`)

Add a "has" relationship that lets users query: *which symbols live inside a container matching a pattern?*

Today, querying symbols by file requires an awkward workaround using `-Q` (qualified name matching). `-Vhas` makes this a first-class pipeline operation consistent with all other `-V<X>` relationship flags.

`-Vhas` is named for "has-a" semantics and is designed to be extensible beyond file→symbol — e.g., class→method, module→class, any container type that can "have" members.

### Architectural Direction (Drew, 2026-03-20)

`-Vhas` should be implemented as a special case of the **existing reference query infrastructure**, not a bespoke file-path JOIN. The conceptual model:

- A "container" is any symbol type that can **declare** other symbols inside it
- The type of reference is a **declaration reference** (member var, global, function/method declaration within a scope)
- The mapping between container type and reference type needs to be defined — this is **Morpheus's design task**
- The join key varies by container type; it must honor the match type selected in stage 1 (glob, regex, exact)
- Use polymorphism to make container types extensible (don't hardcode file→symbol)

> **Action for Morpheus**: Design the "Container" abstraction — what types are valid containers, how each maps to its member reference type, and how to dispatch in `PipelineExecutor`.

### Motivation

Current workaround (awkward):
```bash
via -mr 'store' -tc -Q          # regex on qualified name — brittle, not obvious
```

With `-Vhas` (clean, discoverable):
```bash
via -mg '*store*' -tF -Vhas -tc          # all classes in files matching *store*
via -mg '*service*' -tF -Vhas -tf -n 0   # all functions in service files
via -mg 'watch.py' -tN -Vhas -tm         # all methods in watch.py
```

### Why not `-Vin`?

`-Vin` is too similar to `-Vinh` (inherits-from) — visually ambiguous at a glance. `-Vhas` is distinct, self-documenting, and aligns with "has-a" relationship terminology from OOP.

### Decisions (Drew, 2026-03-20)

| Decision | Answer |
|----------|--------|
| Flag | `-Vhas` (follows `-V<X>` relationship convention) ✅ |
| Long form | `--via-has` — confirm pattern matches other `--via-*` flags |
| Replaces | Initial `-Vin` proposal — rejected, too similar to `-Vinh` ✅ |
| First stage type | Any valid **container type** — Morpheus to define; not limited to `-tF`/`-tN` |
| Second stage type | Any symbol type (`-tc`, `-tf`, `-tm`, `-ti`, `-tg`) — possibly a subset already indexed as references |
| Join key | Varies by container type; honors stage 1 match operator (glob/regex/exact) |
| DB query | May reuse existing reference query infrastructure — Morpheus to confirm |
| `--invert` | Clear error: "does not have (not-has) — not yet supported" |

---

### Story 1: `-Vhas` Has-A Relationship (P0, 3pts — **BLOCKED on ReferenceType arch spec**)

**As a developer**, I want to query `via -mg '<pattern>' -t<Container> -Vhas -t<Member>` to find all symbols of a given type contained in things matching the pattern, so I can explore a module's contents without workarounds.

**Acceptance Criteria**:
- [ ] New relationship flag `-Vhas` / `--via-has` added to `relationship_types.py`
- [ ] `-Vhas` appears in `--help` under Relationship Flags
- [ ] Stage 1 must be a valid **container type** (per Morpheus's container type registry); clear error if not
- [ ] Error messages for invalid args are **precise**: explain *why* the arg is invalid, not just that it is
- [ ] Stage 2 specifies the member symbol type to return (`-tc`, `-tf`, `-tm`, etc.)
- [ ] Result set is all symbols declared within containers matching stage 1
- [ ] Works with all match syntaxes: `-mg`, `-mr`, `-ms`
- [ ] Works with `-n 0` for unlimited results
- [ ] Result cap warning applies (same as all other queries)
- [ ] Works with output flags: `-oL`, `-oT`, `-oR`, `-oF`
- [ ] `--invert` raises a clear error: `"--invert with -Vhas means 'does not have' — not yet supported"`

**Examples**:
```bash
# All functions in files matching *service*
via -mg '*service*' -tF -Vhas -tf -n 0

# All classes in store.py
via -mg 'store.py' -tN -Vhas -tc

# All methods in watch.py, as table
via -mg 'watch.py' -tN -Vhas -tm -oT -n 0

# All symbols (any type) in pipeline/ files
via -mg '*/pipeline/*' -tF -Vhas -n 0

# All test functions across all test files
via -mg 'test_*.py' -tN -Vhas -tf -n 0
```

**Implementation Notes** (updated 2026-03-21):
- New `DECLARES = 'declares'` added to `RelationshipType` enum
- `-Vhas` / `--via-has` maps to `RelationshipType.DECLARES` in `flag_groups.py` and `_SHORT_FLAGS`
- New `_store_declares_relationships()` in `IndexingService` — no parser changes needed:
  - For each non-filepath symbol: insert `(filepath_symbol_id → symbol_id, 'declares')`
  - For each method/inner-class: insert `(parent_class_symbol_id → symbol_id, 'declares')`
  - For each nested function: insert `(parent_function_symbol_id → symbol_id, 'declares')` **(OQ-1: IN SCOPE — Drew confirmed)**
- `PipelineExecutor._execute_relationship_query()` — new dispatch branch for `DECLARES`
- `DatabaseStore.query_relationships()` handles it via existing infrastructure (same `symbol_references` table)
- Morpheus to confirm: join strategy, container type validation, error messages for invalid stage types

**Error Message Standard (applies to all stories)**:
All invalid-argument errors must state:
1. What arg is invalid
2. Why it's invalid for this command
3. What valid values look like

Example: `"Error: -Vhas stage 1 received '-tc' (class), which is not a container type. Valid containers: file (-tF), filename (-tN). Future: class (-tc), module (-tm)."`

---

---

### Story 2: Incremental `prep_tldr` via Temporal Matcher (P1, est. 2–5pts — needs split)

**As a developer running `*ora tldr`**, I want `prep_tldr` to only regenerate data files for files that changed since the last run, so that TLDR sweeps are fast and sub-agents only process files that actually need work.

#### ⚠️ Scope Note (Cypher assessment, 2026-03-20)

Drew's direction shifts Story 2 significantly: rather than a hardcoded `get_files_changed_since()` in `DatabaseStore`, the right approach is a **temporal matcher type** in via's extensible query API (older-than, newer-than, etc.). This is architecturally correct but likely 3–4pts on its own, plus 1–2pts for the `prep_tldr` integration.

**Recommendation**: Split into:
- **Story 2a** (Sprint 9, P1, ~3pts): Temporal matcher type in via — `mtime > <ts>` / `mtime < <ts>` as a first-class query operation; `.last_run` state managed in via lib
- **Story 2b** (Sprint 9, P2, ~2pts): `prep_tldr` integration using the temporal matcher

> **Drew to confirm**: split OK, or keep as one larger story?

**⚠️ Scope Pivot (Drew, 2026-03-21)**: Temporal tracking is per-**symbol**, not just per-file.

> "We want timestamps captured as part of indexing including in watch mode. When a class is modified and detected by watch, the timestamp of that file and **that class** are updated to the file mtime. Other indexed objects that didn't change keep their old timestamp. Resets on full reindex."

This means:
- `symbols` table needs an `mtime` column (schema change — currently only `files.mtime` exists)
- On watch event: update `mtime` on the file's symbols that changed, NOT all symbols in the file
- Other symbols in unchanged files retain their previous `mtime`
- Full reindex: reset all symbol mtimes

**CLI operators** (Drew, OQ-4): Human-friendly: `olderthan`, `newerthan`, `xTimeAgo` style. Not raw Unix timestamps.

**API surface** (Drew, OQ-2): Both CLI flag **and** Python library function.

**Acceptance Criteria** (Story 2a — temporal matcher):
- [ ] `symbols` table gets `mtime` column (schema migration required)
- [ ] On index: symbol `mtime` set to the file's `mtime` at index time
- [ ] On watch event: only symbols in the **changed file** have their `mtime` updated
- [ ] Symbols in unchanged files retain their previous `mtime`
- [ ] Full reindex (`--force`): all symbol mtimes reset
- [ ] New temporal query operators in via CLI: `olderthan <duration>`, `newerthan <duration>` (Morpheus to spec exact syntax)
- [ ] API surface exposed as Python library function as well as CLI flag
- [ ] First run (no prior timestamps): all symbols returned (full sweep)
- [ ] Morpheus to spec: exact CLI syntax, duration format, integration point in pipeline

**Acceptance Criteria** (Story 2b — `prep_tldr` integration):
- [ ] `prep_tldr.py` uses via's temporal matcher (not own DB query) to get changed files
- [ ] `prep_tldr.py --force` bypasses temporal filter and forces full sweep
- [ ] On incremental run: only generate `*_data.txt` for changed files
- [ ] On incremental run: `py_files.txt` and `md_files.txt` list **only changed files** (minimize sub-agent token consumption)
- [ ] On incremental run: data files for **deleted source files** are cleaned up (delete data file if source path no longer exists)
- [ ] On full sweep: delete all existing `_data.txt`, regenerate everything (current behavior)
- [ ] Cleanup (delete stale `_data.txt`) on incremental: only for deleted sources

**Examples**:
```bash
# First run — full sweep
python agents/tools/prep_tldr.py

# Subsequent run — only files changed since last run
python agents/tools/prep_tldr.py

# Force full sweep regardless
python agents/tools/prep_tldr.py --force
```

**Implementation Notes** (current `prep_tldr.py` — confirmed 2026-03-20):

| Item | Status | Detail |
|------|--------|--------|
| `files.mtime` column | ✅ EXISTS | `via/db/schema.py:45` — set from `os.stat().st_mtime` |
| `files.indexed_at` column | ✅ EXISTS | `via/db/schema.py:46` — secondary, not used for change detection |
| `files.path` column | ✅ EXISTS | Relative path from `index_root` |
| Temporal matcher in via | ❌ MISSING | **Morpheus to design** |
| `prep_tldr.py --force` flag | ❌ MISSING | Needs `argparse` added |
| Change timestamp state in via lib | ❌ MISSING | Replaces `build/tldr_prep/.last_run` |
| `DatabaseStore.get_files_changed_since()` | ❌ NOT BUILDING | Superseded by temporal matcher design |

Current `prep_tldr.py` flow (lines to change):
1. Re-indexes via `IndexingService.index()` — already incremental, keep
2. Opens raw `sqlite3.connect` → **replace with via temporal matcher API when available**
3. Stale-file cleanup at lines 120–124 — **condition on full-sweep mode**
4. File loop generates `_data.txt` for every file — **filter to changed files on incremental**
5. `py_files.txt` / `md_files.txt` — **filter to changed files on incremental**

#### Sequence diagram (post-Story 2a)

```
prep_tldr incremental (after first run):

  via.temporal_match(since=last_run_ts) → changed_paths (set)
  IndexingService.index()              # fast — already incremental
  for deleted in (existing data files - changed_paths - current_file_list):
    delete stale data file             # cleanup deleted sources
  write py_files.txt, md_files.txt    # only changed files
  for each file in changed_paths:
    regenerate _data.txt              # symbol query + TLDR coords
  via.update_last_run(time.time())    # stored in via lib
```

---

### Story 3: Expand `-Vr` Reference Tracking (P1, ~3pts — Drew confirmed Sprint 9)

**As a developer**, I want `-Vr` to track reference usages beyond function/method bodies, so that class base declarations, decorators, and module-level usages are all queryable.

**Context**: Trin doc review (Finding 5, 2026-03-21) found that `-Vr` only captures `ast.Name` nodes with `Load` context **inside function/method bodies**. The following are not currently tracked:
- Class base class declarations: `class Child(Base):`
- Decorator names: `@my_decorator`
- Module-level name usage (outside any function/method)
- Type annotations

Drew confirmed: *"Agreed - we will tackle this in sprint 9"*

**Acceptance Criteria**:
- [ ] Class base class names are stored as REFERENCES relationships (e.g., `class Child(Base):` → `Child` references `Base`)
- [ ] Decorator names are stored as REFERENCES relationships
- [ ] Module-level name usages (e.g., top-level assignments referencing another symbol) are stored as REFERENCES
- [ ] Type annotations in **function signatures** are stored as REFERENCES
- [ ] Type annotations in **class bodies** (e.g., `field: MyType`) are stored as REFERENCES **(OQ-8: IN SCOPE — Drew confirmed)**
- [ ] Existing function/method body reference tracking is unchanged
- [ ] 5 xfail tests in `tests/uat/test_documented_queries_uat.py` (Finding 5 tests) now pass
- [ ] No regression in existing reference query behavior

**Implementation Notes**:
- Parser change in `via/parsers/python_parser.py` — extend `ast.Name`/`ast.Annotation` node collection scope
- `_store_reference_relationships()` in `via/services/indexing.py` unchanged — data model stays the same
- Source of xfail tests: `tests/uat/test_documented_queries_uat.py` (5 tests, Finding 5)

---

### Story 4: Fix Class Anchor Bug for `-Vca` (TD/Bug, ~1pt — OQ-5 resolved Sprint 9)

**As a developer**, when I use a class as an anchor with `-Vca`, I want to get the call relationships of its methods, so that `via -mg 'MyClass' -tc -Vca -tf` works as documented.

**Background**: Call relationships are stored from method symbols (`symbol_type = 'method'`), not class symbols. Anchoring on `-tc` returns empty. Drew confirmed: *"This is a bug."*

**Acceptance Criteria**:
- [ ] `via -mg 'MyClass' -tc -Vca -mg '*' -tf` returns functions called by MyClass's methods
- [ ] When anchor is `-tc` for `-Vca`, executor expands query to include all methods where `parent_name = class_name`
- [ ] Existing `-tm` anchor behavior unchanged
- [ ] Trin Finding 2 xfail test in `test_documented_queries_uat.py` now passes
- [ ] `schema.py` example 9 and skill SKILL.md files updated to reflect correct behavior

---

### Story 5: `-Q` Full-Path Matching for File Symbols (TD/Enhancement, ~1pt — OQ-6 resolved Sprint 9)

**As a developer**, I want `via -mg 'via/core/*' -tF -Q` to match file symbols by their full path, not just basename, so I can filter by directory path without a workaround.

**Background**: Currently `-mg` matches `symbol_name` (basename only). For file symbols, `qualified_name = full_path`. Drew approved Option C: "Yes to C" — enable `-Q` to make `-mg` match `qualified_name` for file symbols.

**Acceptance Criteria**:
- [ ] `-Q` flag (already exists for symbol qualified name matching) works for file symbols (`-tF`)
- [ ] `via -mg 'via/core/*' -tF -Q` returns all files under `via/core/`
- [ ] Without `-Q`, file matching stays as basename only (no regression)
- [ ] `schema.py` Ex05 updated to use correct form with `-Q`
- [ ] Trin Finding 1 xfail test (Option C) now passes

---

## Sprint 9 Summary

| Story | Points | Priority | Description | Status |
|-------|--------|----------|-------------|--------|
| Story 1 | ~3 | P0 | `-Vhas` has-a relationship (container→members) | **BLOCKED: ReferenceType arch spec** |
| Story 2a | ~4 | P1 | Temporal matcher + per-symbol timestamps (schema change) | BLOCKED: Morpheus spec |
| Story 3 | ~3 | P1 | Expand `-Vr` reference tracking (class bases, decorators, annotations) | Ready for Neo |
| Story 4 | ~1 | P1 (bug) | Fix class anchor bug for `-Vca` | Ready for Neo |
| Story 5 | ~1 | P2 | `-Q` full-path matching for file symbols | Ready for Neo |
| TD-Phase-1 | ~3 | P2 | TD-REVIEW-1 through TD-REVIEW-5 (Morpheus code review) | Ready for Neo |
| **Total** | **~15** | | | |

**Story 2b** (`prep_tldr` integration using temporal matcher, ~2pts) → **moved to Sprint 10** (Drew, 2026-03-20).

---

## Technical Context (for Morpheus — design exit criteria)

### Story 1 (`-Vhas` / `DECLARES`) — Morpheus design inputs

| Item | Location | Current state |
|------|----------|--------------|
| `RelationshipType` enum | `via/core/relationship_types.py` | Add `DECLARES = 'declares'` |
| `-V<X>` flag definitions | `via/core/flag_groups.py` | Add `-Vhas` / `--via-has` → `DECLARES` |
| `_SHORT_FLAGS` dict | `via/core/relationship_types.py` | Add `RelationshipType.DECLARES: 'has'` |
| `_store_declares_relationships()` | `via/services/indexing.py` | New method — no parser changes; uses `file_path` + `parent_name` |
| `PipelineExecutor._execute_relationship_query()` | `via/pipeline/executor.py` | Add `DECLARES` dispatch branch |
| `symbol_references` table | `via/db/schema.py` | Reused — no schema changes needed |
| `DatabaseStore.query_relationships()` | `via/db/store.py` | No changes — existing infrastructure handles it |

**Morpheus must confirm/spec** (updated 2026-03-21):
- **ReferenceType architecture first** (OQ-9) — how `-Vhas`/`DECLARES` fits in the new model before implementation
- Container type validation: which `-t<X>` types are valid as stage 1 (anchor)
- Error message format for invalid container type (per project error standard)
- Nested function→function declarations: **IN SCOPE** (OQ-1 resolved)
- Polymorphic dispatch strategy in `PipelineExecutor` (or confirm direct `DECLARES` branch is sufficient)

### Story 2 (`temporal matcher`) — Morpheus design inputs

| Item | Location | Current state |
|------|----------|--------------|
| `files.mtime` | `via/db/schema.py:45` | ✅ Exists |
| `files.indexed_at` | `via/db/schema.py:46` | ✅ Exists (not used for temporal) |
| `FileDiscovery` | `via/core/discovery.py` | No temporal filter; may not need one |
| `DatabaseStore` | `via/db/store.py` | No temporal query method yet |

**Morpheus must spec**:
- API surface: via CLI flag (`--since <ts>`)? via library function? both?
- Where last-run timestamp state lives in via lib
- Whether this is part of `match()` or a separate query path
- Integration point for `prep_tldr` to consume

---

## Open Questions

These questions need Drew's input before Sprint 9 implementation begins.

| # | Question | Story | Owner | Status |
|---|----------|-------|-------|--------|
| OQ-1 | Should nested function→function DECLARES relationships be in Sprint 9 scope? | Story 1 | Drew | ✅ YES — in scope |
| OQ-2 | Story 2a API surface: CLI flag only, or also Python library function? | Story 2a | Drew | ✅ BOTH — CLI flag + Python library function |
| OQ-3 | Where does timestamp state live? | Story 2a | Drew | ✅ Per-symbol — `symbols.mtime` column; updated on watch events per-file, resets on full reindex |
| OQ-4 | Temporal matcher operators? | Story 2a | Drew | ✅ Human-friendly: `olderthan`, `newerthan`, `xTimeAgo` (Morpheus to spec exact syntax) |
| OQ-5 | Class call query bug — Sprint 9? | Story 4 | Drew | ✅ Sprint 9 as TD (→ Story 4) |
| OQ-6 | `-Q` path matching — Sprint 9? | Story 5 | Drew | ✅ Sprint 9 as TD (→ Story 5) |
| OQ-7 | TD-REVIEW items — Sprint 9 scope? | Tech Debt | Drew | ✅ Sprint 9 Phase 1 — all 5 items |
| OQ-8 | Class-body type annotations in Story 3 scope? | Story 3 | Drew | ✅ Sprint 9 — "interesting reference type use case" |
| OQ-9 | ReferenceType concept vs. flat RelationshipType? | Arch | Drew | ✅ +1 for ReferenceType as filter on `-Vr` — **Morpheus must spec before Story 1** |

### Context for OQ-9 (RelationshipType scalability)
From a user perspective, both a flat `RelationshipType` extension and a grouped `ReferenceType` concept produce the same CLI behavior for Sprint 9. The concern becomes visible only in `--help` output and discoverability as flags grow. Currently 4 flags (`-Vinh`, `-Vca`, `-Vimp`, `-Vr`); Sprint 9 adds `-Vhas` = 5. If future sprints add `DECORATES`, `ANNOTATES`, `OVERRIDES`, a flat ungrouped list degrades. A `category` property on `RelationshipType` (e.g., `structural` vs. `behavioral`) could drive `--help` section headers at zero user-visible cost now. A full `ReferenceType` class adds user value only if it surfaces as a new query operator (e.g., `-Vany`, `-Vstructural`). Morpheus to decide whether to add grouping now or at the threshold of 6+ flags.

### Context for OQ-5 (class call query bug)
Trin Finding 2: `["-mg", "MyClass", "-tc", "-Vca", ...]` returns empty. Call relationships are stored from **method** symbols, not class symbols. To use a class as anchor for `-Vca`, the executor would need to expand the query to include all methods where `parent_name = class_name`. Drew confirmed this is a bug — fix scope TBD.

### Context for OQ-6 (`-Q` path matching)
Trin Finding 1, Option C: For `-tF` (filepath) symbols, `qualified_name = full_path`. Enabling `-Q` on `-mg` for file queries would make `via -mg 'via/core/*' -tF -Q` match full paths. Separate from `-Vhas` (which handles Finding 1 Ex02 queries via relationship pipeline). Drew approved: "Yes to C".

### Context for OQ-7 (TD-REVIEW)
Morpheus code review (2026-03-21) identified 5 prioritized tech debt items:
- **P1**: TD-REVIEW-1 (remove `_get_match_metadata()`, move to `TableRenderer`) — perf + SRP
- **P1**: TD-REVIEW-2 (add `DatabaseStore.get_symbol_id()`, remove `.conn` access) — abstraction
- **P2**: TD-REVIEW-3 (simplify `delete_file_completely`, trust FK CASCADE)
- **P2**: TD-REVIEW-4 (merge 3 file-storage methods into `_upsert_raw_file`)
- **P2**: TD-REVIEW-5 (merge call+ref relationship methods)

Note: Story 1 (`-Vhas`) adds `_store_declares_relationships()` — TD-REVIEW-2 and TD-REVIEW-5 should ideally be done **before** Story 1 lands to avoid making the smell worse.

---

## Resolved Questions

| # | Question | Answer (Drew, 2026-03-20) |
|---|----------|--------------------------|
| 1 | `--invert` on `-Vhas`? | Clear error: "does not have (not-has) — not yet supported" |
| 2 | `-Vhas` scope: file→symbol only? | No — general container concept; Morpheus designs extensible abstraction |
| 3 | Error message format for invalid stage type? | Precise: state what's invalid, why, and valid alternatives |
| 4 | Change detection: `mtime` or `indexed_at`? | `mtime` — reflects actual file change; integrates with `-w` watch semantics |
| 5 | `py_files.txt`/`md_files.txt`: full list or changed only? | **Changed only** — minimize sub-agent token consumption |
| 6 | Stale data files for deleted sources on incremental? | **Clean up** — delete data file if source no longer exists |
| 7 | Call `IndexingService.index()` on incremental? | Yes — already incremental, cheap |
| 8 | `--since` as via CLI flag? | Yes — part of temporal matcher feature (Story 2a); not just for prep_tldr |
| 9 | `.last_run` location? | In via lib — not in `build/tldr_prep/` |

---

## General Standards (Drew, 2026-03-20)

**Error messages**: All invalid-argument errors must be precise. State:
1. What argument is invalid
2. Why it's invalid for this command/context
3. What valid values or alternatives look like

This applies to all stories going forward — it's a project-wide standard, not just Sprint 9.

---

## Tech Debt Backlog

### TD-REVIEW-1: Remove `_get_match_metadata()`, push column widths to `TableRenderer`
**Priority**: P1 (perf + SRP) | **Source**: Morpheus code review, 2026-03-21
**Area**: `via/db/store.py:553–595`, `via/renderers/`
**Problem**: Every `match()` call fires an extra aggregation SQL query for rendering column widths — even when output is `-oR` (raw). DB layer has no business knowing about column widths.
**Prescription**: Remove `_get_match_metadata()`. `TableRenderer` computes widths during a first pass. `total_matches` count computed lazily only when limit warning is needed.
**Sprint**: OQ-7 — awaiting Drew's sprint assignment

### TD-REVIEW-2: Add `DatabaseStore.get_symbol_id()`, remove `.conn` access from IndexingService
**Priority**: P1 (abstraction) | **Source**: Morpheus code review, 2026-03-21
**Area**: `via/db/store.py`, `via/services/indexing.py:478,501`
**Problem**: IndexingService directly executes SQL via `self.db_store.conn.execute(...)` — bypasses the DatabaseStore abstraction entirely.
**Prescription**: Add `get_symbol_id(name, symbol_type, file_path, parent_name) -> Optional[int]` to DatabaseStore.
**Sprint**: OQ-7 — awaiting Drew's sprint assignment. **Note**: Should be done before Story 1 `-Vhas` adds another similar method.

### TD-REVIEW-3: Simplify `delete_file_completely`, remove `delete_relationships_for_file`
**Priority**: P2 | **Source**: Morpheus code review, 2026-03-21
**Area**: `via/db/store.py:357–384, 1089–1127`
**Problem**: Both methods manually delete `symbol_references` rows that FK CASCADE already handles.
**Prescription**: Delete from `symbols` → cascade handles references. Audit/remove `delete_relationships_for_file`.
**Sprint**: OQ-7 — awaiting Drew's sprint assignment

### TD-REVIEW-4: Merge 3 file-storage methods into `_upsert_raw_file()`
**Priority**: P2 | **Source**: Morpheus code review, 2026-03-21
**Area**: `via/services/indexing.py:560–616`
**Problem**: `_store_unparsed_file`, `_store_oversized_file`, `_store_file_with_error` share identical skeleton differing only in a boolean flag.
**Sprint**: OQ-7 — awaiting Drew's sprint assignment

### TD-REVIEW-5: Merge `_store_call_relationships` + `_store_reference_relationships`
**Priority**: P2 | **Source**: Morpheus code review, 2026-03-21
**Area**: `via/services/indexing.py:472–516`
**Problem**: Near-identical methods differing only in attribute names and `rel_type`.
**Note**: Story 1 will add a third sibling (`_store_declares_relationships()`). Merging before Story 1 lands avoids proliferating the smell.
**Sprint**: OQ-7 — awaiting Drew's sprint assignment

### TD-WATCH-1: Extract `PathFilter` from `FileDiscovery`

**Priority**: Low (functional fix already in place)
**Area**: `via/core/`, `via/services/watch.py`, `via/core/discovery.py`

**Problem**: `WatchService` calls `self._discovery._should_include_dir()` — a private method on `FileDiscovery`. This is fragile coupling.

**Solution**: Extract exclusion logic into `via/core/path_filter.py`:
```python
class PathFilter:
    def __init__(self, root_dir, extra_patterns=None): ...
    def include_dir(self, dir_path: str) -> bool: ...
    def include_file(self, file_path: str) -> bool: ...
```
- `FileDiscovery` composes `PathFilter` internally
- `WatchService` takes a `PathFilter` directly — no `FileDiscovery` dependency
- Gitignore spec stays in `PathFilter`
