---
name: fix
description: Defect and bugfix work-loop. Diagnoses, confirms root cause with the user, applies surgical fixes with reproduction tests, and verifies zero regressions.
---

Defect and bugfix work-loop: diagnoses, confirms root cause, and applies targeted fixes with regression tests.

TLDR:
    Literature: David Agans (*Debugging: The 9 Indispensable Rules for Finding the Most Elusive Bugs*).
    Invariant: Reproduce & Diagnose First. Never touch code based on symptoms alone. Write a failing test, diagnose the cause, and confirm with the user/lead before fixing.
    Chain: Neo (diagnose & reproduce) → User/Lead (confirm diagnosis) → Neo (surgical fix) → Trin (verify & regression sweep) → Morpheus (code review).
    Anti-loop rule: If fix fails twice, consult Oracle before retry; escalate to user before attempt 3.

# Bugfix & Defect Work-Loop (`fix`)

## Triggers

`*fix`, `/fix`

## Requires

`bob-protocol`, `chat`, `make`, `prep-clear`

## Overview

The `fix` work-loop safely resolves defects, regressions, and broken behavior without causing collateral damage. Grounded in David Agans' foundational debugging disciplines, it mandates that root causes are reproduced and confirmed before any code is modified.

---

## Literature Grounding: David Agans (*Debugging*)

> *"Rule 1: Understand the system. Rule 2: Make it fail. Rule 3: Quit thinking and look... Don't guess. Look at the failure occurring, reproduce it deterministically, and find the real fault before attempting a cure."*  
> — David J. Agans, *Debugging: The 9 Indispensable Rules for Finding the Most Elusive Bugs*

In this work-loop:
1. **Understand & Reproduce**: Neo does not jump straight to editing application files. Neo reproduces the bug with a minimal automated test or repeatable command.
2. **Confirm Diagnosis**: The symptom described by the user is not the diagnosis. Neo explains the root cause and proposed fix to the user or lead, and waits for confirmation.
3. **Surgically Fix**: Neo writes the targeted fix that turns the reproduction test green.
4. **Regression Sweep**: Trin verifies that the bug test passes and that no previously passing tests broke.

---

## The `fix` Lifecycle

```mermaid
flowchart TD
    Start["*fix <thing> / /fix <thing>"] --> Step0["0. Neo: Reproduce & Diagnose"]
    Step0 --> Step0a["Write Failing Reproduction Test"]
    Step0a --> Step0b["Propose Root Cause & Fix to User"]
    Step0b --> GateUser{"User / Lead Confirms?"}
    GateUser -- "No / Clarify" --> Step0
    GateUser -- "Yes" --> Step1["1. Neo: Apply Surgical Fix (*swe fix)"]
    Step1 --> Step2["2. Trin: Verify & Regression Test (*qa uat)"]
    Step2 --> BranchTrin{"Trin Verifies?"}
    BranchTrin -- "Fails (Attempt 1)" --> Step1
    BranchTrin -- "Fails (Attempt 2)" --> OracleStop["Anti-Loop: Consult Oracle (*ora ask)"]
    OracleStop --> Escalate["Escalate to User before Attempt 3"]
    BranchTrin -- "Passes" --> Step3["3. Morpheus: Review Fix (*lead review)"]
    Step3 --> Done["Bug Resolved & Logged"]
```

---

## Step-by-Step Procedure

### Step 0: Neo — Reproduce & Diagnose First (DO NOT EDIT CODE YET)
- Work out what the bug actually is. The user's input `<thing>` is an observed symptom, not an architectural diagnosis.
- Reproduce the bug reliably: write a minimal failing test or deterministic verification script.
- Locate the root cause in the source code.
- **Explain to User & Pause**:
  Post an explanation to `agents/CHAT.md` detailing:
  1. Observed behavior (what goes wrong).
  2. Expected behavior (what should happen).
  3. Diagnosed root cause.
  4. Proposed minimal fix.
- **STOP and WAIT for user confirmation** before touching production code.

### Step 1: Neo — Surgical Fix (`*swe fix <thing>`)
- Once confirmed, apply the minimal code modification required to address the root cause.
- Run the reproduction test locally via `bobp make test` to verify it now turns green.
- **Handoff:**
  ```bash
  bobp chat "Fix applied for <thing>; reproduction test green. @Trin *qa uat <thing>" --persona Neo --cmd "swe handoff" --to Trin
  ```

### Step 2: Trin — Verification & Regression Sweep (`*qa uat <thing>`)
- Run the reproduction test to verify the defect is resolved.
- Run the entire test suite via `bobp make test` to prove that no regressions or unintended side-effects were introduced.
- **Handoff on Pass:**
  ```bash
  bobp chat "Defect fix verified; zero regressions across suite. @Morpheus *lead review <thing>" --persona Trin --cmd "qa handoff" --to Morpheus
  ```

### Step 3: Morpheus — Code Review (`*lead review <thing>`)
- Review the diff to confirm it is a clean, minimal, non-leaky fix that aligns with existing architecture.
- Approve fix and close the loop.

---

## Anti-Loop Guard

If Neo's fix attempt fails twice:
1. **PAUSE**: Do not attempt a third blind fix.
2. **Consult Oracle**:
   ```bash
   bobp chat "@Oracle *ora ask Have we encountered this bug pattern before? Error: <trace>" --persona Neo --cmd "swe ask" --to Oracle
   ```
3. Allow ONE retry with Oracle's insight.
4. If that fails, escalate to the user with all logs.

---

## Loop Effectiveness Rubric (`LOOP_FIX`)

Reviewed by Morpheus (at Step 3 Code Review) or Smith (during `*judge fix`).  
Verdict line in `agents/CHAT.md`: `rubric LOOP_FIX: REPRO=L DIAG=L SURG=L NOSIDE=L GUARD=L`

| Code | Criterion | Weak (W) | Acceptable (A) | Strong (S) |
|---|---|---|---|---|
| `REPRO` | **Deterministic Reproduction** | Fix attempted directly on application code based on symptoms alone without an automated reproduction test or script. | Minimal, deterministic failing test or script created that reliably reproduces the observed defect prior to code edits. | Automated reproduction test captures minimal reproducing input, isolates environmental dependencies, and becomes a permanent regression test. |
| `DIAG` | **Root Cause Diagnosis** | Blind edits guessing at the fix; failed to explain underlying fault in CHAT.md; touched code without user/lead confirmation. | Root cause explained in CHAT.md distinguishing symptom from underlying fault; user or lead confirmed proposed fix before edits. | Pinpoints exact faulty invariant/symbol with stack trace analysis; explains why the bug occurred and why proposed fix prevents recurrence. |
| `SURG` | **Surgical Scope** | Sprawling diff modifying unrelated files, reformatting unrelated code, or bundling opportunistic feature changes. | Targeted diff restricted strictly to repairing the diagnosed fault; preserves surrounding conventions and styles. | Minimal lines changed; addresses root cause at the right layer without defensive workarounds or symptom-patching conditionals. |
| `NOSIDE` | **Regression Sweep** | Only checked that reproduction test passed without running full regression suite; new warnings or broken tests introduced. | Trin ran full test suite via `bobp make test`; verified reproduction test passes and all existing tests pass with 0 regressions. | Verified edge cases adjacent to the fix; verified performance was not degraded; clean test output captured in `build/build.out`. |
| `GUARD` | **Anti-Loop & Escalation** | Loop cycled 3+ times without resolution; blind trial-and-error edits; unlogged failure states. | Resolved on attempt 1 or 2; if attempt 2 failed, paused and consulted Oracle before third attempt. | First-pass resolution; defect and resolution logged to `docs/LESSONS.md` or `agents/oracle/lessons.md` to prevent future team recurrence. |
