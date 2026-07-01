# Original User Request

## 2026-06-20T00:12:18Z

An automated verification and evaluation harness for the custom 'judge' skill to test agent query efficiency and identify file-reading fallbacks across scenarios.

Working directory: /home/drusifer/Projects/via
Integrity mode: development

## Requirements

### R1. Standalone Evaluation Harness
Implement a standalone evaluation script that runs the 14 gauntlet scenarios against the `via` command-line tool. The script should run each query and verify the output.

### R2. Query Trace & Fallback Audit
The script must audit the execution trace of each query to check for token efficiency, specifically checking if any queries fell back to raw file reading or pattern grepping.

### R3. Markdown Reporting
The script must compile the evaluation results into a clean, markdown-formatted report containing a summary table with token and efficiency metrics for each scenario.

### R4. Makefile Automation
Expose a Makefile target `via-eval` that activates the project virtual environment, executes the harness, and prints the report to the console.

## Acceptance Criteria

### Execution & Integration
- [ ] A python evaluation script is added under `scripts/`
- [ ] A Makefile target `via-eval` is added to run the harness
- [ ] Executing `make via-eval` runs all 14 gauntlet scenarios and prints the markdown table to stdout
- [ ] The harness runs successfully without any errors or crashes

## Follow-up — 2026-06-20T00:24:13Z

Carry out the rest of the 'judge' custom skill workflow: align skill triggers, create a universal 'via' skill, optimize specialist persona prompts for query efficiency, build a session trace tool for auditing, and execute the verification loop.

Working directory: /home/drusifer/Projects/via
Integrity mode: development

## Requirements

### R1. Skill Trigger Alignment
Align the custom `judge` skill definition (`agents/skills/judge/SKILL.md`) to triggers: `*judge "via usage"`, `*judge via usage`, and `*judge via` using the pre-populated instructions. Run `setup_agent_links.py` to ensure it is registered and discoverable.

### R2. Universal via Skill
Create a new universal customization skill `via` (`agents/skills/via/SKILL.md`) with triggers `*via`, `*via help`, and `*via query`. This skill must contain all general, non-role-specific guidelines for writing efficient `via` relationship queries (declares direction, qualified matching with `-Q`, and avoiding direct SQLite DB queries and file-reads).

### R3. Session Trace Tool
Implement a Python utility script `agents/tools/session_trace.py` that reads the Antigravity session transcript (`transcript.jsonl` or `transcript_full.jsonl` under the app data brain directory), extracts the chronological sequences of `via` tool queries executed by the agent, and prints a formatted summary. This tool will allow the learn skill to audit traces reliably.

### R4. Persona Prompt Optimization
Update all specialist persona instructions (`agents/morpheus.docs/SKILL.md`, `agents/neo.docs/SKILL.md`, `agents/oracle.docs/SKILL.md`, `agents/trin.docs/SKILL.md`) to point and defer to the universal `via` skill for syntax and query design, ensuring role prompts stay DRY and clean while explicitly forbidding direct SQLite queries.

### R5. Verification & Audit Run
Run a final single-loop verification using 3 new query scenarios (Trin) using the updated persona instructions. Generate the session trace report using our trace tool, and record findings in a walkthrough.

## Acceptance Criteria

### Integration & Tooling
- [ ] Triggers `*judge "via usage"`, `*judge via usage`, and `*judge via` are active in the `judge` skill
- [ ] Universal `via` skill (`agents/skills/via/SKILL.md`) exists and is linked via `setup_agent_links.py`
- [ ] `agents/tools/session_trace.py` exists, is runnable, parses the session's JSONL transcript, and outputs the query trace
- [ ] Persona instruction files (Morpheus, Neo, Oracle, Trin) contain updated guidelines referencing the universal `via` skill and explicitly forbidding direct SQLite queries
- [ ] Verification loop is completed and results are summarized in a final walkthrough artifact
- [ ] No regression in the project test suite (1333 tests pass)

## Follow-up — 2026-06-20T02:50:20Z

You are the Teamwork Coordinator. A server restart occurred, stopping previous subagents. The user has triggered: `*judge via skill and tool usage`.

Please coordinate the specialist personas (Trin, Smith, Neo, Bob, etc.) to carry out the new closed-loop `judge` workflow described in `agents/skills/judge/SKILL.md`:
1. Trin runs the 14 gauntlet scenarios, recording exact query commands and outputs to `agents/trin.docs/via_gauntlet_trace.log`.
2. Smith parses the session trace using `session_trace.py` and calculates the Trace Effectiveness Score (TES) using the rubric in SKILL.md, recording it in `agents/smith.docs/trace_eval.md`.
3. If TES < 90, Neo fixes any code bugs and Bob refines prompt/skill guidelines (in `agents/skills/via/SKILL.md` and persona instructions) to eliminate file-reading/grep fallbacks.
4. Trin re-runs the scenarios and re-generates the trace.
5. The loop repeats (up to 5 iterations) until a TES of 90 or higher is achieved.
6. Compile the final score history and findings in a walkthrough report.

Your working directory is /home/drusifer/Projects/via.
Please spawn the Orchestrator subagent to execute this, and report back when the loop terminates with the final optimized score.
