# Cypher Context - VIA Project

**Last Updated**: 2026-03-19

## Current Project
Via - Python codebase indexing and querying CLI tool

## Key Decisions Made

### Sprint 5 - SHIPPED
- STATUS: SHIPPED
- 661 tests (at time of ship), all relationship types implemented
- Docs condition cleared by Oracle

### Sprint 6 - SHIPPED (2026-03-19)
- STATUS: SHIPPED — 709 tests, 0 failures
- Watch Mode (`via index -w`) fully implemented
- Bugs found + fixed in UAT: SQLite thread safety + missing symbol deletion
- Morpheus review: APPROVED, 5 tech debt items in `morpheus.docs/SPRINT_6_REVIEW.md`
- Tech debt to address in Sprint 7: DatabaseStore.delete_file_completely(), IndexingService.reindex_file()

### Index Command Specification
- **Storage**: SQLite database at `.via/index.db`
- **Universal file indexing**: All files (metadata), parse only `.py`, `.pyx`, `.pyi`, `.md`
- **Incremental by default**: Skip unchanged files unless `--force`
- **Watch mode**: `via index -w`, watchdog, debounce 500ms, foreground only
- **10MB parse limit**

### Command Syntax Finalized
```bash
via index [-w] [-v|-vv|-vvv|-vvvv] [--force] [--exclude PATTERN] [<dir>]
```

### Roadmap (2026-03-20)
- **Sprint 7** - MCP Mode (10pts): `via mcp serve` (watch+JSON-RPC), `via install mcp`, `via mcp schema` — **STORIES READY** (updated 2026-03-20), see SPRINT_7_USER_STORIES.md. Needs Morpheus design: watch+server concurrency, JsonRenderer arch, install/status polymorphism.
- **Sprint 8** - Line Index (6pts): `-mL` match type with slice syntax, byte offset indexing
- **Sprint 9** - Container Queries (~6pts): `-Vhas` has-a relationship (container→members) + temporal matcher in via query layer
- **Sprint 10** - (planned) `prep_tldr` integration using temporal matcher (~2pts) + TBD
- User stories reviewed 2026-03-19, Sprint 9 added 2026-03-20 per Drew request

## Session 2026-03-20
- Sprint 9 user story added: `-Vhas` has-a relationship (3pts) — renamed from `-Vin` (too similar to `-Vinh`)
- Syntax: `via -mg '*service*' -tF -Vhas -tf -n 0` — files→symbols containment
- Sprint 9 Story 2 added: incremental `prep_tldr` via `--since` filter (2pts) — stores last run in `.last_run`, only re-generates data files for changed files
- Sprint 9 total now 5pts
- See `agents/cypher.docs/SPRINT_9_USER_STORIES.md`

### Story 2 — Rescoped per Drew feedback (2026-03-20)
- `files.mtime` column EXISTS (`via/db/schema.py:45`) — use for change detection ✅
- Column is `indexed_at` (NOT `last_indexed`)
- `DatabaseStore.get_files_changed_since()` NOT BUILDING — superseded by temporal matcher design
- Story 2 split into 2a (temporal matcher in via, ~3pts) + 2b (prep_tldr integration, ~2pts)
- Temporal matcher is a first-class via query capability; state (last_run) lives in via lib
- `py_files.txt`/`md_files.txt` → changed files ONLY on incremental (minimize sub-agent tokens)
- Stale data files for deleted sources → DELETE on incremental run
- Sprint 9: ~6pts (Story 1 + Story 2a); Story 2b (prep_tldr) → Sprint 10 (Drew confirmed 2026-03-20)
- Error messages project-wide standard: must state what/why/valid-alternatives

## Blockers
None
