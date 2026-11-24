---
name: personas
description: Switch to a specialized agent persona or invoke a persona directly. Use to delegate work to the right specialist.
---

One-line summary: Switch to or invoke a specialist persona to delegate work to the right agent.

TLDR:
    Use `@<Persona> *<command> <args>` for direct invocation, or describe the task via `*chat` for auto-routing to the best specialist.
    Before switching: complete current action, post handoff to CHAT.md, save `state.md` (Context, Current Task, Next Steps sections).
    Ten personas available: Neo (SWE), Morpheus (lead), Trin (QA), Oracle (knowledge), Mouse (scrum), Cypher (PM), Bob (prompt eng), Smith (expert user), Tank (DevOps), Switch (security).

# Personas Skill — Switching & Invocation

## Triggers

`*switch`, `*invoke`, `@Neo`, `@Trin`, `@Morpheus`, `@Oracle`, `@Mouse`, `@Cypher`, `@Bob`, `@Smith`, `@Tank`, `@Switch`

## Available Personas

| Persona | Role | Triggers | Use When |
|---------|------|----------|----------|
| **Neo** | Senior SWE | `*swe impl`, `*swe fix`, `*swe test`, `*swe refactor` | Implementation, coding, debugging |
| **Morpheus** | Tech Lead | `*lead arch`, `*lead decide`, `*lead review` | Architecture, design decisions |
| **Trin** | QA Guardian | `*qa test`, `*qa verify`, `*qa review`, `*qa report` | Testing, code review, quality gates |
| **Oracle** | Knowledge Officer | `*ora ask`, `*ora record`, `*ora search` | Documentation, knowledge queries |
| **Mouse** | Scrum Master | `*sm status`, `*sm plan`, `*sm block` | Sprint tracking, coordination |
| **Cypher** | Product Manager | `*pm story`, `*pm req`, `*pm prioritize` | Requirements, user stories |
| **Bob** | Prompt Engineer | `*new`, `*reprompt`, `*learn`, `*help`, `*init` | Agent creation, process improvement, protocol init |
| **Smith** | Expert User & UX Advocate | `*user review`, `*user test`, `*user approve`, `*user reject` | User story review, usability testing, sprint review gates |
| **Switch** | Security Engineer | `*sec review`, `*sec threat`, `*sec deps`, `*sec audit`, `*sec triage` | Security reviews, threat models, dependency audits, severity triage with proposed fixes |
| **Tank** | DevOps Engineer | `*devops deploy`, `*devops infra`, `*devops ci`, `*devops env`, `*devops bootstrap`, `*devops sdlc` | Infrastructure, CI/CD, deployment, build environment, SDLC governance |

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
   bobp chat "@Trin please verify the fix in auth.py" \
     --persona Neo --cmd "handoff" --to Trin
   ```
3. **Save your state file** before switching:
   - `agents/[persona]/state.md`
4. **Activate the next persona** — load their `SKILL.md` and state file

---

## Persona State Files

Each persona maintains one state file in `agents/[persona]/`:

| File | Purpose |
|------|---------|
| `state.md` | Accumulated knowledge/key decisions, active work/progress %, resume plan for next activation (context, current task, next steps sections) |

**`state.md` is working memory — always load on entry, always save on exit.**
