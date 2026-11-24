# Agent State

Keep this working-memory file current. Preserve exactly these three top-level sections; see the
State Management Protocol in `.agents/skills/bob-protocol/SKILL.md` for entry and exit steps.

## Context
- **Recent decisions:** Ran `bobp update .` to migrate workspace from legacy `agents/<name>.docs/` and `.claude/skills/` layout to `.agents/skills/` (35 skills added, 10 personas including Switch), `AGENTS.md` at project root, single `state.md` per persona, and `bobp` CLI tools (`bobp chat`, `bobp make`, `bobp setup-agent-links`).
- **Key findings:** `via` is enabled in `agents/PROJECT.md` and `.via/index.db` + `.mcp.json` are configured. `task.md` shows Sprint 27 Phase 2 Cycle 1 closed and Cycle 2 (mocking-usage signal) not started; latest git commit is `22cd9ed` (2026-10-21, Makefile consolidation).
- **Important notes:** Always use `bobp chat` and `bobp make` (never bare `make` or removed `agents/tools/chat.py`). Rapid startup honored — no unrequested test runs.

## Current Task
- **Status:** Complete
- **Assigned to:** Bob
- **Started:** 2026-11-23
- **Description:** Initialize Bob Protocol session, run `bobp update .`, reload updated skills, and complete fresh-session startup greeting.
- **Progress:** Completed `bobp update .`, reloaded core and persona skills from `.agents/skills/`, updated `agents/bob/state.md`, announced readiness, and ran start-of-day team check-in.
- **Blockers:** None
- **Consultations:** All 10 personas checked in via start-of-day greeting in `agents/CHAT.md`.

## Next Steps
- **Immediate next action:** Wait for explicit user direction (e.g., Sprint 27 Phase 2 Cycle 2, a new `*plan sprint` / `*impl` / `*fix` loop, or reviewing/committing the `bobp update .` migration diff).
- **Waiting on:** User direction
- **Planned work:** Route next user command to the appropriate persona or Bloop work-loop.

---
*Last updated: 2026-11-23*
