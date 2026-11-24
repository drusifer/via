# Lesson Template

<!--
Copy the entry below into `agents/oracle/lessons.md` (a standing rule agents must follow) or
`docs/LESSONS.md` (an engineering lesson from a sprint) — see the PLACE criterion in the rubric.
Do not copy the rubric at the end.
-->

## [YYYY-MM-DD] {Short Descriptive Title}

> **Tags:** #{Category} #{Component} #{AgentName}

### Context
{Briefly describe the situation, task, or error that led to this lesson. Example: "While debugging the NTAG 424 CMAC calculation..."}

### Observation and Cause
{What happened, how it appeared, and why it happened. Separate confirmed cause from hypothesis.}

### Rule
{A specific action future readers should take when this situation recurs.}

### Evidence and Scope
- **References:** {commit, files, logs, or N/A with reason}
- **Applies when:** {trigger / scope}

<!-- RUBRIC-START -->
## Check — LESSON

- [ ] **PASS** — `WHEN` (Would a future reader recognise the situation it applies to?): It states the situation in terms a reader will meet again ("when swapping an implementation behind a stable contract").
- [ ] **PASS** — `WHAT` (Does it say concretely what happened?): It names what was done, what went wrong and how it showed up.
- [ ] **PASS** — `RULE` (Does it tell the reader what to do differently?): It gives an action a reader can take the next time the situation arises.
- [ ] **PASS** — `CAUSE` (Is it about the cause rather than the symptom?): It identifies why the problem happened and the rule addresses that.
- [ ] **PASS** — `PLACE` (Is it in the right file, and still true?): It is new, in the right file, and names things that exist; anything it replaces is marked superseded.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->

