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

### Roadmap (2026-03-19)
- **Sprint 7** - MCP Mode (10pts): stdio JSON-RPC server, auto-config Claude Code only, tool schema
- **Sprint 8** - Line Index (6pts): `-mL` match type with slice syntax, byte offset indexing
- User stories reviewed 2026-03-19, no changes requested yet — awaiting Drew's input

## Blockers
None
