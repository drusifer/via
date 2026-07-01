# BRIEFING — 2026-06-20T10:24:20Z

## Mission
Refine the universal via skill and specialist agent instructions to use the via tool properly and forbid file-reading/grep fallbacks.

## 🔒 My Identity
- Archetype: Bob (Prompt Engineer)
- Roles: implementer, qa, specialist
- Working directory: /home/drusifer/Projects/via/.agents/worker_bob_prompt1
- Original parent: 1e3c76c2-e7b1-4911-a046-0922e5861c15
- Milestone: Step 4 (Prompt Tuning & Skill Optimization)

## 🔒 Key Constraints
- CODE_ONLY network mode.
- Use make command for automated tasks.
- Adhere to the State Management Protocol.
- Do not cheat, bypass rules, or hardcode verification outputs.

## Current Parent
- Conversation ID: 1e3c76c2-e7b1-4911-a046-0922e5861c15
- Updated: not yet

## Task Summary
- **What to build**: Updated `/home/drusifer/Projects/via/agents/skills/via/SKILL.md` and specialist persona SKILL files with precise directions. Run skill setup and post updates.
- **Success criteria**: All specialist prompts use universal via skill, forbid grep/file-read fallbacks, code-relationship queries are accurate. Link setup runs successfully. Handoff to Trin posted.
- **Interface contracts**: agents/skills/judge/SKILL.md, agents/skills/via/SKILL.md
- **Code layout**: None

## Key Decisions Made
- Updated direction instructions for `declares`, `declared-in`, and `imports` to make them consistent with Neo's fixes to the engine.
- Hardened all specialist persona instructions (`morpheus`, `neo`, `oracle`, `trin`) by explicitly forbidding `view_file` / `cat` / `grep` fallbacks when searching for symbols or tracing code relationships when `via` is enabled.
- Appended handoff message directly to `CHAT.md` when the `make chat` command timed out waiting for user permission.

## Artifact Index
- agents/skills/via/SKILL.md — Universal via query guidelines
- agents/morpheus.docs/SKILL.md — Morpheus persona instructions
- agents/neo.docs/SKILL.md — Neo persona instructions
- agents/oracle.docs/SKILL.md — Oracle persona instructions
- agents/trin.docs/SKILL.md — Trin persona instructions

## Change Tracker
- **Files modified**:
  - `agents/skills/via/SKILL.md` (Updated query directions & fallback rules)
  - `agents/morpheus.docs/SKILL.md` (Added fallback restrictions, referenced universal skill)
  - `agents/neo.docs/SKILL.md` (Added fallback restrictions, referenced universal skill)
  - `agents/oracle.docs/SKILL.md` (Added fallback restrictions, referenced universal skill)
  - `agents/trin.docs/SKILL.md` (Added fallback restrictions, referenced universal skill)
  - `agents/CHAT.md` (Appended handoff message to Trin)
- **Build status**: N/A (no code changes, only prompts/skills)
- **Pending issues**: None

## Quality Status
- **Build/test result**: N/A (no code changes)
- **Lint status**: N/A
- **Tests added/modified**: None

## Loaded Skills
- None
