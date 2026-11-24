# SDLC Language Profile: Python

This is a language-specific insert for sections 1–4 and 10 of `_template_SDLC.md`, not a separate
SDLC document. Copy the relevant facts into the shared SDLC template and remove this insert. For
new Python projects, use Tank's `uv` conventions in `.agents/skills/build-env/SKILL.md`; preserve an
existing project's package-manager and dependency layout unless migration is explicitly planned.

## Toolchain and setup facts

- **Runtime:** Python `{version}`, constrained by `requires-python` in `pyproject.toml`.
- **Manifest:** `pyproject.toml`; identify the project's actual build backend and tools.
- **Manager and environment:** `uv`, `uv.lock`, and isolated `.venv/` for a new uv project.
- **Install and run:** record actual Makefile targets; recipes use `uv sync` and `uv run` for a uv
  project. Agent invocations use `bobp make <target>`.
- **Dependencies:** runtime dependencies belong in `[project].dependencies`; new uv project dev
  dependencies belong in `[dependency-groups].dev`. Preserve existing dependency layout when present.
- **Conformance:** from a clean checkout, verify install/test targets, lockfile consistency, the
  isolated environment, declared imports, ignored `.venv/`, and runtime pin.

<!-- RUBRIC-START -->
## Check — SDLC-PYTHON

- [ ] **PASS** — The profile matches the repository's actual Python manager and dependency layout; new uv guidance uses `[dependency-groups].dev`.
- [ ] **PASS** — Runtime, manifest, lockfile, environment, commands, and conformance checks are internally consistent and verified against actual targets.
- [ ] **FAIL** — Any command or dependency location conflicts with Tank's build-env guidance or repository configuration; correct the profile and shared SDLC references.
<!-- RUBRIC-END -->
