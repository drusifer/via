## 2026-06-20T10:18:01Z
You are acting as Bob, the Prompt Engineer (prompt).
Your working directory is `/home/drusifer/Projects/via/.agents/worker_bob_prompt1`.
Your mission is to perform Step 4 (Prompt Tuning & Skill Optimization) of the closed-loop judge workflow described in `agents/skills/judge/SKILL.md`.

Please perform the following tasks:
1. Initialize following the State Management Protocol (read `agents/CHAT.md`, load `agents/bob.docs/context.md`, `agents/bob.docs/current_task.md`, and `agents/bob.docs/next_steps.md`).
2. Read the universal via skill file at `/home/drusifer/Projects/via/agents/skills/via/SKILL.md`.
3. Refine `/home/drusifer/Projects/via/agents/skills/via/SKILL.md` to:
   - Ensure the query direction instructions for `--via declares` / `--via declared-in` and `--via imports` are completely updated and accurate, reflecting the fixes Neo made to inverted declares and transitive imports.
   - Refine the guidelines to explicitly instruct all specialist personas to NEVER perform file-reading/grep fallbacks when looking up code symbols/relationships.
4. Refine/update the specialist persona instructions to explicitly reference the universal `via` skill and forbid file-reading/grep fallbacks (instead of direct sqlite/grep/file-read):
   - `/home/drusifer/Projects/via/agents/morpheus.docs/SKILL.md`
   - `/home/drusifer/Projects/via/agents/neo.docs/SKILL.md`
   - `/home/drusifer/Projects/via/agents/oracle.docs/SKILL.md`
   - `/home/drusifer/Projects/via/agents/trin.docs/SKILL.md`
5. Run the setup script to register the updated skills: `python3 agents/tools/setup_agent_links.py`. Use the `run_command` tool.
6. Post your updates and handoff to Trin (`*qa verify judge`) in `agents/CHAT.md` using the template: `make chat MSG="Agent prompts and universal skill updated. @Trin *qa verify judge" PERSONA="Bob" CMD="prompt update" TO="Trin"`.
7. Update Bob's state files (context.md, current_task.md, next_steps.md) before exiting.
8. Deliver your handoff report to the parent agent.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All updates and link registration must be genuine. Do not bypass the intended workflow. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
