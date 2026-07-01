## 2026-06-20T00:36:44Z

Please implement the following requirements:

1. Persona Prompt Optimization:
For each of the following specialist persona instructions:
- `agents/morpheus.docs/SKILL.md`
- `agents/neo.docs/SKILL.md`
- `agents/oracle.docs/SKILL.md`
- `agents/trin.docs/SKILL.md`

Replace the entire `## Via Integration` and `### Relationship Queries` sections (and any other redundant `via` query syntax guides in those files) with a concise reference block that points and defers to the universal `via` skill. The replacement must:
- Explicitly direct the persona to read and follow the universal `via` skill at `agents/skills/via/SKILL.md` (which they can query with `*via` or `*via help`).
- Explicitly forbid direct SQLite DB queries on the `.via/index.db` database.
- Explicitly forbid raw file-reads (like `view_file` or `cat`) when `via` queries can retrieve the same symbol or relationship information.
- Keep the prompts DRY, clean, and free of duplicated query syntax instructions.

2. Run Link Setup:
Run `python agents/tools/setup_agent_links.py` to ensure that all symlinks and persona skill instructions are properly refreshed.

3. Verify:
Verify that the main test suite runs successfully with no regressions (`make test`).

Write a handoff report in your working directory (`/home/drusifer/Projects/via/.agents/worker_prompts/handoff.md`).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
