# MCP 2 Documentation Groom Summary

**Date:** 2026-08-06
**Persona:** Oracle
**Scope:** Documentation-only follow-up to the FastMCP → MCPServer migration

## Outcome

- Updated `README.md` to document `MCPServer`, `mcp>=2.0`, Python 3.10+,
  and both MCP tools (`via_query` and `via_ask`).
- Updated `docs/specs/integrations.md` with the MCP SDK 2.x runtime model,
  both tool interfaces, and clearer schema-command scope.
- Updated `docs/specs/installation_and_indexing.md` with the supported Python
  and MCP floors; also corrected the broken `python -tm venv` command to
  `python -m venv`.
- Added supersession notices to the Sprint 7 and Sprint 12 consolidated docs.
  Their FastMCP examples remain intact as historical records, but now point
  readers to the maintained integration guide.
- Added the MCP 2 migration to `CHANGELOG.md` and separated the previously
  released Sprint 12 section from the active Unreleased section.

## Audit Notes

- No stale FastMCP, MCP 1.x, or Python 3.9 runtime claims remain in maintained
  user-facing docs. Remaining matches are explicitly labeled historical sprint
  records or Python feature-history statements in Sprint 3.
- Root markdown remains limited to expected project/tool discovery files; no
  new orphan relocation was warranted.
- `make via ARGS=...` is currently shadowed and reports "Nothing to be done".
  `make -f Makefile.prj via ARGS=...` successfully provides the required VIA
  CLI fallback. This is an automation defect for a future Makefile task.

## Validation

- `git diff --check`: passed.
- Targeted stale-claim sweep: passed for maintained docs.
- No tests run: documentation-only changes, consistent with bounded testing.
