# Bob Context

**Last Updated**: 2026-04-06

## Sprint 14 Implementation (2026-04-06)
- Sprint 14 shipped: JS/TS calls, --lang/--subtype filters, web UI relationship card UX, doc fixes.
- 1178 tests passing (0 failures).

## Bob Protocol Update (2026-04-06)
- Updated all persona SKILL.md files with YAML frontmatter and unified requires/triggers.
- **Smith** (HCI Expert) overhauled with Nielsen's 10 heuristics and formal HCI framework.
- **Trin** (QA) updated with via-based stale test detection (`via -mg '*' -tf --stale`).
- **via MCP** integrated into all personas; symbols/headers lookup via `mcp__via__via_query`.
- `agents/tools/setup_agent_links.py` now includes `via install mcp`.
- Makefile updated with `diff_bob`, `tldr` (ripgrep based), and better rsync patterns.

## Gaps
- State files across all personas are severely out of date. They were not updated during Sprint 14 implementation.
- Need to enforce "EXIT GATE: Save State" rule more strictly.
