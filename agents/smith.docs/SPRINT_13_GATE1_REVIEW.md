# Sprint 13 Gate 1 Review — CLI Relationship Redesign

_Author: Smith | Date: 2026-03-23_

## Decision: APPROVED WITH NOTES

The Sprint 13 PRD directly reflects the design work in `smith.docs/CLI_DESIGN_VIA_SANS_FLAGS.md` and `smith.docs/USE_CASES_20_QUESTIONS.md`. I am the origin of this design — it reflects real user needs and gaps I documented personally. Stories are well-formed. Proceeding with two required fixes and one note for Morpheus.

---

## Required Fixes (before arch)

### Fix 1: Resolve deprecated-alias discrepancy
`CLI_DESIGN_VIA_SANS_FLAGS.md` says: "Short aliases retained as deprecated aliases for one release."
PRD says: "No backward compatibility. Old flags are removed."

**PRD wins** — hard removal is cleaner and avoids a future cleanup sprint. Confirm: old `-V<rel>` flags produce `"unknown flag"` error, never silently pass through. The PRD AC already states this. Just ensuring we're aligned — no code should silently accept old flags.

**Action**: Morpheus ensure parser gives ArgParse `error()` for any `-V<rel>` pattern — do not alias them at all.

### Fix 2: S13-2 `--sans` semantics need a concrete example in --help
AC says: "the result pattern after `--sans` correctly constrains the NOT EXISTS subquery". This is correct but will confuse users if not shown in `--help`. The distinction is subtle:
- `--sans calls --match-glob "*"` = "not called by anything"
- `--sans calls --match-glob "external_*"` = "not called by anything matching `external_*`"

**Action**: S13-4 `--help` must include a concrete example of constrained `--sans` (not just the unconstrained case).

---

## Notes for Morpheus

- **S13-3 `--not` position**: AC says "`--not` applies only to the match stage it precedes". Make sure the parser enforces this positionally, not just logically.
- **S13-5 scope**: E2E Playwright tests in `tests/e2e/app.spec.js` don't test CLI flags directly (they go through the API), but any relationship query tests there should use updated syntax. Include in S13-5 scope if needed.
- **`--ref-type` removal**: S13-1 AC says `--ref-type` is removed (superseded by `--via`). Confirm web API (`/api/query`) is not affected — it uses `relationship_type` JSON field, not the CLI flag. This is Out of Scope per PRD and should stay that way.

---

## Story-by-Story Sign-off

| Story | Status | Notes |
|-------|--------|-------|
| S13-1: `--via`/`--sans` flag parsing | ✅ AC clear | Short forms `-V`/`-S` confirmed |
| S13-2: `--sans` NOT EXISTS execution | ✅ AC clear | Add constrained example to --help (Fix 2) |
| S13-3: `--not` match negation | ✅ AC clear | No short form is correct |
| S13-4: --help update | ✅ AC clear | Fix 2 adds one required example |
| S13-5: Test updates | ✅ AC clear | Add E2E scope check per note above |

**Gate 1: APPROVED.** Proceed to Morpheus arch with notes above.
