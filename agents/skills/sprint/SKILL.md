---
name: sprint
description: Full sprint implementation cycle. Covers planning, phase loop, sprint close, retrospective, and launch. Use *plan sprint to start, then *impl <phase> for each phase.
triggers: ["*plan sprint", "*sprint close", "*sprint retro", "*sprint launch"]
requires: ["bob-protocol", "loops", "chat", "make"]
---

Full sprint cycle from planning through launch, including all review gates, phase loops, and handoff templates.

TLDR:
    Sprints have three stages: Planning (Cypher→Smith→Morpheus→Mouse), Phase Loop (*impl per phase), and Close (Oracle→Smith→All retro→Cypher launch).
    Smith gates after Cypher and Morpheus are mandatory — do not auto-proceed without explicit `*user approve`.
    Keep phases small: 1-3 tasks each. Large phases cause context overflow.

# Sprint — Full Implementation Cycle

## Sprint Stages

```
Stage 1: Planning     → Cypher → Smith gate → Morpheus → Smith gate → Mouse → Morpheus review
Stage 2: Phase Loop   → (Neo → Trin → Morpheus) × N phases
Stage 3: Close        → Oracle → Smith → All retro → Cypher launch
```

---

## Stage 1: Sprint Planning

### Step 1 — Cypher: Stories + Acceptance Criteria
```
Cypher *pm plan sprint
```
- Define user stories with clear acceptance criteria
- Scope the sprint: what's in, what's out
- Hand off to Smith for user review gate

**Handoff:**
```bash
make chat MSG="Stories ready for user review. @Smith *user review <sprint>" PERSONA="Cypher" CMD="pm handoff" TO="Smith"
```

### Gate 1 — Smith: User Story Review
```
Smith *user review <stories>
```
- Evaluate stories against HCI principles and user value
- Check: are acceptance criteria testable and user-facing?
- Must post explicit approve or reject

```bash
# Approve → proceed to Morpheus
make chat MSG="*user approve. Stories approved. @Morpheus *lead arch sprint" PERSONA="Smith" CMD="user approve" TO="Morpheus"

# Reject → back to Cypher
make chat MSG="*user reject REASON: <reason> | FIX: <fix>. @Cypher revise stories." PERSONA="Smith" CMD="user reject" TO="Cypher"
```

### Step 2 — Morpheus: Architecture
```
Morpheus *lead arch sprint
```
- Define architecture decisions and technical design
- Record decisions via `@Oracle *ora record decision`
- Hand off to Smith for architecture review gate

**Handoff:**
```bash
make chat MSG="Architecture complete. @Smith *user feedback <arch summary>" PERSONA="Morpheus" CMD="lead handoff" TO="Smith"
```

### Gate 2 — Smith: Architecture Review
```
Smith *user feedback <arch>
```
- Evaluate architecture for UX impact (flag naming, output formats, breaking changes)
- Must post explicit approve or reject

```bash
# Approve → proceed to Mouse
make chat MSG="*user approve. Architecture approved. @Mouse *sm plan sprint" PERSONA="Smith" CMD="user approve" TO="Mouse"

# Reject → back to Morpheus
make chat MSG="*user reject REASON: <reason> | FIX: <fix>. @Morpheus revise arch." PERSONA="Smith" CMD="user reject" TO="Morpheus"
```

### Step 3 — Mouse: Phase Breakdown
```
Mouse *sm plan sprint
```
- Break sprint into phases of **1-3 tasks each** (no larger — context overflow risk)
- Record phases in `agents/mouse.docs/sprint_log.md`
- Hand off to Morpheus for plan review

**Handoff:**
```bash
make chat MSG="Sprint planned. Phases ready for review. @Morpheus *lead review sprint plan" PERSONA="Mouse" CMD="sm handoff" TO="Morpheus"
```

### Step 3a — Morpheus: Sprint Plan Review
```
Morpheus *lead review sprint plan
```
- Verify phase breakdown aligns with architecture decisions
- Approve or request adjustment to Mouse

**Handoff (approved):**
```bash
make chat MSG="Sprint plan approved. Phase 1 ready. @Neo *swe impl phase-1" PERSONA="Morpheus" CMD="lead handoff" TO="Neo"
```

---

## Stage 2: Phase Loop

Repeat for each phase until all phases complete.

### Step 4 — Neo: Implementation
```
Neo *swe impl <phase N>
```
- TDD: write tests first, then implement
- Keep implementation scoped to this phase only

**Handoff:**
```bash
make chat MSG="Phase N impl complete. @Trin *qa uat phase-N" PERSONA="Neo" CMD="swe handoff" TO="Trin"
```

### Step 5 — Trin: UAT
```
Trin *qa uat <phase N>
```
- Run tests, verify all acceptance criteria for this phase
- Consult Oracle for expected behavior before asserting

**Handoff (pass):**
```bash
make chat MSG="UAT phase N passed. @Morpheus *lead review phase-N" PERSONA="Trin" CMD="qa handoff" TO="Morpheus"
```

**Handoff (fail):**
```bash
make chat MSG="UAT phase N FAILED. @Neo *swe fix <issues>" PERSONA="Trin" CMD="qa reject" TO="Neo"
```

### Step 6 — Morpheus: Code Review
```
Morpheus *lead review <phase N>
```
- Review for architectural correctness, code quality, maintainability

**Handoff (pass — more phases):**
```bash
make chat MSG="Phase N review passed. @Neo *swe impl phase-N+1" PERSONA="Morpheus" CMD="lead handoff" TO="Neo"
```

**Handoff (pass — last phase):**
```bash
make chat MSG="All phases reviewed. @Oracle *ora groom" PERSONA="Morpheus" CMD="lead handoff" TO="Oracle"
```

**Handoff (fail):**
```bash
make chat MSG="Phase N review FAILED. Issues: <issues>. @Neo *swe fix <issues>" PERSONA="Morpheus" CMD="lead reject" TO="Neo"
```

**Fix loop rule:** If Neo fails to fix after one retry → Anti-Loop Protocol applies (Oracle consult + user escalation required).

---

## Stage 3: Sprint Close

### Step 7 — Oracle: Groom
```
Oracle *ora groom
```
- Update docs, record decisions, archive sprint artifacts
- Ensure CHAT.md is archived if over 50-100 messages

**Handoff:**
```bash
make chat MSG="Docs groomed. @Smith *user test <sprint>" PERSONA="Oracle" CMD="ora handoff" TO="Smith"
```

### Step 8 — Smith: End-to-End User Testing
```
Smith *user test <sprint>
Smith *user feedback
```
- Test all delivered features from the user's perspective
- Apply HCI heuristics — flag rough edges, inconsistencies, confusing interfaces

**Handoff (pass):**
```bash
make chat MSG="User testing passed. @all *sprint retro" PERSONA="Smith" CMD="user approve" TO="all"
```

**Handoff (bug found):**
```bash
make chat MSG="*user bug CMD: <cmd> | EXPECTED: <x> | ACTUAL: <y> | UX ISSUE: <z>. @Trin triage." PERSONA="Smith" CMD="user bug" TO="Trin"
```
→ Trin triages → fix loop → re-test before retro

### Step 9 — All Personas: Sprint Retrospective
```
*sprint retro
```
Each persona posts their domain retrospective to CHAT.md:

| Persona | Retrospective focus |
|---------|-------------------|
| Neo | Code quality, tech debt, implementation friction |
| Trin | Test coverage, regressions caught, test suite health |
| Morpheus | Architecture decisions made, anything to revisit |
| Oracle | Documentation gaps, decisions not recorded |
| Mouse | Phase sizing, blockers, velocity |
| Cypher | Story quality, acceptance criteria accuracy |
| Smith | UX issues, HCI gaps, user feedback themes |

Output feeds Cypher's backlog before launch.

```bash
# Each persona posts:
make chat MSG="<persona> retro: <findings>. Backlog items: <items>" PERSONA="<Name>" CMD="retro" TO="Cypher"
```

### Step 10 — Cypher: Launch
```
Cypher *pm launch <sprint>
```
- Announce release
- Add retro feedback to backlog
- Update changelog
- Close sprint

**Handoff:**
```bash
make chat MSG="*pm launch <sprint>. Sprint complete." PERSONA="Cypher" CMD="pm launch" TO="all"
```

**Sprint is complete** when Cypher posts `*pm launch`.

---

## Quick Reference

| Step | Persona | Command | Gate |
|------|---------|---------|------|
| 1 | Cypher | `*pm plan sprint` | → Smith `*user review` |
| 1a | Smith | `*user approve` / `*user reject` | Must approve to proceed |
| 2 | Morpheus | `*lead arch sprint` | → Smith `*user feedback` |
| 2a | Smith | `*user approve` / `*user reject` | Must approve to proceed |
| 3 | Mouse | `*sm plan sprint` | → Morpheus `*lead review sprint plan` |
| 3a | Morpheus | `*lead review sprint plan` | Approve to start phase loop |
| 4 | Neo | `*swe impl <phase N>` | → Trin UAT |
| 5 | Trin | `*qa uat <phase N>` | → Morpheus review |
| 6 | Morpheus | `*lead review <phase N>` | Pass → next phase or Oracle |
| 7 | Oracle | `*ora groom` | → Smith testing |
| 8 | Smith | `*user test` + `*user feedback` | Pass → retro; bug → fix loop |
| 9 | All | `*sprint retro` | Feed backlog to Cypher |
| 10 | Cypher | `*pm launch <sprint>` | Sprint complete |

---

## Rules

- **Short phases**: 1-3 tasks each. Large phases cause context overflow.
- **No skipping gates**: Smith's gates after steps 1 and 2 are mandatory. Never auto-proceed.
- **Fix loop scope**: Fix loop targets the failing phase only — never restart the full sprint.
- **State saves**: Every persona saves state before every handoff (see bob-protocol State Management).
- **Chat first**: Post the handoff `make chat` call BEFORE switching. The next persona reads CHAT.md on entry.
- **Retro is required**: Step 9 is not optional. Retro output is the input to the next sprint's backlog.
