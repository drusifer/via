---
name: bob-tools
description: Use when working in a BobProtocol project and you need to understand or run the project tool scripts in agents/tools, especially chat.py, mkf.py, setup_agent_links.py, and teardown_agent_links.py. This skill explains which commands to run, when to prefer Makefile wrappers, what each tool writes, and how to avoid flooding Codex context.
triggers: ["agents/tools", "chat.py", "mkf.py", "setup_agent_links.py", "teardown_agent_links.py", "bob tools", "BobProtocol tools"]
---

One-line summary: Use BobProtocol project tools through their stable command surfaces, usually `make`, and only call scripts directly for setup or debugging.

TLDR:
    Use `make chat MSG="..." PERSONA="..." CMD="..." TO="..."` for team log messages.
    Use `make <target>` for project automation; `mkf.py` wraps most targets automatically and writes full output to `build/build.out`.
    Use `python agents/tools/setup_agent_links.py` after installing/updating BobProtocol so Claude, Codex, root instruction links, via MCP, and Codex MCP are configured.
    Use `python agents/tools/teardown_agent_links.py --dry-run` to inspect generated links before removing them.

# BobProtocol Tools

## Tool Map

| Tool | Preferred command | Use for | Writes |
|------|-------------------|---------|--------|
| `agents/tools/chat.py` | `make chat MSG="..." PERSONA="..." CMD="..." TO="..."` | Append short structured messages to `agents/CHAT.md` | `agents/CHAT.md` |
| `agents/tools/mkf.py` | `make <target> [V=-v/-vv/-vvv]` | Capture build/test output and post build status | `build/build.out`, `agents/CHAT.md` |
| `agents/tools/setup_agent_links.py` | `python agents/tools/setup_agent_links.py` | Create discovery links for Claude, Codex, root instruction files, delegate MCP setup to via, ensure the via index exists, register via with Codex MCP, and create missing project capabilities | `.claude/skills`, `$CODEX_HOME/skills`, root symlinks; `.mcp.json` via `via`; `.via/index.db`; Codex config via `codex mcp add`; `agents/PROJECT.md` when absent |
| `agents/tools/teardown_agent_links.py` | `python agents/tools/teardown_agent_links.py --dry-run` | Remove discovery links created by setup and delegate MCP teardown to via/Codex | `.claude/skills`, `$CODEX_HOME/skills`, root symlinks; via may remove its own MCP config; Codex config via `codex mcp remove` |

## General Rules

- Prefer the Makefile wrapper when one exists. `make chat` and `make <target>` are the public interface.
- Do not pipe or redirect `make` output into the conversation. `mkf.py` exists to keep full logs in `build/build.out`.
- Inspect `build/build.out` only when the tail or exit code is not enough.
- Keep chat messages under 256 characters. For longer status, write a Markdown summary file and chat the path plus a short summary.
- Consecutive `make` build-status messages replace the previous `make` build entry instead of appending, so routine build/test runs do not fill `agents/CHAT.md`.
- Run setup links after changing `agents/skills/*/SKILL.md`, adding a new persona docs folder, or installing BobProtocol into another project.
- Run teardown with `--dry-run` first. It removes only symlinks that point back into the current project and leaves Codex `.system` skills untouched.

## chat.py

Use through Make:

```bash
make chat MSG="Fixed parser bug" PERSONA="Neo" CMD="swe fix" TO="Trin"
```

Direct form, mainly for debugging:

```bash
python agents/tools/chat.py "Fixed parser bug" --persona Neo --cmd "swe fix" --to Trin
```

Notes:
- `CMD` is auto-prefixed with `*` when missing.
- `TO` defaults to `all`.
- Multiple `--to` flags are supported by the Python tool.
- When `PERSONA=make` and `CMD=build`, `chat.py` overwrites the final chat entry if that entry is also a make build message.

## mkf.py

Do not call `mkf.py` directly during normal work. The Makefile routes normal targets through it.

```bash
make test
make test V=-vv
make tldr V=-vvv
```

Verbosity:
- no `V`: quiet, full log in `build/build.out`
- `V=-v`: stderr
- `V=-vv`: stderr plus filtered failure lines
- `V=-vvv`: full stdout and stderr

After a run, use:

```bash
tail -20 build/build.out
```

## setup_agent_links.py

Run this from the project root after setup or skill changes:

```bash
python agents/tools/setup_agent_links.py
```

It discovers:
- personas from `agents/*.docs/SKILL.md`
- shared skills from `agents/skills/*/SKILL.md`

It creates:
- `.claude/skills/<name>` links for Claude-style skill discovery
- `$CODEX_HOME/skills/<name>` links so Codex loads BobProtocol skills on startup
- root instruction links: `AGENTS.md`, `GEMINI.md`, `CHATGPT.md`, `.cursorrules`, `.github/copilot-instructions.md`
- via MCP integration by running `via install mcp` when `via` is installed, then hardening `.mcp.json` with `HOME=<project-root>` and `--no-web`
- via index creation with `via index <project-root>` when `.via/index.db` is missing
- Codex MCP integration by running `codex mcp add via --env HOME=<project-root> -- <via> mcp serve --no-web <project-root>` when `codex` and `via` are installed
- `agents/PROJECT.md` when it is missing, with `via: enabled` only if via MCP setup succeeded

If writing to `$CODEX_HOME/skills` fails under sandboxing, rerun with approval. Restart Codex after creating or changing Codex skill links.

## teardown_agent_links.py

Run this from the project root to undo setup:

```bash
python agents/tools/teardown_agent_links.py --dry-run
python agents/tools/teardown_agent_links.py
```

It removes only generated links/config owned by this project:
- `.claude/skills/*` symlinks that point into this repo
- `$CODEX_HOME/skills/*` symlinks that point into this repo
- root instruction symlinks: `AGENTS.md`, `GEMINI.md`, `CHATGPT.md`, `.cursorrules`, `.github/copilot-instructions.md`
- via MCP integration by running `via uninstall mcp`
- Codex MCP integration by running `codex mcp remove via`

It does not remove real files, unrelated symlinks, or `$CODEX_HOME/skills/.system`.

Use `--keep-mcp` to skip `via uninstall mcp`.
