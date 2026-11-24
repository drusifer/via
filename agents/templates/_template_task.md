<!--
Sprint task board template. Owned by Mouse — see .agents/skills/mouse/SKILL.md and the sprint skill.
Instantiated as root `task.md` (the single source of truth for sprint execution).
Remove this note and the check block when creating a real artifact; checks belong to templates.
Morpheus reviews this at Step 3a using the PLAN rubric.
-->
# Sprint {N} Task Board: {Short Title}

*   **Goal**: {Two sentences summarizing the primary sprint delivery}
*   **Tier**: {Tier 1 (Major) | Tier 2 (Minor/Fast-track)}
*   **Total Points** (optional): {sum or omit}
*   **Branch**: `sprint-{N}`
*   **Status**: Planning — awaiting Morpheus Step 3a Review

---

## Stage 0: SDLC Gate (Blocker)

- [ ] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`*)

---

## Sprint Execution Phases

### Task complexity levels

Assign every executable task one level during planning. The level describes the task's complexity
and scope, not urgency, duration, importance, or the owner's seniority. A persona may work at any
level; select the smallest level supported by the evidence. Levels guide execution depth, and higher
levels do not mean better performance.

| Level | Observable task characteristics | Expected execution shape |
|---|---|---|
| **L1 — bounded** | One clear deliverable; known pattern; one component or artifact; no unresolved dependency or design choice. | Complete the deliverable directly; make the smallest relevant check; report the result. |
| **L2 — multi-step** | Several connected steps or files within one bounded area; acceptance is clear; established patterns apply; limited dependencies. | Sequence the steps; verify the stated acceptance; mention any material assumption or dependency. |
| **L3 — cross-boundary** | Multiple components/personas, an external interface, meaningful ambiguity, or a consequential trade-off. | Resolve or record the boundary/trade-off; coordinate required owners; verify integration and relevant failure cases. |
| **L4 — systemic** | Broad or high-impact change spanning subsystems/teams, substantial uncertainty, migration, or difficult-to-reverse consequences. | Stage decisions and delivery; identify affected stakeholders and risks; define rollback/mitigation and evidence at each gate. |

Use the lowest level whose characteristics cover the task. If a task has separable parts at different
levels, split it. Do not inflate a level because a task is important or estimate its level from time.

<!-- Phase 0 is REQUIRED if Morpheus flagged a build-environment change (new language, package manager,
     dependency mechanism, or runtime change). Otherwise omit Phase 0. -->
### Phase 0: Build Environment (Conditional)
- [ ] **Task 0.2:** Bootstrap build environment & update `docs/SDLC.md`. (*Owner: Tank | Trace: {story/ADR or N/A — enabling work} | Verification: `bobp make install && bobp make test`*)

### Phase 1: {First Vertical Slice / Component}
*Phase goal: {One sentence on what this phase delivers}*
- [ ] **Task 1.1:** {Write tests & implement core interface/logic}. (*Owner: Neo | Trace: {STORY-ID / ADR-ID} | Verification: `bobp make test`*)
- [ ] **Task 1.2:** {Run UAT & verify phase acceptance criteria}. (*Owner: Trin | Trace: {STORY-ID / acceptance criterion} | Verification: UAT scenario verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 1.3:** {Security review of the phase diff against the design threat model}. (*Owner: Switch | Trace: {STORY-ID / finding ID or N/A — quick pass} | Verification: `security gate (phase 1): ...` verdict line in `agents/CHAT.md`*)
- [ ] **Task 1.4:** {Code review & architectural compliance check}. (*Owner: Morpheus | Trace: {STORY-ID / ADR-ID} | Verification: review checklist/result recorded in CHAT.md*)

### Phase 2: {Second Vertical Slice / Integration}
*Phase goal: {One sentence on what this phase delivers}*
- [ ] **Task 2.1:** {Implementation task}. (*Owner: Neo | Trace: {STORY-ID / ADR-ID} | Verification: `{exact verification command}`*)
- [ ] **Task 2.2:** {UAT verification}. (*Owner: Trin | Trace: {STORY-ID / acceptance criterion} | Verification: UAT scenario verdict and evidence in `agents/CHAT.md`*)
- [ ] **Task 2.3:** {Security review of the phase diff against the design threat model}. (*Owner: Switch | Trace: {STORY-ID / finding ID or N/A — quick pass} | Verification: `security gate (phase 2): ...` verdict line in `agents/CHAT.md`*)
- [ ] **Task 2.4:** {Review & handoff}. (*Owner: Morpheus | Trace: {STORY-ID / ADR-ID} | Verification: review checklist/result recorded in CHAT.md*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Trace: N/A — closeout | Verification: `bobp make distclean && bobp make install && bobp make test`*)
- [ ] **Task C.2:** Document grooming, lesson archiving, and chat report. (*Owner: Oracle | Trace: N/A — closeout | Verification: `bobp chat-report --moniker SPRINT_{N} --summary "{few-sentence sprint summary}"`*)
- [ ] **Task C.3:** End-to-end user usability testing & lesson review. (*Owner: Smith | Trace: {STORY-ID / acceptance criterion} | Verification: Smith acceptance verdict and evidence recorded in `agents/CHAT.md`*)
- [ ] **Task C.4:** Sprint retrospective & backlog grooming. (*Owner: {one accountable owner} | Trace: N/A — closeout | Verification: Retros posted in CHAT.md*)
- [ ] **Task C.5:** Sprint launch & release announcement. (*Owner: Cypher | Trace: N/A — release decision | Verification: Cypher launch decision and announcement recorded in `agents/CHAT.md`*)

<!-- RUBRIC-START -->
## Check — PLAN

- [ ] **PASS** — `SIZE` (Are tasks partitioned into small, bounded phases?): Every phase contains 1–3 tasks; each task represents a focused, incremental increment.
- [ ] **PASS** — `GATE` (Are environmental bookends and conformance checks scheduled?): Phase 0 is assigned to Tank if Morpheus flagged build-env changes; sprint ends with Tank's `*devops sdlc-check` task.
- [ ] **PASS** — `VERIF` (Does every task specify an observable verification command?): Each task specifies an exact command (e.g. `bobp make test`, `via query ...`) or concrete inspection step.
- [ ] **PASS** — `ALIGN` (Do tasks implement the approved stories and architecture without creep?): Each implementation task names its parent story/decision; enabling and closeout work states why it has no story link.
- [ ] **PASS** — `OWNER` (Is every task assigned to the correct specialist persona?): Every task names one accountable owner, and the owner is responsible for the stated deliverable.
- [ ] **PASS** — `LEVEL` (Does each task have a justified complexity level?): Every executable task states L1–L4; its listed scope/dependencies/uncertainty match the level definition, and separable differently leveled work is split.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->
