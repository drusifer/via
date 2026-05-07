---
name: bloop
description: Top-level workflow loops (Bob Loops) that chain multiple personas autonomously. Use *fix, *review, *impl, *qa, or *plan sprint instead of manually invoking each persona in sequence.
triggers: ["*fix", "*review", "*impl", "*qa", "*plan sprint"]
requires: ["bob-protocol", "chat", "make"]
---

Top-level loop commands (Bloop) that run multi-persona chains autonomously without the user needing to invoke each step.

TLDR:
    Use Bloop commands when you want a full workflow, not a single-persona response.
    Each loop runs its persona chain to completion — saving state and posting handoffs at every step.
    For direct single-persona control, use `*chat @persona *command` instead.

# Bloop — Bob Loop Multi-Persona Workflow Commands

## Overview

Bloop commands trigger an **autonomous chain** of personas. Each persona completes its role, saves state, hands off to the next, and the chain continues until the loop is done or a gate requires input.

**Rule:** Every persona in a loop MUST save state and post a handoff message before switching — see bob-protocol State Management.

---

## Bloop Commands

### `*fix <thing>`
**Fix loop** — investigate, fix, test, and review a bug or broken behavior.

```
Chain: Neo → Trin → Morpheus
```

| Step | Persona | Action |
|------|---------|--------|
| 1 | Neo | Investigate and fix: `*swe fix <thing>` |
| 2 | Trin | Verify fix, run tests: `*qa uat <thing>` |
| 3 | Morpheus | Code review: `*lead review <thing>` |

- If Trin's tests fail → back to Neo (`*swe fix`)
- If Morpheus review fails → back to Neo (`*swe fix`)
- Anti-loop: if Neo fails twice → Oracle consult required before retry

**Example:** `*fix auth token expiry bug`

---

### `*impl <phase>`
**Implementation loop** — implement, test, and review a feature or sprint phase.

```
Chain: Neo → Trin → Morpheus
```

| Step | Persona | Action |
|------|---------|--------|
| 1 | Neo | TDD implementation: `*swe impl <phase>` |
| 2 | Trin | UAT — run tests, verify acceptance criteria: `*qa uat <phase>` |
| 3 | Morpheus | Code review — quality and architecture: `*lead review <phase>` |

- If Trin UAT fails → back to Neo for that phase only
- If Morpheus review fails → back to Neo for that phase only
- Do NOT restart the full sprint; fix the failing phase only

**Example:** `*impl phase-2`

---

### `*qa <thing>`
**QA loop** — test and review without reimplementation.

```
Chain: Trin → Morpheus
```

| Step | Persona | Action |
|------|---------|--------|
| 1 | Trin | Test and verify: `*qa test <thing>` |
| 2 | Morpheus | Review results: `*lead review <thing>` |

**Example:** `*qa the new export command`

---

### `*review <thing>`
**Review loop** — architecture and quality review of existing code or a deliverable.

```
Chain: Morpheus → Trin (optional)
```

| Step | Persona | Action |
|------|---------|--------|
| 1 | Morpheus | Architecture review: `*lead review <thing>` |
| 2 | Trin | Quality review (if Morpheus flags issues): `*qa review <thing>` |

**Example:** `*review the new API design`

---

### `*plan sprint`
**Sprint planning loop** — full planning sequence from stories through phase breakdown.

```
Chain: Cypher → [Smith gate] → Morpheus → [Smith gate] → Mouse → Morpheus review
```

| Step | Persona | Action | Gate |
|------|---------|--------|------|
| 1 | Cypher | Write stories + acceptance criteria: `*pm plan sprint` | Smith review |
| 1a | Smith | `*user review <stories>` → `*user approve` or `*user reject` | Must approve |
| 2 | Morpheus | Architecture decisions: `*lead arch sprint` | Smith review |
| 2a | Smith | `*user feedback <arch>` → `*user approve` or `*user reject` | Must approve |
| 3 | Mouse | Break into short phases (1-3 tasks each): `*sm plan sprint` | Morpheus review |
| 3a | Morpheus | Review sprint plan vs. architecture: `*lead review sprint plan` | |

**Gates are hard stops** — Smith must explicitly `*user approve` before the chain continues.

**Example:** `*plan sprint`

---

## When to Use Bloop vs. Direct Invocation

| Situation | Use |
|-----------|-----|
| Fix a bug end-to-end | `*fix <bug>` |
| Implement a feature with tests and review | `*impl <feature>` |
| Just run tests and review | `*qa <thing>` |
| Architect review only | `*review <thing>` |
| Full sprint planning | `*plan sprint` |
| Talk directly to one persona | `*chat @neo *swe fix X` |
| Single-step with full control | `*chat @trin *qa test all` |

---

## Loop Handoff Format

Every persona in a loop posts a handoff before switching:

```bash
make chat MSG="<summary> @NextPersona *command" PERSONA="<Name>" CMD="<prefix> handoff" TO="<next>"
```

The next persona reads CHAT.md on entry — if the handoff isn't there, they start blind.
