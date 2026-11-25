# VIA (`via-index`) — SDLC

How this project is built, tested, changed and released — the source of truth for change
management across the whole project. **Owned by Tank**; to change anything here,
ask `@Tank *devops sdlc <what and why>` — the mechanism and this document change together.

## 1. Toolchain

| | Python | JavaScript (Web UI tests) |
|---|---|---|
| Runtime version | `>=3.10` (developed on Python 3.13.5; CI builds on 3.12) | Node.js v24.13.0 / npm 11.21.1 |
| Manifest | `pyproject.toml` | `package.json` |
| Lockfile | None — dependencies use minimum version pins in `pyproject.toml` | `package-lock.json` (committed) |
| Package manager | `pip` inside `python3 -m venv` | `npm` |
| Local environment | `.venv/` (gitignored) | `node_modules/` (gitignored) |

Other required tools:
- `gitleaks` — secret scanning for `.githooks/pre-commit` and `make security-scan-secrets` (https://github.com/gitleaks/gitleaks#installing)
- `gh` — GitHub CLI, required by `make release` to create GitHub Releases
- `bobp` — Bob Protocol CLI wrapper (`bobp make <target>`, `bobp chat`)

## 2. Setup

From a clean checkout:

```sh
make install-dev
make install-hooks
npm ci
make test
make test-js
```

Prerequisites not installed by `make install-dev`: `python3` (>=3.10), `node`/`npm` (for JS unit and Playwright E2E tests), `gitleaks`, and `gh` (for releases). For Playwright E2E tests (`make test-e2e`), Chromium must be installed via `npx playwright install chromium`.

## 3. Make targets

The [Makefile](../Makefile) is the contributor entry point; recipes call native tools. Agents run these targets through `bobp make <target>`.

| Target | Runs | Notes |
|---|---|---|
| `all` | `install` + `test` | installs runtime package and runs full pytest suite |
| `venv` | `python3 -m venv .venv` | creates `.venv/` via `.venv/venv.stamp` |
| `install` | `.venv/bin/python -m pip install -e .` | idempotent; installs runtime package |
| `install-dev` | `pip install -e ".[dev]"` | installs runtime + dev/build/lint/test/audit extras (including `pip-audit`) |
| `install-hooks` | `git config core.hooksPath .githooks` | enables gitleaks pre-commit hook |
| `install-system` | `pipx install --editable . --force` | optional global editable `via` CLI install |
| `test` | `pytest $(or $(FILE),tests/) $(ARGS)` | full Python suite or targeted `FILE=... ARGS=...` |
| `coverage` | `pytest --cov=via --cov-report=lcov:coverage/lcov.info` | terminal + LCOV export |
| `test-coverage` | `pytest --cov=via --cov-context=test` + `via coverage import-contexts` | captures per-test `covered-by` + `test_runs` into `.via/index.db` |
| `test-js` | `npm test` | Vitest + jsdom unit tests for `via/web/static/` |
| `test-e2e` | `npx playwright test` | Playwright browser E2E suite for the web UI |
| `test-all` | `test` + `test-js` + `test-e2e` | runs all three suites sequentially |
| `lint-fast` | `ruff check via/ --select F401,F841,ERA` | fast hygiene check (~1s) |
| `lint` | `fix` + `ruff check` + `bandit -r via/` | medium hygiene + security check |
| `lint-slow` | `duplicates` + `security` + `vulture` + `ruff` + `pylint` + `bandit` | full static analysis |
| `fix` | `ruff check --fix via/` | auto-fix ruff findings |
| `duplicates` | `pylint via/ --disable=all --enable=duplicate-code` | duplicate code check |
| `security` | `bandit -r via/ -c pyproject.toml` | Python Bandit static security scan |
| `security-scan-secrets` | `gitleaks detect --source . --no-banner` | git-aware secret scan across history |
| `security-scan-python` | `pip-audit` (in `.venv`) | audits installed Python dependencies; fails fast if `pip-audit` is missing |
| `security-scan-npm` | `npm audit --audit-level=high` | audits JS dev dependencies against `package-lock.json`; fails fast if `npm` is missing |
| `security-scan` | `security-scan-secrets` + `security-scan-python` + `security-scan-npm` | runs all build-time security scans (secrets, Python deps, npm deps) |
| `dead-code` | `vulture via/ --min-confidence 80` | dead code detection |
| `via` | `.venv/bin/via $(ARGS)` | run project `via` CLI in `.venv` |
| `via-watch` | `via index -w $(DIR) --port $(PORT)` | watch mode + web UI (default port 7891) |
| `via-mcp-serve` | `via mcp serve $(DIR) --port $(PORT)` | MCP stdio server + watch + web UI |
| `dist` | `python -m build && twine check dist/*` | builds sdist + wheel into `dist/` |
| `release` | `dist` + tag `v<version>` + `git push` + `gh release create` | triggers GitHub Actions OIDC PyPI publish (`via-index` on `drew.gs.works`) |
| `deploy-forgejo` | `$(PI_PATCH)/cluster/scripts/forgejo-publish.sh pypi dist` | publishes wheel/sdist to private pi-patch Forgejo PyPI |
| `clean` | removes `.via/`, `.venv/`, `__pycache__`, `.pytest_cache`, `.coverage`, `htmlcov`, `coverage` | destructive clean (also removes `.venv/`) |
| `help` | prints targets annotated with `##` | default goal |

Standard targets deliberately absent:
- `format` — formatting is handled through `make fix` (`ruff check --fix via/`).
- `distclean` — `make clean` already removes `.venv/` alongside build/test caches.

## 4. Dependencies

- **Add (Python):** add runtime packages to `[project].dependencies` or dev tools to `[project.optional-dependencies].dev` in `pyproject.toml`, then run `bobp make install-dev`.
- **Upgrade / remove (Python):** edit `pyproject.toml` and re-run `bobp make install-dev`.
- **Add / update (JS test tools):** run `npm install --save-dev <pkg>` / `npm uninstall <pkg>` so `package.json` and `package-lock.json` stay in sync.
- **Dev-only tools:** Python dev/lint/build tools live in `[project.optional-dependencies].dev`; JS test/E2E tools live in `package.json` `devDependencies`.
- **Commit afterwards:** `pyproject.toml` (Python); `package.json` + `package-lock.json` (JS).
- **Who:** Neo adds and bumps application dependencies. Switch owns vulnerability-driven dependency changes. A new package manager, language, or runtime version is a mechanism change — Tank's.

## 5. Quality gates

| Gate | Target | Required before |
|---|---|---|
| Python tests | `bobp make test` | every handoff to Trin; sprint close |
| JS unit tests | `bobp make test-js` | changes to `via/web/static/` or `via/web/template.py`; sprint close |
| Browser E2E tests | `bobp make test-e2e` | Smith usability review for web UI changes; sprint close |
| Fast lint | `bobp make lint-fast` | pre-handoff self-validation on touched files |
| Static security (Bandit) | `bobp make security` | security-relevant Python changes |
| Secret scan | `bobp make security-scan-secrets` (and `.githooks/pre-commit`) | every commit (staged) and before release (history) |
| Python dependency audit | `bobp make security-scan-python` | Python dependency changes; before release; sprint close |
| JS dependency audit | `bobp make security-scan-npm` | JS dependency changes; before release; sprint close |
| Aggregate security scan | `bobp make security-scan` | before every PyPI / Forgejo release |
| Package build & check | `bobp make dist` | every PyPI / Forgejo release |

## 6. Change management

This document is the project's source of truth for how a change gets from request to done.
Where another document, skill or habit disagrees with it, this one wins — and the disagreement
is reported to Tank so one of them gets fixed.

### Change classes

| Class | Examples | Proposed by | Approved by | Must pass | Recorded in |
|---|---|---|---|---|---|
| Routine | feature, fix, refactor, docs, dependency bump via Section 4 | User / Cypher story | Trin UAT + Switch security gate + Morpheus review (+ Smith UX gate when user-facing) | Section 5 gates | `task.md`, `agents/CHAT.md`, commit |
| Mechanism | toolchain, manifest layout, make targets, gates, CI, this document | anyone via `@Tank *devops sdlc` | Tank + User | clean verification + Section 5 gates | `docs/SDLC.md`, `agents/CHAT.md`, commit |
| Release / deploy | version bump, PyPI or Forgejo publish | User / Tank | User (including GitHub `pypi` environment reviewer approval) | `bobp make dist` + applicable Section 5 gates | `via/__init__.py`, `CHANGELOG.md`, git tag + GitHub Release |
| Emergency | hotfix outside a sprint | User | User (may be reviewed post-hoc) | `bobp make test` at minimum | `agents/CHAT.md`, reviewed at next sprint close |

### Flow

1. **Request** — User initiates work; multi-step work uses Bob Protocol planning loops (`*plan sprint`) tracked in root `task.md`.
2. **Branch** — Default branch is `main`; work proceeds directly on `main` unless the user requests a feature branch.
3. **Implement** — Run build/test/lint commands through `bobp make <target>`; tests accompany behavior changes (TDD).
4. **Gate** — Applicable Section 5 gates pass before handoff.
5. **Review** — Trin verifies acceptance criteria, Switch runs security review, Morpheus approves architecture/code quality, and Smith tests user-facing UX.
6. **Integrate** — Agents commit, push, or tag only when directed by the user (or during an explicitly user-authorized `bobp make release`). Commit messages use Conventional Commits (`feat:`, `fix:`, `build:`, `docs:`, `chore:`).
7. **Record** — Update `task.md`, persona `state.md`, `agents/CHAT.md`, user docs (`docs/`, `README.md`), and `CHANGELOG.md` at sprint close.

### Rules

- Agents commit, push, or tag only when explicitly authorized by the user.
- Never commit secrets, `.venv/`, `.mcp.json`, `.via/`, `dist/`, `build/`, or generated coverage files.
- **Rollback:** back out an integrated bad change with `git revert <sha>`; PyPI releases are immutable, so fix forward with a new version bump.
- **Changing this document:** only Tank edits `docs/SDLC.md`; every edit updates the *Last verified* line.

## 7. Versioning and release

- **Version lives in:** `via/__init__.py` (`__version__`), read dynamically by `pyproject.toml` (`[tool.setuptools.dynamic]`).
- **Bumped:** by Tank/Cypher on explicit user release authorization (SemVer; PyPI versions are immutable).
- **Artifact:** `bobp make dist` produces `dist/via_index-<version>.tar.gz` and `dist/via_index-<version>-py3-none-any.whl` and validates both with `twine check dist/*`.
- **Public PyPI release:** `bobp make release` tags `v<version>`, pushes the tag, and creates a GitHub Release on `drusifer/via`. That triggers `.github/workflows/publish.yml`, which builds, smoke-tests the wheel in an isolated venv, and publishes `via-index` to PyPI (`drew.gs.works`) via OIDC trusted publishing after required reviewer approval on the `pypi` GitHub environment. `via-index 0.1.0` was published and verified on 2026-11-24.
- **Private Forgejo release:** `bobp make deploy-forgejo` publishes `dist/` to the local pi-patch Forgejo PyPI registry.

## 8. CI / deploy

- **Local-only verification (no push/PR CI workflow):** Tests, linting, and security scans run locally via `bobp make` before committing (plus `.githooks/pre-commit` for staged secrets). There is no push/PR GitHub Actions CI workflow.
- **`.github/workflows/publish.yml`** — runs on `release: [published]`. Uses least-privilege `permissions: { contents: read }` at top level, SHA-pinned actions, builds sdist + wheel, runs `twine check dist/*`, smoke-tests installing the wheel in a fresh venv (`via --help`), and publishes via `pypa/gh-action-pypi-publish` inside the `pypi` environment (`id-token: write`, required reviewer `drusifer`).

## 9. Known deviations

- **No Python lockfile:** `pyproject.toml` declares minimum version bounds without a committed `uv.lock` or `requirements.lock`; `make install-dev` resolves latest compatible versions with `pip`, and `make security-scan-python` (`pip-audit`) audits the installed `.venv` rather than an exported lockfile.
- **Pre-existing gitleaks history finding:** `make security-scan-secrets` currently reports 1 pre-existing `generic-api-key` finding in `.continue/agents/config.yaml:10` (commit `9817f24`, 2026-02-07; not packaged in `dist/*`). Never allowlisted; awaits user verification/rotation and history remediation decision. Tracked in `agents/switch/state.md`.
- **`make clean` removes `.venv/`:** there is no separate `distclean` target; `make clean` performs a full environment clean.

## 10. Conformance check

Run by Tank at sprint close (`*devops sdlc-check`):

1. Verify `bobp make test` (Python), `bobp make test-js` (JS), and `bobp make test-e2e` (Playwright) pass against current code.
2. Verify `bobp make dist` builds sdist + wheel cleanly and passes `twine check dist/*` with zero unintended files in `dist/`.
3. Inspect `pyproject.toml` `[project].dependencies` vs. runtime imports in `via/` — confirm every third-party import is declared.
4. Confirm every target listed in Section 3 exists in `Makefile` (`grep -E '^[a-zA-Z_][a-zA-Z0-9_-]*:' Makefile`) and matches its documented behavior.
5. Confirm `.githooks/pre-commit` is executable and `git config core.hooksPath` returns `.githooks`.
6. Confirm `.venv/`, `node_modules/`, `.mcp.json`, `.via/`, `dist/`, and `build/` remain ignored in `.gitignore`.
7. Confirm Sprint changes followed Section 6 (proper gates, recorded in `task.md`, `agents/CHAT.md`, and docs).

---
*Last verified: 2026-11-24 after removing `.github/workflows/ci.yml` per user direction (local-only verification + `publish.yml` release workflow) by Tank.*
