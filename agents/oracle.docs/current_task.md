# Oracle Current Task

**Task:** `*oracle groom docs` — MCP 2 migration follow-up
**Status:** COMPLETE (100%)
**Updated:** 2026-08-06

## Completed

- [x] Reconciled maintained docs with `MCPServer`, `mcp>=2.0`, and Python
      3.10+.
- [x] Documented both MCP tools: `via_query` and `via_ask`.
- [x] Marked FastMCP content in Sprint 7/12 as historical rather than
      rewriting point-in-time sprint records.
- [x] Added MCP 2 migration to the changelog.
- [x] Corrected invalid installation command `python -tm venv`.
- [x] Audited root markdown and stale MCP/Python claims.
- [x] Validated documentation diffs with `git diff --check`.

## Deferred

- Public `make via ARGS=...` is shadowed/no-op; the explicit
  `make -f Makefile.prj via ARGS=...` target works. Requires a future
  Makefile implementation task, not a documentation edit.

## Detailed Record

See `MCP2_DOC_GROOM_Summary_2026-08-06T17-33.md`.
