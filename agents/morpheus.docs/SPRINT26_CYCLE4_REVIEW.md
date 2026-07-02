# Sprint 26 Cycle 4 Architecture Review — Relationship Type Hierarchy

**Reviewer**: Morpheus (Tech Lead)
**Date**: 2026-07-01

## Verdict: APPROVED

## Architecture Assessment

**Genuine polymorphism, not a lookup table dressed up as one.** `leaves()`
walks `__subclasses__()` recursively — a new leaf class defined anywhere
under a category is automatically included in that category's expansion
with zero changes to any dispatch code. `execute()` is one non-branching
entry point used uniformly by the executor for both a single leaf (runs
once) and a category (fans out + merges) — `is_category()` only appears at
two *policy* boundaries (rejecting `--sans` + category, rejecting chained +
category), not in the query-execution path itself. This is the right
shape: the type hierarchy owns its own execution semantics; the executor
just asks for it.

**Backward compatibility is real, not just tested.** The pre-existing
`ReferenceType` enum (used by the web API and `ViaQueryBuilder`) is
untouched. `execute_relation()` and `is_category()` both duck-type against
either a `Relation` subclass or a bare `ReferenceType` member, so nothing
downstream of the CLI parser needed to change.

## The Design Doc Inconsistency

Confirmed the finding: the approved doc's diagram and its own prose
definition of "upstream"/"downstream" disagreed for the calls/references/
imports/inherits-from/http-calls pairs. Neo's resolution — trust the prose
(defines user-facing meaning) and verify empirically against a real query
plus the pre-existing `callers` canned query (which already encoded
`--via calls -mg {symbol}` = "callers of symbol", i.e. upstream) — is the
correct call. Leaving `declares`/`declared-in` matching the diagram as-is
(genuinely ambiguous, structural rather than dependency-directional) is
also the right judgment call rather than guessing further.

## Two things worth recording, not fixing now

1. **`__subclasses__()` is process-global, not scoped.** Any code
   (including a test file) that defines another subclass of `Any`/
   `UpstreamRef`/`DownstreamRef`/`Relation` in the same Python process would
   silently become part of every category's expansion from then on. Not an
   issue today — no such subclasses exist outside `relationship_types.py`
   itself, and 1372 tests confirm no accidental pollution — but worth
   knowing if a future contributor ever considers a test double here.
2. **Smith's declares/declared-in noise finding** (Trin's UAT) is a real
   product question, not an architecture one — whether `any-ref` should
   include structural containment at all is a UX call, not something to
   resolve in this review.

## Sizing / Scope
Matches the original Cycle 4 scope from `docs/DESIGN_RELATIONSHIP_HIERARCHY.md`,
narrowed to Any/UpstreamRef/DownstreamRef per the user's explicit scope
decision (ReaderRef/WriterRef, which had no defined query semantics, were
correctly left out).

## Closing
Architecture is sound. Handing to Smith for the usability read on the
declares/declared-in finding — that's the only open item before this cycle
closes.
