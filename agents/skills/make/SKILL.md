---
name: make
description: Invoke project Makefile targets. All targets route through mkf automatically — output is captured to build/build.out, not the context window. Use V= to control verbosity.
triggers: ["*make", "*mkf", "*build"]
---

One-line summary: Run `make <target>` — never call mkf.py directly, never pipe make output.

# Make Skill

## The only correct invocation patterns

```bash
make <target>              # silent — exit code + 10-line tail on finish
make <target> V=-v         # show stderr live
make <target> V=-vv        # show stderr + failure lines live
make <target> V=-vvv       # show all output live
```

`V=` is the only way to control verbosity. There is no other interface.

## NEVER do these things

```bash
# WRONG — calls the implementation directly, bypasses make entirely
python agents/tools/mkf.py -vv <target>
./agents/tools/mkf.py <target>

# WRONG — pipes defeat mkf and flood the context window
make <target> 2>&1 | tail -20
make <target> | grep error
make <target> 2>&1

# WRONG — capturing output into context
result=$(make <target>)
```

`mkf.py` is an internal implementation file. It is not a CLI tool for agents. Running it directly bypasses the Makefile, breaks the `MKF_ACTIVE` environment flag, and produces incorrect behavior.

## How to inspect build output

After any `make` run, the full log is at `build/build.out`. Search or tail it directly — do not re-run the build with pipes.

```bash
# See last N lines of output (use instead of make test 2>&1 | tail -N)
tail -n 30 build/build.out

# Search for failures
grep -i "error\|fail\|warning" build/build.out
grep -n "pattern" build/build.out
grep -A5 "TestFoo" build/build.out
```

Use `V=-vv` during the run if you want failure lines to appear live. Use `tail`/`grep` on `build/build.out` after the run if you need to see the results — **never pipe `make` output**.

## Discover available targets

Always check what targets exist before assuming:

```bash
make help
```

## What happens when you run `make <target>`

1. Make invokes the mkf wrapper automatically
2. mkf captures all stdout/stderr to `build/build.out`
3. mkf prints the last 10 lines when the build finishes
4. mkf posts build status to `agents/CHAT.md`
5. Make returns the exit code — 0 = pass, non-zero = fail

You never need to orchestrate any of this. Running `make <target>` is the complete action.

## Verbosity reference

| Flag | What appears in context |
|------|------------------------|
| *(none)* | 10-line tail + exit code only |
| `V=-v` | stderr live + 10-line tail |
| `V=-vv` | stderr + failure/error lines live |
| `V=-vvv` | all output live (large builds will be noisy) |

Use `V=-v` or `V=-vv` when you need to see what went wrong during the run. Use `grep build/build.out` when the build is already done.

## Available targets

```bash
make help    # always up-to-date — prefer this over any hardcoded list
```

Common targets:

| Command | Description |
|---------|-------------|
| `make help` | Show all targets |
| `make test` | Run unit tests (full: lints + secret scan + verbose pytest) |
| `make test-q` | Concise test run — quiet pytest with short tracebacks; **use this for quick feedback instead of piping make test** |
| `make tldr` | Show TL;DR summaries from project files |
| `make via_index` | Build the via symbol index |
| `make install_bob TARGET=/path` | Install BobProtocol into a project |
| `make update_bob TARGET=/path` | Update agents in a project |
| `make pull_bob SRC=/path` | Pull updates from another BobProtocol project |
| `make clean_bob` | Remove generated symlinks and reset state files |
| `make dump-render-env` | Export current Render env vars to `.render-env-export.json` (requires `RENDER_API_KEY` + `RENDER_SERVICE_ID` in `.env`) |
| `make push-key` | Push `FIELD_ENCRYPTION_KEY` from `.env` to Render — validates JSON before pushing, does not redeploy (requires `RENDER_API_KEY` + `RENDER_SERVICE_ID` in `.env`) |

## Adding a new target

Project-specific targets live in **two files**. Both must be updated or the target will either be unknown to `make help` or silently bypass mkf.

### Step 1 — Real recipe in `Makefile.prj`

Add the recipe and include the target in `.PHONY`:

```makefile
.PHONY: ... existing-targets ... new-target   # add to existing .PHONY line

new-target: $(VENV_STAMP) ## One-line description shown in make help
	$(PYTHON) scripts/new_target.py
```

### Step 2 — Stub in `Makefile` (`else` block only)

Add the stub that routes through mkf, and add to the `.PHONY` in the `else` block:

```makefile
# in the else block .PHONY line:
.PHONY: ... existing-targets ... new-target

# stub entry (routes through mkf — captures output, posts to CHAT.md):
new-target: ## One-line description shown in make help
	@./agents/tools/mkf.py $(V) $@
```

### What each file does

| File | Purpose |
|------|---------|
| `Makefile.prj` | Real recipe — runs inside mkf's subprocess (included via `-include Makefile.prj` when `MKF_ACTIVE=1`) |
| `Makefile` (`else` block) | Public stub — intercepts `make new-target` at the shell and delegates to mkf |

### Verification

```bash
make help | grep new-target   # should appear twice: once from Makefile, once from Makefile.prj
```

Appearing twice is correct — `make help` greps both files. If it only appears once, one of the two steps above was missed.

### Targets that bypass mkf

Targets where output must reach the terminal directly (e.g. `help`, `chat`) are defined only in the `else` block with their real recipe — no stub pattern, no `Makefile.prj` entry needed.
