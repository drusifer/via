# Bob Context

**Last Updated**: 2026-04-12

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

## Current State (2026-04-08)
- **Sprint 15**: Planned, implemented, QA'd, and lead-approved across 3 cycles on 2026-04-08
- **Sprint 15 scope shipped**: S15-1 `--slice`, S15-2 MCP output wrapper, S15-3 filepath `--lang` fix, S15-4 markdown declares, S15-5 `-Q` path-glob clarified as docs-only, S15-6 `--help` examples
- **Verification baseline**: `make test` passed at 1235 passed, 1 skipped, 4 warnings
- **Coordination gap**: User requested `*pm close Sprint 15` to Cypher, but Bob/session state had not yet been refreshed
- **State hygiene gap**: Sprint 15 delivery messages landed in CHAT, but several persona state files may still be missing EXIT updates

## Gaps
- State files across all personas are severely out of date. They were not updated during Sprint 14 implementation.
- Sprint 15 appears complete in CHAT, but closure artifacts and persona memory may still lag behind the delivery timeline.
- Need to enforce "EXIT GATE: Save State" rule more strictly.

## Bob Protocol Init (2026-04-12)
- User requested `bob-protocol init`.
- Latest chat context supersedes Bob's 2026-04-08 Sprint 15 state:
  - Sprint 21 closed at 2026-04-12 11:47 with 1259 tests green.
  - User then asked Neo to run all lints and fix errors.
  - Neo reported lint fix complete at 2026-04-12 12:08:56: all 18 C901 complexity errors fixed, 1259 tests green, ready for commit.
  - Morpheus reviewed at 2026-04-12 12:10:29 and approved the changes as non-blocking, ready to commit.
- State hygiene issue: `agents/neo.docs/current_task.md` and `agents/neo.docs/next_steps.md` still contain stale pre-completion C901 resume instructions that conflict with CHAT.md.
- Current protocol resume point: resolve Neo state inconsistency, then proceed with commit/verification workflow if the user requests it.
