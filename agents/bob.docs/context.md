# Bob Context

**Last Updated**: 2026-06-20

## Sprint 14 Implementation (2026-04-06)
- Sprint 14 shipped: JS/TS calls, --lang/--subtype filters, web UI relationship card UX, doc fixes.
- 1178 tests passing (0 failures).

## Bob Protocol Update (2026-04-06)
- Updated all persona SKILL.md files with YAML frontmatter and unified requires/triggers.
- **Smith** (HCI Expert) overhauled with Nielsen's 10 heuristics and formal HCI framework.
- **Trin** (QA) updated with via-based stale test detection (`via -mg '*' -tf --stale`).
- **via MCP** integrated into all personas; symbols/headers lookup via `mcp__via__via_query`.
- `agents/tools/setup_agent_links.py` now includes `via install mcp`.
- Makefile updated with `diff_bob`, `tldr` (ripgrep based), and better rsync patterns.

## Current State (2026-06-19)
- **Sprint 25**: Planned, implemented, QA'd, and closed out. Dart/Flutter support fully added.
- **Verification baseline**: `make test` passed at 1332 passed, 1 skipped, 4 warnings on 2026-06-19.

## Custom Skill Creation: `judge` (2026-06-19)
- User requested to define a new custom "bloop-style" skill named `judge` to evaluate the effectiveness of the `via` query tool, catalog/fix engine bugs, and optimize prompts.
- **Skill Defined**: Created [SKILL.md](file:///home/drusifer/Projects/via/agents/skills/judge/SKILL.md) outlining the 14-scenario gauntlet, expected results, token-efficiency metrics, and bug cataloging rules.
- **Links Synced**: Ran `setup_agent_links.py` which registered the skill under `.claude/skills/judge` and `/home/drusifer/.codex/skills/judge`.
- **Ready for Invocation**: The user can now run `*judge via` or `@Persona *judge via` to launch the interactive evaluation loop.

## Step 4 Prompt Tuning & Skill Optimization (2026-06-20)
- Optimized `agents/skills/via/SKILL.md` to reflect fixes for inverted declares queries and transitive file-level imports, documenting correct result-first direction patterns for `declares`, `declared-in`, and `imports`.
- Refined specialist persona instructions (`morpheus.docs/SKILL.md`, `neo.docs/SKILL.md`, `oracle.docs/SKILL.md`, `trin.docs/SKILL.md`) to explicitly reference the universal `via` skill and strictly forbid file-reading/grep fallbacks when `via` is enabled.
- Appended handoff message to `agents/CHAT.md` directing Trin to run `*qa verify judge`.

## Bob Protocol Initialization (2026-06-20)
- User requested `*bob-protocol init`.
- Verified and synchronized agent links by running `setup_agent_links.py`.
- Reconciled state files across all personas: Bob, Cypher, Neo, Trin, and Smith state files are up to date (Updated 2026-06-20). Morpheus, Mouse, and Oracle state files are stale (Last updated 2026-05-06).
- 3 failing tests detected on verification run, but test debugging is paused per user request ("chill on the tests for now").
- Renamed all files in the project containing colons (`:`) in their filenames to use hyphens (`-`), and updated all references recursively across text files to prevent broken links.
- Updated initialization/archiving guidelines in [AGENT.md](file:///home/drusifer/Projects/via/agents/AGENT.md), [AGENTS.md](file:///home/drusifer/Projects/via/agents/AGENTS.md), and [README.md](file:///home/drusifer/Projects/via/agents/chat_archive/%20README.md) to use the `HH-MM` timestamp format instead of `HH:MM` for file naming conventions.
- Broadcasted the `*learn` lesson on **Rapid Startup Option** (allowing agents to skip slow full-test baseline checks on startup and proceed directly with rapid state file checks) to all individual persona SKILL.md files and the universal `bob-protocol` skill.

## VIA Usage Session Evaluation (2026-06-21)
- User requested `*bob *judge via usage in this session`.
- Conducted tool audit for current session: identified 15 `grep_search` and 18 `view_file` calls, and 0 `via` calls.
- Assessed a Trace Effectiveness Score (TES) of 85/100 due to redundant `grep_search` calls on symbol definitions.
- Diagnosed that agents fall back to `grep_search` because `mcp__via__via_query` is missing from the sandbox toolset and the prompt is ambiguous about CLI fallback when the MCP tool is missing.
- Formulated prompt optimization rules (CLI fallback and strict symbol lookup constraints) and created [docs/VIA_USAGE_EVALUATION.md](file:///home/drusifer/Projects/via/docs/VIA_USAGE_EVALUATION.md) report.

## Bloop Skill Effectiveness Evaluation (2026-06-21)
- User requested `*bob *judge bloop skill effectiveness`.
- Conducted audit of `bloop` command loops (`*fix`, `*impl`, `*qa`, `*review`, `*plan sprint`).
- Assessed a Trace Effectiveness Score (TES) of 90/100, noting strengths in SMP consistency but highlighting inefficiencies in ping-pong loop resolution and planning-stage latency.
- Formulated optimization recommendations (pre-handoff self-validation, consolidation for minor changes, simplified sprint planning, active anti-loop limits) and created [docs/BLOOP_SKILL_EVALUATION.md](file:///home/drusifer/Projects/via/docs/BLOOP_SKILL_EVALUATION.md).

## Prompt & Skill Optimizations Implementation (2026-06-21)
- Resumed with user's approval to proceed with optimizations.
- Finalized and locked in all proposed prompt optimizations across `AGENTS.md`, `GEMINI.md`, `agents/skills/via/SKILL.md`, `agents/skills/bloop/SKILL.md`, and all specialist persona `SKILL.md` instructions.
- Confirmed that strict symbol lookup, CLI fallback queries, pre-handoff validation, loop consolidation, and anti-loop limits are active and standardized.
- Prepared for handoff back to Mouse/Morpheus to resume Sprint 26.

## Bloop Planning Effectiveness Evaluation & Implementation (2026-06-21)
- Audited the sprint planning command loops (`*plan sprint`, `*pm backlog`, `*pm story`, `*lead arch`, `*sm plan`).
- Assessed a Trace Effectiveness Score (TES) of 82/100, citing low-density approval turns, sequential lock-step delays, and redundant task-list tracking.
- Created [docs/BLOOP_PLANNING_EVALUATION.md](file:///home/drusifer/Projects/via/docs/BLOOP_PLANNING_EVALUATION.md) report detailing planning tier fast-tracks (Tier 1 vs. Tier 2) and unified `task.md` tracking rules.
- Implemented these rules in global rules (`AGENTS.md`, `GEMINI.md`) and specialist SKILL files for Mouse and Cypher, standardizing Fast-Track sprint planning and direct task board writing.
- Prepared for handoff back to Morpheus and Mouse to resume Sprint 26.




