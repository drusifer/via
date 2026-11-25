# Sprint 28 Task Board: Hygiene, CI/Security & Coverage UX Polish

*   **Goal**: Establish automated GitHub Actions CI and build-time dependency security scans, clear all 5 pre-existing Ruff complexity errors and vitest cache git-tracking noise, and polish the Coverage web UI empty state and legend contrast.
*   **Tier**: Tier 2 (Hygiene / Maintenance / UX Polish)
*   **Branch**: `main` (per `docs/SDLC.md` Section 6)
*   **Stories & Architecture**: `docs/sprints/USER_STORIES_SPRINT28.md`
*   **Gates Passed**: Smith Gate 1 & Gate 2 APPROVED; Switch Gate 2b (`security gate (design): No blocking findings`); Morpheus Step 3a Plan Review APPROVED; Phase 0–3 & Closeout Gates PASSED
*   **Status**: CLOSED & LAUNCHED (2026-11-24)

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Level: L1 | Owner: Mouse | Trace: N/A — sprint gate | Verification: `test -f docs/SDLC.md`*)

---

## Sprint Execution Phases

### Phase 0: Security Scan Targets, GitHub Actions CI & SDLC Mechanism
*Phase goal: Add Python/JS dependency security scan targets (`STORY-VIA-283`), least-privilege GitHub Actions CI (`STORY-VIA-284`), and update `docs/SDLC.md`.*

- [x] **Task 0.2:** Add `pip-audit>=2.7.0` to `pyproject.toml` `[project.optional-dependencies].dev`, wire `security-scan-python`, `security-scan-npm`, and aggregate `security-scan` targets in `Makefile`, and run both dependency scans (remediating or escalating any findings per `.agents/skills/security/SKILL.md`). (*Level: L2 | Owner: Switch | Trace: STORY-VIA-283 | Verification: `bobp make security-scan-python && bobp make security-scan-npm` — 0 Python vulns, 0 npm vulns after user-approved Vitest 5 upgrade*)
- [x] **Task 0.3:** Create SHA-pinned, least-privilege `.github/workflows/ci.yml` (`test-python` 3.10/3.12 with `ruff check via/`, `pytest`, `via --help`; `test-js` with `npm ci && npm test`; `secrets` with SHA-256-verified `gitleaks`), review Switch's Makefile targets, and update `docs/SDLC.md` Sections 3, 5, 8, and 9. (*Level: L2 | Owner: Tank | Trace: STORY-VIA-283, STORY-VIA-284, ADR-28-2 | Verification: `yaml.safe_load` & `bobp make help` passed*)
- [x] **Task 0.4:** Audit `.github/workflows/ci.yml` permissions, SHA pins, gitleaks checksum, and `Makefile` scan targets. (*Level: L1 | Owner: Switch | Trace: STORY-VIA-283, STORY-VIA-284 | Verification: `security gate (phase 0): No blocking findings` in `agents/CHAT.md`*)

### Phase 1: Ruff Complexity Refactor & Vitest Cache Cleanup
*Phase goal: Bring `ruff check via/` to zero errors via pure helper extraction in `via/db/store.py` and stop `bobp make test-js` from dirtying `git status` (`STORY-VIA-282`).*

- [x] **Task 1.1:** Extract cohesive private helpers for all C901 methods in `via/db/store.py` and 6 other `via/` modules with zero behavioral change; add `node_modules/` to `.gitignore` and untrack all 1,041 vendored files (`git rm -r --cached node_modules/`). (*Level: L2 | Owner: Neo | Trace: STORY-VIA-282, ADR-28-1 | Verification: `.venv/bin/ruff check via/` & `bobp make lint-fast` exit 0*)
- [x] **Task 1.2:** Run full Python and JS test suites and confirm zero regressions and clean `git status` under `node_modules/` after `bobp make test-js`. (*Level: L1 | Owner: Trin | Trace: STORY-VIA-282 AC 2-4 | Verification: `bobp make test` 1,410 passed / 0 failed; `bobp make test-js` 109 passed*)
- [x] **Task 1.3:** Security review of Phase 1 diff (`via/db/store.py` SQL/query safety and gitleaks hook check). (*Level: L1 | Owner: Switch | Trace: STORY-VIA-282 | Verification: `security gate (phase 1): No blocking findings` in `agents/CHAT.md`*)
- [x] **Task 1.4:** Code & architectural review of `DatabaseStore` helper decomposition. (*Level: L2 | Owner: Morpheus | Trace: STORY-VIA-282, ADR-28-1 | Verification: `rubric LOOP_IMPL:` verdict recorded in `agents/CHAT.md`*)

### Phase 2: Coverage UX Polish (Efficiency Empty-State & Legend Contrast)
*Phase goal: Add a clear Efficiency empty-state hint (keeping column headers visible per Smith Gate 2) and improve `#legend-mid` swatch contrast (`STORY-VIA-281`).*

- [x] **Task 2.1:** Using TDD (JS + Playwright E2E tests first), add `#coverage-efficiency-empty` below `#coverage-efficiency-table` (shown when 0 rows, hidden when rows exist; table headers remain visible) and darken/border `#legend-mid` in `via/web/template.py` and `via/web/static/app.js`. (*Level: L2 | Owner: Neo | Trace: STORY-VIA-281 | Verification: `bobp make test-js` 109 passed & `bobp make test-e2e` 27 passed*)
- [x] **Task 2.2:** Verify Coverage JS unit tests, Playwright E2E assertions, and error-fallback behavior. (*Level: L1 | Owner: Trin | Trace: STORY-VIA-281 AC 1-4 | Verification: `bobp make test-js && bobp make test-e2e`*)
- [x] **Task 2.3:** Security review of Phase 2 diff (XSS safety on empty-state DOM and gitleaks hook check). (*Level: L1 | Owner: Switch | Trace: STORY-VIA-281 | Verification: `security gate (phase 2): No blocking findings` in `agents/CHAT.md`*)
- [x] **Task 2.4:** Code review of Phase 2 template/JS changes. (*Level: L1 | Owner: Morpheus | Trace: STORY-VIA-281 | Verification: `rubric LOOP_IMPL:` verdict recorded in `agents/CHAT.md`*)

### Phase 3: Canonical Domain Model (`docs/DOMAIN.md`)
*Phase goal: Author and review `docs/DOMAIN.md` capturing VIA's bounded contexts, ubiquitous language, invariants, and documented drifts (`STORY-VIA-285`).*

- [x] **Task 3.1:** Co-author `docs/DOMAIN.md` from `agents/templates/_template_DOMAIN.md` (template notes and rubric block removed), grounded 1:1 in verified `via/` symbols and linked from `README.md`. (*Level: L2 | Owner: Cypher & Morpheus | Trace: STORY-VIA-285 | Verification: `test -f docs/DOMAIN.md && ! grep -q 'RUBRIC-START' docs/DOMAIN.md`*)
- [x] **Task 3.2:** Review `docs/DOMAIN.md` against the `DOMAIN` rubric (`LANG`, `BOUND`, `INVAR`, `STATE`, `EVENT`) and post verdict line. (*Level: L1 | Owner: Smith | Trace: STORY-VIA-285 AC 1-4 | Verification: `rubric DOMAIN:` verdict in `agents/CHAT.md`*)

---

## Stage 3: Sprint Closeout

- [x] **Task C.1:** Run SDLC conformance check and update `docs/SDLC.md` *Last verified* line. (*Level: L2 | Owner: Tank | Trace: N/A — closeout | Verification: `bobp make test && bobp make test-js && bobp make security-scan-python && bobp make security-scan-npm && bobp make dist`*)
- [x] **Task C.2:** Groom docs (`README.md`, `docs/SDLC.md`), apply SDLC rubric to updated `docs/SDLC.md`, and archive Sprint 28 chat report. (*Level: L1 | Owner: Oracle | Trace: N/A — closeout | Verification: `bobp chat-report --moniker SPRINT_28 --summary "..."`*)
- [x] **Task C.3:** End-to-end usability testing in real Chromium, inspecting `ux-10-coverage-heatmap.png` (`#legend-mid` contrast) and `ux-11-coverage-efficiency.png` (empty-state hint + visible headers). (*Level: L1 | Owner: Smith | Trace: STORY-VIA-281 AC 1-3 | Verification: `bobp make test-e2e` 27 passed & `rubric UAT:` verdict in `agents/CHAT.md`*)
- [x] **Task C.4:** Coordinate team retrospective and feed backlog items to Cypher. (*Level: L1 | Owner: Mouse | Trace: N/A — closeout | Verification: Retro messages posted in `agents/CHAT.md`*)
- [x] **Task C.5:** Update `CHANGELOG.md`, groom `agents/cypher/BACKLOG.md`, and post Sprint 28 launch announcement. (*Level: L1 | Owner: Cypher | Trace: N/A — release decision | Verification: `*pm launch Sprint 28` posted in `agents/CHAT.md`*)

---

## Prior Sprints (Completed)
- **Sprint 27 (Phase 1 & Phase 2):** CLOSED & LAUNCHED (2026-11-24, commit `676952f`) — per-test coverage capture, D3 zoomable-icicle intensity heatmap (LOC sizing, outliers, leaf drill-down), efficiency table + imported-module coverage & `mocks_only` signal, `docs/SDLC.md`, `via-index 0.1.0` live on PyPI. Archive: `agents/chat_archive/CHAT_SPRINT_27.md`.
- **Sprint 26:** CLOSED (2026-07-01) — CLI/executor registries, CTE query optimization, polymorphic relationship hierarchy (`blast`).
