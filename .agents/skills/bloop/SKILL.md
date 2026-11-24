---
name: bloop
description: Work-Loops conductor and catalog. Autonomous multi-persona execution loops for features (*impl), bugfixes (*fix), refactoring (*refactor), spikes (*spike), UAT (*uat), deployments (*deploy), and agent/skill evaluation (*judge).
---

Top-level conductor and catalog for Bob Work-Loops (autonomous multi-persona execution chains).

TLDR:
    Work Loops are the atomic engineering execution units of Bob Protocol, deferred to by Sprint Planning.
    Seven specialized Work Loops: Feature (*impl), Bugfix (*fix), Tech Debt (*refactor), Spike (*spike), UAT (*uat), Deploy (*deploy), and Agent/Skill Quality (*judge).
    Each loop runs autonomously to completion — saving state and posting handoffs at every persona transition.
    Context Budget: If context > 60% between work loops, run *prep-clear before /clear.
    Anti-Loop Guard: Max 2 failures before Oracle consultation and user escalation.

# Bloop — Work-Loops Conductor & Catalog

## Triggers

`*bloop`, `/bloop`, `*work-loop`

## Requires

`bob-protocol`, `chat`, `make`, `prep-clear`, `impl`, `fix`, `refactor`, `spike`, `uat`, `deploy`, `judge`

## Overview

In the Bob Protocol SDLC hierarchy, **Planning Loops** (`epic` $\rightarrow$ `story` $\rightarrow$ `sprint`) determine *what* to build and *why*, breaking deliverables into an ordered pipeline in `task.md`.

**Work Loops (`bloop`)** are the atomic execution engines that determine *how* code is built, tested, and shipped. Each work loop is a self-contained, multi-persona chain grounded in established software engineering literature.

---

## The Work-Loops Catalog

| Work-Loop | Command | Primary Literature | Invariant / Hard Rule | Canonical Skill |
| :--- | :--- | :--- | :--- | :--- |
| **Feature** | `*impl <phase>` | Kent Beck (*TDD / XP*) | **Test-First**: Every feature requires an observable failing test before code is written. | [skills/impl](impl/SKILL.md) |
| **Bugfix** | `*fix <issue>` | David Agans (*Debugging*) | **Reproduce First**: Must reproduce with a test and confirm diagnosis with user before fixing. | [skills/fix](fix/SKILL.md) |
| **Tech Debt** | `*refactor <target>` | Martin Fowler (*Refactoring*) | **Two Hats**: Zero behavioral change. 100% test pass before and after. No new features. | [skills/refactor](refactor/SKILL.md) |
| **Spike** | `*spike <topic>` | Cunningham / Singer (*Shape Up*) | **Disposable**: Timeboxed exploration. Commits zero production code; produces `FINDING.md`. | [skills/spike](spike/SKILL.md) |
| **UAT** | `*uat <scope>` | Crispin & Gregory (*Agile Testing*) | **Real-World Experience**: Evaluates whole user journey against acceptance criteria & UX rubrics. | [skills/uat](uat/SKILL.md) |
| **Deploy** | `*deploy <env>` | Humble & Farley (*Continuous Delivery*) | **Pipeline as Code**: Driven through Makefile targets in `docs/SDLC.md` + post-deploy smoke test. | [skills/deploy](deploy/SKILL.md) |
| **Agent/Skill Quality** | `*judge <persona-or-skill>` | Eval-driven development | **Evidence-Led Revision**: Run a fixed scenario and rubric, fix diagnosed behavior, then verify in a fresh fixture; never retry unchanged prompts until green. | [skills/judge](judge/SKILL.md) |

---

## Work-Loop Handoff Format

Every persona participating in a work-loop must update their working memory in `state.md` and post an explicit handoff message to `agents/CHAT.md` before switching:

```bash
bobp chat "<summary> @NextPersona *command" --persona <Name> --cmd "<prefix> handoff" --to <next>
```

---

## Universal Work-Loop Invariants & Guard Rules

1. **Active Anti-Loop Guard (CRITICAL)**:
   If any loop iteration (e.g. Neo fix $\rightarrow$ Trin test fail $\rightarrow$ Neo fix) repeats **more than twice** without resolution:
   - **STOP** immediately.
   - Consult Oracle: `bobp chat "@Oracle *ora ask <error>" --persona <Name> --cmd ask --to Oracle`.
   - Attempt ONE retry with a new approach.
   - If that fails, escalate to the user with all logs. **No third attempt without explicit user approval.**

2. **Pre-Handoff Self-Validation**:
   Developers (Neo) must run targeted local tests and linters (`bobp make test`) before handing off code to QA (Trin). Trivial syntax or import errors should be resolved before persona transitions.

3. **Context Budgeting (`prep-clear`)**:
   Between consecutive work loops in `task.md`, inspect context token consumption. If context saturation exceeds **60%**, run `*prep-clear` to secure state before issuing `/clear` or `/compact`.

4. **No Protocol / Sub-Skill Reloading**:
   Do NOT re-invoke `bob-protocol`, `chat`, or `make` via meta-skill tools if already active in the session. Use `bobp` CLI commands directly via shell tools.

5. **Consolidation for Minor Changes**:
   For trivial configuration tweaks or single-line typo fixes, do not trigger a full multi-persona loop. Execute implementation, verification, and state update in a single focused step.

---

## Conductor Orchestration Rubric (`LOOP_BLOOP`)

Reviewed by Bob or Smith (during `*judge bloop`).  
Verdict line in `agents/CHAT.md`: `rubric LOOP_BLOOP: HANDOFF=L STATE=L ANTILOOP=L CAPTURE=L CONTEXT=L`

| Code | Criterion | Weak (W) | Acceptable (A) | Strong (S) |
|---|---|---|---|---|
| `HANDOFF` | **Handoff Ergonomics** | Silent transitions without handoff message; generic messages lacking command or why-rationale; messages exceeding 512 chars. | Formatted per `bobp chat` standard: `<summary> @NextPersona *command` with `why?` explanation under 512 chars. | Concise, highly informative handoffs specifying exact artifact paths, test counts, and immediate actionable directive. |
| `STATE` | **State Protocol Compliance** | Persona switched without updating `state.md`; missing Context, Current Task, or Next Steps sections; stale timestamps. | `state.md` updated with completed progress, active blockers, and concrete next actions before handoff. | Exemplary state fidelity: exact task percentages, crystal-clear cold-start resume plan, verified against `_template_state.md`. |
| `ANTILOOP` | **Anti-Loop Enforcement** | Agents repeatedly retried failing steps (3+ attempts); blind repetitive edits; thrashing between implementer and tester. | Paused immediately upon second failure; consulted Oracle for guidance; escalated to user if third attempt was needed. | Proactive root-cause triage on first failure preventing second; Oracle knowledge leveraged effectively to break impasses. |
| `CAPTURE` | **Automation & Capture** | Bare `make` or uncaptured raw shell commands executed; console flooded with verbose untracked output. | All build, test, and deploy operations executed via `bobp make <target>`; status automatically reported to CHAT.md. | Target discovery verified via `bobp make help`; quiet flags (`-q`) used during inner loops; build artifacts cleanly maintained. |
| `CONTEXT` | **Context Budgeting** | Context allowed to reach saturation/compaction without state checkpointing; working memory lost to context truncation. | Context checked between work loops; `*prep-clear` triggered when saturation exceeded 60% before issuing `/clear`. | Seamless multi-loop execution spanning multiple context resets with zero lost knowledge or redundant initialization steps. |
