## 2026-06-20T00:26:36Z
Please implement the following requirements:

1. Skill Trigger Alignment:
Modify the triggers in the custom `judge` skill definition (`agents/skills/judge/SKILL.md`) to be exactly: `*judge "via usage"`, `*judge via usage`, and `*judge via`. Make sure to update the triggers list in the YAML frontmatter.

2. Universal via Skill:
Create a new universal customization skill `via` at `agents/skills/via/SKILL.md`. The frontmatter should be:
```yaml
---
name: via
description: Guidelines for writing efficient via relationship queries.
triggers: ["*via", "*via help", "*via query"]
requires: ["bob-protocol", "chat", "make"]
---
```
And the content must outline general guidelines for writing efficient `via` relationship queries, specifically:
- Declare direction properly (e.g. subject on left, relationship, object on right).
- Use qualified matching with `-Q` / `--qualified`.
- Explicitly forbid direct SQLite DB queries and raw file-reads.

3. Run Link Setup:
Run `python agents/tools/setup_agent_links.py` from the project root to ensure these skills are registered and discoverable.

Verify all changes are correct, compilation/syntax is clean, and the setup script executes successfully. Write a handoff report in your working directory (/home/drusifer/Projects/via/.agents/worker_skills/handoff.md).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
