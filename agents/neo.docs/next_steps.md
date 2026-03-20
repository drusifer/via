**Next Steps for Neo**:

## Sprint 6 TD Items (for Sprint 7 cleanup)
1. `DatabaseStore.delete_file_completely(path)` — encapsulate deletion triad
2. `IndexingService.reindex_file(path)` — public method with begin/commit_transaction
3. Clean up watch.py: move lazy imports, fix private _should_include_file call, remove IOBase

## Sprint 7 - MCP Mode (next up)
- Spec: `agents/cypher.docs/SPRINT_7_USER_STORIES.md`
- User story review in progress — await Cypher/Drew sign-off before starting
- `via/mcp/server.py` — JSON-RPC 2.0 over stdio
- `via/mcp/schema.py` — tool schema generator
- `via mcp install` — Claude Code auto-config

## Sprint 8 - Line Index
- Spec: `agents/cypher.docs/SPRINT_8_USER_STORIES.md`
- `-mL` match type + slice syntax
- line_offsets table in DB schema
