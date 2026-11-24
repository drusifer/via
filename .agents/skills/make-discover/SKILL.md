---
name: make-discover
description: Self-discovery guide for a project's Makefile targets. Run `bobp make help` (or read the Makefile) to see what's available — there's no bob-authored target list to rely on.
---

One-line summary: This project's Makefile is not bob-managed — discover its targets the normal way, then invoke them via the `make` skill's `bobp make <target>`.

# Make Target Discovery

## Triggers

`*bobp make help`, `*make discover`, `*build help`

## Discover available targets

Bob doesn't install, template, or own this project's `Makefile` — it's an ordinary Makefile
that belongs to the project. There's no second file, no `ifdef` block, and no guaranteed
`bobp make help` target contributed by bob. To find out what's available:

```bash
bobp make help                              # if the project defines one — often the fastest path
grep -E '^[a-zA-Z_-]+:' Makefile       # otherwise, read the target names directly
cat Makefile                           # or just read the whole thing if it's short
```

Don't rely on hardcoded target lists in docs or memory — the Makefile is the source of truth
and can change independently of bob.

## Running a target

See the `make` skill for the full invocation contract. Short version:

```bash
bobp make <target>              # captured to build/build.out, status posted to CHAT.md
bobp make -vv <target>          # same, but show failures live
```

Never invoke a target with bare `make <target>` when you want the capture/CHAT.md behavior —
that's what `bobp make` is for.

## Adding a new target

Add it to the project's Makefile exactly as you would in any other repo. No dual-file
convention, no stub/recipe split — `bobp make <target>` runs whatever `make <target>` runs.
