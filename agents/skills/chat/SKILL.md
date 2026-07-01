---
name: chat
description: Post a message (max 512 chars) with a 'why?' explanation to the team chat log (agents/CHAT.md). Use to communicate between personas, log progress updates, and coordinate handoffs between agents.
triggers: ["*chat", "*msg", "*chat log"]
---
# Chat Skill

## Overview

The `chat` skill posts structured messages to `agents/CHAT.md`, the shared team communication log. All personas use this to coordinate work and hand off tasks.

## Usage

```bash
make chat MSG="<message>" [PERSONA="<Name>"] [CMD="<command>"] [TO="<recipient>"]
```

### Arguments

| Argument | Variable | Default | Description |
|----------|----------|---------|-------------|
| message | `MSG` | required | Message content |
| persona | `PERSONA` | `$USER` | Who is sending (e.g. `Neo`, `Trin`) |
| cmd | `CMD` | `chat` | Command prefix (auto-prefixed with `*`) |
| to | `TO` | `all` | Recipient persona name |

### Output Format

```
[DATETIME] [**Persona**]->[**recipient**] *cmd*:

 message
```

## Examples

### Log a user request
```bash
make chat MSG="fix the bug in parser.py" PERSONA="User" CMD="request"
```

### Post a persona response
```bash
make chat MSG="Fixed bug in parser.py line 42" PERSONA="Neo" CMD="swe fix" TO="Trin"
```

### Assign work to another persona
```bash
make chat MSG="@Trin please verify the fix in parser.py" PERSONA="Neo" CMD="handoff" TO="Trin"
```

## Guidelines & Rules

1.  **Character Limit (HARD):** Every chat message must be under **512 characters** (using UTF-8 characters).
2.  **Elaborations ("the why?"):** All chat entries MUST include a brief explanation detailing *why* you are taking the action or proposing the handoff.

## When to Post

- **ENTRY**: After reading CHAT.md to acknowledge context.
- **WORK**: After completing each significant step. Include why the step was necessary.
- **HANDOFF**: When switching to another persona — assign the next task explicitly with the rationale.
- **HELP**: When you are not sure what to do next and need help from another agent or human.
- **EXIT**: Before saving state files.

## Reading the Chat Log

Always read `agents/CHAT.md` (newest messages at the END) before starting work:

```
Read agents/CHAT.md  # last 10-20 messages for context
```

One-line summary: Posts structured messages to the shared team chat log at `agents/CHAT.md` (max 512 chars).

TLDR:
    Use `make chat MSG="..." PERSONA="..." CMD="..." TO="..."` to log activity and coordinate handoffs (max 512 chars).
    All personas must include a 'why?' explanation. Post on entry, work steps, handoff, and exit.
    Newest messages are at the END of `agents/CHAT.md` — always read the bottom for current context.

