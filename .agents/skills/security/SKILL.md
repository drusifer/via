---
name: security
description: Shared security practice for Bob Protocol projects. Covers build-time scans (secrets, dependency audits), triaging vulnerable dependencies, and how to swap or remove them safely. Used by Switch; other personas follow its gates.
---

One-line summary: How the team scans for security problems at build time and fixes vulnerable dependencies without breaking the build.

TLDR:
    Run `bobp make security-scan` (secrets + Python + npm audits). Fix findings by the smallest safe change: upgrade, swap, or remove the dependency. Never accept High/Critical risk without the user.
    Switch owns scans and security-driven dependency changes; Tank owns the Makefile mechanism and `docs/SDLC.md`; Neo owns application code.

# Security Skill

## Triggers

`*sec deps`, `*sec audit`, `*sec scan`, and any request to set up build-time security scanning.

## Requires

- [bob-protocol](../bob-protocol/SKILL.md)
- [make](../make/SKILL.md)
- [test-runner](../test-runner/SKILL.md)

## 1. Build scans

Every project gets scans for the ecosystems it uses, fronted by `make` targets and run through `bobp make <target>`:

| Scan | Typical tool | Target |
|---|---|---|
| Committed secrets (git-aware, never `--no-git`) | `gitleaks detect --source .` | `security-scan-secrets` |
| Python dependencies | `pip-audit` on the exported lockfile | `security-scan-python` |
| JavaScript dependencies | `npm audit` on the lockfile | `security-scan-npm` |
| Aggregate | all of the above | `security-scan` |

### Gitleaks is always set up

Switch verifies this at the start of every review, audit, or scan, and fixes any gap:

- [ ] `gitleaks` is on `PATH` (`gitleaks version`); if not, give the install step and stop the secrets scan as "not run".
- [ ] `.githooks/pre-commit` exists, is executable, and runs `gitleaks git --pre-commit --staged --redact` (shows the banner; fails if gitleaks is missing).
- [ ] The Makefile has `install-hooks` (`git config core.hooksPath .githooks`) and `security-scan-secrets`.
- [ ] `git config core.hooksPath` returns `.githooks`; if not, run `bobp make install-hooks`.
- [ ] Scans are git-aware (`gitleaks detect --source .`); `--no-git` is never used and `.env` files are never allowlisted.
- [ ] Prove it works once after setup: stage a fake key in an ignored scratch file and confirm the hook exits non-zero, then unstage and delete it.

Tank owns the secret-scanning standards; Switch applies and verifies them on each project. A missing or disabled hook is reported as a finding.

Setup procedure:
1. Detect ecosystems from manifests (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`); add a scan target for each, in the project `Makefile`.
2. Scan only lockfile-pinned versions so results are reproducible. If an ecosystem has no lockfile, report it as a gap rather than auditing an unpinned tree.
3. Run through `bobp make`, never an uncaptured command. If a scanner is not installed, say so and name the install step; do not skip silently.
4. Record the targets and the gate ("`security-scan` clean before release") in `docs/SDLC.md`. Tank owns that document: post `@Tank *devops sdlc <change and why>`, or include the SDLC edit for Tank's review.

## 2. Triage a vulnerable dependency

1. Identify whether it is **direct** or **transitive**, its **scope** (runtime or dev/tooling), the advisory, and whether the vulnerable code path is reachable here.
2. Rate severity for *this project*, not only the advisory score. A dev-only tool with denial-of-service risk differs from a runtime package parsing untrusted input.
3. Choose the least disruptive fix, in order:
   1. **Upgrade** to the patched release of the same package.
   2. **Override or pin** a patched transitive version (npm `overrides`, uv constraints) when the parent has not caught up.
   3. **Swap** to a maintained alternative with equivalent behavior.
   4. **Remove** the dependency if it is unused or trivial to replace.
4. **Never "fix" with a downgrade** to a much older or unrelated release (for example a tool's suggested `--force` fix that installs an ancient major version). Report it instead.

## 3. Apply the change safely

- Make one dependency change at a time, using the ecosystem's own tool (`uv add`/`uv remove`/`uv lock`, `npm install`/`npm uninstall`), so the lockfile updates with the manifest.
- Run `bobp make test` and the relevant scan before and after; the change is done when the scan is clean and tests still pass.
- If an API change breaks application code, stop: give Neo the failing tests and a proposed patch. Switch does not edit application source.
- Escalate to the user before: a major-version jump that changes behavior, removing a package the product depends on, or accepting a finding that has no fix.
- Record every finding and dependency change in `agents/switch/findings/` using [`_template_SECURITY_FINDING.md`](../../../agents/templates/_template_SECURITY_FINDING.md), including advisory ID, old and new versions, test result, and the Next Action table.

## 4. Accepting risk

**Hard block — never accepted: secrets.** `security-scan-secrets` (gitleaks) has no acceptance path. A finding means remove the secret and rotate the credential. No `.gitleaksignore`, allowlist, or baseline; Switch never adds one, and a change that does is a High finding.

**Acceptable with expiry — dependency advisories (npm and Python).** `tools/audit_gate.py` backs both `security-scan-npm` and `security-scan-python`. Only the user may accept an advisory, always with an expiry (below). The preferred fix is still to upgrade, swap, or remove the package; Python advisories count as blocking (pip-audit gives no severity) until fixed or accepted. Never add `--ignore-vuln` or an ignore file outside the gate.

Only the user accepts risk. **Every acceptance has an expiration date** (`expires`, YYYY-MM-DD, at most 90 days after it is granted; default 90). After that date the acceptance no longer counts: the gate blocks again until the user renews it with a fresh review or the risk is fixed. Switch warns 14 days ahead, lists expired acceptances as open in every review, and never records an acceptance without an expiry. Record an accepted advisory (npm or Python; match by GHSA, PYSEC, or CVE id) in `agents/switch/accepted-risks.json` (id, package, finding, who and when, reason, `expires`, re-check trigger); `tools/audit_gate.py` then notes it instead of failing the scan, and any new advisory still blocks. Record the accepted finding with its reason, scope, and a re-check trigger (for example, "re-run when promptfoo publishes a release that bumps glob"). An accepted High finding stays visible in `agents/switch/state.md`.
