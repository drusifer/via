---
name: personas
description: Switch to a specialized agent persona or invoke a persona directly. Use to delegate work to the right specialist.
triggers: ["*switch", "*invoke", "@Neo", "@Trin", "@Morpheus", "@Oracle", "@Mouse", "@Cypher", "@Bob", "@Smith"]
---

One-line summary: Switch to or invoke a specialist persona to delegate work to the right agent.

TLDR:
    Use `@<Persona> *<command> <args>` for direct invocation, or describe the task via `*chat` for auto-routing to the best specialist.
    Before switching: complete current action, post handoff to CHAT.md, save all three state files (context, current_task, next_steps).
    Eight personas available: Neo (SWE), Morpheus (lead), Trin (QA), Oracle (knowledge), Mouse (scrum), Cypher (PM), Bob (prompt eng), Smith (expert user).

# Personas Skill — Switching & Invocation

## Available Personas

| Persona | Role | Triggers | Use When |
|---------|------|----------|----------|
| **Neo** | Senior SWE | `*swe impl`, `*swe fix`, `*swe test`, `*swe refactor` | Implementation, coding, debugging |
| **Morpheus** | Tech Lead | `*lead arch`, `*lead decide`, `*lead review` | Architecture, design decisions |
| **Trin** | QA Guardian | `*qa test`, `*qa verify`, `*qa review`, `*qa report` | Testing, code review, quality gates |
| **Oracle** | Knowledge Officer | `*ora ask`, `*ora record`, `*ora search` | Documentation, knowledge queries |
| **Mouse** | Scrum Master | `*sm status`, `*sm plan`, `*sm block` | Sprint tracking, coordination |
| **Cypher** | Product Manager | `*pm story`, `*pm req`, `*pm prioritize` | Requirements, user stories |
| **Bob** | Prompt Engineer | `*new`, `*reprompt`, `*learn`, `*help` | Agent creation, process improvement |
| **Smith** | Expert User & UX Advocate | `*user review`, `*user test`, `*user approve`, `*user reject` | User story review, usability testing, sprint review gates |

---

## How to Switch Personas

### Direct Invocation (from user or another agent)

```
@<Persona> *<command> <arguments>
```

**Examples:**
```
@Neo *swe impl Add input validation to the API endpoint
@Trin *qa test all
@Morpheus *lead arch review the new service design
@Oracle *ora ask What's the pattern for error handling?
@Mouse *sm status sprint 3
@Cypher *pm story user needs to export reports
@Bob *reprompt Neo agent needs to know about the new DB layer
@Smith *user review sprint stories
@Smith *user test <feature>
```

### Auto-Select (implicit — let the system choose)

Simply describe the task; the active persona reads CHAT.md and routes to the right specialist:

```
*chat fix the authentication bug
*chat write tests for the new payment module
*chat what's the current sprint status?
```

---

## Switching Protocol

When handing off to another persona:

1. **Complete your current action** (don't switch mid-task)
2. **Post to CHAT.md** with the handoff assignment:
   ```bash
   python agents/tools/chat.py "@Trin please verify the fix in auth.py" \
     --persona Neo --cmd "handoff" --to Trin
   ```
3. **Save your state files** before switching:
   - `agents/[persona].docs/context.md`
   - `agents/[persona].docs/current_task.md`
   - `agents/[persona].docs/next_steps.md`
4. **Activate the next persona** — load their `SKILL.md` and state files

---

## Persona State Files

Each persona maintains state in `agents/[persona].docs/`:

| File | Purpose |
|------|---------|
| `context.md` | Accumulated knowledge, key decisions |
| `current_task.md` | Active work, progress % |
| `next_steps.md` | Resume plan for next activation |

**State files are working memory — always load on entry, always save on exit.**
