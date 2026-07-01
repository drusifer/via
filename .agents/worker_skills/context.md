# Context - Skill Alignment and Creation

## Key Decisions
- Adjusted custom triggers for the `judge` skill in `agents/skills/judge/SKILL.md` to match the exact requirement: `*judge "via usage"`, `*judge via usage`, and `*judge via`.
- Created a new universal custom skill `via` at `agents/skills/via/SKILL.md` that instructs on proper directionality (`subject` on left, `relationship` in middle, `object` on right), qualified matching (`-Q`/`--qualified`), and explicitly prohibits direct SQLite database queries or raw file-reading for relationship discovery.
- Executed `setup_agent_links.py` to regenerate symlinks for both Claude skills (`.claude/skills/`) and Codex skills (`~/.codex/skills/`), registering the new and updated skills.

## Findings
- The setup links script successfully registered 13 shared skills (including `via` and `judge`).
- The project test suite is clean and passing (`1333 passed, 1 skipped`).
