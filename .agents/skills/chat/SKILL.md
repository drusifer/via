---
name: chat
description: Post a message (max 512 chars) with a 'why?' explanation to the team chat log (agents/CHAT.md). Use to communicate between personas, log progress updates, and coordinate handoffs between agents.
---
# Chat Skill

## Triggers

`*chat`, `*msg`, `*chat log`

## Overview

The `chat` skill posts structured messages to `agents/CHAT.md`, the shared team communication log. All personas use this to coordinate work and hand off tasks.

Every post also regenerates `agents/CHAT.diagram.md` — a Mermaid sequence diagram view of the same log, for humans following the conversation flow. It's a derived file; don't hand-edit it or read it back into agent context. Regenerate on demand with `bobp chat-diagram` (see `bob-tools` skill).

## Usage

```bash
bobp chat "<message>" [--persona <Name>] [--cmd <command>] [--to <recipient>]
```

### Arguments

| Argument | Flag | Default | Description |
|----------|------|---------|-------------|
| message | (positional) | required | Message content |
| persona | `--persona`/`-p` | `$USER` | Who is sending (e.g. `Neo`, `Trin`) |
| cmd | `--cmd`/`-c` | `chat` | Command prefix (auto-prefixed with `*`) |
| to | `--to`/`-t` | `all` | Recipient persona name (repeat the flag for multiple recipients) |

### Output Format

```
[DATETIME] [**Persona**]->[**recipient**] *cmd*:

 message
```

## Examples

### Log a user request
```bash
bobp chat "fix the bug in parser.py" --persona User --cmd request
```

### Post a persona response
```bash
bobp chat "Fixed bug in parser.py line 42" --persona Neo --cmd "swe fix" --to Trin
```

### Assign work to another persona
```bash
bobp chat "@Trin please verify the fix in parser.py" --persona Neo --cmd handoff --to Trin
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
    Use `bobp chat "..." --persona ... --cmd ... --to ...` to log activity and coordinate handoffs (max 512 chars).
    All personas must include a 'why?' explanation. Post on entry, work steps, handoff, and exit.
    Newest messages are at the END of `agents/CHAT.md` — always read the bottom for current context.

