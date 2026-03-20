---
name: make-discover
description: Self-discovery guide for Makefile targets. Run `make help` to see all current targets. Covers Makefile structure, when to add targets, and how to extend the build correctly.
triggers: ["*make help", "*make discover", "*build help"]
---

One-line summary: Self-discovery guide for Makefile targets — always run `make help` before assuming what targets exist.

TLDR:
    Run `make help` to get the current, authoritative target list; never rely on hardcoded lists in docs or memory.
    New targets require a real recipe in `ifdef MKF_ACTIVE` and a public stub in `else`, both with a `## comment` for discoverability.
    Bob-managed targets live in `agents/Makefile.bob` (included via `-include`); inspect last build output at `build/build.out`.

# Make Target Discovery

## Discover Available Targets

**Always run this first** to see the current, authoritative list of targets:

```bash
make help
```

This outputs all targets with their descriptions. The list is always up to date — do not rely on hardcoded lists in docs or memory.

## Makefile Structure

The Makefile uses two blocks:

```makefile
ifdef MKF_ACTIVE
    # ── Real recipes ─────────────────────────────────────────
    # Actual shell commands go here.
    # mkf routes all output through build/build.out.

else
    # ── Interception layer ────────────────────────────────────
    # Targets visible to users/agents go here.
    # All targets (except help and chat) delegate to mkf:
    #   @./agents/tools/mkf.py $(V) $@
    # Special targets (help, chat) are defined here directly.

endif
```

### Rules for Adding a New Target

1. **Real recipe** goes inside `ifdef MKF_ACTIVE` — this is where the shell commands live.
2. **Public stub** goes inside `else` — a one-liner that delegates to mkf (or runs directly for interactive/bypass targets).
3. **Always add a `## comment`** to the public stub so it appears in `make help`.

#### Example: adding `make lint`

```makefile
ifdef MKF_ACTIVE

lint: ## Run linting checks
    @ruff check .

else

lint: ## Run linting checks
    @./agents/tools/mkf.py $(V) $@

endif
```

## Bypass vs mkf Targets

| Type | Where defined | When to use |
|------|--------------|-------------|
| Normal targets | Both blocks | Default — output captured by mkf |
| Bypass targets (like `help`, `chat`) | `else` block only | Interactive output, must reach terminal directly |

## Quick Discovery Workflow

```bash
make help              # list all targets
cat build/build.out    # inspect last build output
make <target> V=-vv    # run with filtered stdout (errors only)
make <target> V=-vvv   # run with full stdout
```

See the `make` skill for full mkf verbosity and output details.

## How Bob Targets Arrive in a Project

Bob installs a self-contained fragment at `agents/Makefile.bob`. The project Makefile includes it:

```makefile
-include agents/Makefile.bob
```

The `-include` (note the dash) means make silently ignores the file if missing — safe to commit before install runs. `agents/Makefile.bob` is updated automatically when `make update_bob TARGET=<path>` is run.
