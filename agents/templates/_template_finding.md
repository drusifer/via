<!--
Research finding, technical spike, benchmark, evaluation, or root-cause record. Any persona may
write one; see the spike/fix workflow for process. Remove this note and the check block when used.
-->
# Finding: {Question or discovery}

- **Type:** {Research | Spike | Benchmark | Tool evaluation | Root cause}
- **Date / author:** {YYYY-MM-DD / persona}
- **Status:** {Complete | Abandoned | Follow-up needed}
- **Related work:** {story, issue, ADR, or N/A with reason}

## Question and Context

- **Question or objective:** {What uncertainty, defect, or risk was investigated?}
- **Expected outcome / hypothesis** (when testable): {Expected result or N/A with reason}
- **Trigger and scope:** {Why this mattered; what was and was not investigated}
- **Timebox** (for a spike): {limit or omit}

## Method and Evidence

{Describe the method. Include environment, versions, input, and relevant configuration when they affect the result.}

- **Sources / reproduction:** {Exact command and output, benchmark data, source citations, or file/issue links appropriate to this finding}
- **Observed evidence:** {Results separated from interpretation}

## Alternatives (when relevant)

| Approach | Evidence-based benefit | Cost / limitation | Outcome |
|---|---|---|---|
| {Approach} | {Evidence} | {Evidence} | {Selected / rejected} |

## Conclusion and Follow-up

- **Conclusion:** {Direct answer supported by evidence}
- **Recommendation:** {Proceed | Pivot | Stop | More investigation, with reason}
- **Temporary code:** {Removed, isolated, or retained with location and owner}
- **Actions:** {Action, owner, due/trigger, or None}

<!-- RUBRIC-START -->
## Check — FINDING

- [ ] **PASS** — The question/objective and scope identify what was investigated and why; a testable hypothesis is included when applicable.
- [ ] **PASS** — Evidence is appropriate to the finding type, distinguishes observation from interpretation, and can be checked through a source, reproduction, or referenced record.
- [ ] **PASS** — Relevant alternatives are compared with evidence, or the document explains why comparison does not apply.
- [ ] **PASS** — The conclusion answers the question and follow-up actions have an owner, or explicitly state that none are needed.
- [ ] **PASS** — Temporary code is removed or its location and disposition are explicit.
- [ ] **FAIL** — Any required evidence, conclusion, or disposition is missing or contradictory; cite the gap and smallest correction.
<!-- RUBRIC-END -->
