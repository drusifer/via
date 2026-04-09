# Sprint 19 — ViaQueryBuilder

**Author**: Cypher (PM)  
**Date**: 2026-04-08  
**Theme**: make the via query surface usable from Python code by introducing a fluent builder API that compiles into the existing pipeline model.  
**Sources**: `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21:22.md`  
**Points**: ~5pt  
**Baseline**: Sprint 18 shipped with 96 targeted tests passing locally

---

## Sprint Goal

Today, code-level consumers of via still have to think like the CLI: build argv, build fake `argparse.Namespace` objects, or bypass the pipeline entirely. Sprint 19 should introduce a real Python-facing query builder that preserves via's existing semantics while making programmatic queries readable and safe to compose.

This is not a new query engine. The product value is ergonomic reuse of the existing engine.

---

## Stories

### S19-1: Fluent Programmatic Query Builder (P0, 3pt)

**As a** Python developer embedding via,  
**I want** a fluent query builder API,  
**so that** I can construct via queries in code without fabricating CLI argv or manual `Namespace` objects.

#### Acceptance Criteria

1. Add a new programmatic builder surface rooted at `ViaQueryBuilder`.
2. The builder compiles into the same internal query model already consumed by `PipelineExecutor`.
3. The initial builder supports current match semantics needed by real callers:
   - match syntax (`glob`, `regex`, `sql`)
   - symbol types
   - case-insensitive matching
   - qualified matching
   - `--not` / negated pattern
   - `--lang`
   - `--subtype`
   - `--contains`
   - limit and slice
   - render type
   - relationship queries via positive and negative relationship filters
4. The builder does not invent capabilities the CLI does not already have.
5. A compiled query object is distinct from execution.
6. **Tests**: direct builder compilation coverage and at least one execution-path test showing builder-built queries return normal results.

**Files expected to change:**
- new API module(s)
- pipeline-adapter layer
- tests

---

### S19-2: Replace Web API Namespace Assembly with Builder Compilation (P0, 2pt)

**As a** maintainer of via's web/API surfaces,  
**I want** the web query layer to use the same builder API as other programmatic callers,  
**so that** we stop duplicating query construction logic in one-off translation code.

#### Acceptance Criteria

1. `via/web/api/query.py` stops hand-building `argparse.Namespace` for match stages.
2. The web API uses `ViaQueryBuilder` (and related compiled-query objects) to construct the executable query.
3. Existing web query behavior stays unchanged for:
   - plain match queries
   - relationship queries
   - output format handling
4. The web layer may still perform response shaping, but not bespoke match-stage construction.
5. **Tests**: existing web query unit coverage remains green, with new coverage where needed for builder-backed translation.

**Files expected to change:**
- `via/web/api/query.py`
- web query tests

---

## Deferred Beyond Sprint 19

| Item | Reason Deferred |
|------|-----------------|
| CLI parser migration to the builder | separate risk profile; CLI already works |
| Query-engine redesign | out of scope; reuse current executor |
| ORM-like repository API over `DatabaseStore` | different product problem |

---

## Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S19-1 | Fluent programmatic query builder | 3 | P0 |
| S19-2 | Web API builder adoption | 2 | P0 |
| **Total** | | **5pt** | |

---

## Recommended Planning Flow

1. Smith Gate 1 review of the builder scope
2. Morpheus converts the existing builder note into sprint architecture
3. Mouse plans 2 short cycles:
   - Cycle 1: builder API + builder execution tests
   - Cycle 2: web API migration + regression pass
