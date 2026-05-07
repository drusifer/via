---
name: bob-protocol
description: Multi-persona coordination protocol. Enables AI to switch between specialized personas (Neo, Morpheus, Trin, Oracle, Mouse, Cypher, Bob, Smith) based on task needs. Use for *chat workflow, state management, and cross-agent communication.
triggers: ["*chat"]
requires: ["chat", "bloop", "sprint", "make"]
---

Orchestrates multi-persona AI coordination through a shared chat log using the `*chat` trigger.

TLDR:
    Routes `*chat` messages to the right specialist persona — by explicit `@mention` or auto-selection.
    Each persona loads state on entry, executes one task, saves state on exit, posts to `agents/CHAT.md`.
    For full workflow chains use loop commands (*fix, *impl, *qa, *review, *plan sprint) — see bloop skill.
    Key rule: no third fix attempt without Oracle consult + user sign-off.

# Bob Protocol — Multi-Persona Coordination

## Overview

One AI dynamically switches between specialized personas. All coordination happens through `agents/CHAT.md`. On cold start, each persona reads their state files to resume where they left off.

## Available Personas

Each persona is defined in `agents/<name>.docs/SKILL.md`:

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

---

## The `*chat` Workflow

### Step 1: Log User Message (ALWAYS FIRST)
```bash
make chat MSG="<user's message>" PERSONA="User" CMD="request"
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

For multi-step workflows, use a Bloop command instead: `*fix`, `*impl`, `*qa`, `*review`, `*plan sprint`.

### Step 4: Load Persona and Execute
1. Read `agents/<name>.docs/SKILL.md`
2. Load persona's state files: `context.md`, `current_task.md`, `next_steps.md`
3. If PROJECT.md exists: read `agents/PROJECT.md` for project capabilities
4. Adopt the persona and execute the command

### Step 5: Perform ONE Action
Execute one focused task. **Short iterations are key** — complete one thing, then stop.

### Step 6: Post Response to Chat
```bash
make chat MSG="<response>" PERSONA="<Name>" CMD="<command>" TO="<recipient>"
```

### Step 7: Save State — HARD GATE (MANDATORY BEFORE ANY SWITCH)
**Do not switch personas until all four steps below are complete.**

1. Write `agents/[persona].docs/context.md` — what was learned, key decisions
2. Write `agents/[persona].docs/current_task.md` — progress %, what was done, what's next
3. Write `agents/[persona].docs/next_steps.md` — exact resume instructions for a cold start
4. Post handoff: `make chat MSG="<summary> @Next *command" PERSONA="<Name>" CMD="handoff" TO="<next>"`

---

## State Management

**State files are the only memory that survives context overflow and session restarts.**
Write them as if you will never be asked again and someone else must continue.

### ENTRY
1. Read `agents/CHAT.md` — last 10-20 messages
2. Load `agents/[persona].docs/context.md`
3. Load `agents/[persona].docs/current_task.md`
4. Load `agents/[persona].docs/next_steps.md`
5. If `agents/PROJECT.md` exists — read it for project capabilities

### WORK
6. Execute assigned tasks
7. Post updates to `agents/CHAT.md` after each significant step

### EXIT — HARD GATE
8. Update `context.md`
9. Update `current_task.md`
10. Update `next_steps.md`
11. Post handoff message
12. Only now switch or stop

---

## Cold Start Recovery

When resuming after a context clear or new session with no memory:

1. Read bottom 20 messages of `agents/CHAT.md` — find the last handoff
2. Identify which persona was active and what command was pending
3. Load that persona's state files (`context.md`, `current_task.md`, `next_steps.md`)
4. Post a resume message: `make chat MSG="Resuming <task> from last session." PERSONA="<Name>" CMD="resume"`
5. Continue from `next_steps.md` — do not restart from scratch

If CHAT.md has no clear handoff, ask the user: "I'm resuming — what should I pick up?"

---

## Cross-Persona Communication

Use `@mentions` in CHAT.md to route work:

```bash
make chat MSG="@Neo *swe impl Task 4" PERSONA="Morpheus" CMD="lead handoff" TO="Neo"
make chat MSG="@Trin *qa test all" PERSONA="Neo" CMD="swe handoff" TO="Trin"
make chat MSG="@Oracle *ora ask Have we seen this error before?" PERSONA="Neo" CMD="swe ask" TO="Oracle"
make chat MSG="@Morpheus *lead decide <choice>" PERSONA="Trin" CMD="qa handoff" TO="Morpheus"
```

---

## Anti-Loop Protocol

If a fix attempt fails:

1. **STOP** — do not retry the same approach
2. **Consult Oracle**: `make chat MSG="@Oracle *ora ask Have we seen this error before? Error: <error>" PERSONA="<Name>" CMD="ask" TO="Oracle"`
3. Read error logs carefully — understand the root cause
4. ONE retry with a new approach
5. If that also fails → escalate: `make chat MSG="Blocked after 2 attempts on <task>. Tried: <A>, <B>. Recommend: <C>. Awaiting user input." PERSONA="<Name>" CMD="blocked" TO="User"`

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
