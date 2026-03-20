# Neo Next Steps

## Resume Point: Sprint 8 — Line Index (`-mL`)

Sprint 7 is SHIPPED (2026-03-20). 794 tests passing.

### Before Starting Sprint 8
1. Read `agents/mouse.docs/context.md` for sprint status
2. Read `agents/cypher.docs/SPRINT_8_USER_STORIES.md` for stories
3. Ask Morpheus for architecture review (`@Morpheus *lead arch Sprint 8`)
4. TDD: write tests first, see red, implement, see green

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
