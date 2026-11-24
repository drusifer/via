---
name: bob-protocol
description: Multi-persona coordination protocol. Enables AI to switch between specialized personas (Neo, Morpheus, Trin, Oracle, Mouse, Cypher, Bob, Smith, Tank, Switch) based on task needs. Use for *chat workflow, state management, and cross-agent communication.
---

Orchestrates multi-persona AI coordination through a shared chat log using the `*chat` trigger.

TLDR:
    Routes `*chat` messages to the right specialist persona — by explicit `@mention` or auto-selection.
    Each persona loads state on entry, executes one task, saves state on exit, posts to `agents/CHAT.md`.
    For full workflow chains use loop commands (*fix, *impl, *qa, *review, *plan sprint) — see bloop skill.
    Key rule: no third fix attempt without Oracle consult + user sign-off.

# Bob Protocol — Multi-Persona Coordination

## Triggers

`*chat`

## Requires

`chat`, `bloop`, `sprint`, `make`, `init`, `prep-clear`

## Overview

One AI dynamically switches between specialized personas. All coordination happens through `agents/CHAT.md`. On cold start, each persona reads their state files to resume where they left off.

## Planning Questions and Assumptions

During planning, ask the user about an unresolved decision only when the answer could materially change user-visible scope or outcomes, obligations, safety or privacy, data handling, compatibility, a hard-to-reverse architectural choice, or a significant resource or release commitment. Explain why the decision matters and offer focused options when useful. Continue any planning work that does not depend on the answer.

For routine or reversible choices—such as naming, formatting, implementation details, or a conventional tool choice—follow repository conventions and established best practices. State a material assumption briefly and keep planning; do not interrupt the user to resolve ordinary details.

## Available Personas

Each persona is defined in `.agents/skills/<name>/SKILL.md`:

| Persona | Role | Prefix | Use When |
|---------|------|--------|----------|
| **Neo** | Senior SWE | `*swe` | Implementation, coding, debugging |
| **Morpheus** | Tech Lead | `*lead` | Architecture, design decisions |
| **Trin** | QA Guardian | `*qa` | Testing, code review |
| **Oracle** | Knowledge Officer | `*ora` | Documentation, knowledge queries |
| **Mouse** | Scrum Master | `*sm` | Sprint tracking, coordination |
| **Cypher** | Product Manager | `*pm` | Requirements, user stories |
| **Bob** | Prompt Engineer | `*prompt` | Agent creation, process improvement |
| **Smith** | HCI Expert | `*user` | UX review, usability testing, sprint gates |
| **Tank** | DevOps Engineer | `*devops` | Infrastructure, CI/CD, deployment, env hygiene |
| **Switch** | Security Engineer | `*sec` | Security review, threat modeling, build scans, dependency fixes, severity triage |

---

## The `*chat` Workflow

### Step 1: Log User Message (ALWAYS FIRST)
```bash
bobp chat "<user's message>" --persona User --cmd request
```

**Note on External Invocations**: Different AI harnesses use different prefixes for direct persona invocation (e.g., `@persona` or `/persona` in Gemini CLI, `/persona` in Claude, `$persona` in Codex). If you are invoked directly via such a command, you MUST log the invocation to `agents/CHAT.md` immediately upon entry if it has not already been logged. This ensures the shared team context is complete.

### Step 2: Read Chat Log
Read the bottom of `agents/CHAT.md` (newest messages at END, last 10-20 messages).

### Step 3: Identify Persona and Command

#### Mode A — Direct Invocation (Explicit `@mention`)
```
*chat @neo *fix bug in parser.py
*chat @trin *test all
*chat @morpheus *arch review the API design
*chat @smith *user review the sprint stories
```
Parse: `@neo` → persona, `*fix` → command (`*swe fix`), remainder → arguments. Skip to Step 4.

#### Mode B — Auto-Select (No `@mention`)
Analyze the request and route to the best persona:

| Request type | Route to |
|-------------|----------|
| Coding, debugging, implementation | Neo (`*swe`) |
| Architecture, design decisions | Morpheus (`*lead`) |
| Testing, code review | Trin (`*qa`) |
| Documentation, knowledge queries | Oracle (`*ora`) |
| Sprint status, coordination | Mouse (`*sm`) |
| Requirements, user stories | Cypher (`*pm`) |
| Agent creation, prompt improvement | Bob (`*prompt`) |
| UX review, usability, sprint gates | Smith (`*user`) |
| Infrastructure, CI/CD, deployment | Tank (`*devops`) |
| Security review, threat model, vulnerability triage | Switch (`*sec`) |

For multi-step workflows, use a Bloop command instead: `*fix`, `*impl`, `*qa`, `*review`, `*plan sprint`.

### Step 4: Load Persona and Execute
1. Read `.agents/skills/<name>/SKILL.md`
2. Load persona's state: `agents/<name>/state.md` (context, current task, and resume plan in one file)
3. If PROJECT.md exists: read `agents/PROJECT.md` for project capabilities
4. Adopt the persona and execute the command

### Step 5: Perform ONE Action
Execute one focused task. **Short iterations are key** — complete one thing, then stop.

### Step 6: Post Response to Chat
```bash
bobp chat "<response>" --persona <Name> --cmd <command> --to <recipient>
```

### Step 7: Save State — HARD GATE (MANDATORY BEFORE ANY SWITCH)
**Do not switch personas until both steps below are complete.**

1. Write `agents/[persona]/state.md` — what was learned/decided, progress %, what's next, and exact resume instructions for a cold start, all in one file
2. Post handoff: `bobp chat "<summary> @Next *command" --persona <Name> --cmd handoff --to <next>`

---

## State Management

**`state.md` is the only memory that survives context overflow and session restarts.**
Write it as if you will never be asked again and someone else must continue.

Each persona has exactly one state file — `agents/[persona]/state.md` — with three sections: `## Context` (what was learned, key decisions), `## Current Task` (progress %, what was done, what's next), `## Next Steps` (exact resume instructions for a cold start). This replaces the older three-file convention (`context.md`/`current_task.md`/`next_steps.md`); consolidating cut state-management tool calls per switch by two-thirds with no loss of resilience, since the file is still written every switch, just as one call instead of three.

For a **large, growing reference doc** (not `state.md` itself — those stay small) like `agents/oracle/lessons.md`, `agents/oracle/memory.md`, or `docs/ARCH.md`, don't re-read the whole file on every entry once it accumulates many dated entries. If `via` is enabled, locate the section you need first (`via -mg '*SectionName*' -tH` returns `file:start-end`), then read only that range (`Read` with `offset`/`limit`) — see the `via` skill's "Section-Scoped Reads" note. Do not rely on `via`'s `-oR -A N` alone for this: `-A N` is a blind line-count window, not section-aware, and will run past the section boundary into the next one if `N` is too large.

### ENTRY (When Activating / Rapid Startup)

See instructions here -> `.agents/skills/init/SKILL.md`

1. Read `agents/CHAT.md` — last 10-20 messages
2. Load `agents/[persona]/state.md`
3. **Rapid Startup Option (CRITICAL)**: Do NOT run a full test suite baseline check (`bobp make test`) or other heavy execution cycles on initialization unless explicitly requested or implementing/testing bug fixes. Reconcile state quickly and proceed.
4. Verify that agent links are synced (run `bobp setup-agent-links` if needed).
5. Post your persona initialization message using `bobp chat` immediately.
6. If `agents/PROJECT.md` exists — read it for project capabilities

### WORK
7. Execute assigned tasks
8. Post updates to `agents/CHAT.md` after each significant step

### EXIT — HARD GATE

See instructions here -> `.agents/skills/prep-clear/SKILL.md`

9. Update `agents/[persona]/state.md` (Context, Current Task, Next Steps sections)
10. Post handoff message
11. Only now switch or stop

---

## Cold Start Recovery

See instructions here -> `.agents/skills/init/SKILL.md`

When resuming after a context clear or new session with no memory:

1. Read bottom 20 messages of `agents/CHAT.md` — find the last handoff
2. Identify which persona was active and what command was pending
3. Load that persona's `state.md`
4. Post a resume message: `bobp chat "Resuming <task> from last session." --persona <Name> --cmd resume`
5. Continue from the `## Next Steps` section of `state.md` — do not restart from scratch

If CHAT.md has no clear handoff, ask the user: "I'm resuming — what should I pick up?"

---

## Cross-Persona Communication

Use `@mentions` in CHAT.md to route work:

```bash
bobp chat "@Neo *swe impl Task 4" --persona Morpheus --cmd "lead handoff" --to Neo
bobp chat "@Trin *qa test all" --persona Neo --cmd "swe handoff" --to Trin
bobp chat "@Oracle *ora ask Have we seen this error before?" --persona Neo --cmd "swe ask" --to Oracle
bobp chat "@Morpheus *lead decide <choice>" --persona Trin --cmd "qa handoff" --to Morpheus
```

---

## Anti-Loop Protocol

If a fix attempt fails:

1. **STOP** — do not retry the same approach
2. **Consult Oracle**: `bobp chat "@Oracle *ora ask Have we seen this error before? Error: <error>" --persona <Name> --cmd ask --to Oracle`
3. Read error logs carefully — understand the root cause
4. ONE retry with a new approach
5. If that also fails → escalate: `bobp chat "Blocked after 2 attempts on <task>. Tried: <A>, <B>. Recommend: <C>. Awaiting user input." --persona <Name> --cmd blocked --to User`

**No third attempt without Oracle consult + explicit user approval.**

---

## Chat Message Format

```
[DATETIME] [**Persona**]->[**recipient**] *cmd*:

 message
```

---

## Direct Invocation Quick Reference

| User Types | Persona | Command Executed |
|------------|---------|-----------------|
| `*chat @neo *fix X` | Neo | `*swe fix X` |
| `*chat @neo *impl Y` | Neo | `*swe impl Y` |
| `*chat @trin *test all` | Trin | `*qa test all` |
| `*chat @morpheus *arch Z` | Morpheus | `*lead arch Z` |
| `*chat @oracle *ask Q` | Oracle | `*ora ask Q` |
| `*chat @mouse *status` | Mouse | `*sm status` |
| `*chat @cypher *req R` | Cypher | `*pm req R` |
| `*chat @bob *prompt P` | Bob | `*prompt P` |
| `*chat @smith *user review S` | Smith | `*user review S` |
| `*chat @smith *user approve` | Smith | `*user approve` |
| `*chat @tank *devops deploy` | Tank | `*devops deploy` |
| `*chat @tank *devops sdlc` | Tank | `*devops sdlc` |
| `*chat @switch *sec review` | Switch | `*sec review` |
