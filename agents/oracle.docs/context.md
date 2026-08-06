# Oracle Context

**Last Updated**: 2026-08-06

## MCP 2 Doc Groom (2026-08-06)

- Maintained MCP documentation now reflects the current implementation:
  `mcp.server.MCPServer`, `mcp>=2.0`, Python 3.10+, and both `via_query` and
  `via_ask` tools.
- Sprint 7 and Sprint 12 retain FastMCP excerpts as point-in-time history but
  carry prominent supersession notices linking to the maintained integration
  spec.
- `CHANGELOG.md` now records the MCP 2 migration under a true Unreleased
  section; the released Sprint 12 section is no longer mislabeled Unreleased.
- `docs/specs/installation_and_indexing.md` contained an invalid
  `python -tm venv` command; corrected to `python -m venv`.
- Automation debt: public `make via ARGS=...` is shadowed/no-op, while
  `make -f Makefile.prj via ARGS=...` works. This requires a code/Makefile
  task, not further doc grooming.

## *ora groom docs (2026-07-02)
- Verified via `via/core/relationship_types.py` (not guessed) the exact
  relationship/category names before documenting them: `any-ref` IS the
  informal "blast radius" query (both directions); `upstream-ref` =
  dependencies (`calls`/`references`/`imports`/`inherits-from`/
  `http-calls`); `downstream-ref` = dependents (the `-by` inverses).
  `declares`/`declared-in` deliberately excluded from `any-ref` (structural,
  not a dependency edge — same reasoning Smith/Neo already applied at
  Sprint 26 Cycle 4 for blast-query noise).
- This closes docs debt that sat unfixed across 2+ sprint closes (flagged
  repeatedly in CHAT.md history as "Oracle's job at close," never done)
  — the entire inverse-relationship/category system and the entire
  `via coverage` subsystem had zero spec coverage until now.
- Found the root-file staleness (`ARCH.md`, `TEST_STATUS.md`) and the
  broken README link by directly grepping for actual usage before
  moving/editing anything — confirmed no code/config dependency broke.
- Full findings: `agents/oracle.docs/current_task.md`.

## Sprint 26 Doc Groom (2026-07-01)

### Changes Made
- Distilled monolithic `docs/USER_GUIDE.md` into 7 focused specifications in `docs/specs/`.
- Replaced `docs/USER_GUIDE.md` with a clean index file linking to all distilled specs.
- Consolidated all per-sprint documentation (Sprints 1-26) from individual agent folders into `docs/sprints/sprint_{N}.md`.
- Deleted over 200 redundant individual sprint files.
- Linked `docs/sprints/` in `agents/DOCUMENTATION_INDEX.md`.
- Completed codebase-wide TLDR sweep, applying Code Module docstrings with TLDR blocks to all 14 remaining Python files.
- Relocated scratch helper scripts (audit, consolidation, and distillation) to `agents/tools/` for project reuse.

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
