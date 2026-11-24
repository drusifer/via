---
name: judge
description: Work-loop to evaluate and improve agent skills, personas, and tools using Promptfoo scenarios or usage traces (e.g. *judge bob, *judge via).
---

Work-loop for evaluating the effectiveness of a target skill, tool, or persona, using repeatable evidence to identify behavior defects, improve prompts or code, and verify the fix without tuning to a single output.

TLDR:
    The loop runs: Trin (runs Promptfoo scenarios or compiles a valid tool trace) → Smith (validates failures and catalogs defects) → Neo (fixes harness/tool bugs) or Bob (updates prompts/skills) → Trin (fresh verification run).
    Keep scenarios/rubrics fixed while fixing the target; change them only when evidence proves they are invalid.

# Judge — Agent, Skill & Tool Quality Work-Loop

## Triggers

`*judge`

## Requires

`bob-protocol`, `chat`, `make`

```
Trin (Usage Run) → Smith (UX/Token/Compliance Review & Bug log) → Neo (Bug Fixes) → Bob (Prompt/Skill Updates) → Trin (Verification Run)
```

`*judge` is the quality loop for agent skills and tools in the Bloop catalog. For persona skills with
catalogued Promptfoo suites, Promptfoo is the runner and grader; Trin owns the run and evidence review,
Smith validates the interpretation, and Bob or Neo makes the corresponding change. For targets without
a Promptfoo suite, use the applicable real workflow and trace-annotation path below.

---

## Target-Specific Contexts

When executing `*judge <target>`, the loop evaluates the specified target (e.g., `via`, `make`, `trin`):
- **`via`**: Focuses on database queries, query efficiency (avoiding fallback file reads/grep), qualified matches, result counts, and CLI parser reliability.
- **`make`**: Focuses on use of Makefile targets, avoidance of raw commands, captured logs, and verbosity flags.
- **`trin`** (or other personas): Focuses on adherence to persona role, handoff instructions, State Management Protocol compliance, and coordination clarity.
- **Persona/skill with a catalogued Promptfoo suite**: Run `uv run bobp persona-eval <suite-or-persona>`; inspect the saved JSON report and generated fixture, especially each failed assertion's `gradingResult.reason`. Do not use Claude transcript TES as a substitute for this artifact evaluation.
- **Workflow Loops (`impl`, `fix`, `refactor`, `spike`, `uat`, `deploy`, `epic`, `story`, `sprint`, `bloop`)**: Evaluates loop execution against the canonical Loop Effectiveness Rubrics (`LOOP_<TARGET>`) defined in each loop's `SKILL.md` and indexed in `agents/templates/ARTIFACTS.md`.
- **Other tools/skills**: Focuses on correct parameter passing, error handling, avoidance of failure loops, and optimal token utilization.

---

## Promptfoo Persona/Skill Evaluation Path

Use this path when `bobp persona-eval --list` shows a suite for the target.

1. **Trin — Run the fixed scenario.** Run `uv run bobp persona-eval <suite-id>` (or the persona selector). Default to one fresh fixture. For a material change, use `--repeat 3` and require every run to pass. Record the report and fixture paths.
2. **Trin — Triage evidence.** Inspect the output artifact and each assertion's pass/fail result and grader reason. Distinguish target defects from a flawed scenario, rubric, evaluator, or missing fixture capability. Do not accept a grader claim without checking the cited artifact evidence. If the report conflicts with inspectable evidence (for example, a skill-use trace contradicts a failed usage assertion, or a model grader contradicts an explicit rubric instruction), record the raw failure, evidence, and a reviewer-approved false-positive override; route recurring grader/harness defects to Neo rather than changing the target prompt.
3. **Smith — Validate the failure.** Confirm that the criterion is relevant, observable, and supported by the scenario. If the scenario or rubric is invalid, correct it with a recorded rationale before resuming; do not weaken a valid criterion to make the target pass.
4. **Neo or Bob — Make one focused change.** Neo fixes evaluator, tool, or packaging defects. Bob updates persona/skill instructions for target-behavior defects. Keep the test request and rubric fixed during target fixes; preserve the failed report as the before result.
5. **Trin — Verify in a fresh fixture.** Rerun the same suite after the change. A pass requires every required assertion to pass, or to have an explicit reviewer-approved false-positive override backed by artifact/trace evidence; report raw and adjudicated outcomes separately. For a material change, also complete the three-run repeat and pass at least one relevant holdout suite when available. A rerun without a target or validated test change is not progress.
6. **Close or escalate.** On pass, record the before/after reports, specific behavior change, and remaining limits. If the same failure persists for two focused fix-and-verify iterations, stop, post the evidence, consult Oracle, and ask the user before another attempt, following the shared anti-loop rule.

### Jev Rubric and Context Guidance

There is no separate TypeSafe/Jev style guide in this repository. The persona evaluator uses the installed `typesafe-sdk`'s `Choice` classifier and ordered `Score` rubric together: classify each criterion as `meets`, `partially_meets`, or `does_not_meet`, and record a three-level rubric score (expected value 0–2) with its confidence and probabilities.

- Keep one classifier and one score question per atomic, observable rubric check. Split compound checks so a result identifies the missing dimension instead of grading a bundle of unrelated requirements.
- Put the criterion itself in `instructions`. In `Choice.criteria`, define evidence for every classification level. In `Score.criteria`, use the same ordered anchors. Do not change the classifier labels or score scale to compensate for unclear criteria.
- Use `meets` as the pass gate and require the classifier label to match the score distribution's most likely rubric level. Do not infer a score level by rounding the probability-weighted expected score; preserve that expected score separately as a diagnostic. If the two most likely levels differ, flag the component for human review instead of silently overriding either result.
- Give Jev the relevant scenario, full rubric, persona skill instructions, candidate response or artifact, expected artifact path, and a concise inventory of declared capabilities and available project paths. Include only fixture files needed to judge the work; omit chat logs, state files, secrets, and unrelated transcripts.
- Jev does not return a natural-language rationale for these typed questions. Make component labels and rubric rows specific enough to locate a miss in the report. Review low-confidence or classifier/score-disagreement results against the artifact and fixture evidence.
- Keep the selected class, raw score, confidence values, probabilities, and pass decision in the report. Record a reviewer-supported false-positive override separately from the raw result.

Promptfoo runs and scores scenarios; `*judge` coordinates diagnosis, ownership, changes, and verification. A
failed rubric result is feedback to inspect, not an instruction to edit until green. Keep a holdout case
separate from the scenario used to diagnose and fix the target to reduce test-specific overfitting.

---

## Step 1 — Trin: Usage Run & Trace Compilation
```
Trin *qa judge <target>
```
- **Required tool — `bobp trace-annotate [--date YYYY-MM-DD] [--format html|md]`**: invoke this Bobp CLI directly; it does not require a target project Makefile. It parses Claude Code JSONL transcripts (`~/.claude/projects/<slug>/*.jsonl`) for the selected date and flags tool-use patterns via `agents/tools/trace_rules.json`. Output defaults to `agents/trin/judge_tool_trace.html` (or `.md` with `--format md`).
- **Harness coverage:** this annotator currently reads Claude Code transcripts only. It does not capture Codex tool calls. If the session being judged ran in Codex, report that the tool trace is unavailable and do not issue a numeric TES from CHAT.md or state files; those records support process/protocol review only.
- **Do not hand-reconstruct a tool trace from `agents/CHAT.md`.** CHAT.md cannot show tool-call-level behavior and produces a systematically over-optimistic trace. Use `bobp trace-annotate` for Claude tool-use judging; use CHAT.md and persona state only for process/protocol adherence (chain sequencing, gate compliance, handoffs).
- **Manual review is still required after running the tool**: read the raw flags before scoring — the rule regexes are heuristics and can both over-flag (e.g. a `make <target> | tail` where the invocation wasn't actually via `bobp make`, so there's no build.out capture to be redundant with) and under-flag. Note any flag you're overriding and why in the trace report, per-flag, not as a blanket dismissal.
- Trin writes the analysis (raw counts + manual-review verdict per flag type + any additional scenario coverage the tool can't see) to `agents/trin/judge_<target>_trace.md`.
- **Trin's constraints**: Ensure that the target is exercised in realistic conditions representing typical developer/agent workflow.
- **Live vs. completed sessions**: `bobp trace-annotate` scores the JSONL transcript as it exists *right now*. If the `*judge` loop is run inside the same live session it's evaluating, every subsequent step of the loop (reading the trace, editing files, re-running the tool) appends more tool calls to that same transcript — the call/flag counts will keep growing across iterations, and a fresh Smith TES score at each iteration is not comparing like-for-like. Prefer running `*judge` on a session that has already ended. If run mid-session anyway, treat iteration 1's score as the baseline for defect-finding only, verify specific fixes by checking whether the specific previously-flagged entries are now absent (not by chasing a fresh 90+ on an ever-growing trace), and defer a real numeric re-score to the next `*judge` invocation on a completed session.

### Handoff:
```bash
bobp chat "[target] run complete. @Smith *user feedback judge <target>" --persona Trin --cmd "qa handoff" --to Smith
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
- **Bug/Defect Cataloging**: If any command crashes, returns incorrect results, violates constraints, or behaves unexpectedly, Smith logs the details in `agents/smith/bugs.md` (or `bugs_<target>.md`).
- **Decision & Loop Control**:
  - Record the final score in `agents/smith/trace_eval.md` (or `trace_eval_[target].md`).
  - **Target Score**: **90 points** or higher is considered optimal.
  - **Branching**:
    - **If TES >= 90** and no bugs/anti-patterns remain: Hand off to Trin to finalize and exit.
    - **If TES < 90** or bugs/anti-patterns remain:
      - If code/script bugs exist: Hand off to Neo (`*swe fix judge <target>`).
      - If prompts/skills are sub-optimal but code is correct: Hand off to Bob (`*prompt update judge <target>`).

### Handoff (Bugs Found or TES < 90 with code/script issues):
```bash
bobp chat "Score: [TES]. Bugs cataloged in bugs.md. @Neo *swe fix judge <target>" --persona Smith --cmd "user feedback" --to Neo
```

### Handoff (No Bugs but TES < 90 with usage/query/prompt issues):
```bash
bobp chat "Score: [TES]. Sub-optimal patterns. @Bob *prompt update judge <target>" --persona Smith --cmd "user feedback" --to Bob
```

### Handoff (TES >= 90 & No Bugs):
```bash
bobp chat "Optimal score [TES] reached! No bugs. @Trin *qa done" --persona Smith --cmd "user feedback" --to Trin
```

---

## Step 3 — Neo: Bug Fixes & Test Verification
```
Neo *swe fix judge <target>
```
- Neo resolves the bugs or structural issues cataloged in `agents/smith/bugs.md` (or target bug file).
- Neo ensures any scripts, Makefiles, or codebase modules behave correctly.
- Neo runs the project tests (`bobp make test`) to ensure a completely green baseline.

### Handoff:
```bash
bobp chat "Bugs resolved and test suite verified green. @Bob *prompt update judge <target>" --persona Neo --cmd "swe handoff" --to Bob
```

---

## Step 4 — Bob: Prompt Tuning & Skill Optimization
```
Bob *prompt update judge <target>
```
- Bob extracts the optimal usage patterns identified by Smith and updates:
  - The universal customization skill guidelines under `.agents/skills/<target>/SKILL.md` (or the relevant skill/persona file).
  - Specialist persona instructions (`.agents/skills/<persona>/SKILL.md`) to guide future agent interactions and prevent identified anti-patterns.
- Bob registers the updated skills/rules configurations.

### Handoff:
```bash
bobp chat "Agent prompts and target skill updated. @Trin *qa verify judge <target>" --persona Bob --cmd "prompt update" --to Trin
```

---

## Step 5 — Trin: Re-run & Loop Verification
```
Trin *qa verify judge <target>
```
- Trin re-executes the target scenarios/actions using the updated skills and prompts.
- Generates a new session trace report.
- **If verifying inside the same live session** (see the live-vs-completed note in Step 1): confirm the specific previously-cataloged bug entries are gone from the new trace and that no real detections were lost — do not require a fresh TES >= 90 on the now-larger trace before closing the loop.
- **Handoff to Smith for Re-scoring (Looping)**: Hand off to Smith to re-evaluate the new session trace. The loop continues (**Trin -> Smith -> [Neo ->] Bob -> Trin**) after a focused correction; if the same failure persists for two iterations, follow the shared anti-loop rule and stop for Oracle/user guidance. Do not use repeated unchanged runs to chase `TES >= 90`.

### Handoff (Trigger Next Scoring Iteration):
```bash
bobp chat "New run complete and trace generated. @Smith *user feedback judge <target>" --persona Trin --cmd "qa verify" --to Smith
```

### Handoff (Loop Complete - TES >= 90):
```bash
bobp chat "Verification complete. Optimal score reached and loop closed successfully." --persona Trin --cmd "qa done" --to all
```
