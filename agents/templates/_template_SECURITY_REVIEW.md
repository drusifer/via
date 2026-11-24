<!--
Security review report. Owned by Switch (`*sec review`, `*sec audit`); one per reviewed target.
Structure follows OWASP Code Review Guide practice (scope from risk and threat model, then
area checklists), ASVS-style assurance levels, and NIST SSDF PW.7 (review human-readable code
against standards, track issues, record root causes). Individual issues go in
`_template_SECURITY_FINDING.md` files; this report summarizes and links them.
Remove this note and the check block when used. File as `agents/switch/reviews/<YYYY-MM-DD>-<slug>.md`.
-->
# Security Review: {Target}

- **Verdict:** {Blocked | No blocking findings | Incomplete (coverage gaps listed below)}
- **Date / reviewer:** {YYYY-MM-DD} / Switch
- **Target and version:** {diff range, commit, PR, feature, or component, with version}
- **Assurance level:** {L1 baseline | L2 standard | L3 high assurance} — {why this level fits the target's risk}
- **Findings:** {N total: Critical X, High X, Medium X, Low X, Info X}
- **Related work:** {story, ADR, prior review, or N/A with reason}

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| {Neo / Tank / Trin / Morpheus / Switch / User} | {Specific action} | {Before merge / next sprint / when X} |

{The first row is the single next step. A Blocked verdict names who unblocks it.}

## Scope and Threat Model

- **In scope / out of scope:** {Files, services, dependencies, workflows reviewed, and what was deliberately excluded}
- **Assets worth protecting:** {Data, credentials, integrity, availability}
- **Entry points and trust boundaries:** {User input, files, network, CI, third-party code, who is trusted}
- **Threats considered:** {Abuse cases or STRIDE categories (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege) that apply, and ones judged not applicable with a reason}

## Method and Coverage

- **Reviewed by:** {Manual read of changed code and its callers; scanners run with exact commands, e.g. `bobp make security-scan`}
- **Tool results:** {Tool, version, command, and outcome. Say "not run" with the reason if a scanner was unavailable.}
- **Not covered:** {Areas, files, or checks skipped, and why. "None" only when true.}

## Area Checklist

Mark each area **Pass**, **Finding** (link the SEC ID), or **N/A** (give the reason). Do not leave an area blank.

| Area | What to check | Result |
|---|---|---|
| Input handling and injection | Untrusted input validated at the boundary; no shell, SQL, path, template, or deserialization injection | {Pass / SEC-NNN / N/A: reason} |
| Authentication and sessions | Credential handling, session lifetime, token storage, brute-force limits | {…} |
| Authorization and access control | Every sensitive action checks the caller; least privilege; no direct object access | {…} |
| Secrets and cryptography | No secrets in code, logs, or history; vetted algorithms and libraries; keys rotated | {…} |
| Data protection and privacy | Sensitive data minimized, encrypted in transit and at rest where required, not over-logged | {…} |
| Error handling and logging | Errors leak no internals; security events logged; logs free of secrets | {…} |
| Dependencies and supply chain | Pinned versions, lockfile audited, unmaintained or vulnerable packages triaged | {…} |
| Configuration, build, and CI | Safe defaults; workflow permissions minimal; actions and images pinned; no debug in release | {…} |
| Files, processes, and network | Safe temp files and paths; subprocess use; outbound requests restricted; resource limits | {…} |
| Business logic and abuse cases | Workflows cannot be reordered, replayed, or abused for gain | {…} |

## Findings

| ID | Title | Severity | Status | Owner |
|---|---|---|---|---|
| {SEC-NNN} | {Title, linked to its finding file} | {Severity} | {Open / Fixed / Accepted risk} | {Persona} |

{Write "No findings" when empty; do not delete the table.}

## Root Causes and Recommendations

{Patterns behind the findings (for example, missing validation at a shared boundary) and the smallest systemic fix, or None.}

## Sign-off

- **Re-review needed:** {Yes, trigger / No}
- **Risk acceptance:** {None | Accepted by {user} on {date}, **expires {YYYY-MM-DD}**, per finding ID. Expired acceptances are listed as open.}
- **Verification:** {Tests and scans run after fixes, with results, or Pending}

<!-- RUBRIC-START -->
## Check — SECURITY REVIEW

- [ ] **PASS** — Verdict, target and version, assurance level (with a risk-based reason), and findings count are filled and agree with the Findings table.
- [ ] **PASS** — Scope names what was and was not reviewed; the threat model lists assets, entry points, trust boundaries, and applicable threats with reasons for any omitted.
- [ ] **PASS** — Method records the exact scanner commands and outcomes, and states any "not run" with a reason; Not covered is honest and specific.
- [ ] **PASS** — Every checklist area has Pass, a finding ID, or N/A with a reason; no area is blank, and each Pass could be backed by something the reviewer actually read or ran.
- [ ] **PASS** — Every finding in the table has its own `_template_SECURITY_FINDING.md` file with severity, evidence, and a Next Action table.
- [ ] **PASS** — The Next Action table names a persona, concrete action, and trigger for each row; a Blocked verdict states who unblocks it and how.
- [ ] **PASS** — Verdict follows the findings: any open High or Critical gives Blocked, and Incomplete is used when coverage gaps prevent a conclusion.
- [ ] **PASS** — No secrets, working exploits, or private data appear; risk acceptance is recorded only by the user and every acceptance has an expiry date.
- [ ] **FAIL** — Any required field, area, or evidence is missing or contradictory; cite the gap and smallest correction.
<!-- RUBRIC-END -->
