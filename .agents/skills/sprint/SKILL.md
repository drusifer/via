---
name: sprint
description: Sprint planning and execution container loop. Orchestrates SDLC verification, breaks stories into an ordered sequence of typed Work Loops in task.md, executes them, and manages sprint close.
---

Sprint planning and execution container loop: orchestrates the sprint cadence from SDLC gate through work-loop execution to launch.

TLDR:
    Literature: Ken Schwaber & Jeff Sutherland (*The Scrum Guide*).
    Hierarchy: Third Planning Loop, consuming deliverables from Epic (`*plan epic`) and Story (`*plan story`) loops.
    Composition: Compiles stories into an ordered pipeline of typed Work Loops (*impl, *fix, *refactor, *spike, *uat, *deploy) in `task.md`.
    Between work loops: Runs *prep-clear if context > 60% before /clear.
    Sprint Close: Tank SDLC check → Oracle groom & report → Smith acceptance → Team retro → Cypher launch.

# Sprint — Planning & Cadence Container Loop

## Triggers

`*plan sprint`, `/sprint`, `*sprint close`, `*sprint retro`, `*sprint launch`

## Requires

`bob-protocol`, `bloop`, `chat`, `make`, `prep-clear`, `epic`, `story`, `impl`, `fix`, `refactor`, `spike`, `uat`, `deploy`

## Overview

In the Bob Protocol SDLC hierarchy, the `sprint` loop serves as the **Execution Container**. It takes ready stories from the `story` planning loop, verifies SDLC governance ([docs/SDLC.md](file:///home/drusifer/Projects/bob_protocol/docs/SDLC.md)), structures `task.md` as an ordered sequence of typed **Work Loops**, manages context budgeting (`prep-clear`), and coordinates sprint close.

---

## Sprint Stages

```
Stage 0: SDLC Gate         → docs/SDLC.md verified by Tank (Blocker)
Stage 1: Sprint Planning   → Smith story gate → Morpheus arch → Smith + Switch design gates → Mouse structures task.md as typed Work Loops; Morpheus reviews
Stage 2: Work-Loop Execution → Sequential execution of Work Loops (*impl, *fix, *refactor, *spike, *uat, *deploy); each coding phase ends with a Switch security review
Stage 3: Sprint Close      → Tank SDLC check → Oracle groom → Smith UAT → Retro → Cypher launch
```


---

## Stage 0: SDLC Gate (blocker)

Before any story is written, check that `docs/SDLC.md` exists. It is Tank's definition of how
this project is built, tested, changed and released (see the `build-env` skill) — the source of
truth for change management. Every later step assumes it, and where this skill's generic steps
differ from what the SDLC says for this repository, follow the SDLC.

- **Present** → proceed to Stage 1.
- **Missing** → stop. Do not plan. Ask Tank to create it and wait for Tank's confirmation:

```bash
bobp chat "Sprint blocked: docs/SDLC.md is missing. @Tank *devops sdlc" --persona <Name> --cmd blocked --to Tank
```

This only checks that the document exists. Whether the project still matches it is checked at
close (Step 6a).

### Source control follows the SDLC

How a sprint uses git is defined by the project's `docs/SDLC.md` (change-management section),
not by this skill. Read it before the first change and apply it at three points:

- **Start** — if the SDLC calls for a sprint branch, create it before Cypher writes stories.
- **During** — commit as the SDLC says (who, how often, message convention), normally as each
  phase passes Morpheus's review. Mouse posts a phase marker to CHAT.md at the start of each
  phase: `bobp chat "<phase description>" --persona Mouse --cmd "phase <N>"`.
- **Close** — after Cypher's launch, integrate, version and tag as the SDLC says. Push only if
  the SDLC explicitly gives agents that right.

If the SDLC is silent on source control, do not commit; ask the user.

---

## Stage 1: Sprint Planning

### Step 1 — Cypher: Stories + Acceptance Criteria
```
Cypher *pm plan sprint
```
- Write the stories from `agents/templates/_template_USER_STORIES.md` (delete its rubric block)
- Define user stories with clear acceptance criteria
- Scope the sprint: what's in, what's out
- Self-check against the template's STORIES rubric before handing off
- Hand off to Smith for user review gate

**Handoff:**
```bash
bobp chat "Stories ready for user review. @Smith *user review <sprint>" --persona Cypher --cmd "pm handoff" --to Smith
```

### Gate 1 — Smith: User Story Review
```
Smith *user review <stories>
```
- Evaluate stories against HCI principles and user value
- Apply the STORIES rubric and report its verdict line (`rubric STORIES: OUT=A TEST=S ...`); any Weak rejects, naming the criterion and the fix — see `agents/templates/ARTIFACTS.md`
- Must post explicit approve or reject

```bash
# Approve → proceed to Morpheus
bobp chat "*user approve. Stories approved. @Morpheus *lead arch sprint" --persona Smith --cmd "user approve" --to Morpheus

# Reject → back to Cypher
bobp chat "*user reject REASON: <reason> | FIX: <fix>. @Cypher revise stories." --persona Smith --cmd "user reject" --to Cypher
```

### Step 2 — Morpheus: Architecture
```
Morpheus *lead arch sprint
```
- Write the architecture from `agents/templates/_template_ARCH.md` (delete its rubric block)
- Self-check against the template's ARCH rubric before handing off
- **Build-environment check:** read `docs/SDLC.md`. If the design adds a language, a new
  third-party dependency mechanism, a different package manager, a runtime version change, or a
  new standard make target, say so explicitly in the handoff — Mouse schedules it as a Tank
  Phase 0. Adding an ordinary dependency through the process the SDLC already describes is not a
  mechanism change.
- Record decisions via `@Oracle *ora record decision`
- Hand off to Smith for architecture review gate

**Handoff:**
```bash
bobp chat "Architecture complete. @Smith *user feedback <arch summary>" --persona Morpheus --cmd "lead handoff" --to Smith
```

### Gate 2 — Smith: Architecture Review
```
Smith *user feedback <arch>
```
- Evaluate architecture for UX impact (flag naming, output formats, breaking changes)
- Apply the ARCH rubric and report its verdict line (`rubric ARCH: BOUND=A FLOW=A FAIL=A USER=S DECS=A FEAS=A`); any Weak rejects, naming the criterion and the fix — see `agents/templates/ARTIFACTS.md`
- Must post explicit approve or reject

```bash
# Approve → proceed to Switch's security design gate
bobp chat "*user approve. Architecture approved. @Switch *sec threat sprint" --persona Smith --cmd "user approve" --to Switch

# Reject → back to Morpheus
bobp chat "*user reject REASON: <reason> | FIX: <fix>. @Morpheus revise arch." --persona Smith --cmd "user reject" --to Morpheus
```

### Gate 2b — Switch: Security Design Review
```
Switch *sec threat <sprint>
```
- Threat-model the approved architecture: assets, entry points, trust boundaries, abuse cases, and new dependencies, workflows, or secrets handling. Review the ADRs and `ARCH.md` against the Scope and Threat Model section of `agents/templates/_template_SECURITY_REVIEW.md`.
- Record any issue as a finding (`agents/templates/_template_SECURITY_FINDING.md`) with a Next Action table. Design-level fixes go back to Morpheus; Switch advises, Morpheus decides.
- **Depth scales with risk.** If the design adds no new input, data, dependency, permission, or pipeline surface, Switch posts a one-line quick pass that names what was checked and why nothing applies. Never skip the post.
- Post the verdict line `security gate (design): No blocking findings` or `Blocked SEC-NNN`. Any open High or Critical finding blocks the gate until it is fixed or the user accepts the risk.

```bash
# Clear → proceed to Mouse
bobp chat "Security design gate: No blocking findings. @Mouse *sm plan sprint" --persona Switch --cmd "sec handoff" --to Mouse

# Blocked → back to Morpheus
bobp chat "Security design gate: Blocked SEC-NNN. Next action in finding. @Morpheus revise arch." --persona Switch --cmd "sec reject" --to Morpheus
```

### Step 3 — Mouse: Phase Breakdown
```
Mouse *sm plan sprint
```
- Write sprint tasks to root `task.md` using `agents/templates/_template_task.md` (delete rubric block)
- Break sprint into phases of **1-3 tasks each** (no larger — context overflow risk)
- Give every coding phase a Switch security-review task after Trin's UAT and before Morpheus's review (Step 5a)
- Assign each executable task an L1–L4 complexity level using the task-template definitions. Base it on observable scope, dependencies, and uncertainty; use the lowest fitting level and split separable work with different levels. The level sets execution depth, not priority, duration, or persona rank.
- If Morpheus flagged a build-environment change, make it **Phase 0**, assigned to Tank
  (`*devops bootstrap` or `*devops sdlc`), before any Neo phase — Neo cannot build on an
  environment that does not exist yet. Deploy tasks, by contrast, stay last.
- Always include the close-out task "Tank `*devops sdlc-check`"
- Self-check against the template's PLAN rubric before handing off
- Record phases in `agents/mouse/sprint_log.md`
- Hand off to Morpheus for plan review

**Handoff:**
```bash
bobp chat "Sprint planned. Phases ready for review. @Morpheus *lead review sprint plan" --persona Mouse --cmd "sm handoff" --to Morpheus
```

### Step 3a — Morpheus: Sprint Plan Review
```
Morpheus *lead review sprint plan
```
- Verify phase breakdown aligns with architecture decisions
- Apply the PLAN rubric and report its verdict line (`rubric PLAN: SIZE=A GATE=A VERIF=A ALIGN=A OWNER=A LEVEL=A`); any Weak rejects, naming criterion and fix — see `agents/templates/ARTIFACTS.md`
- Approve or request adjustment to Mouse

**Handoff (approved):**
```bash
bobp chat "Sprint plan approved. Phase 1 ready. @Neo *swe impl phase-1" --persona Morpheus --cmd "lead handoff" --to Neo
```

---

## Stage 2: Phase Bloop

Repeat for each phase until all phases complete.

### Step 4 — Neo: Implementation
```
Neo *swe impl <phase N>
```
- TDD: write tests first, then implement
- Keep implementation scoped to this phase only

**Handoff:**
```bash
bobp chat "Phase N impl complete. @Trin *qa uat phase-N" --persona Neo --cmd "swe handoff" --to Trin
```

### Step 5 — Trin: UAT
```
Trin *qa uat <phase N>
```
- Run tests, verify all acceptance criteria for this phase using `agents/templates/_template_UAT_PLAN.md` (self-checked against the **UAT rubric**)
- Consult Oracle for expected behavior before asserting

**Handoff (pass):**
```bash
bobp chat "UAT phase N passed. @Switch *sec review phase-N" --persona Trin --cmd "qa handoff" --to Switch
```

**Handoff (fail):**
```bash
bobp chat "UAT phase N FAILED. @Neo *swe fix <issues>" --persona Trin --cmd "qa reject" --to Neo
```

### Step 5a — Switch: Security Implementation Review
```
Switch *sec review <phase N>
```
- Review the phase's diff (`git diff` for the phase) against the design gate's threat model and the area checklist in `agents/templates/_template_SECURITY_REVIEW.md`. Confirm the gitleaks setup first, as the Switch skill requires.
- Run `bobp make security-scan` when the phase touched dependencies, manifests, workflows, or secrets handling; otherwise the secrets scan is enough.
- Switch fixes vulnerable dependencies itself (tests and scan must pass afterward) and proposes patches for application source for Neo to apply.
- **Depth scales with risk.** A phase with no security-relevant change gets a one-line quick pass that states what was checked. Never skip the post.
- Post the verdict line `security gate (phase N): No blocking findings` or `Blocked SEC-NNN`. Any open High or Critical finding blocks the phase until it is fixed or the user accepts the risk.

**Handoff (clear):**
```bash
bobp chat "Security gate phase N: No blocking findings. @Morpheus *lead review phase-N" --persona Switch --cmd "sec handoff" --to Morpheus
```

**Handoff (blocked):**
```bash
bobp chat "Security gate phase N: Blocked SEC-NNN. Proposed fix in finding. @Neo *swe fix SEC-NNN" --persona Switch --cmd "sec reject" --to Neo
```
After the fix, Trin re-runs UAT, then Switch re-reviews (Anti-Loop applies: two failed rounds → Oracle, then user).

### Step 6 — Morpheus: Code Review
```
Morpheus *lead review <phase N>
```
- Review for architectural correctness, code quality, maintainability

**Handoff (pass — more phases):**
```bash
bobp chat "Phase N review passed. @Neo *swe impl phase-N+1" --persona Morpheus --cmd "lead handoff" --to Neo
```

**Handoff (pass — last phase):**
```bash
bobp chat "All phases reviewed. @Tank *devops sdlc-check" --persona Morpheus --cmd "lead handoff" --to Tank
```

**Handoff (fail):**
```bash
bobp chat "Phase N review FAILED. Issues: <issues>. @Neo *swe fix <issues>" --persona Morpheus --cmd "lead reject" --to Neo
```

**Fix loop rule:** If Neo fails to fix after one retry → Anti-Loop Protocol applies (Oracle consult + user escalation required).

---

Read [sprint close](references/sprint-close.md) when all phases have passed review and you are closing a sprint.

## Quick Reference

| Step | Persona | Command | Gate |
|------|---------|---------|------|
| 0 | (starter) | check `docs/SDLC.md` exists | Missing → `@Tank *devops sdlc`, blocked until written |
| 1 | Cypher | `*pm plan sprint` | → Smith `*user review` |
| 1a | Smith | `*user approve` / `*user reject` | Must approve to proceed |
| 2 | Morpheus | `*lead arch sprint` | → Smith `*user feedback` |
| 2a | Smith | `*user approve` / `*user reject` | Must approve to proceed |
| 2b | Switch | `*sec threat <sprint>` | Clear → Mouse; Blocked → Morpheus revises |
| 3 | Mouse | `*sm plan sprint` | → Morpheus `*lead review sprint plan` |
| 3a | Morpheus | `*lead review sprint plan` | Approve to start phase Bloop |
| 4 | Neo | `*swe impl <phase N>` | → Trin UAT |
| 5 | Trin | `*qa uat <phase N>` | → Switch security review |
| 5a | Switch | `*sec review <phase N>` | Clear → Morpheus; Blocked → Neo `*swe fix` |
| 6 | Morpheus | `*lead review <phase N>` | Pass → next phase or Tank |
| 6a | Tank | `*devops sdlc-check` | Pass → Oracle; regression → fix Bloop |
| 7 | Oracle | `*ora groom` | → Smith testing |
| 8 | Smith | `*user test` + `*user feedback` | Pass → retro; bug → fix Bloop |
| 9 | All | `*sprint retro` | Feed backlog to Cypher |
| 10 | Cypher | `*pm launch <sprint>` | Sprint complete |

---

## Rules

- **Short phases**: 1-3 tasks each. Large phases cause context overflow.
- **No skipping gates**: Smith's gates after steps 1 and 2, Switch's design gate (2b), and Switch's review after every coding phase (5a) are mandatory. Never auto-proceed. A gate may be a one-line quick pass when nothing security-relevant changed, but the verdict line must be posted.
- **SDLC bookends**: no planning without `docs/SDLC.md` (Stage 0); no close without Tank's `*devops sdlc-check` (Step 6a). Only Tank edits the SDLC.
- **Fix Bloop scope**: Fix Bloop targets the failing phase only — never restart the full sprint.
- **State saves**: Every persona saves state before every handoff (see bob-protocol State Management).
- **Chat first**: Post the handoff `bobp chat` call BEFORE switching. The next persona reads CHAT.md on entry.
- **Retro is required**: Step 9 is not optional. Retro output is the input to the next sprint's backlog.

---

Read [loop rubric](references/loop-rubric.md) when evaluating the sprint process.
