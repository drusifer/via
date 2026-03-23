# Sprint 12 — Smith Review

**Reviewer**: Smith (Expert User)
**Date**: 2026-03-22
**Status**: APPROVED WITH NOTES — revisions required before Morpheus arch

---

## Verdict: Approved with Required Revisions

Stories are solid overall. Two issues must be resolved before Morpheus arch; one item is a note for Morpheus.

---

## Issue 1 (REQUIRED) — S12-3: Missing Two-Stage Pattern for Relationship Queries

**Problem**: via's relationship queries require TWO match patterns:
```bash
via -mg '*service*' -tF -Vhas -mg 'test_*' -tf
       ↑ anchor                    ↑ target
```
The UI has ONE Match Card. A user trying to run any relationship query would have no way to specify the second (target) pattern. This is not a nice-to-have — relationship queries are broken without it.

**Required fix**: Add a second "Target Pattern" section to the Relationships Card (or a second Match Card that conditionally appears when a relationship type is selected):
- Target match type dropdown (Glob/Regex/SQL)
- Target pattern text input
- Target symbol types toggle-button group

When relationship = "(none)", the target section is hidden.

---

## Issue 2 (REQUIRED) — S12-2: `results` array has no schema

**Problem**: `POST /api/query` response is `{ "results": [...] }` but the shape of each result object is unspecified. The frontend renderer (S12-4) needs to know what fields to expect.

**Required fix**: Define the result object schema in S12-2 AC:
```json
{
  "symbol_name": str,
  "qualified_name": str,
  "symbol_type": str,
  "file_path": str,
  "line_number": int,
  "language": str
}
```
For diagram format, `results` may instead be `{ "mermaid_source": str }` — clarify this.

---

## Issue 3 (REQUIRED) — S12-5 vs Non-Goals Contradiction

**Problem**: S12-5 AC says "status updates within 1s of re-index completion" for the toast. Non-Goals says "No WebSocket push (polling is fine for MVP)." These are contradictory — 5s polling cannot deliver 1s toast.

**Required fix**: Choose one:
- Option A: Relax S12-5 AC to "within one poll cycle (≤5s)" — keeps polling-only simple.
- Option B: Add SSE (Server-Sent Events) as in-scope for S12-5 specifically (push re-index events, not full WebSocket). Move this to OQ-3 resolution.

Recommend Option A for MVP simplicity.

---

## Note for Morpheus — S12-3: Dual relationship controls are confusing

The Relationships Card has both:
- Dropdown: relationship type (`-V<X>` flags)
- Text input: "Ref type override" (`--ref-type`)

These are redundant to a user. Recommend the UI exposes only the dropdown; Morpheus should decide whether `--ref-type` maps to the dropdown or is dropped from the web UI entirely.

---

## What's Good

- S12-1: Clean integration with watch mode. `--no-web` escape hatch is exactly right.
- S12-2: CORS, health endpoint, elapsed_ms — all the right production details.
- S12-4: Empty state, error state, loading spinner — solid UX basics covered.
- S12-5 status card (P1): Excellent idea. "3 seconds ago" relative time is the right UX.
- Non-goals list is clear and prevents scope creep.
- Open questions for Morpheus are well-formed.

---

## Required Actions (Cypher)

1. Add two-stage pattern to S12-3 Relationships Card spec
2. Add `results` object schema to S12-2 AC
3. Resolve S12-5 vs Non-Goals contradiction (pick Option A or B)
4. Add note re: `--ref-type` UI simplification for Morpheus

Once revised, re-post for Smith final approve. Fast-track — changes are additive, no story restructuring needed.
