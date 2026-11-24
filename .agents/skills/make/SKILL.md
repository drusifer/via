---
name: make
description: Wrap a project's own `make <target>` with output capture (build/build.out) and a CHAT.md status post. Use `bobp make [-v|-vv|-vvv] <target>` — never bare `make`.
---

One-line summary: Run `bobp make <target>` — never call bare `make`, never call `bobp.tools.make` directly, never pipe the output.

# Make Skill

## Triggers

`*make`, `*build`

## Load this BEFORE your first raw build command

If a `Makefile` exists in the repo root, check what targets it defines (or load this skill)
**before** running any raw `pytest`/`ruff`/`pylint`/`pip install`/`.venv`-or-`venv`-prefixed
command via Bash — not after one fails or after you've already piped output once. Don't wait
to discover a target exists.

## Ownership: this project's Makefile is not bob's

`bobp` does not install, generate, or modify this project's `Makefile`. There is no
`Makefile.prj`, no `Makefile.bob`, no `ifdef MKF_ACTIVE` split — just one ordinary Makefile
that belongs entirely to this project. `bobp make` is a generic wrapper that runs whatever
target you name in *that* Makefile; it has no opinion about what targets exist.

## The only correct invocation patterns

```bash
bobp make <target>              # silent — exit code + 10-line tail on finish
bobp make -v <target>           # show stderr live
bobp make -vv <target>          # show stderr + failure lines live
bobp make -vvv <target>         # show all output live
```

The verbosity flag comes **before** the target (`bobp make -vv test`, not `bobp make test -vv`
and not `bobp make test V=-vv`) — `bobp make` parses its own argv, it does not pass `V=` through
to make.

## NEVER do these things

```bash
# WRONG — bypasses capture entirely, prints straight to the terminal/context
make <target>

# WRONG — calls the implementation module directly
python -m bobp.tools.make -vv <target>

# WRONG — pipes defeat the capture and flood the context window
bobp make <target> 2>&1 | tail -20
bobp make <target> | grep error
result=$(bobp make <target>)
```

## How to inspect build output

After any `bobp make` run, the full log is at `build/build.out`. Search or tail it directly —
do not re-run the build with pipes.

```bash
# See last N lines of output (use instead of bobp make <target> 2>&1 | tail -N)
tail -n 30 build/build.out

# Search for failures
grep -i "error\|fail\|warning" build/build.out
grep -n "pattern" build/build.out
grep -A5 "TestFoo" build/build.out
```

Use `-vv` during the run if you want failure lines to appear live. Use `tail`/`grep` on
`build/build.out` after the run if you need to see the results — **never pipe `bobp make`
output**.

## Discover available targets

This project's Makefile is not bob-managed, so there's no bob-authored `bobp make help` guarantee.
Check what the project itself defines:

```bash
bobp make help                              # if the project defines one
grep -E '^[a-zA-Z_-]+:' Makefile       # otherwise, read the target names directly
```

## What happens when you run `bobp make <target>`

1. `bobp make` shells out to `make <target>` in this project's own Makefile
2. It captures all stdout/stderr to `build/build.out`
3. It prints the last 10 lines when the build finishes
4. It posts build status to `agents/CHAT.md`
5. It exits with make's exit code — 0 = pass, non-zero = fail

You never need to orchestrate any of this yourself. Running `bobp make <target>` is the
complete action.

## Verbosity reference

| Flag | What appears in context |
|------|------------------------|
| *(none)* | 10-line tail + exit code only |
| `-v` | stderr live + 10-line tail |
| `-vv` | stderr + failure/error lines live |
| `-vvv` | all output live (large builds will be noisy) |

Use `-v` or `-vv` when you need to see what went wrong during the run. Use
`grep build/build.out` when the build is already done.

## Adding a new target

Add a normal target to this project's own Makefile, the same way you would in any other repo —
no special `ifdef` block, no second file to keep in sync. `bobp make <target>` picks it up
automatically since it just runs `make <target>` under the hood.
