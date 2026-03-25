# Oracle Context

**Last Updated**: 2026-03-24

## Sprint 13 Doc Groom (2026-03-24)

### Changes Made
- `README.md`: Updated TLDR, Features, Relationship Queries table, Sprint History through Sprint 13
- `docs/USER_GUIDE.md`: Full rewrite of Relationship Queries and Container Queries sections for new `--via`/`--sans`/`--not` syntax
- Moved `DESIGN_RENDER_PIPELINE.md` and `DESIGN_SPRINT3_INTERNAL_PIPELINE.md` from root to `docs/`

### Sprint 13 Features (for reference)
- `--via <rel>` / `-V <rel>` — positive relationship filter (replaces `-Vinh`/`-Vca`/`-Vimp`/`-Vr`/`-Vhas`)
- `--sans <rel>` / `-S <rel>` — NOT EXISTS negative relationship (replaces `--invert`/`-iv`)
- `--not` — negate the immediately following pattern flag
- `--ref-type` REMOVED (was Sprint 10; removed in Sprint 13 CLI redesign)
- All old `-Vxxx` short flags REMOVED — breaking change

## Key Files
- `docs/USER_GUIDE.md` - Main user-facing documentation (current)
- `README.md` - Project overview (current)
- `via/core/flag_groups.py` - Flag definitions (RELATIONSHIP group removed)
- `via/__main__.py` - CLI help text

## Sprint Status
- Sprint 10: COMPLETE — doc groomed 2026-03-22
- Sprint 11-12: COMPLETE — Web UI (no doc groom needed; CHANGELOG has it)
- Sprint 13: COMPLETE — CLI relationship redesign; doc groomed 2026-03-24

## Lessons Learned (Sprints 1-7, carried forward)
### L1: SQLite + threading.Timer = check_same_thread=False required
### L2: Symbols table is NOT cascade-linked to files table (plain TEXT column)
### L3: IndexingService._index_file() bypasses transactions (use reindex_file())

## Sprint 9-10 Decisions Recorded
- DECLARES relationship = -Vhas syntactic sugar over structural containment
- Temporal tracking is per-symbol (symbols.mtime), not just per-file
- -Q flag enables full-path matching for -tF queries
- All patterns case-sensitive by default; -I for case-insensitive
- -th (lowercase) is invalid; -tH (uppercase) is the only header type flag
- --stale filter logic: result.mtime < anchor.mtime (strict less-than)
- PathFilter extracted as standalone class

## Sprint 13 Decisions Recorded
- --via/--sans/--not replace all old -Vxxx/--invert/--ref-type flags (breaking change)
- is_negative bool in RelationshipFilter replaces invert bool
- --sans uses NOT EXISTS SQL subquery (query_negative_relationships())
- --not negates the immediately following -mg/-mr/-ms flag only
