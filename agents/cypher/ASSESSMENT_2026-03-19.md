# Product Assessment — 2026-03-19

**Author**: Cypher (PM)
**Date**: 2026-03-19
**Scope**: Roadmap vs. actual codebase state

---

## TL;DR

Sprint 5 is fully shipped. Sprints 6, 7, and 8 are **not implemented**. The commit labeled "Sprint 6 Phase 1 complete" was planning/docs + test cleanup — NOT WatchService code.

---

## Sprint Status

| Sprint | Theme | Points | Status | Evidence |
|--------|-------|--------|--------|----------|
| Sprint 5 | Relationships | — | ✅ SHIPPED | 661 tests pass (2026-03-19) |
| Sprint 6 | Watch Mode | 12 | ❌ NOT STARTED | `-w` flag errors "not implemented" |
| Sprint 7 | MCP Mode | 10 | ❌ NOT STARTED | No MCP files in codebase |
| Sprint 8 | Line Index | 6 | ❌ NOT STARTED | No `-mL` or `line_offset` anywhere |

**Total unimplemented**: 28 points across 10 stories

---

## Sprint 6 — Watch Mode Detail

### What exists:
- `-w` / `--watch` argparse flag in `via/commands/index.py`
- `__main__.py:222` — guard that prints "Error: Watch mode (-w) is not implemented yet"

### What is missing:
- `via/services/watch.py` — WatchService class (does not exist)
- `watchdog` event handler wired to `IndexingService`
- Debounce logic (500ms)
- SIGINT/Ctrl-C graceful shutdown
- Symbol cleanup on file delete
- Relationship re-resolution on change

### Clarification on "Sprint 6 Phase 1 complete" commit (2026-02-13):
That commit contained **only**: user stories docs, arch review docs, tech debt notes, and test refactors (removed `match.py` command). Zero WatchService implementation.

---

## Sprint 7 — MCP Mode Detail

### What exists:
- `.continue/mcpServers/` as reference (Continue.dev integration)
- `PipelineParser` + `PipelineExecutor` ready to serve as query engine

### What is missing:
- `via/mcp/` directory and all files
- `via --mcp` flag
- `via mcp install/uninstall/status/schema` subcommands
- JSON-RPC 2.0 stdio server
- Claude Code auto-config integration

---

## Sprint 8 — Line Index Detail

### What exists:
- Byte offsets tracked per symbol in DB (ready foundation)
- `-m<X>` match flag convention established

### What is missing:
- `line_offsets` table in DB schema
- Line indexing pass in `IndexingService`
- `-mL` match type in `flag_groups.py` and `PipelineParser`
- Slice syntax parser

---

## Recommended Next Action

**Start Sprint 6.** It is fully specced (5 stories, 12pts), architecture decided (Morpheus: foreground-only, no daemon). The only dependency is `watchdog` library.

Hand off to:
- **@Morpheus** — confirm WatchService arch before Neo starts
- **@Neo** — implement `via/services/watch.py` per Sprint 6 Story 1
- **@Mouse** — set up Sprint 6 task board
