# Sprint 26 Cycle 4 Usability Read — declares/declared-in in blast categories

**Reviewer**: Smith (HCI)
**Date**: 2026-07-01

## Verdict: Recommend removing declares/declared-in from the categories (small fix, not a blocker to discuss further)

## Analysis

**HEURISTIC: #8 Aesthetic and Minimalist Design.** A user running
`--canned blast --args symbol=helper` expects "what breaks if I change
helper" — actionable call-graph impact. Getting the containing file back
too (as both a `filepath` and `filename` symbol) isn't actionable: the user
already knows what file their own named symbol lives in. It's noise, not signal.

**This isn't just a taste call — the design doc's own prose backs it up.**
Re-read `docs/DESIGN_RELATIONSHIP_HIERARCHY.md`'s "Actual Requirements"
section (the ground-truth statement of what's needed, not the diagram):

> - Upstream References: Callers, referencers, importers, or subclasses that
>   depend on the targeted symbol.
> - Downstream References: Callees, referencees, imported modules, or parent
>   classes that the targeted symbol utilizes.

No mention of containers or members anywhere. Only the Mermaid diagram
included `Declares`/`DeclaredIn` under the categories — the same kind of
diagram-vs-prose gap Neo already found and fixed for the upstream/downstream
direction. Applying the same principle here: trust the prose.

## Recommendation
Remove `Declares`/`DeclaredIn` as subclasses of `DownstreamRef`/`UpstreamRef`
(make them direct `Relation` leaves with no category parent). They stay
fully usable standalone (`--via declares`, `--via declared-in` unchanged) —
they just stop being swept into `any-ref`/`upstream-ref`/`downstream-ref`/
`blast`. Cheap, low-risk, improves the actual feature's signal-to-noise
ratio, and is more faithful to the approved requirement than the diagram was.

## Handoff
Recommend Neo make this small adjustment before closing Cycle 4.
