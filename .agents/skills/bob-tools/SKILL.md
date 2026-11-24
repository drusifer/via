---
name: bob-tools
description: Use when working in a BobProtocol project and you need to understand or run the bobp CLI subcommands, especially chat, chat-diagram, make, setup-agent-links, and teardown-agent-links. This skill explains which commands to run, what each writes, and how to avoid flooding Codex context.
---

One-line summary: Use BobProtocol's tools through the `bobp` CLI's stable subcommands — never reach for the implementation modules under `bobp.tools` directly.

TLDR:
    Use `bobp chat "..." --persona X --cmd Y --to Z` for team log messages — it also regenerates `agents/CHAT.diagram.md` (a Mermaid sequence diagram of the log) automatically.
    Use `bobp chat-diagram` to regenerate the diagram on demand without posting a message.
    Use `bobp make <target>` to run this project's own `make <target>` — it captures output to `build/build.out` and posts build status. bobp does not install, own, or modify the project's Makefile.
    Use `bobp setup-agent-links` after installing/updating BobProtocol so Claude, Codex, root instruction links, via MCP, and Codex MCP are configured.
    Use `bobp teardown-agent-links --dry-run` to inspect generated links before removing them.

# BobProtocol Tools

## Triggers

`bobp chat`, `bobp make`, `bobp setup-agent-links`, `bobp teardown-agent-links`, `bob tools`, `BobProtocol tools`

## Tool Map

| Subcommand | Use for | Writes |
|------|---------|--------|
| `bobp chat "<msg>" --persona X --cmd Y --to Z` | Append short structured messages to `agents/CHAT.md` | `agents/CHAT.md`, `agents/CHAT.diagram.md` |
| `bobp chat-diagram [--include-builds]` | Render `agents/CHAT.md` as a Mermaid sequence diagram, for humans following the conversation flow | `agents/CHAT.diagram.md` |
| `bobp make [-v/-vv/-vvv] <target>` | Run this project's own `make <target>`, capturing build/test output and posting build status | `build/build.out`, `agents/CHAT.md` |
| `bobp setup-agent-links` | Create discovery links for Claude, Codex, root instruction files, delegate MCP setup to via, ensure the via index exists, register via with Codex MCP, and create missing project capabilities | `.agents/skills`, `$CODEX_HOME/skills`, root symlinks; `.mcp.json` via `via`; `.via/index.db`; Codex config via `codex mcp add`; `agents/PROJECT.md` when absent |
| `bobp teardown-agent-links [--dry-run]` | Remove discovery links created by setup and delegate MCP teardown to via/Codex | `.agents/skills`, `$CODEX_HOME/skills`, root symlinks; via may remove its own MCP config; Codex config via `codex mcp remove` |

## General Rules

- Always go through the `bobp` subcommand. Never call `python -m bobp.tools.<module>` or reach into the package internals directly — the subcommand is the stable interface.
- Do not pipe or redirect `bobp make` output into the conversation. It exists to keep full logs in `build/build.out`.
- Inspect `build/build.out` only when the tail or exit code is not enough.
- Keep chat messages under 256 characters. For longer status, write a Markdown summary file and chat the path plus a short summary.
- Consecutive `bobp make` build-status messages replace the previous build entry instead of appending, so routine build/test runs do not fill `agents/CHAT.md`.
- Run `bobp setup-agent-links` after changing `.agents/skills/*/SKILL.md`, adding a new persona folder (`agents/<name>/`), or installing BobProtocol into another project.
- Run teardown with `--dry-run` first. It removes only symlinks that point back into the current project and leaves Codex `.system` skills untouched.

## bobp chat

```bash
bobp chat "Fixed parser bug" --persona Neo --cmd "swe fix" --to Trin
```

Notes:
- `--cmd` is auto-prefixed with `*` when missing.
- `--to` defaults to `all`; pass it multiple times for multiple recipients.
- When `--persona make` and `--cmd build`, `bobp chat` overwrites the final chat entry if that entry is also a build message (this is what `bobp make` relies on to avoid flooding CHAT.md with routine build noise).
- Every successful post regenerates `agents/CHAT.diagram.md` as a best-effort side effect (a rendering failure prints a warning but never blocks the chat post).

## bobp chat-diagram

`agents/CHAT.diagram.md` is a derived Mermaid `sequenceDiagram` view of `agents/CHAT.md` — one arrow per `Persona->recipient` message, grouped with a date `Note` whenever the day changes, with build-status entries filtered out by default (they're noise for following the persona-to-persona conversation, not part of it). It splits the diagram at phase boundaries (`phase <N>` markers), sprint close (`pm launch`), and epic close (the transition from `plan epic` to `plan story`, or an explicit `epic close`): the diagram closes, a markdown section recaps the close-out (and announces the next phase), and a new self-contained diagram begins. These are deterministic recaps of logged outcome messages, not generated from hidden context. It's regenerated automatically by `bobp chat`; it's a read-only artifact for humans — don't hand-edit it, and agents shouldn't parse it back for context (read `agents/CHAT.md` itself, per the `chat` skill).

Regenerate on demand, e.g. after manually editing `CHAT.md` or archiving old messages:

```bash
bobp chat-diagram                    # skip build-status entries (default)
bobp chat-diagram --include-builds   # include them
```

## bobp make

See the `make` skill for the full contract. Short version: this project owns its own plain
`Makefile` — `bobp` never installs, generates, or modifies it. `bobp make` just runs
`make <target>` in it, captured:

```bash
bobp make test
bobp make -vv test
bobp make -vvv tldr
```

Verbosity (the flag comes *before* the target):
- *(none)*: quiet, full log in `build/build.out`
- `-v`: stderr
- `-vv`: stderr plus filtered failure lines
- `-vvv`: full stdout and stderr

After a run, use:

```bash
tail -20 build/build.out
```

## bobp setup-agent-links

Run this from the project root after setup or skill changes:

```bash
bobp setup-agent-links
```

It first converts an older project to the current layout: persona folders with the old `.docs`-suffixed names are renamed to `agents/<name>/` and the path references in the project's agent docs are updated to match (chat logs are left as history). `bobp update` runs the same conversion before refreshing files.

It discovers:
- personas from `.agents/skills/<name>/SKILL.md` (any folder directly under `agents/` that holds a `SKILL.md`)
- shared skills from `.agents/skills/*/SKILL.md`

It creates:
- `.agents/skills/<name>` links for Claude-style skill discovery, one per persona and shared skill. If `.agents/skills` is itself a symlink into `agents/` (e.g. `-> .agents/skills`), it is replaced with a real directory first so persona links never land inside `agents/`
- `$CODEX_HOME/skills/<name>` links so Codex loads BobProtocol skills on startup
- root instruction links: `AGENTS.md`, `GEMINI.md`, `CHATGPT.md`, `.cursorrules`, `.github/copilot-instructions.md`
- via MCP integration by running `via install mcp` when `via` is installed, then hardening `.mcp.json` with `HOME=<project-root>` and `--no-web`
- via index creation with `via index <project-root>` when `.via/index.db` is missing
- Codex MCP integration by running `codex mcp add via --env HOME=<project-root> -- <via> mcp serve --no-web <project-root>` when `codex` and `via` are installed
- `agents/PROJECT.md` when it is missing, with `via: enabled` only if via MCP setup succeeded

If writing to `$CODEX_HOME/skills` fails under sandboxing, rerun with approval. Restart Codex after creating or changing Codex skill links.

## bobp teardown-agent-links

Run this from the project root to undo setup:

```bash
bobp teardown-agent-links --dry-run
bobp teardown-agent-links
```

It removes only generated links/config owned by this project:
- `.agents/skills/*` symlinks that point into this repo
- `$CODEX_HOME/skills/*` symlinks that point into this repo
- root instruction symlinks: `AGENTS.md`, `GEMINI.md`, `CHATGPT.md`, `.cursorrules`, `.github/copilot-instructions.md`
- via MCP integration by running `via uninstall mcp`
- Codex MCP integration by running `codex mcp remove via`

It does not remove real files, unrelated symlinks, or `$CODEX_HOME/skills/.system`.

Use `--keep-mcp` to skip `via uninstall mcp`.
