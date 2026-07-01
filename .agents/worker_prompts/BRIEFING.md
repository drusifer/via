# BRIEFING — 2026-06-20T00:36:44Z

## Mission
Optimize specialist persona prompts by referencing the universal via skill and forbidding direct db queries or raw file-reads when via can be used, run the setup tool to update links, and verify correctness.

## 🔒 My Identity
- Archetype: implementer, qa, specialist
- Roles: implementer, qa, specialist
- Working directory: /home/drusifer/Projects/via/.agents/worker_prompts
- Original parent: 5771a298-c2c7-4b49-a154-0ee693c95d95
- Milestone: Persona Prompt Optimization

## 🔒 Key Constraints
- Explicitly direct the persona to read and follow the universal via skill at agents/skills/via/SKILL.md.
- Explicitly forbid direct SQLite DB queries on the .via/index.db database.
- Explicitly forbid raw file-reads when via queries can retrieve the same symbol or relationship information.
- Keep prompts DRY, clean, and free of duplicated query syntax instructions.
- Ensure all symlinks and persona skill instructions are properly refreshed.
- Verify that the main test suite runs successfully with no regressions (make test).

## Current Parent
- Conversation ID: 5771a298-c2c7-4b49-a154-0ee693c95d95
- Updated: not yet

## Task Summary
- **What to build**: Persona prompt optimization and symlink setup refresh.
- **Success criteria**:
  - SKILL.md of morpheus, neo, oracle, trin optimized.
  - Links refreshed via setup_agent_links.py.
  - Main test suite runs successfully with make test.
- **Interface contracts**: agents/PROJECT.md
- **Code layout**: agents/tools/setup_agent_links.py

## Key Decisions Made
- Replace duplicated `## Via Integration` and `### Relationship Queries` sections in morpheus, neo, oracle, and trin's SKILL.md with a DRY reference block.
- Corrected status extraction logic bug in `agents/tools/session_trace.py` that caused a unit test failure where status/exit code of `0` was falsy and fell back to `None`.

## Artifact Index
- /home/drusifer/Projects/via/.agents/worker_prompts/handoff.md — Final handoff report

## Change Tracker
- **Files modified**:
  - agents/morpheus.docs/SKILL.md (Optimized via section)
  - agents/neo.docs/SKILL.md (Optimized via section)
  - agents/oracle.docs/SKILL.md (Optimized via section)
  - agents/trin.docs/SKILL.md (Optimized via section)
  - agents/tools/session_trace.py (Fixed exit status extraction bug)
- **Build status**: PASS
- **Pending issues**: None

## Quality Status
- **Build/test result**: PASS (1339 passed, 1 skipped)
- **Lint status**: PASS
- **Tests added/modified**: None (verified using pre-existing test suite)

## Loaded Skills
- **Source**: antigravity-guide
- **Local copy**: /home/drusifer/Projects/via/.agents/worker_prompts/antigravity_guide/SKILL.md
- **Core methodology**: Provides a comprehensive guide, quick reference, and sitemap for Google Antigravity (AGY).
