---
name: judge
description: Interactive loop to evaluate the query efficiency of the via tool, catalog/fix bugs, and optimize agent prompt instructions. Use *judge via to kick off the gauntlet.
triggers: ["*judge \"via usage\"", "*judge via usage", "*judge via"]
requires: ["bob-protocol", "chat", "make"]
---

Full workflow for evaluating the effectiveness of the `via` query tool, ensuring correct results, cataloging bugs, and updating agent prompts to minimize token usage.

TLDR:
    The loop runs: Trin (runs gauntlet) → Smith (judges token waste & catalogs bugs) → Neo (fixes bugs) → Bob (updates prompts) → Trin (verification run).
    Any tool defect or query crash MUST be filed as a bug, NOT accepted or entrenched in test assertions.

# Judge — Evaluation & Optimization Loop

```
Trin (Gauntlet Scenarios) → Smith (UX/Token Review & Bug log) → Neo (Bug Fixes) → Bob (Prompt Updates) → Trin (Verification Run)
```

---

## Step 1 — Trin: Gauntlet Run
```
Trin *qa judge via
```
- Trin executes the 14 gauntlet lookup scenarios interactively using `make via` (CLI) or direct SQLite queries on `.via/index.db`.
- **Constraint**: Trin MUST NOT read source files or use `grep` during this run.
- Trin records the exact query command lines, the results, and writes the trace log to `agents/trin.docs/via_gauntlet_trace.log`.

### Handoff:
```bash
make chat MSG="Gauntlet run complete. @Smith *user feedback judge" PERSONA="Trin" CMD="qa handoff" TO="Smith"
```

---

## Step 2 — Smith: Trace Evaluation & Scoring
```
Smith *user feedback judge
```
- Smith reviews the gauntlet trace to evaluate usability, correctness, and token efficiency.
- **Trace Effectiveness Score (TES) Rubric (Max: 100 points)**:
  - **Start at 100 points.**
  - **Correctness**: Deduct **-5 points** for each scenario where the agent failed to find the correct answer or returned incorrect/incomplete results.
  - **Fallback Penalties (Token Waste)**:
    - Deduct **-5 points** for each raw file-read tool call (e.g. `view_file`) or `grep` search performed to trace symbols/relationships where a `via` query could have resolved it directly.
    - Deduct **-3 points** for each query returning overly verbose outputs due to omitting limits (omitting `-n` or using a limit larger than necessary).
    - Deduct **-2 points** for queries triggering namespace collisions that should have used qualified name matching (`-Q`).
  - **Efficiency Bonuses**:
    - Add **+2 points** (up to **+10 points** maximum) for exceptionally precise multi-stage chained queries that minimize intermediate steps.
- **Bug Cataloging**: If any query crashes, returns incorrect results, or behaves unexpectedly, Smith logs the details in `agents/smith.docs/bugs.md`.
- **Decision & Loop Control**:
  - Record the final score in `agents/smith.docs/trace_eval.md`.
  - **Target Score**: **90 points** or higher is considered optimal.
  - **Branching**:
    - **If TES >= 90** and no bugs remain: Hand off to Trin to finalize and exit.
    - **If TES < 90** or bugs remain:
      - If code bugs exist: Hand off to Neo (`*swe fix judge`).
      - If queries are sub-optimal but code is correct: Hand off to Bob (`*prompt update judge`).

### Handoff (Bugs Found or TES < 90 with code issues):
```bash
make chat MSG="Score: [TES]. Bugs cataloged in bugs.md. @Neo *swe fix judge" PERSONA="Smith" CMD="user feedback" TO="Neo"
```

### Handoff (No Bugs but TES < 90 with query issues):
```bash
make chat MSG="Score: [TES]. Sub-optimal query patterns. @Bob *prompt update judge" PERSONA="Smith" CMD="user feedback" TO="Bob"
```

### Handoff (TES >= 90 & No Bugs):
```bash
make chat MSG="Optimal score [TES] reached! No bugs. @Trin *qa done" PERSONA="Smith" CMD="user feedback" TO="Trin"
```

---

## Step 3 — Neo: Bug Fixes & Test Verification
```
Neo *swe fix judge
```
- Neo resolves the issues listed in `agents/smith.docs/bugs.md`.
- **Constraint**: Fix the core code (parser, executor, database store) rather than adapting queries to work around the defect.
- Neo runs the test suite (`make test`) and ensures all tests are green (1332+ passing).

### Handoff:
```bash
make chat MSG="Bugs resolved and test suite verified green. @Bob *prompt update judge" PERSONA="Neo" CMD="swe handoff" TO="Bob"
```

---

## Step 4 — Bob: Prompt Tuning & Skill Optimization
```
Bob *prompt update judge
```
- Bob extracts the optimal query patterns identified by Smith and updates:
  - The universal customization skill [via](file:///home/drusifer/Projects/via/agents/skills/via/SKILL.md) guidelines.
  - Specialist persona instructions (`agents/morpheus.docs/SKILL.md`, `agents/neo.docs/SKILL.md`, `agents/oracle.docs/SKILL.md`, `agents/trin.docs/SKILL.md`).
- Bob registers the updated skills using `setup_agent_links.py`.

### Handoff:
```bash
make chat MSG="Agent prompts and universal skill updated. @Trin *qa verify judge" PERSONA="Bob" CMD="prompt update" TO="Trin"
```

---

## Step 5 — Trin: Re-run & Loop Verification
```
Trin *qa verify judge
```
- Trin re-executes the query scenarios using the updated skills and prompts.
- Generates a new session trace report using `session_trace.py`.
- **Handoff to Smith for Re-scoring (Looping)**: Hand off to Smith to re-evaluate the new session trace. The loop continues (**Trin -> Smith -> [Neo ->] Bob -> Trin**) until Smith issues a `TES >= 90` verdict (or after 5 consecutive iterations without score improvement).

### Handoff (Trigger Next Scoring Iteration):
```bash
make chat MSG="New run complete and trace generated. @Smith *user feedback judge" PERSONA="Trin" CMD="qa verify" TO="Smith"
```

### Handoff (Loop Complete - TES >= 90):
```bash
make chat MSG="Verification complete. Optimal score reached and loop closed successfully." PERSONA="Trin" CMD="qa done" TO="all"
```

---

## 14 Gauntlet Scenarios Reference

1. **Scenario 1 (Simple Class Lookup)**
   - *Intended Question*: What is the location of the `PipelineParser` class?
   - *Expected Result*: Class `PipelineParser` is in `via/pipeline/parser.py`.
   - *Token/Efficiency Metric*: Looked up class name only; did not read the file content.

2. **Scenario 2 (Inverse Relationships)**
   - *Intended Question*: Which classes inherit from `ParserABC`?
   - *Expected Result*: `PythonParser`, `MarkdownParser`, `JavaScriptParser`, and `DartParser`.
   - *Token/Efficiency Metric*: Queried relationship `inherits-from` targeting `ParserABC` without reading individual parser files.

3. **Scenario 3 (File Exclusions)**
   - *Intended Question*: What functions are in `via/core/` but not in test files?
   - *Expected Result*: Functions defined in files under `via/core/` (excluding anything with `test` in the path).
   - *Token/Efficiency Metric*: Handled via `--not` negation on file path glob, without listing test functions or reading core files.

4. **Scenario 4 (Negative Relationships)**
   - *Intended Question*: Which classes do not declare any methods?
   - *Expected Result*: Classes with only variables, docstrings, or no method declarations.
   - *Token/Efficiency Metric*: Queried using `--sans declares` relationship filter, avoiding manual inspection of class files.

5. **Scenario 5 (SQL Pattern Match)**
   - *Intended Question*: What indexed symbols contain "reindex" (case-insensitive)?
   - *Expected Result*: Symbols like `reindex_file`, `notify_reindex`, `add_reindex_listener`, etc.
   - *Token/Efficiency Metric*: Queried using SQL LIKE matching (`-ms` with `%reindex%`), avoiding regex matching of all symbols or manual code scanning.

6. **Scenario 6 (Direct SQLite Query)**
   - *Intended Question*: How many total symbols are currently indexed in the SQLite database?
   - *Expected Result*: A single integer count from the database.
   - *Token/Efficiency Metric*: Executed direct SQL query `SELECT COUNT(*) FROM symbols;` on `.via/index.db` instead of loading all symbols into memory or running CLI match-all.

7. **Scenario 7 (Import Check)**
   - *Intended Question*: Which files import `sqlite3`?
   - *Expected Result*: `via/db/store.py` (and potentially some tests).
   - *Token/Efficiency Metric*: Used `--via imports` matching `sqlite3`, avoiding a grep search across the codebase.

8. **Scenario 8 (Markdown Header Search)**
   - *Intended Question*: What are the section headers in `docs/USER_GUIDE.md`?
   - *Expected Result*: Markdown headers (symbol_type = `header`).
   - *Token/Efficiency Metric*: Filtered by type `-sH` / `--type-header` and path, avoiding reading the entire markdown file.

9. **Scenario 9 (Line Slicing)**
   - *Intended Question*: What are lines 50-70 of `via/pipeline/executor.py`?
   - *Expected Result*: The specific range of lines.
   - *Token/Efficiency Metric*: Used `-mL` / `--match-line` line slice syntax, avoiding reading the whole file.

10. **Scenario 10 (Complex Multi-Filter)**
    - *Intended Question*: Find functions named `parse` declared inside a class named `PythonParser`.
    - *Expected Result*: Function `parse` in class `PythonParser` in `via/parsers/python_parser.py`.
    - *Token/Efficiency Metric*: Chained match/type/relationship stages, avoiding reading `python_parser.py`.

11. **Scenario 11 (Call Sites)**
    - *Intended Question*: Where is `DatabaseStore.connect` called?
    - *Expected Result*: All symbols calling `connect` (or `DatabaseStore.connect`).
    - *Token/Efficiency Metric*: Used relationship query `--via calls`, avoiding raw text search.

12. **Scenario 12 (Declaration Site)**
    - *Intended Question*: Where is `PipelineParseError` declared (exact line)?
    - *Expected Result*: `via/pipeline/errors.py` (with line number).
    - *Token/Efficiency Metric*: Queried symbol name `PipelineParseError` with type `class`, avoiding reading files.

13. **Scenario 13 (Type Hierarchy Expansion)**
    - *Intended Question*: What is the inheritance hierarchy of `ParserABC`?
    - *Expected Result*: Visual tree diagram.
    - *Token/Efficiency Metric*: Generated using diagram output `-oD`, avoiding manual tree reconstruction.

14. **Scenario 14 (Test Coverage Mapping)**
    - *Intended Question*: What tests cover or reference code in `via/pipeline/executor.py`?
    - *Expected Result*: Test files/methods containing assertions or imports of `executor`.
    - *Token/Efficiency Metric*: Traced via references/imports relationship, avoiding scanning test code manually.
