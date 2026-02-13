# Sprint 7 - MCP Integration

**Author**: Cypher (PM)
**Date**: 2026-02-11
**Theme**: AI Agent Protocol Support
**Points**: 10

---

## Epic: MCP Mode (`via --mcp`)

Make `via` a first-class tool for AI agents. In MCP mode, `via` acts as a Model Context Protocol server, accepting the same query syntax but over JSON/MCP protocol instead of stdout. It should auto-configure itself into agent tool discovery paths.

### Decisions (Drew, 2026-02-11)

| Decision | Answer |
|----------|--------|
| Transport | stdio (JSON-RPC 2.0) |
| Target agents | Claude Code, Gemini, ChatGPT |

---

### Story 1: MCP Server Mode (P0, 5pts)

**As an AI agent developer**, I want to run `via` as an MCP server so that Claude, Gemini, and ChatGPT agents can query the codebase index programmatically.

**Acceptance Criteria**:
- [ ] `via --mcp` starts an MCP-compatible server (stdio transport)
- [ ] Accepts the same query syntax as CLI (e.g., `-mg '*' -tc`, `-Vinh`, etc.)
- [ ] Returns results as structured JSON instead of terminal output
- [ ] Supports all existing query types: match, relationship, stats
- [ ] JSON output includes: symbol name, type, file path, line number, byte offset, qualified name
- [ ] Error responses are structured JSON with error type and message

**Notes**:
- MCP uses JSON-RPC 2.0 over stdio
- Tool definitions map to via's pipeline syntax
- Same query engine, different I/O layer

---

### Story 2: MCP Auto-Configuration (P1, 3pts)

**As a developer**, I want `via` to automatically register itself as an available tool for my AI coding assistants, so I don't have to manually configure each one.

**Acceptance Criteria**:
- [ ] `via mcp install` generates a tool spec and deploys it to standard locations
- [ ] Claude Code: Creates/updates entry in `~/.claude/` MCP config (or project `.mcp.json`)
- [DEFERRED] Gemini: Creates config in `.gemini/` or appropriate location
- [DEFERRED] ChatGPT: Creates config in appropriate location
- [ ] Tool spec includes: tool name, description, parameter schema, and example invocations
- [ ] `via mcp uninstall` removes the tool configuration
- [ ] `via mcp status` shows which agents have via configured

**Notes**:
- Continue.dev integration already exists as reference (`.continue/mcpServers/chat.yaml`)
- Each agent has its own config format - need to generate per-agent specs
- Should be idempotent (safe to run multiple times)
- **UPDATE (2026-02-13)**: Gemini/ChatGPT auto-config deferred to backlog per Drew. Focus on Claude Code only.

---

### Story 3: MCP Tool Schema (P1, 2pts)

**As an AI agent**, I want a well-defined tool schema so I can understand what queries are available and construct them correctly.

**Acceptance Criteria**:
- [ ] Tool schema defines available operations: `search`, `relationships`, `stats`, `index`
- [ ] Each operation has typed parameters matching CLI flags
- [ ] Schema includes enum values for relationship types, symbol types, output formats
- [ ] Schema includes example invocations with expected output shapes
- [ ] `via mcp schema` outputs the tool schema as JSON

---

## Sprint 7 Summary

| Story | Points | Priority | Description |
|-------|--------|----------|-------------|
| Story 1 | 5 | P0 | MCP server mode (stdio JSON-RPC) |
| Story 2 | 3 | P1 | Auto-config for Claude/Gemini/ChatGPT |
| Story 3 | 2 | P1 | Tool schema generation |
| **Total** | **10** | | |

---

## Technical Context

**What already exists**:
- Continue.dev MCP config as reference (`.continue/mcpServers/chat.yaml`)
- `PipelineParser` and `PipelineExecutor` handle query parsing/execution
- All query types have structured internal representations

**What needs to be built**:
- `via/mcp/server.py` - MCP server with JSON-RPC 2.0 over stdio
- `via/mcp/schema.py` - Tool schema generator from flag groups
- `via mcp install` - Agent config deployer (Claude, Gemini, ChatGPT)
- JSON serialization layer for match results
