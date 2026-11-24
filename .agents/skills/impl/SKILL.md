---
name: impl
description: Feature implementation work-loop. Delivers new capabilities through Test-Driven Development (TDD), acceptance verification, and code review.
---

Feature implementation work-loop: executes bounded feature tasks using strict Test-Driven Development (TDD).

TLDR:
    Literature: Kent Beck (*Test-Driven Development: By Example* & *Extreme Programming Explained*).
    Invariant: Test-First. Every new capability must be driven by an observable failing test before production code is written.
    Chain: Neo (TDD: Red-Green-Refactor) → Trin (Verify acceptance) → Switch (Security review) → Morpheus (Code review) → [Tank if infra] → [Smith if UX] → [Context check].
    If verification fails: delegates to `*fix` loop; max 2 failures before Oracle escalation.

# Feature Implementation Work-Loop (`impl`)

## Triggers

`*impl`, `/impl`

## Requires

`bob-protocol`, `chat`, `make`, `prep-clear`, `fix`

## Overview

The `impl` work-loop delivers new user or developer capabilities. Grounded in Kent Beck’s Extreme Programming (XP) and Test-Driven Development, it moves code from requirement to verified production status in short, bounded increments.

---

## Literature Grounding: Kent Beck (TDD & XP)

> *"Write tests before you code. Fast automated tests give developers immediate feedback, maintain system stability, and convert specifications into executable contracts."*  
> — Kent Beck, *Test-Driven Development: By Example*

In this work-loop:
1. **Red**: Neo writes a failing unit/integration test capturing the acceptance criterion.
2. **Green**: Neo writes the minimal code necessary to make the test pass.
3. **Refactor**: Neo cleans up design, removing duplication while keeping tests green.
4. **Accept**: Trin verifies functional acceptance; Morpheus reviews architectural integrity.

---

## The `impl` Lifecycle

```mermaid
flowchart TD
    Start["*impl <phase> / /impl <phase>"] --> Step0["0. Resolve Phase Scope (task.md)"]
    Step0 --> Step1["1. Neo: TDD Implementation (*swe impl)"]
    Step1 --> Step2["2. Trin: UAT Verification (*qa uat)"]
    Step2 --> BranchTrin{"Trin Verifies?"}
    BranchTrin -- "Fails" --> FailTrin["Delegate to *fix Loop (max 2)"]
    FailTrin --> Step1
    BranchTrin -- "Passes" --> Step2a["2a. Switch: Security Review (*sec review)"]
    Step2a --> BranchSwitch{"Switch Clears?"}
    BranchSwitch -- "Blocked" --> FailSwitch["Neo applies fix / Switch fixes deps (*fix)"]
    FailSwitch --> Step1
    BranchSwitch -- "Clears" --> Step3["3. Morpheus: Code Review (*lead review)"]
    Step3 --> BranchMorph{"Morpheus Approves?"}
    BranchMorph -- "Rejects" --> FailMorph["Revise with Neo (*swe fix)"]
    FailMorph --> Step1
    BranchMorph -- "Approves" --> Step3a{"Touches Infra / Env?"}
    Step3a -- "Yes" --> TankStep["3a. Tank: DevOps Review (*devops review)"]
    Step3a -- "No" --> Step3b{"Visible UX / CLI Behavior?"}
    TankStep --> Step3b
    Step3b -- "Yes" --> SmithStep["3b. Smith: UX Verification (*user test)"]
    Step3b -- "No" --> Step4["4. Context Check & Next Steps"]
    SmithStep --> Step4
    Step4 --> CheckContext{"Context > 60%?"}
    CheckContext -- "Yes" --> PrepClear["Run *prep-clear before next loop"]
    CheckContext -- "No" --> Done["Mark Task Complete in task.md"]
```

---

## Step-by-Step Procedure

### Step 0: Scope Resolution
If `<phase>` is "next phase", read `task.md` or `agents/mouse/state.md` to identify the active phase number. Log resolution to `agents/CHAT.md`.

### Step 1: Neo — TDD Implementation (`*swe impl <phase>`)
- Read phase specifications and acceptance criteria from `USER_STORIES.md` or `task.md`.
- **Test-First (Mandatory)**: Write automated tests reproducing the acceptance criteria *before* creating implementation code.
- Implement minimal, modular code satisfying the tests.
- Run local tests via `bobp make test` (or targeted test runner) to confirm green status.
- **Handoff:**
  ```bash
  bobp chat "Phase <N> implemented with TDD; unit tests green. @Trin *qa uat <phase>" --persona Neo --cmd "swe handoff" --to Trin
  ```

### Step 2: Trin — Acceptance Verification (`*qa uat <phase>`)
- Execute full test suite and phase verification tests via `bobp make test`.
- Verify all declared acceptance criteria for the phase are satisfied.
- **If tests fail**: Do NOT rewrite code as Trin; hand off immediately to Neo via `*fix` with exact failure logs.
- **Handoff on Pass:**
  ```bash
  bobp chat "Phase <N> UAT passed; all tests green. @Switch *sec review <phase>" --persona Trin --cmd "qa handoff" --to Switch
  ```

### Step 2a: Switch — Security Implementation Review (`*sec review <phase>`)
- Review the phase diff against the design gate's threat model and the area checklist in `agents/templates/_template_SECURITY_REVIEW.md`; confirm gitleaks is set up; run `bobp make security-scan` when dependencies, manifests, workflows, or secrets handling changed.
- Switch fixes vulnerable dependencies itself and proposes patches for application source; Neo applies those through `*fix`, then Trin re-verifies and Switch re-reviews.
- **Depth scales with risk**: a phase with no security-relevant change gets a one-line quick pass naming what was checked. The verdict line is always posted: `security gate (phase N): No blocking findings` or `Blocked SEC-NNN`. An open High or Critical finding blocks the phase.
- **Handoff on Clear:**
  ```bash
  bobp chat "Security gate phase <N>: No blocking findings. @Morpheus *lead review <phase>" --persona Switch --cmd "sec handoff" --to Morpheus
  ```
- **Handoff on Blocked:**
  ```bash
  bobp chat "Security gate phase <N>: Blocked SEC-NNN. Proposed fix in finding. @Neo *swe fix SEC-NNN" --persona Switch --cmd "sec reject" --to Neo
  ```

### Step 3: Morpheus — Code & Architectural Review (`*lead review <phase>`)
- Audit code changes against architectural standards, modularity, and ADRs in `ARCH.md`.
- Ensure no architectural drift or layer leaks occurred.
- If issues found $\rightarrow$ request surgical revision from Neo.

### Step 3a: Tank — DevOps Gate (Conditional)
*Required if the phase touches dependencies, runtime versions, environment variables, CI configuration, or deployment manifests.*
- Tank reviews infrastructure impact via `*devops review <phase>`.
- Confirms build reproducibility and pipeline safety. Skip if phase is pure application code.

### Step 3b: Smith — UX Evaluation Gate (Conditional)
*Required if the phase introduces or alters human-facing interaction (CLI flags, stdout/stderr formatting, error prompts, interactive UI).*
- Smith tests live running behavior via `*user test <phase>`.
- Evaluates clarity, usability, and feedback ergonomics. Skip if phase is purely internal (e.g. database schema or internal utility).

### Step 4: Context Budget Check
- Check token saturation. If context saturation is $> 60\%$:
  - Advise user to run `*prep-clear` followed by `/clear` before starting the next work loop.

---

## Anti-Loop Guard

If any implementation verification fails more than twice:
1. **STOP** execution immediately.
2. Consult **Oracle**: `bobp chat "@Oracle *ora ask <error>" --persona Neo --cmd "swe ask" --to Oracle`.
3. Allow ONE retry with a fresh approach.
4. If it fails again, halt and escalate to the user with full logs.

---

## Loop Effectiveness Rubric (`LOOP_IMPL`)

Reviewed by Morpheus (at Step 3 Code Review) or Smith (during `*judge impl`).  
Verdict line in `agents/CHAT.md`: `rubric LOOP_IMPL: TFIRST=L VERIF=L MODUL=L REGRESS=L BUDGET=L`

| Code | Criterion | Weak (W) | Acceptable (A) | Strong (S) |
|---|---|---|---|---|
| `TFIRST` | **Test-First Invariant** | Production code was written before or concurrently with tests; test added post-hoc without demonstrating an initial red phase. | Failing unit/integration test reproducing acceptance criterion was written and confirmed failing before minimal passing code was added. | Test cleanly isolates requirement in a minimal fixture; failure message explicitly documents the missing capability; zero excess test harness overhead. |
| `VERIF` | **Acceptance Verification** | Trin accepted on developer assertions alone without test runs; mocks mask real behavior; criteria skipped. | Trin ran full suite and targeted acceptance tests via `bobp make test`, confirming 100% green against declared phase criteria. | Trin tested edge cases and boundary conditions beyond happy path; verified output contracts; full run captured in `build/build.out`. |
| `MODUL` | **Modularity & Cleanliness** | Over-engineered speculative abstractions; leaky module boundaries; duplicative boilerplate retained. | Minimal code necessary to pass tests; respects established architectural layers and naming conventions from `ARCH.md`. | Highly cohesive, loosely coupled functions/classes; zero dead code; self-documenting naming requiring no explanatory comments for basic flow. |
| `REGRESS` | **Regression & Suite Hygiene** | Unrelated test suite broke and was ignored or disabled; dirty git working tree; uncaptured shell test runs. | Zero regressions across existing test suite; captured output in `build/build.out` with clean exit code 0. | Test run time bounded; no flaky tests introduced; all new tests cleanly integrated into standard Makefile test targets. |
| `BUDGET` | **Loop & State Discipline** | Persona switch without `state.md` flush; CHAT.md message exceeded 512 chars; loop iterated $>2$ times without Oracle consult. | Handoff messages properly formatted with why-rationale; `state.md` updated; context saturation checked after loop. | Seamless handoffs with concise, actionable summaries; proactive `*prep-clear` run before context reached saturation threshold. |
