# Oracle Context

**Last Updated**: 2026-03-22

## Sprint 10 Doc Groom (2026-03-22)

### Changes Made
- `docs/USER_GUIDE.md`:
  - TLDR updated: added `--ref-type` and `--stale` to relationship query description
  - New section: **`--stale`: Cross-Stage Temporal Filter** (after `--ref-type` section)
    - 3 examples: stale test files, stale subclasses, stale call sites
    - Note: no-op on plain queries, rebuild index if mtime missing
- `README.md`:
  - TLDR updated: added `--ref-type` and `--stale` to relationship queries description
  - Features: added `--ref-type` mention, added new **Stale Detection** bullet for `--stale`
  - Relationship Queries table: added `--ref-type` and `--stale` rows

### Sprint 10 Features (for reference)
- S10-1: `--ref-type` flag (alternative to `-Vinh`/`--via inherits-from` etc.) — valid values: `inherits-from`, `calls`, `imports`, `references`, `declares`
- S10-2: `--stale` flag — filters relationship results where result.mtime < anchor.mtime
- S10-3: `prep_tldr.py` incremental mode — argparse with `root` + `--force`/`-f`; `.via/prep_tldr_last_run` timestamp file
- TD-WATCH-1: `PathFilter` extracted from `FileDiscovery` into `via/core/path_filter.py`

## Key Files
- `docs/USER_GUIDE.md` - Main user-facing documentation (current)
- `README.md` - Project overview (current)
- `via/core/flag_groups.py` - Flag definitions
- `via/__main__.py` - CLI help text

## Sprint Status
- Sprint 9: COMPLETE — shipped
- Sprint 10: implementation COMPLETE (3 cycles, all Morpheus reviews passed, Oracle groomed)
- Next: Smith end-to-end test → Cypher launch

## Lessons Learned (Sprints 1-7, carried forward)
### L1: SQLite + threading.Timer = check_same_thread=False required
### L2: Symbols table is NOT cascade-linked to files table (plain TEXT column)
### L3: IndexingService._index_file() bypasses transactions (use reindex_file())

## Sprint 9 Decisions Recorded
- DECLARES relationship = -Vhas syntactic sugar over structural containment
- Temporal tracking is per-symbol (symbols.mtime), not just per-file
- -Q flag enables full-path matching for -tF queries
- All patterns case-sensitive by default; -I for case-insensitive
- -th (lowercase) is invalid; -tH (uppercase) is the only header type flag

## Sprint 10 Decisions Recorded
- --stale filter logic: result.mtime < anchor.mtime (strict less-than)
- --stale on subject-side is silently ignored (no-op; safe behavior)
- PathFilter extracted as standalone class; WatchService gets its own instance (no longer accesses FileDiscovery private methods)
- prep_tldr last-run file lives in .via/prep_tldr_last_run (runtime state, not build output)
