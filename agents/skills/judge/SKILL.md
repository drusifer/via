---
name: judge
description: Interactive loop to evaluate agent skill/tool/persona usage (e.g. *judge via, *judge make, *judge trin), catalog bugs/anti-patterns, and optimize agent prompt instructions.
triggers: ["*judge"]
requires: ["bob-protocol", "chat", "make"]
---

Full workflow for evaluating the effectiveness of a target skill, tool, or persona, ensuring correct usage, correctness, cataloging bugs, and updating agent prompts to minimize token usage and optimize efficiency.

TLDR:
    The loop runs: Trin (runs target scenarios / compiles session traces) → Smith (judges token waste, compliance, and catalogs bugs) → Neo (fixes code/script bugs) → Bob (updates prompts/skills) → Trin (verification run).
    Any defect, resource waste, or compliance failure must be cataloged and resolved, rather than accepted.

# Judge — Evaluation & Optimization Loop

```
Trin (Usage Run) → Smith (UX/Token/Compliance Review & Bug log) → Neo (Bug Fixes) → Bob (Prompt/Skill Updates) → Trin (Verification Run)
```

---

## Target-Specific Contexts

When executing `*judge <target>`, the loop evaluates the specified target (e.g., `via`, `make`, `trin`):
- **`via`**: Focuses on database queries, query efficiency (avoiding fallback file reads/grep), qualified matches, result counts, and CLI parser reliability.
- **`make`**: Focuses on use of Makefile targets, avoidance of raw commands, captured logs, and verbosity flags.
- **`trin`** (or other personas): Focuses on adherence to persona role, handoff instructions, State Management Protocol compliance, and coordination clarity.
- **Other tools/skills**: Focuses on correct parameter passing, error handling, avoidance of failure loops, and optimal token utilization.

---

## Step 1 — Trin: Usage Run & Trace Compilation
```
Trin *qa judge <target>
```
- Trin compiles or executes a set of representative test cases or usage scenarios for the specified `<target>`.
- Trin captures the session history, commands run, output size, and writes a trace report to `agents/trin.docs/judge_<target>_trace.log` (or similar).
- **Trin's constraints**: Ensure that the target is exercised in realistic conditions representing typical developer/agent workflow.

### Handoff:
```bash
make chat MSG="[target] run complete. @Smith *user feedback judge <target>" PERSONA="Trin" CMD="qa handoff" TO="Smith"
```

---

## Step 2 — Smith: Trace Evaluation & Scoring
```
Smith *user feedback judge <target>
```
- Smith reviews the execution trace to evaluate usability, correctness, and token efficiency.
- **Trace Effectiveness Score (TES) Rubric (Max: 100 points)**:
  - **Start at 100 points.**
  - **Correctness & Success**: Deduct **-5 points** for each scenario or action where the target failed to accomplish the goal or returned incorrect results.
  - **Resource Waste (Tokens / Commands)**:
    - Deduct **-5 points** for each redundant or fallback tool call (e.g., using `grep` or file reads when `via` queries or a simple `make` target could have succeeded, or invoking the same tool/command multiple times unnecessarily).
    - Deduct **-3 points** for each command returning overly verbose outputs due to lack of limits or poor formatting.
    - Deduct **-2 points** for failing to use standard project automation (e.g., executing raw pytest or shell commands instead of using the designated `make` target).
  - **Protocol & Persona Adherence**:
    - Deduct **-5 points** for any violation of the State Management Protocol (missing context files, incorrect summarizing, improper handoffs).
  - **Efficiency/Design Bonuses**:
    - Add **+2 points** (up to **+10 points** maximum) for highly efficient, precise usage patterns or elegant scripting.
- **Bug/Defect Cataloging**: If any command crashes, returns incorrect results, violates constraints, or behaves unexpectedly, Smith logs the details in `agents/smith.docs/bugs.md` (or `bugs_<target>.md`).
- **Decision & Loop Control**:
  - Record the final score in `agents/smith.docs/trace_eval.md` (or `trace_eval_[target].md`).
  - **Target Score**: **90 points** or higher is considered optimal.
  - **Branching**:
    - **If TES >= 90** and no bugs/anti-patterns remain: Hand off to Trin to finalize and exit.
    - **If TES < 90** or bugs/anti-patterns remain:
      - If code/script bugs exist: Hand off to Neo (`*swe fix judge <target>`).
      - If prompts/skills are sub-optimal but code is correct: Hand off to Bob (`*prompt update judge <target>`).

### Handoff (Bugs Found or TES < 90 with code/script issues):
```bash
make chat MSG="Score: [TES]. Bugs cataloged in bugs.md. @Neo *swe fix judge <target>" PERSONA="Smith" CMD="user feedback" TO="Neo"
```

### Handoff (No Bugs but TES < 90 with usage/query/prompt issues):
```bash
make chat MSG="Score: [TES]. Sub-optimal patterns. @Bob *prompt update judge <target>" PERSONA="Smith" CMD="user feedback" TO="Bob"
```

### Handoff (TES >= 90 & No Bugs):
```bash
make chat MSG="Optimal score [TES] reached! No bugs. @Trin *qa done" PERSONA="Smith" CMD="user feedback" TO="Trin"
```

---

## Step 3 — Neo: Bug Fixes & Test Verification
```
Neo *swe fix judge <target>
```
- Neo resolves the bugs or structural issues cataloged in `agents/smith.docs/bugs.md` (or target bug file).
- Neo ensures any scripts, Makefiles, or codebase modules behave correctly.
- Neo runs the project tests (`make test`) to ensure a completely green baseline.

### Handoff:
```bash
make chat MSG="Bugs resolved and test suite verified green. @Bob *prompt update judge <target>" PERSONA="Neo" CMD="swe handoff" TO="Bob"
```

---

## Step 4 — Bob: Prompt Tuning & Skill Optimization
```
Bob *prompt update judge <target>
```
- Bob extracts the optimal usage patterns identified by Smith and updates:
  - The universal customization skill guidelines under `agents/skills/<target>/SKILL.md` (or the relevant skill/persona file).
  - Specialist persona instructions (`agents/<persona>.docs/SKILL.md`) to guide future agent interactions and prevent identified anti-patterns.
- Bob registers the updated skills/rules configurations.

### Handoff:
```bash
make chat MSG="Agent prompts and target skill updated. @Trin *qa verify judge <target>" PERSONA="Bob" CMD="prompt update" TO="Trin"
```

---

## Step 5 — Trin: Re-run & Loop Verification
```
Trin *qa verify judge <target>
```
- Trin re-executes the target scenarios/actions using the updated skills and prompts.
- Generates a new session trace report.
- **Handoff to Smith for Re-scoring (Looping)**: Hand off to Smith to re-evaluate the new session trace. The loop continues (**Trin -> Smith -> [Neo ->] Bob -> Trin**) until Smith issues a `TES >= 90` verdict (or after 5 consecutive iterations without score improvement).

### Handoff (Trigger Next Scoring Iteration):
```bash
make chat MSG="New run complete and trace generated. @Smith *user feedback judge <target>" PERSONA="Trin" CMD="qa verify" TO="Smith"
```

### Handoff (Loop Complete - TES >= 90):
```bash
make chat MSG="Verification complete. Optimal score reached and loop closed successfully." PERSONA="Trin" CMD="qa done" TO="all"
```
