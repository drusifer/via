# Agent State

Keep this working-memory file current. Preserve exactly these three top-level sections; see the
State Management Protocol in `.agents/skills/bob-protocol/SKILL.md` for entry and exit steps.

## Context
- **Recent decisions:** Audited Tank's PyPI release pipeline (`.github/workflows/publish.yml`, `pyproject.toml`, `Makefile`, `dist/*`) and verified gitleaks pre-commit hook setup.
- **Key findings:**
  - Release pipeline (`.github/workflows/publish.yml`): SHA-pinned actions, top-level `permissions: contents: read`, `id-token: write` scoped to `publish` job only, `environment: pypi` with required reviewer `drusifer`, isolated wheel smoke check. Wheel/sdist contain zero secrets, zero `.via/*.db`, zero `agents/`/`tests/`/`.continue/`, and use `drew@gs.works`.
  - Gitleaks checklist: `gitleaks` on PATH, `.githooks/pre-commit` executable, `install-hooks` & `security-scan-secrets` in `Makefile`, `git config core.hooksPath` = `.githooks`.
  - **Pre-existing repo finding (High):** `bobp make security-scan-secrets` found 1 leak (`generic-api-key`) at `.continue/agents/config.yaml:10` (commit `9817f24`, 2026-02-07; file still tracked in HEAD). Not packaged in `dist/*`, but repo is public (`drusifer/via`) — needs verification/rotation if real and removal from repo/history.
- **Important notes:** Never allowlist or ignore gitleaks findings.

## Current Task
- **Status:** Complete
- **Assigned to:** Switch
- **Started:** 2026-11-23
- **Description:** Security audit of PyPI release pipeline and repository secret scan before `via-index` release.
- **Progress:** Release workflow and built artifacts passed audit; pre-existing gitleaks finding surfaced and reported to Tank and User.
- **Blockers:** Open High secret-scan finding in `.continue/agents/config.yaml:10` (pre-existing, commit `9817f24`).
- **Consultations:** Tank (release pipeline audit).

## Next Steps
- **Immediate next action:** Await user verification/rotation of `.continue/agents/config.yaml:10` and removal if real; re-run `bobp make security-scan-secrets` after remediation.
- **Waiting on:** User / Tank
- **Planned work:** Re-verify `bobp make security-scan-secrets` clean after `.continue/agents/config.yaml` is addressed.

---
*Last updated: 2026-11-23*
