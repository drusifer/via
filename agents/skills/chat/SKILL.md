---
name: chat
description: Post a short (max 255 chars) message to the team chat log (agents/CHAT.md). Use to communicate between personas, log progress updates, and coordinate handoffs between agents.
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

## When to Post

- **ENTRY**: After reading CHAT.md to acknowledge context
- **WORK**: After completing each significant step
- **HANDOFF**: When switching to another persona — assign the next task explicitly
- **HELP**: When your are not sure what to do next and need help from another agent or human
- **EXIT**: Before saving state files

## Reading the Chat Log

Always read `agents/CHAT.md` (newest messages at the END) before starting work:

```
Read agents/CHAT.md  # last 10-20 messages for context
```

One-line summary: Posts structured messages to the shared team chat log at `agents/CHAT.md`.

TLDR:
    Use `make chat MSG="..." PERSONA="..." CMD="..." TO="..."` to log persona activity and coordinate handoffs between agents.
    All personas should post on entry, after significant work steps, on handoff, and before saving state on exit.
    Newest messages are at the END of `agents/CHAT.md` — always read the bottom for current context.

