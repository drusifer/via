# BRIEFING — 2026-06-20T00:31:06Z

## Mission
Align skill triggers for custom `judge` skill, implement universal `via` skill, and register them via setup_agent_links.py.

## 🔒 My Identity
- Archetype: implementer/qa/specialist
- Roles: implementer, qa, specialist
- Working directory: /home/drusifer/Projects/via/.agents/worker_skills
- Original parent: 5771a298-c2c7-4b49-a154-0ee693c95d95
- Milestone: Custom Skills Alignment

## 🔒 Key Constraints
- CODE_ONLY network mode (no external network/HTTP requests).
- No cheating or dummy implementations. All changes must be genuine.
- Use Makefile for tasks where applicable.

## Current Parent
- Conversation ID: 5771a298-c2c7-4b49-a154-0ee693c95d95
- Updated: not yet

## Task Summary
- **What to build**: 
  1. Modify `agents/skills/judge/SKILL.md` triggers to: `*judge "via usage"`, `*judge via usage`, and `*judge via`.
  2. Create a new universal skill at `agents/skills/via/SKILL.md` specifying efficiency guidelines for `via` queries.
  3. Register skills by running `python agents/tools/setup_agent_links.py`.
- **Success criteria**: Triggers modified, new skill created with exact content, link setup script executes successfully, all tests pass.
- **Interface contracts**: Custom skill structures in `agents/skills/`
- **Code layout**: `agents/skills/<skill_name>/SKILL.md`

## Key Decisions Made
- Created new custom skill `via` at `agents/skills/via/SKILL.md` with guidelines on directionality, qualified names, and forbidden direct SQL/raw file reads.
- Configured custom triggers for `judge` skill at `agents/skills/judge/SKILL.md`.

## Artifact Index
- `agents/skills/via/SKILL.md` — Universal custom skill for via query guidelines
- `agents/skills/judge/SKILL.md` — Aligned custom judge skill

## Change Tracker
- **Files modified**: 
  - `agents/skills/judge/SKILL.md`: Modified triggers list in YAML frontmatter.
  - `agents/skills/via/SKILL.md`: Created new file with frontmatter and guidelines content.
- **Build status**: pass (1333 passed, 1 skipped)
- **Pending issues**: None

## Quality Status
- **Build/test result**: pass (1333 passed, 1 skipped)
- **Lint status**: clean
- **Tests added/modified**: None (no code changes required tests)

## Loaded Skills
- **Source**: none loaded yet
- **Local copy**: TBD
- **Core methodology**: TBD
