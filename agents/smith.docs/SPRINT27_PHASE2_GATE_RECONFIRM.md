# Smith — Gate 1+2 Re-confirmation: Sprint 27 Phase 2 (Revised)

**Date**: 2026-07-01
**Reviewing**: `agents/cypher.docs/SPRINT27_PHASE2_USER_STORIES.md` (revised) +
`agents/morpheus.docs/SPRINT27_PHASE2_ARCHITECTURE.md` (revised)
**Verdict**: APPROVED WITH 2 NEW NOTES

## Why this needed re-confirmation

The merge changes what a user actually sees: instead of a coverage heatmap
(binary-ish, one question) plus a separate grouped-list (redundancy, a
second question), there's now one hierarchical view answering both via a
single continuous metric with an overlaid statistical flag. That's a good
simplification, but it introduces a genuinely new HCI question the old
design didn't have: color now has to carry *two different meanings*
(absolute intensity level, and peer-relative outlier status), and those can
disagree with each other. Worth catching before Neo builds it.

## New note 1 — outlier flag needs its own visual encoding, not just "very warm" on the intensity scale

`is_outlier` is a peer-group-relative statistical signal (per Cypher AC5),
but the color scale encodes absolute `intensity_pct`. These can diverge: a
method in a peer group that normally runs cold could be a genuine outlier
at, say, 250% (3x its group's norm) while a method elsewhere shows 250%
just because its whole peer group runs hot and isn't anomalous at all.
Relying on "how warm is the color" to communicate "is this an outlier" will
mislead users in exactly that case. **Recommend a separate, explicit visual
marker for `is_outlier: true`** (e.g. a border/outline or icon on the node)
independent of the continuous color fill — the color says "how much," the
marker says "is this unusual for its kind."

## New note 2 — pick a colorblind-safe hue pair for the diverging scale, not cold/warm as currently underspecified

The architecture doc says "cooler toward 0%, warmer toward high multiples"
but doesn't name specific hues. A naive warm/cool diverging scale often
defaults to red↔green, which is exactly the pairing ~8% of men can't
distinguish — the same issue flagged (and fixed in spec) for the original
Story 1. **Recommend blue↔orange** (or another colorblind-safe diverging
pair) instead of red↔green, centered at the 100% midpoint. This should be
named explicitly in the architecture doc / implementation, not left as
"warm/cool" which doesn't constrain the actual hue choice.

## Everything else — confirmed good

- Numeric `intensity_pct` always shown regardless of color (carries forward
  the original "never color alone" requirement) — confirmed present.
- D3 zoomable icicle for navigation — appropriate reuse of a standard
  library pattern, consistent with the user's explicit "don't build from
  scratch" instruction.
- Constructor/expected-high exclusion via peer-group comparison rather than
  a single global threshold — correctly avoids flagging every `__init__` as
  an "anomaly."
- No automated action tied to `is_outlier` (it's a flag for a human to look
  at, not a recommendation to delete/refactor) — consistent with the
  standing non-goal.
- Simplification (dropping the Jaccard-bucketing algorithm) is a genuine
  risk reduction, not just a scope cut — agree with Cypher/Morpheus's
  framing.

## Handoff

Approved with the 2 notes above folded in as Cycle 1 tasks (not blocking
re-architecture — both are UI-detail additions to the same endpoint/view,
not new data or endpoints). To Mouse for cycle re-breakdown (old Cycle 2
test-overlap grouping no longer exists as a separate cycle).
