<!--
Security finding. Owned by Switch (`*sec`); fill every field so a reader who sees only this
file knows what is wrong, how bad it is, and who does what next. Remove this note and the
check block when used. File as `agents/switch/findings/<YYYY-MM-DD>-<slug>.md`.
-->
# SEC-{NNN}: {Short title naming the weakness and where}

- **Severity:** {Critical | High | Medium | Low | Info} — {one sentence on impact and exploitability in this project}
- **Status:** {Open | Fix proposed | Fixed | Accepted risk | Not applicable}
- **Verdict:** {Blocked | No blocking findings}
- **Date / author:** {YYYY-MM-DD} / Switch
- **Affected:** {file:line, package@version, workflow, or config}
- **Class / reference:** {CWE, advisory ID (GHSA/CVE), or short weakness class}

## Next Action

| Who | Does what | By / trigger |
|---|---|---|
| {Neo / Tank / Trin / Morpheus / Switch / User} | {Specific action: apply patch, add test, accept risk, re-scan} | {Before merge / next sprint / when X is released} |

{Every row names one persona and one concrete action. The first row is the single next step.}

## Evidence

- **Reproduce / detect:** {Exact command and output, or file and line. Safe confirmation only; no working exploit.}
- **Observed:** {Facts only}
- **Confidence:** {High | Medium | Low, with what would raise it}

## Impact and Reachability

{What an attacker or failure could cause, whether the vulnerable path is reachable here, and whether the scope is runtime or dev/tooling.}

## Recommendation

- **Fix:** {Smallest change: diff, upgrade, swap, or removal, with the version or code}
- **Verify:** {Test or scan that proves it is fixed, e.g. `bobp make security-scan` clean}
- **Alternatives rejected:** {Option and why, or None}

## Risk Acceptance

{Not accepted | Accepted by {user} on {date}, **expires {YYYY-MM-DD}** (at most 90 days out): reason, scope, and re-check trigger. After the expiry date the acceptance no longer counts: the user renews it or the risk is fixed.}

<!-- RUBRIC-START -->
## Check — SECURITY FINDING

- [ ] **PASS** — Severity, status, verdict, affected item, and reference are all filled, and the severity sentence explains impact in this project's context.
- [ ] **PASS** — The Next Action table has at least one row; each row names a single persona, a concrete action, and a trigger or deadline.
- [ ] **PASS** — Evidence is reproducible or checkable, separates observation from interpretation, and contains no secrets or working exploit.
- [ ] **PASS** — Impact states reachability and scope; the recommendation gives the smallest fix and how to verify it.
- [ ] **PASS** — Risk acceptance is recorded only by the user, with reason, scope, re-check trigger, and an expiry date no more than 90 days out; otherwise it says Not accepted.
- [ ] **FAIL** — A required field is empty, the next owner or action is vague, or a High/Critical finding has no verdict of Blocked; cite the gap and smallest correction.
<!-- RUBRIC-END -->
