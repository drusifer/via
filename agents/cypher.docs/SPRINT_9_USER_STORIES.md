# Sprint 9 - Has-A Relationship (`-Vhas`) + Incremental `prep_tldr`

**Author**: Cypher (PM)
**Date**: 2026-03-20 (updated with Drew feedback)
**Theme**: Has-A Containment Queries + Temporal Matching
**Points**: ~6 (Story 1: 3pts + Story 2a: ~3pts; Story 2b moved to Sprint 10 — Drew, 2026-03-20)

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

### Story 1: `-Vhas` Has-A Relationship (P0, 3pts — pending Morpheus design)

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

**Implementation Notes** (pending Morpheus design):
- Likely reuses existing `symbol_references` table — declaration references may already be indexed
- Container type dispatch in `PipelineExecutor._execute_relationship_query()` — new branch for `HAS`
- Add `HAS = 'has'` to `RelationshipType` enum + `'has': RelationshipType.HAS` to `_SHORT_FLAGS`
- Morpheus to specify: container type registry, join strategy, and valid container→member mappings

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

**Acceptance Criteria** (Story 2a — temporal matcher):
- [ ] New temporal match capability in via query layer: filter files by `mtime` (newer-than / older-than a timestamp)
- [ ] Morpheus to spec the API surface (via CLI flag vs. via library function vs. both)
- [ ] `mtime` column in `files` table used as the change timestamp (already exists — ✅)
- [ ] Temporal matcher honors `-w` watch mode semantics (tracks "freshness" consistently)
- [ ] State (`last_run` timestamp) managed in via lib — not in `build/tldr_prep/`
- [ ] First run (no stored timestamp): all files returned (full sweep)

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

## Sprint 9 Summary

| Story | Points | Priority | Description | Status |
|-------|--------|----------|-------------|--------|
| Story 1 | 3 | P0 | `-Vhas` has-a relationship (container→members) | Needs Morpheus design |
| Story 2a | ~3 | P1 | Temporal matcher in via query layer | Needs Morpheus design |
| **Total** | **~6** | | | |

**Story 2b** (`prep_tldr` integration using temporal matcher, ~2pts) → **moved to Sprint 10** (Drew, 2026-03-20).

---

## Technical Context (for Morpheus — design exit criteria)

### Story 1 (`-Vhas`) — Morpheus design inputs

| Item | Location | Current state |
|------|----------|--------------|
| `RelationshipType` enum | `via/core/relationship_types.py` | Add `HAS = 'has'` |
| `-V<X>` flag definitions | `via/core/flag_groups.py` | Add `-Vhas` / `--via-has` |
| `PipelineExecutor._execute_relationship_query()` | `via/pipeline/executor.py` | Add `HAS` dispatch branch |
| `symbols.file_path` column | `via/db/schema.py` | Exists; may or may not be the join key |
| `symbol_references` table | `via/db/schema.py` | Likely reused for declaration references |
| `DatabaseStore.query_relationships()` | `via/db/store.py` | May extend or add `query_has()` |

**Morpheus must spec**:
- Container type registry (which `-t<X>` types are valid containers)
- Declaration reference type mapping (container type → `reference_type` string in `symbol_references`)
- Whether declaration references are already indexed or need parser changes
- Polymorphic dispatch strategy in `PipelineExecutor`

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
