# Scope: Closed-loop Judge Workflow

## Architecture
- Workflows involve coordinating persona states: Trin (QA), Smith (HCI/UX), Neo (SWE), Bob (Prompts).
- Data Flow: via CLI tool / index database -> Trin (via_gauntlet_trace.log) -> Smith (trace_eval.md, bugs.md) -> Neo (code fix, verify via make test) -> Bob (SKILL.md update) -> Trin (re-run).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Gauntlet Run 1 | Trin runs 14 gauntlet scenarios, outputs trace log | none | DONE (6a5cb982) |
| 2 | Scoring & Bug Cataloging 1 | Smith parses trace, computes TES, logs bugs | M1 | DONE (c6ee4221) |
| 3 | Bug Fixes 1 | Neo resolves codebase bugs, runs tests | M2 | DONE (bc97e7f3) |
| 4 | Prompt Tuning 1 | Bob refines skill guidelines and persona instructions | M3 | DONE (7984fe42) |
| 5 | Gauntlet Run 2 | Trin runs 14 gauntlet scenarios, outputs trace log | M4 | DONE (45aef610) |
| 6 | Scoring & Bug Cataloging 2 | Smith parses trace, computes TES, logs bugs | M5 | IN_PROGRESS (6e688a87) |
| 7 | Walkthrough Report | Compile score history and findings walkthrough | M1-M6 | PLANNED |
