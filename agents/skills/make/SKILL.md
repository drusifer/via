---
name: make
description: Invoke project Makefile targets. All targets route through mkf (build output filter) automatically — output is captured to build/build.out and status is posted to CHAT.md.
triggers: ["*make"]
---

One-line summary: Invoke project Makefile targets — all output is captured by mkf to `build/build.out`, not the context window.

TLDR:
    Run `make <target>` (optionally with `V=-v/-vv/-vvv` for verbosity); never pipe with `2>&1` as that defeats mkf and floods context.
    mkf captures output, posts build status to `agents/CHAT.md`, and returns the exit code for pass/fail detection.
    If a needed target doesn't exist, add it to the Makefile — do not invoke tools directly.

# Make Skill

## Discover Available Targets

**Always run this first** to see the current, authoritative list of targets:

```bash
make help
```

This outputs all targets with their descriptions. The list is always up to date — do not rely on hardcoded lists in docs or memory.

## Overview

All project automation runs through `make`. Every target (except `help`, `chat`, `install_bob`,
`update_bob`, `pull_bob`, and `clean_bob`) is automatically routed through **mkf**
(`agents/tools/mkf.py`) — the build output filter. You do not need to call mkf directly; just run
`make <target>`.

## CRITICAL — Do not capture make output into context

**Never** run make with output redirected into the conversation context:

```bash
# WRONG — floods context window, defeats mkf entirely
Bash(make update_bob 2>&1)
Bash(make update_bob V=-vvv 2>&1)

# CORRECT — mkf handles output; only the tail + exit code appear
Bash(make update_bob)
Bash(make update_bob V=-vv)
```

mkf exists specifically to keep build output out of the context window. Piping or capturing the full output (via `2>&1` or shell redirection into a variable) defeats this and bloats the context. Always let mkf manage the output — check `build/build.out` directly if you need details after a run.

---

## What mkf does

- Captures all build output to `build/build.out`
- Prints the last 10 lines of output on exit
- Posts build status + tail to `agents/CHAT.md` as persona `make`; consecutive make build messages replace the previous make build entry
- Returns the make exit code — callers can rely on it for pass/fail

## Verbosity

Control how much output appears in your terminal during the run using `V=`:

| Flag | Terminal output |
|------|----------------|
| *(none — default)* | Silent. Exit code only. Full log in `build/build.out`. |
| `V=-v`   | stderr only |
| `V=-vv`  | stderr + filtered stdout (failures, errors) |
| `V=-vvv` | stderr + full stdout (everything) |

```bash
make pull_bob                  # silent — exit code + tail on finish
make pull_bob V=-v             # show stderr live
make pull_bob V=-vvv           # show everything live
```

## Targets

### General
| Command | Description |
|---------|-------------|
| `make help` | Show available make targets (bypasses mkf) |
| `make chat` | Post a message to CHAT.md (bypasses mkf) |
| `make tldr` | Show TL;DR summaries from all project files |

### Installation & Maintenance
| Command | Description |
|---------|-------------|
| `make install_bob` | Copy agents into a project and set up skill links (`make install_bob TARGET=/path`) |
| `make update_bob` | Update agents and skills in a project, preserving state (`make update_bob TARGET=/path`) |
| `make pull_bob` | Pull updates from another project using BobProtocol (`make pull_bob SRC=/path`) |
| `make clean_bob` | Remove generated symlinks and reset agent memory/state files |

## Output file

Full build log is always at `build/build.out`. Inspect it after any run:

```bash
cat build/build.out        # full log
tail -20 build/build.out   # last 20 lines
```

## Making targets discoverable

`make help` shows targets that have an inline `## description` comment:

```makefile
lint: ## Run linting checks
    @ruff check .
```

Targets without `##` still appear in `make help` under "Project targets" (by name only). Adding `##` gives them a description.

## Adding a New Target

The Makefile uses two blocks — real recipes inside `ifdef MKF_ACTIVE`, public stubs in `else`:

```makefile
ifdef MKF_ACTIVE

lint: ## Run linting checks
    @ruff check .

else

lint: ## Run linting checks
    @./agents/tools/mkf.py $(V) $@

endif
```

| Type | Where defined | When to use |
|------|--------------|-------------|
| Normal targets | Both blocks | Default — output captured by mkf |
| Bypass targets (like `help`, `chat`) | `else` block only | Interactive output, must reach terminal directly |

In an installed project, add project-specific targets to `Makefile.prj` instead. Bob manages `agents/Makefile.bob` (included via `-include agents/Makefile.bob`) and never touches `Makefile.prj`.

## Fallback

If a target does not exist, add it to the Makefile — do not invoke tools directly. See **Adding a New Target** above.
