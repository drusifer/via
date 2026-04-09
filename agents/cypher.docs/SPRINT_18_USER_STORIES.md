# Sprint 18 — Polymorphic JS Parser Refactor

**Author**: Cypher (PM)  
**Date**: 2026-04-08  
**Theme**: Convert the JavaScript parser's top-level node dispatch from large conditional blocks into bounded polymorphic handlers without changing parser behavior.  
**Sources**: `agents/morpheus.docs/POLYMORPHIC_REFACTOR_PLAN_2026-04-08T20:52.md`, `agents/morpheus.docs/POLYMORPHIC_REFACTOR_CLASSES_2026-04-08T20:58.md`  
**Points**: ~2pt  
**Baseline**: Sprint 17 shipped with 138 targeted tests passing locally

---

## Sprint Goal

Sprint 17 added more JS/TS extraction paths, but the parser still relies on a large top-level node-type switch that is getting harder to extend safely. Sprint 18 should land the first refactor slice from Morpheus's class plan: extract the top-level symbol dispatch into handler objects while preserving the exact product behavior.

This sprint is intentionally a refactor sprint, not a feature sprint. Users should get the same query behavior as Sprint 17, but the code should be easier to extend for later parser work.

---

## Story

### S18-1: Polymorphic Top-Level JS Parser Handlers (P0, 2pt)

**As a** maintainer extending JS/TS indexing,  
**I want** top-level JS parser node handling split into stable handler classes,  
**so that** new symbol forms can be added without expanding a single large `if`/`elif` block.

#### Acceptance Criteria

1. `via/parsers/javascript_parser.py` replaces the current large top-level symbol-dispatch conditional with a handler registry or equivalent polymorphic dispatch.
2. The refactor covers the existing top-level symbol forms already supported in Sprint 17:
   - imports
   - functions
   - classes
   - TS interfaces and enums
   - top-level variable/lexical declarations
   - TS type aliases
   - export wrappers
3. Export-wrapper handling reuses the same handler path rather than duplicating extraction logic in a second large conditional.
4. Product behavior remains unchanged:
   - same extracted symbol types
   - same names and metadata
   - same partial-parse behavior
5. The sprint does not include executor strategy refactors; those remain backlog for a later slice.
6. **Tests**: add regression coverage proving representative JS/TS fixtures still extract the same symbols after the refactor, including exported declarations and TS-specific declarations.

**Files expected to change:**
- `via/parsers/javascript_parser.py`
- targeted parser regression tests

---

## Deferred Beyond Sprint 18

| Item | Reason Deferred |
|------|-----------------|
| `FunctionBodyAnalyzer` extraction | Can follow once handler seams are stable |
| Executor strategy classes | Separate refactor slice with different risks |
| Query/output behavior changes | This sprint is structure-only |

---

## Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S18-1 | Polymorphic top-level JS parser handlers | 2 | P0 |
| **Total** | | **2pt** | |

---

## Recommended Planning Flow

1. Smith Gate 1 review of the bounded refactor scope
2. Morpheus architecture confirmation for the handler shape
3. Mouse plans a single short cycle:
   - Cycle 1: S18-1 handler extraction + regression tests
