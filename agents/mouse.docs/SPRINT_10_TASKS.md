# Sprint 10 Task Board

**Sprint**: 10
**Theme**: `--ref-type` CLI Unification + `--stale` + `prep_tldr` Incremental + PathFilter
**Start**: 2026-03-22
**Baseline**: 908 tests

---

## Cycle 1: S10-1 `--ref-type` CLI Unification

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| S10-1a | `via/pipeline/parser.py:_find_relationship_split()` — add `--ref-type` scan loop | 1 | [ ] |
| S10-1b | `via/pipeline/parser.py:_create_match_parser()` — add `--ref-type` with `choices=` | 0.5 | [ ] |
| S10-1c | Tests: unit (all 5 types, invalid type error) + integration | 1.5 | [ ] |

**Neo impl → Trin UAT (Cycle 1)**

---

## Cycle 2: S10-2 `--stale` + S10-3 `prep_tldr`

### S10-2: `--stale`

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| S10-2a | `via/core/match_record.py` — add `mtime`, `anchor_mtime` fields to `MatchRecord`; update `MatchRecordFactory` | 0.5 | [ ] |
| S10-2b | `via/db/store.py:query_relationships()` — JOIN anchor mtime, set `anchor_mtime` on results | 1 | [ ] |
| S10-2c | `via/pipeline/relationship_filter.py` — add `result_stale: bool = False` | 0.25 | [ ] |
| S10-2d | `via/pipeline/parser.py:_create_match_parser()` — add `--stale` flag | 0.25 | [ ] |
| S10-2e | `via/pipeline/executor.py` — check `result_stale`, post-filter results | 0.5 | [ ] |
| S10-2f | Tests: unit (stale/fresh filter, None mtime error) + integration | 0.5 | [ ] |

### S10-3: `prep_tldr` Incremental

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| S10-3a | `agents/tools/prep_tldr.py` — add argparse (`root`, `--force`/`-f`) | 0.25 | [ ] |
| S10-3b | `agents/tools/prep_tldr.py` — `read_last_run()` / `write_last_run()` | 0.25 | [ ] |
| S10-3c | `agents/tools/prep_tldr.py` — `get_changed_files()` using `symbols.mtime` | 0.5 | [ ] |
| S10-3d | `agents/tools/prep_tldr.py` — incremental mode: skip unchanged, clean stale data files | 0.5 | [ ] |
| S10-3e | Tests: unit (timestamp r/w, skip logic, force override) | 0.5 | [ ] |

**Neo impl → Trin UAT (Cycle 2)**

---

## Cycle 3: TD-WATCH-1 PathFilter

| Task | File(s) | Points | Status |
|------|---------|--------|--------|
| TD-W1a | `via/core/path_filter.py` — new `PathFilter` class (extracted from `FileDiscovery`) | 0.5 | [ ] |
| TD-W1b | `via/core/discovery.py` — delegate `_should_include_dir/file` to `PathFilter` | 0.25 | [ ] |
| TD-W1c | `via/services/watch.py` — use own `PathFilter`, remove `_discovery` private method calls | 0.25 | [ ] |
| TD-W1d | Tests: unit `PathFilter` + verify all `FileDiscovery` tests pass | 0 (regressions) | [ ] |

**Neo impl → Trin UAT (Cycle 3)**

---

## Smith Implementation Notes (from Gate 2)

1. **S10-1**: `--via` + `--ref-type` in same stage: `--via` wins by scan order. Document this or add a warning.
2. **S10-2**: `--stale` on subject side is silently ignored. Neo: detect and warn or confirm acceptable.

---

## Velocity Tracking

| Sprint | Tests Start | Tests End | Delta |
|--------|-------------|-----------|-------|
| 9 | 837 | 908 | +71 |
| 10 | 908 | TBD | TBD |
