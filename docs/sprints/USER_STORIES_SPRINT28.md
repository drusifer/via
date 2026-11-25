# Sprint 28 User Stories & Architecture: Hygiene, CI/Security & Coverage UX Polish

*   **Tier**: Tier 2 (Hygiene / Maintenance / UX Polish)
*   **Branch**: `main` (per `docs/SDLC.md` Section 6)
*   **Source**: User selected Option A during `/sprint 28 plan` (2026-11-24), seeded by Sprint 27 retrospective items in `agents/cypher/BACKLOG.md`
*   **Status**: Approved — Smith Gate 1 & 2, Switch Gate 2b, Morpheus Step 3a Plan Review

## Goal

Close out the operational, security, lint, and UX polish gaps surfaced during Sprint 27 so that `via-index` has automated GitHub Actions CI, build-time Python/JS dependency security scans, zero Ruff complexity errors, a clean git working tree after JS tests, and clearer Coverage UI states. When this sprint is done, every contributor and agent gets fast automated feedback on pushes/PRs and a sharper Coverage web interface.

## Assumptions made for the owner

1. Work proceeds directly on `main` per `docs/SDLC.md` Section 6 (no separate sprint branch unless requested).
2. For `STORY-VIA-283` and `STORY-VIA-284`, the pre-existing gitleaks history finding at `.continue/agents/config.yaml:10` (commit `9817f24`) will **never** be allowlisted or suppressed; CI will scan incoming PR/push diffs (or full history once the owner confirms rotation/removal) and flag the pre-existing history finding openly until the owner resolves it.
3. No PyPI version bump (`0.2.0`) is included inside Sprint 28 execution unless explicitly requested at sprint close.

---

## STORY-VIA-281: Coverage UX Polish (Efficiency Empty-State & Legend Contrast)
**Owner:** Neo (verified by Trin, Smith)

**As a** developer opening the Coverage view before running `make test-coverage`,
**I want** the Efficiency tab to show an explicit empty-state hint and the Heatmap's `"Adequate (100%)"` legend swatch to be clearly visible against the card background,
**so that** I immediately know how to populate test efficiency data and can distinguish all four legend items at a glance.

### Acceptance Criteria
1. When `/api/coverage/test-efficiency` returns an empty list (`[]`), the Efficiency view displays a visible message instructing the user to run `make test-coverage` (consistent with Heatmap's empty state) instead of a blank table body.
2. When `/api/coverage/test-efficiency` returns one or more rows, the empty-state message is hidden and the table renders normally with all 7 columns (`Test`, `Status`, `Duration (s)`, `Symbols Covered`, `Imported Covered`, `Symbols/sec`, `Mocks`).
3. The `#legend-mid` (`Adequate (100%)`) swatch in the Heatmap legend has a distinct visible border and darker neutral fill so it is clearly legible on the white/light surface (verified visually in Playwright E2E screenshot).
4. Failure behavior: if `/api/coverage/test-efficiency` fails to fetch, the existing Coverage view fallback error state displays the error message without crashing.

---

## STORY-VIA-282: Zero Ruff Complexity Errors & Clean JS Test Working Tree
**Owner:** Neo (verified by Trin)

**As a** maintainer running static analysis and JS tests locally or in CI,
**I want** `ruff check via/` to exit 0 with zero complexity warnings and `bobp make test-js` to leave `git status` clean,
**so that** lint and git hygiene can serve as strict, noise-free quality gates.

### Acceptance Criteria
1. All 5 pre-existing C901 complexity findings in `via/db/store.py` (`initialize_schema`, `query_relationships`, `query_negative_relationships`, `_build_relationship_cte_sql`, `_build_negative_relationship_cte_sql`) are refactored into cohesive helper methods with `max-complexity <= 10`.
2. `ruff check via/` and `bobp make lint-fast` both exit 0 with zero errors or warnings.
3. Full Python test suite (`bobp make test`) passes with zero behavioral regressions.
4. `node_modules/.vite/vitest/da39a3ee5e6b4b0d3255bfef95601890afd80709/results.json` is untracked from git (`git ls-files node_modules/` returns empty), and running `bobp make test-js` leaves no dirty tracked files under `node_modules/`.
5. Failure behavior: N/A — internal refactoring and git-tracking cleanup; no user input surface changes.

---

## STORY-VIA-283: Dependency & Aggregate Security Scan Targets
**Owner:** Switch (targets) & Tank (Makefile review & `docs/SDLC.md`)

**As a** project maintainer preparing releases for PyPI (`via-index`),
**I want** repeatable `bobp make` security scan targets covering secrets, Python dependencies, and JS dev dependencies,
**so that** known vulnerabilities are caught before publishing a release.

### Acceptance Criteria
1. `Makefile` defines `security-scan-python` (running `pip-audit` against the installed `.venv` environment), `security-scan-npm` (running `npm audit --audit-level=high` against `package-lock.json`), and aggregate `security-scan` (`security-scan-secrets`, `security-scan-python`, `security-scan-npm`).
2. Each target exits 0 when clean and non-zero on findings or missing required tooling, with an actionable error message naming the missing tool if unavailable.
3. Running `bobp make security-scan-python` and `bobp make security-scan-npm` succeeds locally (any discovered vulnerable dependencies are remediated by Switch via upgrade/override per `.agents/skills/security/SKILL.md`, or escalated to the user if a major jump/acceptance is needed).
4. `docs/SDLC.md` Sections 3, 5, and 9 are updated by Tank to reflect the new targets and remove the corresponding Section 9 deviation.
5. Failure behavior: if a scanner binary is missing (e.g., `pip-audit`, `npm`, `gitleaks`), the target fails fast with a non-zero exit code and clear install hint rather than silently passing.

---

## STORY-VIA-284: GitHub Actions Push/PR CI Workflow
**Owner:** Tank (audited by Switch)

**As a** maintainer pushing to `main` or reviewing pull requests,
**I want** an automated GitHub Actions CI workflow that runs Python tests, Ruff lint, CLI smoke check, JS unit tests, and gitleaks secret scanning,
**so that** regressions and leaked secrets are caught automatically on every push and PR.

### Acceptance Criteria
1. `.github/workflows/ci.yml` triggers on `push` to `main` and on `pull_request`.
2. Top-level `permissions: { contents: read }` is set (least privilege) and every third-party Action is pinned to a full commit SHA with a version comment.
3. CI runs:
   - Python job (matrix `3.10`, `3.12`): `pip install -e ".[dev]"`, `ruff check via/`, `pytest tests/ -q`, and `via --help` smoke check.
   - JS job: `npm ci` and `npm test`.
   - Secrets job: pinned, SHA-256-verified `gitleaks` binary scanning commit changes (full history once `.continue/agents/config.yaml:10` is cleared by the user; commit-range / staged-diff scan on PRs so the job catches new leaks immediately without allowlisting the pre-existing commit).
4. `docs/SDLC.md` Sections 8 and 9 are updated by Tank to document `.github/workflows/ci.yml`.
5. Failure behavior: any failing test, Ruff error, CLI crash, or gitleaks finding fails the workflow with non-zero exit code and surfaces the failure in GitHub Checks.

---

## STORY-VIA-285: Canonical Domain Model & Ubiquitous Language (`docs/DOMAIN.md`)
**Owner:** Cypher & Morpheus (reviewed by Smith & Morpheus)

**As a** contributor or agent onboarding to `via`,
**I want** a canonical `docs/DOMAIN.md` defining VIA's bounded contexts, ubiquitous language, aggregate invariants, entity lifecycles, and documented boundary drifts,
**so that** architectural decisions and future features share one consistent vocabulary grounded in the actual codebase.

### Acceptance Criteria
1. `docs/DOMAIN.md` exists and follows `agents/templates/_template_DOMAIN.md` (with template notes and rubric block removed).
2. Explicitly defines VIA's 4 bounded contexts (**Indexing**, **Querying**, **Test Quality**, **Presentation & MCP**), their in-scope/out-of-scope boundaries, and upstream/downstream consumers.
3. Ubiquitous language glossary maps every core domain term 1:1 to real verified symbols in `via/` (marking any unimplemented or drifted items explicitly, including the 4 known drifts: `SymbolType` missing `'test'`/`'external_class'`, `MatchRecord` `column_widths`/CLI mixins, `DatabaseStore` concentration, and `ReferenceType`/`Relation` dual vocabulary).
4. Documents aggregate roots, transactional invariants, and symbol/index lifecycles truthfully; passes Smith + Morpheus `DOMAIN` rubric (`LANG`, `BOUND`, `INVAR`, `STATE`, `EVENT`).
5. Failure behavior: N/A — documentation artifact with no runtime input surface.

---

## Out of Scope
- Rewriting git history to scrub `.continue/agents/config.yaml:10` (requires explicit owner decision after verifying/rotating the key).
- New query language features (Boolean operators, Git history queries, Cross-project queries — remain in `agents/cypher/BACKLOG.md`).
- Adding a Python lockfile (`uv.lock`) — tracked separately in `docs/SDLC.md` Section 9.
- Running Playwright Chromium E2E tests in GitHub Actions (stays local via `bobp make test-e2e` to keep CI fast and deterministic).
- PyPI `0.2.0` release (separate user-authorized release action after Sprint 28 closes).

## Open Questions
1. **`.continue/agents/config.yaml:10` remediation (Owner: User):** Is the flagged `apiKey` real (needs rotation + removal from HEAD and git history) or a dummy value? Until answered, Sprint 28 never allowlists it; CI `secrets` job scans new commits (`--log-opts`) on PRs/pushes and documents the pre-existing commit `9817f24` honestly in `docs/SDLC.md`.

---

# Architecture Document: Sprint 28 — Hygiene, CI/Security & Coverage UX Polish

*   **Status**: Approved — Smith Gate 2 & Switch Gate 2b
*   **Author**: Morpheus
*   **Last Updated**: 2026-11-24
*   **Scope**: Sprint 28 Architecture

## 1. Executive Summary & System Overview

Sprint 28 strengthens operational hygiene, static quality gates, and Coverage UI ergonomics across four decoupled areas without altering the database schema, CLI flags, or core query semantics:
1. **Coverage Web UI polish** (`via/web/template.py`, `via/web/static/app.js`) — empty-state visibility for `#coverage-efficiency-wrap` and higher-contrast `#legend-mid` swatch.
2. **`DatabaseStore` complexity refactor** (`via/db/store.py`) — extract cohesive private helper methods from 5 existing C901 hotspots with zero SQL or return-shape changes.
3. **Build-time security scan targets** (`Makefile`, `pyproject.toml`, `docs/SDLC.md`) — add `security-scan-python`, `security-scan-npm`, and aggregate `security-scan`.
4. **GitHub Actions CI** (`.github/workflows/ci.yml`, `docs/SDLC.md`) — least-privilege, SHA-pinned automated verification on pushes and PRs.

## 2. System Context & Boundaries

- **Web UI boundary:** Pure browser DOM/CSS adjustment inside existing single-page app (`via/web/template.py` + `via/web/static/app.js`). No new HTTP routes or API schema changes.
- **Database boundary:** Refactoring stays strictly private inside `DatabaseStore` (`via/db/store.py`). Public method signatures, return types, SQL semantics, and `SCHEMA_VERSION` (8) remain unchanged.
- **CI & Supply-Chain boundary:** `.github/workflows/ci.yml` executes untrusted PR code in isolated GitHub-hosted runners with `contents: read` token only (no write scopes, no PyPI OIDC token, no secrets exposed). `pip-audit` and `npm audit` query advisory databases locally when invoked via `bobp make security-scan*`.

## 3. Component & Container Architecture

| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `via/web/template.py` + `via/web/static/app.js` | Render `#coverage-efficiency-empty` when `efficiencyData.length === 0`; style `#legend-mid` with crisp border/fill | `GET /api/coverage/test-efficiency` JSON array | DOM table or empty-state hint |
| `via/db/store.py` | Factor 5 complex methods into private helpers (`_apply_migration_v*`, `_build_rel_query_parts`, `_append_cte_clauses`, etc.) with McCabe complexity `<= 10` | Existing `DatabaseStore` calls | Identical SQL results & schema state |
| `Makefile` + `pyproject.toml` | Expose `security-scan-python`, `security-scan-npm`, `security-scan` (adding `pip-audit` to `[project.optional-dependencies].dev`) | `.venv` packages, `package-lock.json`, git repo | Exit 0 on clean, non-zero on findings |
| `.github/workflows/ci.yml` | Run Python test/lint/smoke matrix, JS tests, and gitleaks check on pushes to `main` and PRs | GitHub push / PR events | GitHub Check statuses |

## 4. Runtime Interaction & Critical Flows

- **Efficiency empty-state flow:** `loadCoverageView()` fetches `/api/coverage/test-efficiency` → calls `renderEfficiencyTable(results)` → if `results.length === 0`, keeps `#coverage-efficiency-table` column headers visible (Recognition Rather Than Recall — Smith Gate 2 note), clears tbody, and displays `#coverage-efficiency-empty` (`Run make test-coverage to capture per-test efficiency data.`) directly beneath the table; otherwise hides `#coverage-efficiency-empty` and renders sorted rows.
- **DatabaseStore refactor flow:** Every refactored public method delegates step-wise work to cohesive private helpers; existing unit, integration, and UAT suites validate 100% behavioral equivalence.
- **CI flow:** On push to `main` or PR → parallel `test-python` (3.10, 3.12), `test-js`, and `secrets` jobs run independently with `permissions: contents: read`.

## 5. Interface & Contract Specifications

- **Make targets (new):**
  - `bobp make security-scan-python` → runs `.venv/bin/pip-audit` (installed via `dev` optional deps); exit 0 = clean, non-zero = vulnerabilities found or tool missing.
  - `bobp make security-scan-npm` → runs `npm audit --audit-level=high`; exit 0 = clean, non-zero = high/critical findings or tool missing.
  - `bobp make security-scan` → depends on `security-scan-secrets security-scan-python security-scan-npm`.
- **DOM contract (new element):**
  - `#coverage-efficiency-empty` inside `#coverage-efficiency-wrap` (hidden by default when rows exist; visible with `make test-coverage` guidance when 0 rows).
- **No CLI flag, MCP tool, or HTTP JSON contract changes.**

## 6. Cross-Cutting Concepts & Resilience

### Failure Modes & Error Handling
| Failure Mode | Trigger / Condition | System Behavior | User / Client Impact | Blast Radius |
|---|---|---|---|---|
| Empty efficiency dataset | `make test-coverage` not yet run | Hide empty table, show `#coverage-efficiency-empty` | Clear guidance instead of blank screen | Efficiency sub-view only |
| Missing scanner binary | `gitleaks`/`npm`/`pip-audit` absent | Target prints install hint and exits 1 | Fail-loud, never silently green | Local scan invocation only |
| Vulnerable dependency detected | `pip-audit` or `npm audit` flags CVE | Non-zero exit code with advisory list | Blocks release until fixed or user-accepted | Dependency audit gate |
| Regression during `store.py` refactor | Subtle SQL/migration mismatch | Existing 1,409-test suite fails immediately | Caught before Trin handoff | Isolated to `via/db/store.py` |

### Security & Privacy
- **Trust / access boundaries:** `.github/workflows/ci.yml` runs with `permissions: { contents: read }`, SHA-pinned actions, and SHA-256-verified gitleaks download. Zero secrets or OIDC write tokens in CI.
- **Sensitive data:** No `.gitleaksignore` or allowlist is ever introduced. Pre-existing `.continue/agents/config.yaml:10` remains openly tracked in `docs/SDLC.md` and `agents/switch/state.md`.

## 7. Technical Stack & SDLC / Build Impact

- **Languages & Runtime:** Python `>=3.10` (CI matrix 3.10, 3.12; local 3.13.5), Node.js `v24` / npm `11` (CI Node 22 LTS).
- **Core Libraries & Tools:** Adds `pip-audit>=2.7.0` to `[project.optional-dependencies].dev` in `pyproject.toml`; reuses existing `npm`, `gitleaks`, `ruff`, `pytest`, `vitest`.
- **Build-Environment Check (CRITICAL):**
  - Does this design add a new Makefile mechanism, CI workflow, or SDLC gate? **Yes** — adds `.github/workflows/ci.yml`, `security-scan*` Make targets, and `pip-audit` dev tool, requiring `docs/SDLC.md` updates.
  - **Explicitly flagged for Mouse:** Schedule **Phase 0 (Tank + Switch)** to establish the CI workflow, `security-scan*` Makefile targets, and `docs/SDLC.md` mechanism updates cleanly.

## 8. Architectural Decisions (ADRs) & Technical Debt

### Decision Records
- **ADR-28-1 (Pure Helper Extraction in `via/db/store.py`):** Reduce McCabe complexity (`C901 <= 10`) strictly by extracting cohesive private helpers inside `DatabaseStore` rather than rewriting query architecture or splitting modules mid-maintenance sprint. Minimizes diff risk while achieving 0 Ruff warnings.
- **ADR-28-2 (CI `secrets` Job Scope):** Run SHA-256-verified `gitleaks` in CI on pushed/PR commit ranges (`--log-opts`) while `.continue/agents/config.yaml:10` awaits owner rotation/history decision, avoiding both false-green allowlists and permanently red unrelated PRs. Switch upgrades to full-history scan once the owner clears `9817f24`.

### Acknowledged Technical Debt & Trade-offs
- **Python lockfile deferred:** `pip-audit` audits the installed `.venv` rather than an exported `uv.lock`; documented in `docs/SDLC.md` Section 9 until the project adopts a Python lockfile.
- **Playwright E2E stays local:** Keeps CI under ~2 minutes without browser-download flakiness; Smith/Trin continue running `bobp make test-e2e` locally for web UI changes.
