# Sprint 26 Cycle 4 — Class-Based Relationship Type Hierarchy

**Author**: Neo
**Date**: 2026-07-01

## What shipped
- `via/core/relationship_types.py`: real polymorphic hierarchy — `Relation`
  base, `Any`/`UpstreamRef`/`DownstreamRef` categories, leaf classes
  (`Calls`, `CalledBy`, `References`, ...). Category expansion uses
  `__subclasses__()` recursion (`leaves()`), not a lookup table — adding a
  new leaf class anywhere under a category automatically includes it.
- `execute_relation()` / `Relation.execute()`: one uniform interface. The
  executor never checks `is_category()` to decide HOW to run a query — a
  leaf's `leaves()` is just itself, so `execute()` runs once; a category's
  `leaves()` returns many, so it fans out and merges (dedupe by identity,
  sort by file/line). `is_category()` is only used for two *policy* guard
  checks (`--sans` + category is rejected; chained multi-relationship
  queries + category is rejected) — both explicit scope boundaries, not
  implemented this cycle.
- `via/pipeline/parser.py`, `executor.py`, `relationship_filter.py`,
  `stage_builder.py`: updated to resolve/carry/execute the new hierarchy
  classes, while the older `ReferenceType` enum (used by the web API and
  `ViaQueryBuilder`) is completely untouched and still works standalone.
- `via/canned.py`: added the `blast` canned query
  (`--canned blast --args symbol=X`).
- 20 new tests: `tests/unit/test_sprint26_c4.py`.

## Bugs found and fixed during implementation
1. **Design doc inconsistency**: the approved doc's Mermaid diagram put
   `Calls` under `DownstreamRef` and `CalledBy` under `UpstreamRef` — but its
   own prose defines upstream as "symbols that point *to* the target" (i.e.
   callers). Empirically verified against a real query
   (`--via calls -mg <anchor>` returns the anchor's *callers*, matching the
   prose's "upstream" definition) and against the pre-existing `callers`
   canned query (`--via calls -mg {symbol}`), which already encoded this
   exact direction. Fixed the class assignments to match the prose/empirical
   behavior for calls/references/imports/inherits-from/http-calls.
   `declares`/`declared-in` (structural containment, not call-graph
   dependency — genuinely ambiguous) kept exactly as the diagram specifies.
2. **`RelationshipFilter.inverted` vs `relationship_type.inverted`**: these
   are two separate fields; expanding a category into per-leaf
   `RelationshipFilter` copies via `dataclasses.replace()` only swapped
   `relationship_type`, silently leaving the stale category-level
   `inverted=False`. Fixed by replacing both together.
3. **Plain `ReferenceType` has no `.inverted`**: older call sites (tests,
   web API path) construct `RelationshipFilter` with a bare `ReferenceType`
   enum member, which doesn't have `.inverted` at all (only my new `Relation`
   subclasses do) — crashed with `AttributeError`. Fixed with
   `getattr(leaf_cls, 'inverted', rel.inverted)` fallback.
4. **Category fan-out + per-leaf type validation**: a category like
   `any-ref` includes `Declares`, which validates container types (a
   function can't be a `declares` container) — a mismatch there aborted the
   *entire* blast query with a `ValueError`. Fixed: category fan-out treats
   a per-leaf `ValueError` as "this leaf contributes nothing," while a
   direct `--via declares` query with the same invalid combination still
   raises its normal, clear error (policy differs by *why* the leaf is
   being run, not by mechanism).

## Verified
- 20 new tests + full suite: 1372 passed, 1 skipped (pending final re-run).
- Real end-to-end blast-radius queries against a scratch project confirm
  upstream-ref/downstream-ref/any-ref/blast all return intuitively correct
  results.

## Scope boundaries (explicit, not implemented)
- Categories are not supported with `--sans` (NOT EXISTS across a category
  is a different, un-implemented semantic — clear parse-time error).
- Categories are not supported when chaining multiple `--via`/`--sans`
  filters in one query (clear runtime error) — only as the sole/final
  relationship filter, which covers the `blast` canned query's actual use case.

## Post-review adjustment (Smith's usability finding)
Removed `Declares`/`DeclaredIn` from the `DownstreamRef`/`UpstreamRef`
category parents (now plain `Relation` leaves, no category). The design
doc's diagram had included them, but its own "Actual Requirements" prose
never mentions structural containment (containers/members) as part of blast
radius — only callers/callees/importers/subclasses. Including them made
`any-ref`/`blast` surface the containing file as noise alongside genuine
call-graph results. Still fully usable standalone via `--via declares` /
`--via declared-in` — just no longer swept into
`any-ref`/`upstream-ref`/`downstream-ref`. Updated the test that exercised
category fan-out error-suppression (previously relied on `Declares`'
container-type check; now uses a monkeypatched synthetic failure on
`references` instead, testing the mechanism directly rather than depending
on which leaves happen to be in a category). 20/20 targeted tests pass;
full suite re-verified as the final checkpoint.
