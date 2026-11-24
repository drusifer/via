<!--
High-level Quality & UAT Strategy template.
Owned by Trin (QA Guardian / Lead SDET) — see .agents/skills/trin/SKILL.md.
Instantiated as `docs/TEST_STRATEGY.md` (or `docs/UAT_STRATEGY.md`).
Remove this note and the check block when creating a real artifact; checks belong to templates.
Morpheus and Smith review this using the STRATEGY rubric.
-->
# Quality & UAT Strategy: {Project Name}

*   **Lead SDET / QA Guardian**: Trin
*   **Status**: {Draft | Active | Under Revision}
*   **Last Updated**: {YYYY-MM-DD}
*   **Target Environments**: `{Local developer venv, CI pipeline, Staging container}`

---

## 1. Quality Vision & Testing Principles

{Describe the core testing philosophies governing this codebase. Focus on fast feedback, deterministic suites, and regression prevention.}

* **Shift-Left Quality:** Verification begins during story refinement and phase implementation, not as a post-sprint freeze.
* **Deterministic feedback:** Keep tests isolated and repeatable. Record the project commands in the quality-gates table.
* **External dependencies:** Use contract or integration checks against real services/tools when risk warrants and execution is safe. Document when mocks are used and what independent evidence covers their assumptions.
* **Simplicity & Maintainability:** Prefer clean, well-factored code with clear test seams over complex mocking frameworks.

---

## 2. Testing Levels & The Quality Pyramid

| Level | Purpose and risk covered | Where it runs / command | When it is appropriate |
|---|---|---|---|
| Unit | {Fast isolated rules and edge cases} | `{actual target or N/A — reason}` | {Risk addressed} |
| Integration | {Interactions across boundaries} | `{actual target or N/A — reason}` | {Risk addressed} |
| End-to-end / acceptance | {Critical user workflows} | `{actual procedure or target}` | {Risk addressed} |

Add only levels used by this project. Do not set universal test-count ratios; justify any project targets with observed risk or cost.

---

## 3. Ownership and Review

{Link to the project skills or process documents that assign test authoring, QA review, and usability review. Avoid copying persona responsibilities here.}

## 4. Automated Quality Gates

List only gates that exist in this repository. Agents invoke targets through `bobp make`; CI may call the underlying Makefile targets.

| Gate | Existing target / command | Pass condition | Required at |
|---|---|---|---|
| {Tests} | `{actual target}` | {observable exit/result; note approved skips} | {handoff / CI / release} |
| {Lint or type check} | `{actual target or omit}` | {observable result} | {when} |

## 5. Test Environment & Fixture Management

* **Isolation:** Tests must never depend on state left by a previous test. All test files, databases, or mocks must be scoped per test or test module.
* **Scratch & Cleanup:** File operations must write to isolated temporary directories (`build/test_scratch/` or pytest `tmp_path`) and clean up upon completion.
* **Non-Destructive Execution:** Test scripts must never perform destructive actions on production or user home directories.

---

## 6. Defect Handling

{Link to the project's canonical defect severity, routing, and escalation procedure. Define local
severity levels here only when they differ from the shared workflow and have an agreed owner.}

<!-- RUBRIC-START -->
## Check — STRATEGY

- [ ] **PASS** — `PYRAMID` (Does it define test levels with clear boundaries?): Defines the test levels used by this project, their distinct risks, and omits unsupported proportions.
- [ ] **PASS** — `REALITY` (Does it enforce real-binary testing over unvalidated mocks?): States when real-service/tool checks are appropriate and how mock assumptions are independently validated.
- [ ] **PASS** — `GATES` (Are quality gates deterministic and tied to automated commands?): Every listed gate names an existing project target/command and an observable pass condition.
- [ ] **PASS** — `TRIAGE` (Does it establish clear defect severity and triage routing?): Links to the canonical defect-triage procedure or defines the project’s actual owner and escalation path.
- [ ] **PASS** — `ROLES` (Are quality responsibilities clearly divided between roles?): Links to the canonical ownership guidance without restating contradictory role policy.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->
