# Sprint 7 - MCP Mode

**Author**: Cypher (PM)
**Date**: 2026-02-11 (updated 2026-03-20 with Drew feedback + MCP spec research)
**Theme**: AI Agent Protocol Support — Make via a first-class MCP tool
**Points**: 10
**Status**: READY FOR SPRINT — Sprint 6 shipped 2026-03-19 (713 tests, 0 failures)

---

## Epic: MCP Mode

Make `via` a first-class tool for AI agents. In MCP mode, `via` acts as a Model Context Protocol server — always-current index (watch mode built-in), JSON-RPC 2.0 over stdio, and auto-configures itself into Claude Code's tool discovery path.

### Decisions (Drew, 2026-02-11 / updated 2026-03-20)

| Decision | Answer |
|----------|--------|
| Transport | stdio (JSON-RPC 2.0) |
| Target agents | Claude Code **only** (Gemini/ChatGPT deferred to backlog) |
| Entry point | `via mcp serve` |
| Watch mode | **Always on** — `via mcp serve` implicitly runs with watch mode; index is always current |
| Query interface | Single `via_query` tool with polymorphic dispatch — CLI args as input |
| Output renderer | New `JsonRenderer` / MCP output type leveraging existing renderer architecture |
| Install command | `via install mcp` (extensible `install` namespace, not `via mcp install`) |
| Status command | `via status mcp` (polymorphic `status` namespace) |
| Result output | Raw JSON records always — agent decides how to display |
| Required MCP methods | `initialize` + `tools/list` + `tools/call` only (tools capability only) |
| Pagination | Not applicable for `tools/call` — agent controls result size via `args` (e.g. `["-n", "50"]`) |

---

## MCP Spec Research (2026-03-20)

Key facts confirmed before implementation:

| Question | Answer |
|----------|--------|
| Pagination for `tools/call`? | ❌ Not in spec — only list ops (`tools/list`) support cursor pagination. Agent sets limit via args. |
| Required methods for tools-only server? | `initialize` + `tools/list` + `tools/call`. `resources/list`, `prompts/list` optional — skip if not declaring those capabilities. |
| How does Claude Code learn tool schema? | Calls `tools/list` at session startup dynamically. Config files (`.mcp.json`) only tell Claude how to launch the server. |
| Claude Code MCP config paths? | Project scope: `.mcp.json` (project root, committed). User scope: `~/.claude.json` (home root — not `~/.claude/settings.json`). |
| `initialize` response required fields? | `protocolVersion`, `capabilities`, `serverInfo` (name + version). Client then sends `notifications/initialized`. |

---

## Current Codebase State (confirmed 2026-03-20)

| Item | Location | Status |
|------|----------|--------|
| CLI entry + subcommand dispatch | `via/__main__.py` | ✅ Exists — `mcp`, `install`, `status` subparsers to be added |
| `_run_pipeline_command()` | `via/__main__.py:363` | ✅ Exists — logic to be extracted/reused |
| `WatchService` | `via/services/watch.py` | ✅ Exists — integrate into `mcp serve` |
| Renderer architecture | `via/renderers/` | ✅ Exists — add `JsonRenderer` following existing pattern |
| `MatchRecord` | `via/core/match_record.py` | ❌ Needs `to_dict()` for JSON serialization |
| `via/mcp/` module | — | ❌ Does not exist |
| `.mcp.json` in project root | — | ❌ Does not exist |
| `install` / `status` subcommands | `via/__main__.py` | ❌ Do not exist |

---

## Story 1: MCP Server Mode (P0, 5pts)

**As an AI agent developer**, I want to run `via mcp serve` so that Claude Code can query an always-current codebase index via JSON-RPC 2.0 over stdio.

### Acceptance Criteria

- [ ] `via mcp serve` starts: (a) WatchService in background thread, (b) JSON-RPC 2.0 listener on main thread (stdin/stdout)
- [ ] Index is always current — watch mode starts automatically; no separate `via index` needed once server is running
- [ ] Implements JSON-RPC 2.0: `initialize`, `notifications/initialized` (accept), `tools/list`, `tools/call`
- [ ] `initialize` response includes: `protocolVersion` (echoed), `capabilities: {"tools": {}}`, `serverInfo: {name: "via", version: <VERSION>}`
- [ ] `tools/list` returns single tool: `via_query` with typed input schema (see below)
- [ ] `via_query` routes through existing pipeline via new `JsonRenderer` — no separate query logic
- [ ] Results returned as JSON array of symbol objects (raw — no terminal formatting)
- [ ] Each symbol: `symbol_name`, `symbol_type`, `file_path`, `line_number`, `byte_offset`, `qualified_name`, `parent_name`
- [ ] Error responses: JSON-RPC error format `{code, message, data}` with **precise** error messages (what, why, valid alternatives)
- [ ] Stats queries (`args: ["stats"]`) work through `via_query`
- [ ] `via mcp serve` exits cleanly on stdin EOF (agent disconnect); watch service shuts down too
- [ ] All protocol events log to stderr only (`-v` flag) — stdout is protocol-only
- [ ] Database path resolved by walking up from cwd to `.via/index.db`
- [ ] If no index found: JSON-RPC error response, **not** crash: `"Index not found — run 'via index .' first"`
- [ ] Resources and prompts capabilities NOT declared (not implemented in Sprint 7)

### Tool Schema for `via_query`

```json
{
  "name": "via_query",
  "description": "Query the VIA codebase index. Pass the same arguments you would use on the CLI (e.g., [\"-mg\", \"*Test*\", \"-tc\"] finds all test classes). Use \"-n 0\" for unlimited results.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "args": {
        "type": "array",
        "items": {"type": "string"},
        "description": "CLI args for via (same syntax as command line, excluding 'via' itself)"
      }
    },
    "required": ["args"]
  }
}
```

### Example JSON-RPC exchanges

```
→ {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"claude-code"}}}
← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"via","version":"0.7.0"}}}

→ {"jsonrpc":"2.0","method":"notifications/initialized"}
  [no response — notification]

→ {"jsonrpc":"2.0","id":2,"method":"tools/list"}
← {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"via_query",...}]}}

→ {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"via_query","arguments":{"args":["-mg","*Parser*","-tc"]}}}
← {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"[{\"symbol_name\":\"PipelineParser\",...}]"}]}}
```

### Implementation Notes

#### New files
- `via/mcp/__init__.py`
- `via/mcp/server.py` — JSON-RPC 2.0 dispatcher + stdio loop
- `via/renderers/json_renderer.py` — new `JsonRenderer` following existing renderer pattern

#### New renderer: `JsonRenderer`
Add `JsonRenderer` to the renderer architecture (`via/renderers/`). It consumes `Iterator[MatchRecord]` and outputs a JSON array string. Registered in `RendererFactory` like all other renderers. This is the output type used when in MCP context.

#### Watch mode + server concurrency
`via mcp serve` must run two loops simultaneously:
- `WatchService` (background thread) — keeps index current
- JSON-RPC stdio loop (main thread) — handles agent requests

When JSON-RPC loop exits (stdin EOF), signal watch service to stop. **Morpheus to confirm threading strategy** — consider whether `WatchService` already supports clean shutdown via event flag.

#### MatchRecord serialization
Add `to_dict() -> dict` to `MatchRecord` in `via/core/match_record.py`. `JsonRenderer` calls this.

#### Subcommand structure in `__main__.py`
```
via mcp serve          # Story 1 — MCP server (watch + JSON-RPC)
via mcp schema         # Story 3 — print tool schema (human inspection only)
via install mcp        # Story 2 — write .mcp.json config
via install <future>   # extensible
via status mcp         # Story 2 — show MCP config status
via status <future>    # extensible (polymorphic status classes)
```

`mcp install/uninstall/status` are **not** standard MCP protocol commands — they are via management commands in a separate namespace. `via mcp` only exposes `serve` and `schema`.

---

## Story 2: MCP Auto-Configuration for Claude Code (P1, 3pts)

**As a developer**, I want `via install mcp` to automatically register via as a Claude Code tool, so I don't have to manually edit `.mcp.json` or `~/.claude.json`.

### Acceptance Criteria

- [ ] `via install mcp` writes/updates `.mcp.json` in the project root (where `.via/` lives) — project scope
- [ ] `via install mcp --global` writes to `~/.claude.json` — user scope (all projects)
- [ ] Generated config registers `via mcp serve` as the MCP server command
- [ ] `via install mcp` is idempotent — safe to run multiple times (updates, doesn't duplicate)
- [ ] `via uninstall mcp` removes the via entry (or deletes file if via was the only entry)
- [ ] `via status mcp` prints which config locations have via registered (project / global / none)
- [ ] `via status mcp` is the polymorphic entry point — future: `via status index`, `via status watch`
- [ ] `via install mcp` prints the config path it wrote on success
- [ ] Existing entries in `.mcp.json` / `~/.claude.json` are preserved — only the via entry is touched
- [ ] `via install mcp` fails with clear error if project root (`.via/`) is not found

### Generated `.mcp.json` format (Claude Code project scope)

```json
{
  "mcpServers": {
    "via": {
      "command": "via",
      "args": ["mcp", "serve"],
      "description": "VIA codebase index — search symbols, query relationships, get stats"
    }
  }
}
```

### Implementation Notes

- Config paths (confirmed from MCP spec research):
  - Project: `.mcp.json` in project root (next to `.via/`)
  - User global: `~/.claude.json` (home root) — **not** `~/.claude/settings.json`
- Project root detection: reuse `find_index_db()` from `via/core/discovery.py`
- JSON parsing: `json` stdlib — no new dependencies
- `via status mcp` reads both `.mcp.json` and `~/.claude.json` for via entry
- `via install` / `via status` / `via uninstall` are new top-level subparsers in `__main__.py`
- Use polymorphic install/status classes so future targets (`via install project`, `via status index`) follow same pattern

---

## Story 3: MCP Tool Schema (P1, 2pts)

**As a developer or agent**, I want `via mcp schema` to print the complete tool schema so I can inspect what queries are available and debug agent interactions.

### Why this is needed

Claude Code learns the schema dynamically from `tools/list` at session startup — `via mcp schema` is **not** required for Claude Code to work. Its value is for:
1. Human inspection — developers can see exactly what Claude Code is seeing
2. Debugging agent interactions — compare schema against what agent actually uses
3. Generating documentation

### Acceptance Criteria

- [ ] `via mcp schema` outputs the same schema that `tools/list` would return — single source of truth
- [ ] Schema documents all flag groups: match, type, output, format, relationship
- [ ] Schema includes enum values for all relationship types and symbol types
- [ ] Schema includes 8+ annotated example invocations covering common use cases
- [ ] Schema is generated programmatically from `flag_groups.py` and `relationship_types.py` — not hardcoded
- [ ] `via mcp schema --format json` (default) and `--format markdown` for human-readable docs
- [ ] Schema is NOT run during `via install mcp` (Claude Code fetches it live via `tools/list`)

### Implementation Notes

- `via/mcp/schema.py` generates schema by reading `MATCH_FLAGS`, `TYPE_FLAGS`, etc. from `flag_groups.py`
- Same schema object used in both `via mcp schema` CLI output and `server.py` `tools/list` response
- `RelationshipType` enum + `SymbolType` enum provide valid enum values

---

## Sprint 7 Summary

| Story | Points | Priority | Description | Blocked? |
|-------|--------|----------|-------------|---------|
| Story 1 | 5 | P0 | MCP server (`via mcp serve`) — watch + JSON-RPC + JsonRenderer | No |
| Story 2 | 3 | P1 | Auto-config (`via install mcp`, `via status mcp`) | No |
| Story 3 | 2 | P1 | Tool schema (`via mcp schema`) — human inspection | Depends on Story 1 |
| **Total** | **10** | | | |

**Recommended order**: Story 1 (serve + renderer) → Story 3 (schema, reuses server schema) → Story 2 (install)

**Morpheus design needed before Story 1**:
- `WatchService` thread + JSON-RPC main thread concurrency strategy
- `JsonRenderer` placement in renderer architecture
- `via install` / `via status` subcommand polymorphism design

---

## Technical Context

### What already exists (confirmed 2026-03-20)

| Item | Location | Note |
|------|----------|------|
| CLI entry + subcommand dispatch | `via/__main__.py:123` | `mcp`, `install`, `status` parsers to add |
| `_run_pipeline_command()` | `via/__main__.py:363` | Query logic — extract and reuse |
| `WatchService` | `via/services/watch.py` | Integrate into `mcp serve` |
| Renderer base | `via/renderers/base.py` | `JsonRenderer` follows this pattern |
| `RendererFactory` | `via/renderers/factory.py` | Register `JsonRenderer` here |
| `flag_groups.py` | `via/core/flag_groups.py` | Schema generation source |
| `RelationshipType` | `via/core/relationship_types.py` | Schema enum source |
| `find_index_db()` | `via/core/discovery.py` | Reuse for project root detection in install |
| Continue.dev reference | `.continue/mcpServers/chat.yaml` | Format reference (already working) |

### What needs to be built

- `via/mcp/__init__.py`, `via/mcp/server.py`, `via/mcp/schema.py`
- `via/renderers/json_renderer.py` — new renderer type
- `MatchRecord.to_dict()` in `via/core/match_record.py`
- `mcp` subparser + `install` subparser + `status` subparser in `via/__main__.py`
- Unit tests: JSON-RPC parsing, JsonRenderer, schema generation, install idempotency
- Integration test: full `via mcp serve` round-trip (stdin→tools/call→stdout)

---

## Resolved Questions

| # | Question | Answer (Drew + research) |
|---|----------|--------------------------|
| 1 | Single tool vs multiple typed tools? | Single `via_query` — use polymorphism internally ✅ |
| 2 | `via mcp serve` error if no index? | Yes — JSON-RPC error with precise message ✅ |
| 3 | Claude Code MCP config path? | Project: `.mcp.json`. Global: `~/.claude.json` (NOT `~/.claude/settings.json`) ✅ confirmed by research |
| 4 | Raw JSON or formatted output? | Raw JSON always ✅ |
| 5 | Handle `resources/list`, `prompts/list`? | No — don't declare those capabilities; skip entirely ✅ |
| 6 | MCP pagination for results? | Not in spec for `tools/call`. Agent sets limit via `args: ["-n", "50"]`. No MCP-level pagination. ✅ |
| 7 | `via mcp serve` implies watch mode? | Yes — always on. Watch starts automatically on server start. ✅ |
