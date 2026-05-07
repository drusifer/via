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

After any `make` run, the full log is at `build/build.out`. Search it directly — do not re-run the build with pipes.

```bash
grep -i "error\|fail\|warning" build/build.out
grep -n "pattern" build/build.out
grep -A5 "TestFoo" build/build.out
```

Use `V=-vv` during the run if you want failure lines to appear live. Use `grep build/build.out` after the run if you need to search the full log.

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
| `make test` | Run unit tests |
| `make tldr` | Show TL;DR summaries from project files |
| `make via_index` | Build the via symbol index |
| `make install_bob TARGET=/path` | Install BobProtocol into a project |
| `make update_bob TARGET=/path` | Update agents in a project |
| `make pull_bob SRC=/path` | Pull updates from another BobProtocol project |
| `make clean_bob` | Remove generated symlinks and reset state files |

## Adding a new target

If a target does not exist, add it to the Makefile — do not invoke tools directly.

The Makefile has two blocks gated by `MKF_ACTIVE`. **Both lines below go inside the Makefile — neither is a shell command.**

```makefile
ifdef MKF_ACTIVE

# Real recipe — runs inside mkf's subprocess environment
lint: ## Run linting checks
    @ruff check .

else

# Public stub — this Makefile line is what triggers mkf; do NOT replicate it at the shell
lint: ## Run linting checks
    @./agents/tools/mkf.py $(V) $@

endif
```

The `./agents/tools/mkf.py` line is Makefile plumbing. It exists so that typing `make lint` at the shell automatically routes through mkf. It is not an indication that agents should call `mkf.py` directly.

In an installed project, add project-specific targets to `Makefile.prj`. Bob manages `agents/Makefile.bob` and never modifies `Makefile.prj`.

Targets that bypass mkf (output must reach the terminal directly, like `help` and `chat`) are defined only in the `else` block.
