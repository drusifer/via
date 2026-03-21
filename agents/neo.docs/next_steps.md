# Neo Next Steps

## Resume Point: Sprint 9 — Has-A Relationship (`-Vhas`) + Incremental prep_tldr

Sprint 8 SHIPPED (2026-03-21). 837 tests passing. Sprint 9 is next.

### Before Starting Sprint 9
1. Read `agents/cypher.docs/SPRINT_9_USER_STORIES.md` for stories
2. Ask Morpheus for architecture review
3. TDD: write tests first, see red, implement, see green

### Tech Debt to pick up (TD-WATCH-1)
Extract `PathFilter` from `FileDiscovery` — WatchService currently calls private `_should_include_dir()`. Low urgency.

### Remaining Tech Debt (low priority)
- TD-3: Move lazy `from via.core.discovery import DiscoveredFile` in `watch.py._reindex_file` to module level
- TD-4: Make `FileDiscovery._should_include_file` public
- TD-S7-1: Async queue for DB if concurrent writers added (Sprint 8+)
- TD-S7-2: Evaluate lighter MCP transport (Sprint 8+)

### Key Sprint 7 Files Added
- `via/renderers/json_renderer.py` — JsonRenderer + _to_dict()
- `via/mcp/__init__.py`, `via/mcp/schema.py`, `via/mcp/server.py`
- `via/commands/install.py` — McpInstallTarget + INSTALL_TARGETS
- `tests/unit/test_json_renderer.py`, `test_sprint7_p2-p6.py`
- `tests/uat/test_sprint7_uat.py`

### Sprint 7 CLI Commands Added
- `via mcp schema` → prints via_query tool schema as JSON
- `via mcp serve [dir]` → starts FastMCP stdio server
- `via install mcp [--global]` → writes .mcp.json
- `via uninstall mcp [--global]` → removes .mcp.json entry
- `via status mcp` → shows install state
