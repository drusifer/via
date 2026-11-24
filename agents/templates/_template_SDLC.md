<!--
SDLC template (base). Owned by Tank — see .agents/skills/build-env/SKILL.md.
Copy to docs/SDLC.md and replace every {placeholder}. Describe what is true in this repo
today, as commands a reader can run. Where a section does not apply, write "None" and why;
do not delete the heading. For a single-language project start from
_template_SDLC.<language>.md instead; for several languages, use this file and repeat the per-language rows/blocks.
Remove this note and the check block when creating a real artifact; checks belong to templates.
-->
# {Project} — SDLC

How this project is built, tested, changed and released — the source of truth for change
management across the whole project. **Owned by Tank**; to change anything here,
ask `@Tank *devops sdlc <what and why>` — the mechanism and this document change together.

## 1. Toolchain

| | {Language} |
|---|---|
| Runtime version | {version} — pinned in {file} |
| Manifest | `{manifest}` |
| Lockfile | `{lockfile}` (committed) / None — {why} |
| Package manager | {tool} |
| Local environment | `{dir}/` (gitignored) |

Other required tools: {tool — why — how it is obtained} / None.

## 2. Setup

From a clean checkout:

```sh
make install
make test
```

Prerequisites not installed by `make install`: {list} / None.

## 3. Make targets

The Makefile is the contributor entry point; recipes call native tools. Agents run these targets through `bobp make <target>`.

| Target | Runs | Notes |
|---|---|---|
| `install` | {command} | idempotent; only target that uses the network |
| `test` | {command} | `ARGS="..."` passes through |
| `lint` | {command} | |
| `format` | {command} | |
| `build` | {command} | |
| `run` | {command} | |
| `clean` | {what it removes} | keeps the environment |
| `distclean` | `clean` + removes `{dir}/` | |
| `help` | lists targets | |
| {project-specific target} | {command} | |

Standard targets deliberately absent: {target — why} / None.

## 4. Dependencies

- **Add:** {edit which file/section, then which command}
- **Upgrade / remove:** {how}
- **Dev-only tools:** {where they are declared}
- **Commit afterwards:** {manifest, lockfile}
- **Who:** Neo adds and bumps dependencies. A new package manager, language or runtime version
  is a mechanism change — Tank's.

## 5. Quality gates

| Gate | Target | Required before |
|---|---|---|
| Tests | `make test` | every handoff to Trin; sprint close |
| {Lint / types / secret scan} | `make {target}` | {when} |

## 6. Change management

This document is the project's source of truth for how a change gets from request to done.
Where another document, skill or habit disagrees with it, this one wins — and the disagreement
is reported to Tank so one of them gets fixed.

### Change classes

| Class | Examples | Proposed by | Approved by | Must pass | Recorded in |
|---|---|---|---|---|---|
| Routine | feature, fix, refactor, docs, adding a dependency via section 4 | {anyone / Cypher story} | {Morpheus review} | section 5 gates | {task board, commit} |
| Mechanism | toolchain, manifest layout, make targets, gates, CI, this document | anyone, via `@Tank *devops sdlc` | Tank{ + user} | from-clean rebuild + section 5 | this file, `{decisions log}` |
| Release / deploy | version bump, publish, deploy | {who} | {who} | {gates} | {changelog / tag} |
| Emergency | hotfix outside a sprint | {who} | {who — may be after the fact} | `make test` at minimum | {where}, reviewed at next sprint close |

### Flow

1. **Request** — {where changes are requested and how they are sized/planned}.
2. **Branch** — {default branch; branch naming; or "work directly on the default branch"}.
3. **Implement** — through `make` targets only; tests accompany behaviour changes.
4. **Gate** — the section 5 gates pass locally before handoff.
5. **Review** — {who reviews what; what counts as approval}.
6. **Integrate** — {who commits/merges/pushes, and when; commit message convention}.
7. **Record** — {what is updated: task board, decisions log, changelog, user docs}.

### Rules

- {Who may commit, push, tag — e.g. agents commit only when the user asks.}
- {What must never be committed: secrets, the local environment, generated artifacts.}
- **Rollback:** {how a bad change is backed out}.
- **Changing this document:** only Tank edits it; every edit updates the Last verified line.

## 7. Versioning and release

- **Version lives in:** {file/field}
- **Bumped:** {when, by whom}
- **Artifact:** {what `make build` produces and where it goes} / None — not shipped.

## 8. CI / deploy

{What runs automatically, on which events, configured in which file; deploy targets and
environments} / None — everything runs locally.

CI must call the same `make` targets as section 5.

## 9. Known deviations

{Where this project departs from the build-env skill's conventions, and why} / None.

## 10. Conformance check

Run by Tank at sprint close (`*devops sdlc-check`):

1. `make distclean && make install && make test` passes{, plus each gate in section 5}.
2. Every third-party import is declared in `{manifest}`; nothing was installed by hand.
3. Every target in section 3 exists and still does what the table says; new targets are listed.
4. No doc or script tells people to bypass `make` or install outside `{dir}/`.
5. Runtime pin, lockfile and ignore rules are as section 1 states.
6. This sprint's changes followed section 6: right class, right approval, recorded where it says.
7. {Project-specific checks} 

---
*Last verified: {YYYY-MM-DD} against {commit or sprint} by Tank.*

<!-- RUBRIC-START -->
## Check — SDLC

- [ ] **PASS** — `TRUE` (Does it describe what exists today?): Everything stated as present is present; anything not yet built is labelled as such.
- [ ] **PASS** — `WHOLE` (Can a newcomer find every part of the lifecycle?): Every section is filled in, or says "None" with a reason.
- [ ] **PASS** — `CLEAN` (Could someone go from a fresh checkout to passing tests using only this?): Prerequisites and exact commands are listed in order.
- [ ] **PASS** — `CLASS` (Can a reader tell how *their* change must be handled?): Any ordinary change falls into exactly one class with a named approver, gates and a place it is recorded.
- [ ] **PASS** — `CHECK` (Is the conformance check something that can be run?): Each item is a command or an inspection with a definite pass condition.
- [ ] **PASS** — `GAPS` (Does it admit what is missing or unverified?): Deviations from convention and unverified areas are listed with reasons.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->
