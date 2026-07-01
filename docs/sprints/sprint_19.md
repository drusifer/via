# Sprint 19 Consolidated Documentation

This document consolidates all documentation for Sprint 19.

## Table of Contents

- [SPRINT_19_CLOSEOUT_2026-04-08T21-37.md](#sprint-19-closeout-2026-04-08t21-37md) (originally `agents/cypher.docs/SPRINT_19_CLOSEOUT_2026-04-08T21-37.md`)

- [SPRINT_19_USER_STORIES.md](#sprint-19-user-storiesmd) (originally `agents/cypher.docs/SPRINT_19_USER_STORIES.md`)

- [SPRINT_19_ARCHITECTURE.md](#sprint-19-architecturemd) (originally `agents/morpheus.docs/SPRINT_19_ARCHITECTURE.md`)

- [SPRINT_19_REVIEW_2026-04-08T21-37.md](#sprint-19-review-2026-04-08t21-37md) (originally `agents/morpheus.docs/SPRINT_19_REVIEW_2026-04-08T21-37.md`)

- [SPRINT_19_GATE1_REVIEW.md](#sprint-19-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_19_GATE1_REVIEW.md`)

- [SPRINT_19_GATE2_REVIEW.md](#sprint-19-gate2-reviewmd) (originally `agents/smith.docs/SPRINT_19_GATE2_REVIEW.md`)

- [SPRINT_19_SCRUM_CLOSEOUT_Summary_2026-04-08T21-37.md](#sprint-19-scrum-closeout-summary-2026-04-08t21-37md) (originally `agents/mouse.docs/SPRINT_19_SCRUM_CLOSEOUT_Summary_2026-04-08T21-37.md`)

- [SPRINT_19_TASKS.md](#sprint-19-tasksmd) (originally `agents/mouse.docs/SPRINT_19_TASKS.md`)

- [SPRINT_19_Summary_2026-04-08T21-37.md](#sprint-19-summary-2026-04-08t21-37md) (originally `agents/neo.docs/SPRINT_19_Summary_2026-04-08T21-37.md`)

- [SPRINT_19_UAT_Summary_2026-04-08T21-37.md](#sprint-19-uat-summary-2026-04-08t21-37md) (originally `agents/trin.docs/SPRINT_19_UAT_Summary_2026-04-08T21-37.md`)


---


## SPRINT_19_CLOSEOUT_2026-04-08T21-37.md

**Original Location**: `agents/cypher.docs/SPRINT_19_CLOSEOUT_2026-04-08T21-37.md`


## Sprint 19 Closeout

**Author**: Cypher  
**Date**: 2026-04-08T21:37

### Outcome

Sprint 19 is SHIPPED.

#### Delivered

- S19-1: fluent programmatic `ViaQueryBuilder`
- S19-2: web API adoption of builder-backed query construction

#### Verification

- 30 targeted tests passed locally through `make test`
- Coverage included direct builder tests plus plain and relationship web query regressions

#### Product Notes

- Sprint 19 makes via materially easier to use from Python code without changing the underlying query model
- CLI parser migration remains backlog material, not part of this ship decision


---


## SPRINT_19_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_19_USER_STORIES.md`


## Sprint 19 — ViaQueryBuilder

**Author**: Cypher (PM)  
**Date**: 2026-04-08  
**Theme**: make the via query surface usable from Python code by introducing a fluent builder API that compiles into the existing pipeline model.  
**Sources**: `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21-22.md`  
**Points**: ~5pt  
**Baseline**: Sprint 18 shipped with 96 targeted tests passing locally

---

### Sprint Goal

Today, code-level consumers of via still have to think like the CLI: build argv, build fake `argparse.Namespace` objects, or bypass the pipeline entirely. Sprint 19 should introduce a real Python-facing query builder that preserves via's existing semantics while making programmatic queries readable and safe to compose.

This is not a new query engine. The product value is ergonomic reuse of the existing engine.

---

### Stories

#### S19-1: Fluent Programmatic Query Builder (P0, 3pt)

**As a** Python developer embedding via,  
**I want** a fluent query builder API,  
**so that** I can construct via queries in code without fabricating CLI argv or manual `Namespace` objects.

##### Acceptance Criteria

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

#### S19-2: Replace Web API Namespace Assembly with Builder Compilation (P0, 2pt)

**As a** maintainer of via's web/API surfaces,  
**I want** the web query layer to use the same builder API as other programmatic callers,  
**so that** we stop duplicating query construction logic in one-off translation code.

##### Acceptance Criteria

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

### Deferred Beyond Sprint 19

| Item | Reason Deferred |
|------|-----------------|
| CLI parser migration to the builder | separate risk profile; CLI already works |
| Query-engine redesign | out of scope; reuse current executor |
| ORM-like repository API over `DatabaseStore` | different product problem |

---

### Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S19-1 | Fluent programmatic query builder | 3 | P0 |
| S19-2 | Web API builder adoption | 2 | P0 |
| **Total** | | **5pt** | |

---

### Recommended Planning Flow

1. Smith Gate 1 review of the builder scope
2. Morpheus converts the existing builder note into sprint architecture
3. Mouse plans 2 short cycles:
   - Cycle 1: builder API + builder execution tests
   - Cycle 2: web API migration + regression pass


---


## SPRINT_19_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_19_ARCHITECTURE.md`


## Sprint 19 Architecture — ViaQueryBuilder

**Author**: Morpheus  
**Date**: 2026-04-08  
**Sprint**: Sprint 19 — ViaQueryBuilder  
**Input**: `agents/cypher.docs/SPRINT_19_USER_STORIES.md`, `agents/smith.docs/SPRINT_19_GATE1_REVIEW.md`, `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21-22.md`

### Verdict

Proceed with a new API layer that compiles into the existing `PipelineStage` model, then prove it by migrating `via/web/api/query.py`.

### Design Goals

1. Add a readable Python-facing query-construction API.
2. Preserve all current query semantics.
3. Avoid inventing a second execution path.
4. Remove web-layer `Namespace` fabrication.

### Chosen Shape

#### New package

Create:

- `via/api/__init__.py`
- `via/api/query_builder.py`

#### Public classes

- `ViaQueryBuilder`
- `RelationshipQueryBuilder`
- `ViaQuery`
- `ViaRunner`

#### Internal rule

The builder collects typed state, then compiles once at the compatibility seam into `PipelineStage(StageType.MATCH, Namespace(...))`.

That keeps Sprint 19 additive and avoids rewriting `PipelineExecutor`.

### Builder Surface

#### Plain match methods

- `glob(pattern)`
- `regex(pattern)`
- `sql(pattern)`
- `types(*symbol_types)`
- `classes()`
- `functions()`
- `methods()`
- `files()`
- `filenames()`
- `imports()`
- `globals()`
- `headers()`
- `strings()`
- `links()`
- `case_insensitive(enabled=True)`
- `qualified(enabled=True)`
- `negate(enabled=True)`
- `language(name)`
- `subtype(name)`
- `contains(pattern)`
- `limit(n)`
- `slice(start, end=None)`
- `render(render_type)`

#### Relationship methods

- `via(relationship_type)`
- `sans(relationship_type)`

These should return a `RelationshipQueryBuilder`, which sets the object-side query and returns to the parent with `.done()`.

### Execution Model

`ViaRunner` is a thin wrapper over `PipelineExecutor`.

```python
records = ViaRunner(db_store).run(builder.build())
```

No hidden execution during build.

### Web API Adoption

`via/web/api/query.py` should:

1. translate JSON body fields into builder calls
2. build a `ViaQuery`
3. execute it with `ViaRunner`
4. keep existing HTTP response shaping logic

The web layer remains an adapter, but not a place that knows `Namespace` field wiring.

### Explicit Non-Goals

1. Do not migrate CLI parsing to the builder in Sprint 19.
2. Do not redesign `PipelineExecutor`.
3. Do not change response payload formats.
4. Do not introduce validation rules beyond existing via semantics.

### Risks

1. Relationship builder chaining becoming order-sensitive or unclear.
2. Builder defaults drifting from current web defaults.
3. Public API leaking raw argparse concepts.

### Mitigations

1. Keep `RelationshipQueryBuilder` narrow and explicit.
2. Reuse existing enum/string values for symbol types, relationships, and render types.
3. Prove parity through existing web query tests plus direct builder tests.

### Implementation Handoff

Mouse should plan this in two short cycles:

1. builder core + execution + builder tests
2. web API migration + regression pass


---


## SPRINT_19_REVIEW_2026-04-08T21-37.md

**Original Location**: `agents/morpheus.docs/SPRINT_19_REVIEW_2026-04-08T21-37.md`


## Sprint 19 Review

**Author**: Morpheus  
**Date**: 2026-04-08T21:37

### Verdict

APPROVED

### Review Notes

- The builder is additive and compiles into the existing `PipelineStage` compatibility seam
- `PipelineExecutor` remains the single execution engine
- The web API is now a real adopter of the builder rather than a second hand-wired query-construction path

### Architecture Match

Sprint 19 shipped as designed. CLI parser migration remains correctly deferred.


---


## SPRINT_19_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_19_GATE1_REVIEW.md`


## Sprint 19 Gate 1 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 19 — ViaQueryBuilder  
**Source Reviewed**: `agents/cypher.docs/SPRINT_19_USER_STORIES.md`

### Verdict

**APPROVED**

### Summary

Sprint 19 targets a real usability problem for programmatic consumers: via is currently easy to use from the CLI but awkward to use in code. The stories keep the mental model grounded by requiring the builder to preserve existing query semantics instead of inventing a new abstraction language.

### Story Verdicts

#### S19-1: Fluent Programmatic Query Builder
**Verdict**: APPROVED

Why:
- It addresses a genuine usability issue for Python callers.
- The story correctly distinguishes query construction from query execution.
- Requiring parity with existing CLI semantics prevents a confusing split-brain API.

Notes for Morpheus:
- Transparency matters: the builder should read like via, not like an unrelated ORM.
- Prefer method names users can map back to current via concepts quickly.

#### S19-2: Replace Web API Namespace Assembly with Builder Compilation
**Verdict**: APPROVED

Why:
- This is the right proving ground for the new API because the current web layer is already acting as a programmatic caller.
- Removing hand-built `Namespace` objects reduces one of the sharpest maintenance edges.

Notes for Morpheus:
- Preserve existing web behavior exactly; users should not experience a semantic change because an internal adapter changed.
- Keep response shaping separate from query construction so the web layer still reads clearly.

### Gate Notes

1. The builder must preserve via’s existing mental model rather than hiding it behind generic data-access vocabulary.
2. This sprint should not quietly change relationship semantics, output-format behavior, or default limits.
3. Docs and examples should eventually show at least one plain-match and one relationship builder example, even if that doc work lands after the code.

### Handoff

Sprint 19 Gate 1 is approved to proceed to architecture.


---


## SPRINT_19_GATE2_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_19_GATE2_REVIEW.md`


## Sprint 19 Gate 2 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 19 — ViaQueryBuilder  
**Source Reviewed**: `agents/morpheus.docs/SPRINT_19_ARCHITECTURE.md`

### Verdict

**APPROVED**

### Summary

The architecture keeps the builder understandable by tying it directly to current via semantics and by preserving `PipelineExecutor` as the only execution engine. Using the web API as the first adopter is the right proof because it exercises real programmatic construction without changing the public CLI.

### Review Notes

1. Keeping response shaping in the web layer while moving only query construction to the builder is the correct separation.
2. The explicit non-goals are important; this sprint should not turn into a parser/executor rewrite.
3. Relationship builder chaining is acceptable as long as it stays explicit and bounded.

### Handoff

Sprint 19 Gate 2 is approved to proceed to task planning.


---


## SPRINT_19_SCRUM_CLOSEOUT_Summary_2026-04-08T21-37.md

**Original Location**: `agents/mouse.docs/SPRINT_19_SCRUM_CLOSEOUT_Summary_2026-04-08T21-37.md`


## Sprint 19 Scrum Closeout Summary

**Author**: Mouse  
**Date**: 2026-04-08T21:37

### Status

Sprint 19 is archived.

### Completed Flow

- Cypher planned Sprint 19
- Smith approved Gate 1
- Morpheus produced Sprint 19 architecture
- Smith approved Gate 2
- Mouse opened the board
- Neo implemented the builder layer and web adoption
- Trin verified targeted parity and regressions
- Morpheus and Cypher marked the sprint shipped
- Mouse archived the board

### Verification Reference

- Targeted make-based suite: 30 passed


---


## SPRINT_19_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_19_TASKS.md`


## Sprint 19 Task Board

**Sprint**: 19  
**Theme**: ViaQueryBuilder  
**Status**: COMPLETE

### Cycles

| Cycle | Stories | Status |
|-------|---------|--------|
| 1 | S19-1 builder core + execution tests | ✅ Done |
| 2 | S19-2 web API migration + regression pass | ✅ Done |

### Notes

- Gate 1 approved by Smith
- Architecture completed by Morpheus
- Sprint remains additive: builder layer plus web adoption, no executor redesign
- Exit criteria met: builder tests green, web query regressions green, QA parity pass, lead review pass


---


## SPRINT_19_Summary_2026-04-08T21-37.md

**Original Location**: `agents/neo.docs/SPRINT_19_Summary_2026-04-08T21-37.md`


## Sprint 19 Summary

**Author**: Neo  
**Date**: 2026-04-08T21:37

### Delivered

- Added `via/api/query_builder.py` with `ViaQueryBuilder`, `RelationshipQueryBuilder`, `ViaQuery`, and `ViaRunner`
- Migrated `via/web/api/query.py` from manual `Namespace` assembly to builder-backed query compilation
- Exported builder API from `via/api/__init__.py` and top-level `via/__init__.py`
- Added focused builder coverage in `tests/unit/test_sprint19_c1.py`

### Files Changed

- `via/api/__init__.py`
- `via/api/query_builder.py`
- `via/web/api/query.py`
- `via/__init__.py`
- `tests/unit/test_sprint19_c1.py`

### Verification

- `make test FILE=tests/unit/test_sprint19_c1.py` → 3 passed
- `make test FILE=tests/unit/test_web_query.py` → 15 passed
- `make test FILE=tests/unit/test_web_query_relationship.py` → 12 passed
- Targeted baseline for Sprint 19 signoff: 30 passed


---


## SPRINT_19_UAT_Summary_2026-04-08T21-37.md

**Original Location**: `agents/trin.docs/SPRINT_19_UAT_Summary_2026-04-08T21-37.md`


## Sprint 19 UAT Summary

**Author**: Trin  
**Date**: 2026-04-08T21:37

### Verdict

PASS

### Verified

- `ViaQueryBuilder` builds executable plain-match and relationship queries
- `ViaRunner` executes compiled queries through the existing pipeline path
- Web query translation now uses the builder while preserving plain and relationship behavior

### Regression Coverage

- Sprint 19 builder tests
- Existing web query suite
- Existing web relationship query suite

### Verification Baseline

- Targeted make-based suite: 30 passed


---
