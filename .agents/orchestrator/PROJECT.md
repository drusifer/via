# Project: VIA Custom Judge Skill Workflow Execution

## Architecture
- **Skill Trigger Alignment (`agents/skills/judge/SKILL.md`)**: Align triggers to `*judge "via usage"`, `*judge via usage`, and `*judge via`.
- **Universal via Skill (`agents/skills/via/SKILL.md`)**: A new universal skill outlining guidelines for writing efficient `via` relationship queries.
- **Session Trace Tool (`agents/tools/session_trace.py`)**: A Python utility to read the Antigravity session transcript (`transcript.jsonl` or `transcript_full.jsonl` under the app data brain directory), extract chronological sequences of `via` tool queries, and format them.
- **Persona Prompt Optimization**: Defer syntax instructions in Morpheus, Neo, Oracle, and Trin prompts to the universal `via` skill and forbid direct SQLite queries.
- **Verification Walkthrough**: Validate updated instructions via Trin with 3 new scenarios, output the trace report, and verify that the main test suite runs successfully with no regressions.

## Code Layout
- `agents/skills/judge/SKILL.md` — Updated judge skill triggers.
- `agents/skills/via/SKILL.md` — Universal via skill definition.
- `agents/tools/session_trace.py` — Session transcript trace parser.
- `agents/morpheus.docs/SKILL.md` — Updated Tech Lead prompt.
- `agents/neo.docs/SKILL.md` — Updated SWE prompt.
- `agents/oracle.docs/SKILL.md` — Updated Knowledge Officer prompt.
- `agents/trin.docs/SKILL.md` — Updated QA prompt.
- `setup_agent_links.py` — Tool to register skills (run via worker).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Skill Triggers & Universal via | Align `judge` triggers, create universal `via` skill, run setup | none | DONE |
| 2 | Session Trace Tool | Create `session_trace.py` tool to parse JSONL transcripts | M1 | DONE |
| 3 | Persona Prompt Optimization | Update Morpheus, Neo, Oracle, Trin skill instructions | M1 | DONE |
| 4 | Verification & Forensic Audit | Run 3 scenarios, run session trace, verify 1339 tests pass, run auditor | M2, M3 | PLANNED |
