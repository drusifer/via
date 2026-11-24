---
name: build-env
description: Set up a project's build environment the way its language expects (Python pyproject.toml + .venv, JavaScript package.json + lockfile, Go, Rust, ...), with the Makefile as the single front door, and record it in docs/SDLC.md. Tank runs this for initial setup, when a language is added, to write or update the SDLC doc, and to check for drift at sprint close.
---

One-line summary: Tank bootstraps a build environment using the language's own manifest and tools, isolated inside the project, and exposes it through a standard set of `make` targets.

TLDR:
    Detect what exists first; never replace a package manager or manifest the project already chose.
    For new Python projects, use uv by default.
    The language's manifest is the source of truth (pyproject.toml, package.json, go.mod, Cargo.toml); the Makefile only fronts the native tool.
    Everything installs inside the project (.venv, node_modules) — never system-wide, never with sudo.
    Done means: from a clean checkout, `bobp make install && bobp make test` works, and docs/SDLC.md describes it.
    Tank owns docs/SDLC.md. No sprint starts without it; Tank checks the project against it at every sprint close.

# Build Environment Skill

## Triggers

`*devops bootstrap`, `*devops build-env`, `*build-env`, `*devops sdlc`, `*devops sdlc-check`

## When to use

Tank owns this. Run it when:

- a project has no build environment yet (new repo, or code with no manifest);
- a new language or runtime is being added to an existing repo;
- the first third-party dependency is about to be added and there is nowhere declared to put it;
- setup is ad hoc — a bare `requirements.txt`, install steps that live only in a README, "works on
  my machine" reports, or an interpreter that refuses installs (e.g. Python's PEP 668
  "externally-managed-environment" error).

Any persona who hits one of these hands off rather than improvising:
`@Tank *devops bootstrap <language>`.

After the initial setup the manifest belongs to the people changing the code: Neo adds and bumps
dependencies in it. Tank is called back only when the *mechanism* changes — a new language, a
different package manager, a new tool-version pin, or a new standard target.

## Principles

These explain the choices below, so apply them to languages this skill doesn't list.

1. **Detect before you create.** A lockfile or manifest already in the repo is a decision someone
   made. Build on it. Switching package managers is a separate proposal for the user, not part of
   a bootstrap.
2. **Use the ecosystem's convention, not your own.** Each language has one manifest that its tools,
   editors and CI already understand. Put dependencies, tool settings and entry points there.
   Do not invent parallel files or wrapper scripts for things the native tool does.
3. **Isolate inside the project.** Dependencies go in a project-local environment that is
   gitignored. Never install into the system or user interpreter, never use `sudo`, never pass
   override flags such as `--break-system-packages` or `npm install -g`. System installs collide
   with the OS package manager and make the project unreproducible.
4. **The Makefile is the front door; the native tool does the work.** Every routine task is one
   `make` target with the same name in every project, so people and agents never need to know
   which language they are in. Recipes are one or two lines that call the native tool. If a recipe
   grows logic, that logic belongs in the manifest's script section or a checked-in script.
5. **Reproducible by default.** Commit the lockfile when the ecosystem has one. Pin the
   language/runtime version in the place that ecosystem reads it. `install` must be safe to run
   twice.
6. **Prove it from clean.** Setup is not done until it has been deleted and rebuilt once.

## Procedure

1. **Survey.** List manifests, lockfiles, version pins, existing Makefile targets, CI config and
   any install instructions in docs. Check which tools are actually on the machine
   (`command -v uv npm pnpm go cargo ...`) and whether the system interpreter is managed by the OS.
2. **Decide and say why.** Pick the manifest, package manager and environment location. Prefer, in
   order: what the repo already uses → what a present lockfile implies → the ecosystem default in
   the tables below. Post the choice and the reason to CHAT.md before writing files.
3. **Write the manifest.** Project metadata, runtime dependencies, a separate dev/test dependency
   group, tool configuration, and entry points for any CLI. Migrate existing dependency lists
   into it without changing versions.
4. **Wire the Makefile.** Add the standard targets (next section). Keep existing target names
   working; add to the project's Makefile, never replace it.
5. **Ignore and pin.** Add the environment directory to `.gitignore`. Add the runtime version pin.
6. **Verify from clean.** Remove the environment directory, then `bobp make install` followed by
   `bobp make test`. Run `bobp make install` a second time to confirm it is idempotent.
7. **Write `docs/SDLC.md`** (see below) so the choices outlive this session.
8. **Hand off.** Update the README setup section to the two commands above, post the summary to
   CHAT.md (what was chosen, how to add a dependency, anything not verified), and note the
   decision for Oracle.

Ask the user before deleting or replacing a file someone else maintains (an old
`requirements.txt`, a `setup.py`, a hand-written install script). Migrating its contents is in
scope; removing it is their call.

## `docs/SDLC.md` — the project's source of truth for change management, owned by Tank

A bootstrap leaves decisions behind: which manifest, which package manager, which targets are the
gates. If those live only in a chat log, the next sprint re-decides them or quietly works around
them. `docs/SDLC.md` is where they are written down. Tank writes it, Tank keeps it current, and
other personas read it instead of guessing.

Its scope is wider than the build environment: it is **the source of truth for change
management across the whole project** — how any change is requested, classified, approved,
gated, integrated and recorded. Sprint and persona instructions describe the team's general
workflow; the SDLC says how that workflow is applied in *this* repository. Where they disagree,
the SDLC wins, and whoever notices reports it to Tank so the conflict is removed rather than
worked around. Write the change-management section from how the project actually operates —
ask the user about anything you cannot observe (branching, who may push, release approval)
instead of inventing a process.

**Tank is the only persona who changes the SDLC.** Anyone can propose a change
(`@Tank *devops sdlc <what and why>`); Tank updates the mechanism and the document together.

### What it contains

Describe what is true in this repo today — commands a reader can run, not aspirations. Keep it
to a page or two. Use these sections, writing "None" (with a reason) where one doesn't apply:

| Section | Answers |
|---|---|
| **Toolchain** | Languages and pinned runtime versions; manifest and lockfile per language; package manager; where the local environment lives. |
| **Setup** | The exact commands from clean checkout to passing tests. |
| **Make targets** | Every standard target the project defines, what it runs, and which standard targets are deliberately absent and why. |
| **Dependencies** | How to add, upgrade and remove one; who may; what must be committed afterwards. |
| **Quality gates** | What must pass before work is handed off and before a sprint closes (tests, lint, type checks, secret scan), as `make` targets. |
| **Change management** | Change classes (routine, mechanism, release, emergency) with who proposes, who approves, what must pass and where each is recorded; the request → branch → implement → gate → review → integrate → record flow; commit/push rules; rollback. |
| **Versioning and release** | Where the version lives, when it is bumped, how an artifact is built or published. |
| **CI / deploy** | What runs automatically and where it is configured — or that there is none. |
| **Known deviations** | Anything that departs from the conventions in this skill, and why (e.g. a venv using system site-packages for an OS-only dependency). |
| **Conformance check** | The project-specific list Tank runs at sprint close (see below). |

End the file with a "Last verified" line: date, and the commit or sprint it was checked against.

### Templates

Start from a template rather than a blank page — they live with the team's other templates in
`agents/templates/`:

| Template | Use for |
|---|---|
| `agents/templates/_template_SDLC.python.md` | Python: `pyproject.toml` + uv + `.venv` |
| `agents/templates/_template_SDLC.javascript.md` | JavaScript / TypeScript: `package.json` + lockfile |
| `agents/templates/_template_SDLC.md` | Any other language, or a repo with several languages |

Copy the one that fits to `docs/SDLC.md`, replace every `{placeholder}`, and delete the review
rubric at the end of the template (from `RUBRIC-START` to `RUBRIC-END`). The language
templates come pre-filled with that ecosystem's conventional answers; correct any line that is
not true for the repo — the document describes this project, not the convention. For a
multi-language repo use the base template, with one Toolchain column and one set of
`-<lang>` targets per language. When you bootstrap a language that has no template yet and
expect to meet it again, add `agents/templates/_template_SDLC.<language>.md` in the same shape.

### Review rubric

Each SDLC template ends with the **SDLC rubric**: six criteria (`TRUE`, `WHOLE`, `CLEAN`,
`CLASS`, `CHECK`, `GAPS`) for judging whether the document is useful to its readers. Check your
draft against it before posting, and fix anything you would call Weak. Oracle applies the same
rubric at groom in any sprint where `docs/SDLC.md` changed and rejects on any Weak. The rubric
judges the *document*; `*devops sdlc-check` below judges whether the *project* matches it — do
not merge the two. How rubrics work: `agents/templates/ARTIFACTS.md`.

### `*devops sdlc` — create or update it

- **No SDLC yet, environment already exists:** survey it (Procedure step 1), verify it from clean,
  then document what you found. Fix gaps against this skill's checklist first if they are small;
  list larger ones under Known deviations and raise them with the user.
- **No SDLC and no environment:** run the bootstrap Procedure; the SDLC is its step 7.
- **Mechanism change requested:** change the manifest/Makefile, re-verify from clean, update the
  affected sections and the Last verified line in the same piece of work.

### Sprint-start gate (blocker)

No sprint is planned without `docs/SDLC.md`. Whoever starts a sprint checks that the file exists
before the first story is written. If it is missing, planning stops and the request goes to Tank:
`@Tank *devops sdlc` — planning resumes when Tank posts that the file is written. This is a
check that the document exists, not a re-verification; drift is caught at close.

### `*devops sdlc-check` — conformance check at sprint close

Run after the last phase is reviewed and before Oracle grooms the docs, so that any correction
lands in the documentation pass. The question is whether the sprint left the project matching
its SDLC. Check at least:

1. **Rebuild from clean.** `bobp make distclean`, `bobp make install`, `bobp make test` (and each
   other quality-gate target the SDLC lists).
2. **Manifest matches the code.** Every third-party import is declared in the manifest; nothing
   was installed by hand into the environment; no new dependency file appeared beside the manifest.
3. **Targets match the document.** Targets the SDLC lists still exist and do what it says; new
   targets added this sprint are either documented or removed.
4. **No side doors.** No README, doc or script introduced this sprint tells people to bypass
   `make` or install outside the project.
5. **Pins and ignores still hold.** Runtime pin unchanged or deliberately bumped; lockfile
   committed if the ecosystem has one; environment directory still ignored.
6. **Changes followed the process.** This sprint's changes were of the class they were treated
   as, had the approval the SDLC requires, and were recorded where it says.
7. Anything listed under the SDLC's own Conformance check section.

Outcome, posted to CHAT.md:

- **Conforms** → update the Last verified line and hand off to Oracle.
- **Drift that is an improvement** (the sprint legitimately changed the mechanism) → Tank updates
  `docs/SDLC.md` to match, then hands off.
- **Drift that is a regression** → `@Neo *swe fix <issue>`; the sprint does not close until Tank
  re-checks. The usual fix-loop limit applies.

## Standard Makefile contract

Use these names. Omit a target only when it has no meaning for the project; never rename one.

| Target | Does | Notes |
|---|---|---|
| `install` | Create the local environment and install all dependencies, including dev tools | Idempotent. The only target allowed to touch the network. |
| `test` | Run the test suite | The gate Trin and CI use — must be the same command in both. |
| `lint` | Static checks (style, types) without changing files | |
| `format` | Rewrite files to the project style | |
| `build` | Produce the distributable artifact | Only if the project ships one. |
| `run` | Start the app / primary entry point | Use `ARGS="..."` for arguments. |
| `clean` | Remove build outputs and caches | Leaves the environment in place. |
| `distclean` | `clean` plus remove the local environment | Used for the from-clean check. |
| `help` | List targets with descriptions | Parse `## comment` suffixes. |

Rules for recipes:

- Call tools through the local environment so no one has to activate anything
  (`.venv/bin/python -m pytest`, `npm run test`), usually via a variable at the top of the file.
- Fail with a one-line hint when the environment is missing ("run `make install`"), not with a
  raw import or command-not-found error.
- Pass extra arguments through `ARGS` (`make test ARGS="-k name"`).
- In a repo with more than one language, add suffixed targets (`install-py`, `install-js`,
  `test-py`, `test-js`) and make the unsuffixed target depend on all of them.
- Agents invoke targets with `bobp make <target>` (see the `make` skill).

Read [language conventions](references/language-conventions.md) when creating or changing a language-specific build environment.

## Done when

- [ ] The manifest declares every dependency the code imports, with dev tools in a dev group.
- [ ] `install`, `test` and `help` exist; `lint`, `format`, `build`, `run`, `clean`, `distclean`
      exist where meaningful.
- [ ] The environment directory is gitignored; the lockfile (if any) is committed.
- [ ] The runtime version is pinned where the ecosystem expects it.
- [ ] Removing the environment and running `bobp make install` then `bobp make test` succeeds,
      and a second `bobp make install` changes nothing.
- [ ] Nothing was installed outside the project directory.
- [ ] `docs/SDLC.md` exists, covers every section above, and carries a Last verified line.
- [ ] README setup instructions are the `make` commands, not raw tool commands.
- [ ] CHAT.md handoff posted: choices and reasons, how to add a dependency, anything unverified.

## Boundaries

- Tank does not edit application source to make a build pass. Report the failure to Neo.
- Do not change dependency versions while migrating them into a manifest; raise upgrades separately.
- CI, containers and deploy configuration should call the same `make` targets — wiring them is
  Tank's `*devops ci` / `*devops infra` work, not part of this skill.
