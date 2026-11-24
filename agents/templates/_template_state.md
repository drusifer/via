# Agent State

Keep this working-memory file current. Preserve exactly these three top-level sections; see the
State Management Protocol in `.agents/skills/bob-protocol/SKILL.md` for entry and exit steps.

## Context
- **Recent decisions:** {decision and reason, or None}
- **Key findings:** {finding and why it matters, or None}
- **Important notes:** {relevant durable context, or None}

## Current Task
- **Status:** {Not started | In progress | Waiting | Complete}
- **Assigned to:** {persona}
- **Started:** {YYYY-MM-DD or N/A}
- **Description:** {one-sentence task, or No active task}
- **Progress:** {completed work and remaining work}
- **Blockers:** {blocker and needed action, or None}
- **Consultations:** {persona and outcome, or None}

## Next Steps
- **Immediate next action:** {one concrete action, or None}
- **Waiting on:** {person/event, or None}
- **Planned work:** {ordered actions, or None}

---
*Last updated: {YYYY-MM-DD}*

<!-- RUBRIC-START -->
## Check — STATE

- [ ] **PASS** — The file has exactly the required Context, Current Task, and Next Steps sections.
- [ ] **PASS** — Status, update date, and next action (or explicit None) reflect the current work state.
- [ ] **PASS** — Blockers and waiting dependencies are named, or explicitly marked None.
- [ ] **FAIL** — A required section is absent, stale, or leaves current work/next action ambiguous; update it before handoff.
<!-- RUBRIC-END -->
