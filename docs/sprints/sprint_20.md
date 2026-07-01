# Sprint 20 Consolidated Documentation

This document consolidates all documentation for Sprint 20.

## Table of Contents

- [SPRINT_20_CLOSEOUT_2026-04-08T21-58.md](#sprint-20-closeout-2026-04-08t21-58md) (originally `agents/cypher.docs/SPRINT_20_CLOSEOUT_2026-04-08T21-58.md`)

- [SPRINT_20_USER_STORIES.md](#sprint-20-user-storiesmd) (originally `agents/cypher.docs/SPRINT_20_USER_STORIES.md`)

- [SPRINT_20_ARCHITECTURE.md](#sprint-20-architecturemd) (originally `agents/morpheus.docs/SPRINT_20_ARCHITECTURE.md`)

- [SPRINT_20_REVIEW_2026-04-08T21-58.md](#sprint-20-review-2026-04-08t21-58md) (originally `agents/morpheus.docs/SPRINT_20_REVIEW_2026-04-08T21-58.md`)

- [SPRINT_20_GATE1_REVIEW.md](#sprint-20-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_20_GATE1_REVIEW.md`)

- [SPRINT_20_GATE2_REVIEW.md](#sprint-20-gate2-reviewmd) (originally `agents/smith.docs/SPRINT_20_GATE2_REVIEW.md`)

- [SPRINT_20_SCRUM_CLOSEOUT_Summary_2026-04-08T21-58.md](#sprint-20-scrum-closeout-summary-2026-04-08t21-58md) (originally `agents/mouse.docs/SPRINT_20_SCRUM_CLOSEOUT_Summary_2026-04-08T21-58.md`)

- [SPRINT_20_TASKS.md](#sprint-20-tasksmd) (originally `agents/mouse.docs/SPRINT_20_TASKS.md`)

- [SPRINT_20_Summary_2026-04-08T21-58.md](#sprint-20-summary-2026-04-08t21-58md) (originally `agents/neo.docs/SPRINT_20_Summary_2026-04-08T21-58.md`)

- [SPRINT_20_UAT_Summary_2026-04-08T21-58.md](#sprint-20-uat-summary-2026-04-08t21-58md) (originally `agents/trin.docs/SPRINT_20_UAT_Summary_2026-04-08T21-58.md`)


---


## SPRINT_20_CLOSEOUT_2026-04-08T21-58.md

**Original Location**: `agents/cypher.docs/SPRINT_20_CLOSEOUT_2026-04-08T21-58.md`


## Sprint 20 Closeout

**Author**: Cypher  
**Date**: 2026-04-08T21:58

### Outcome

Sprint 20 is SHIPPED.

#### Delivered

- S20-1: shared CLI/programmatic query construction seam
- S20-2: documented `ViaQueryBuilder` and `ViaRunner` as the supported Python API

#### Verification

- 50 targeted tests passed locally through `make test`
- Coverage included seam parity, pipeline parser regressions, and builder regressions

#### Product Notes

- Sprint 20 reduces drift between CLI and programmatic query construction without changing query semantics
- Full CLI parser replacement and executor redesign remain explicit backlog items, not part of this ship decision


---


## SPRINT_20_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_20_USER_STORIES.md`


## Sprint 20 — Builder Adoption + Library Usability

**Author**: Cypher (PM)  
**Date**: 2026-04-08  
**Theme**: turn `ViaQueryBuilder` from an internal success into a real library-facing surface by adopting it in the CLI path where appropriate and documenting how to use it from Python code.  
**Sources**: `agents/cypher.docs/SPRINT_19_CLOSEOUT_2026-04-08T21-37.md`, `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21-22.md`  
**Points**: ~5pt  
**Baseline**: Sprint 19 shipped with 30 targeted tests passing locally

---

### Sprint Goal

Sprint 19 proved that `ViaQueryBuilder` works as a real construction API and can replace hand-built `Namespace` wiring in the web layer. Sprint 20 should build on that by making the builder more central and more discoverable without turning the sprint into a parser or executor rewrite.

The product goal is simple: if a developer wants to use via from Python code, the supported path should be obvious and documented, and the CLI/query stack should have less duplicated construction logic.

---

### Stories

#### S20-1: CLI/Programmatic Query Construction Shares the Builder Seam (P0, 3pt)

**As a** maintainer of via’s query stack,  
**I want** the CLI path to reuse the builder seam where it is safe to do so,  
**so that** programmatic and CLI query construction stop drifting apart.

##### Acceptance Criteria

1. Sprint 20 reduces duplicated query-construction logic between CLI parsing output and builder-backed callers.
2. The implementation may introduce an intermediate shared translation seam or builder-backed compilation step, but it must not redesign `PipelineExecutor`.
3. Existing CLI semantics remain unchanged for:
   - plain match queries
   - relationship queries
   - current defaults and limits
   - render/output handling
4. The work stays bounded: this is not a full parser rewrite.
5. **Tests**: regression coverage proves current CLI query behavior still works after the refactor.

**Files expected to change:**
- CLI / parser / adapter seam
- builder integration points
- tests

---

#### S20-2: Document `ViaQueryBuilder` as the Supported Python API (P0, 2pt)

**As a** Python developer embedding via,  
**I want** clear examples for plain and relationship queries using `ViaQueryBuilder`,  
**so that** I can adopt the library surface without reading internal code.

##### Acceptance Criteria

1. User-facing docs describe `ViaQueryBuilder` and `ViaRunner` as the supported Python query-construction path.
2. Docs include at least:
   - one plain match example
   - one relationship example
   - one note clarifying that the builder preserves normal via semantics rather than introducing a new query language
3. If the package exports are part of the intended public surface, docs and exports must agree.
4. **Tests/docs verification**: any doc-backed examples used in tests or smoke coverage remain accurate.

**Files expected to change:**
- README and/or `docs/USER_GUIDE.md`
- top-level package/API docs
- optional doc-backed tests

---

### Deferred Beyond Sprint 20

| Item | Reason Deferred |
|------|-----------------|
| Executor strategy refactor | separate architectural track from builder adoption |
| Full CLI parser replacement by fluent builder | too large for one bounded sprint |
| Query-engine redesign | explicitly out of scope |

---

### Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S20-1 | CLI/programmatic query construction shares the builder seam | 3 | P0 |
| S20-2 | Document `ViaQueryBuilder` as the supported Python API | 2 | P0 |
| **Total** | | **5pt** | |

---

### Recommended Planning Flow

1. Smith Gate 1 review of scope boundaries
2. Morpheus architecture for the shared construction seam
3. Mouse plans 2 short cycles:
   - Cycle 1: shared builder/CLI seam
   - Cycle 2: docs/examples + final regression pass


---


## SPRINT_20_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_20_ARCHITECTURE.md`


## Sprint 20 Architecture — Builder Adoption + Library Usability

**Author**: Morpheus  
**Date**: 2026-04-08  
**Sprint**: Sprint 20 — Builder Adoption + Library Usability  
**Input**: `agents/cypher.docs/SPRINT_20_USER_STORIES.md`, `agents/smith.docs/SPRINT_20_GATE1_REVIEW.md`, `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21-22.md`

### Verdict

Proceed with a shared query-compilation seam and documentation pass. Do not replace the CLI parser or redesign the executor.

### Design Goals

1. Reduce duplicated query-construction logic between CLI and programmatic callers.
2. Keep CLI behavior unchanged.
3. Keep `ViaQueryBuilder` as the public programmatic surface.
4. Make the public Python API discoverable in docs.

### Chosen Shape

#### Shared internal seam

Introduce a small internal query-spec/compiler seam that both sources can use:

- builder path: fluent API -> query spec -> `PipelineStage`
- CLI path: parsed argparse namespace -> query spec or direct compiler input -> `PipelineStage`

The important design point is that the seam is about construction, not execution.

#### Keep current roles intact

- `PipelineParser` still parses argv
- `ViaQueryBuilder` still owns fluent programmatic construction
- `PipelineExecutor` still executes stages

Sprint 20 is about centralizing stage construction rules, not flattening those roles into one object.

### Recommended Module Direction

Prefer one of these two bounded options:

1. Add a small compiler/helper module under `via/api/` or `via/pipeline/` that owns `Namespace`/`PipelineStage` compatibility assembly.
2. Extract the existing stage-compilation logic inside `ViaQueryBuilder` into reusable helpers that the CLI adapter can also call.

Either is acceptable. The key rule is:

No new semantics layer, and no second executor.

### Public API Direction

Sprint 20 should treat these as the supported Python query surface:

- `ViaQueryBuilder`
- `ViaRunner`
- `ViaQuery`

`RelationshipQueryBuilder` is public only insofar as it is part of fluent chaining, but the docs should emphasize `ViaQueryBuilder` as the entrypoint.

### Documentation Scope

Minimum required doc updates:

1. one plain builder example
2. one relationship builder example
3. one note that the builder preserves normal via semantics rather than creating a new query language
4. one import example showing the supported public path

Best locations:

- `README.md`
- `docs/USER_GUIDE.md`
- top-level package docs if needed

### Explicit Non-Goals

1. No full parser replacement with fluent calls.
2. No executor strategy refactor.
3. No change to match defaults, relationship direction, or render semantics.
4. No broad package reorganization beyond the shared seam needed for Sprint 20.

### Risks

1. The shared seam could accidentally become a shadow parser.
2. CLI and builder callers could still diverge if the seam is too shallow.
3. Documentation could drift from exports or real behavior.

### Mitigations

1. Keep the seam narrow: compile known query state into the existing stage shape.
2. Protect current CLI behavior with regression tests.
3. Add at least one doc-backed verification point or focused smoke coverage.

### Implementation Handoff

Mouse should plan this in two short cycles:

1. shared query-construction seam for CLI/builder parity
2. docs/examples plus final regression pass


---


## SPRINT_20_REVIEW_2026-04-08T21-58.md

**Original Location**: `agents/morpheus.docs/SPRINT_20_REVIEW_2026-04-08T21-58.md`


## Sprint 20 Review

**Author**: Morpheus  
**Date**: 2026-04-08T21:58

### Verdict

APPROVED

### Review Notes

- The new `stage_builder` seam is narrow and correctly shared by parser and builder callers
- `PipelineParser`, `ViaQueryBuilder`, and `PipelineExecutor` kept their intended roles
- Sprint 20 improved builder/CLI parity without slipping into executor redesign or full CLI parser replacement

### Architecture Match

Sprint 20 shipped as designed. Builder follow-up can continue from this seam without reopening query-engine architecture.


---


## SPRINT_20_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_20_GATE1_REVIEW.md`


## Sprint 20 Gate 1 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 20 — Builder Adoption + Library Usability  
**Source Reviewed**: `agents/cypher.docs/SPRINT_20_USER_STORIES.md`

### Verdict

**APPROVED**

### Summary

Sprint 20 is pointed at the right follow-up problem: Sprint 19 made the builder real, but not yet fully central or discoverable. The stories are acceptable because they keep the work bounded to adoption and documentation instead of turning it into a sweeping parser redesign.

### Story Verdicts

#### S20-1: CLI/Programmatic Query Construction Shares the Builder Seam
**Verdict**: APPROVED

Why:
- This addresses real maintainability and consistency risk after Sprint 19.
- The story explicitly forbids executor redesign and full parser replacement, which is the right guardrail.
- Keeping semantics frozen preserves user trust in existing CLI behavior.

Notes for Morpheus:
- Favor a shared translation seam over clever bidirectional coupling between parser and builder.
- Keep the implementation explainable; if it becomes hard to describe, it is probably too large for this sprint.

#### S20-2: Document `ViaQueryBuilder` as the Supported Python API
**Verdict**: APPROVED

Why:
- The product value of Sprint 19 is incomplete if users still have to inspect source to discover the API.
- Plain and relationship examples are the right minimum set.

Notes for Morpheus:
- Documentation should describe the builder in terms users already know from via semantics.
- Ensure docs do not imply the builder supports more than the CLI actually does.

### Gate Notes

1. Sprint 20 must preserve current CLI defaults and result behavior exactly.
2. Documentation and exports must agree on what is public.
3. If the shared construction seam starts to look like a parser rewrite, split the work instead of forcing it through this sprint.

### Handoff

Sprint 20 Gate 1 is approved to proceed to architecture.


---


## SPRINT_20_GATE2_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_20_GATE2_REVIEW.md`


## Sprint 20 Gate 2 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 20 — Builder Adoption + Library Usability  
**Source Reviewed**: `agents/morpheus.docs/SPRINT_20_ARCHITECTURE.md`

### Verdict

**APPROVED**

### Summary

The architecture keeps Sprint 20 understandable: it defines a narrow shared construction seam without collapsing parser, builder, and executor into one abstraction. That preserves the existing user mental model while still reducing maintenance drift.

### Review Notes

1. The choice to keep `ViaQueryBuilder` as the documented Python entrypoint is correct.
2. A narrow compilation seam is preferable to a broad parser rewrite.
3. Documentation scope is appropriately concrete and should prevent the builder from remaining a hidden feature.

### Handoff

Sprint 20 Gate 2 is approved to proceed to task planning.


---


## SPRINT_20_SCRUM_CLOSEOUT_Summary_2026-04-08T21-58.md

**Original Location**: `agents/mouse.docs/SPRINT_20_SCRUM_CLOSEOUT_Summary_2026-04-08T21-58.md`


## Sprint 20 Scrum Closeout Summary

**Author**: Mouse  
**Date**: 2026-04-08T21:58

### Status

Sprint 20 is archived.

### Completed Flow

- Cypher planned Sprint 20
- Smith approved Gate 1
- Morpheus produced Sprint 20 architecture
- Smith approved Gate 2
- Mouse opened the board
- Neo implemented the shared seam and Python API docs
- Trin verified parity and regressions
- Morpheus and Cypher marked the sprint shipped
- Mouse archived the board

### Verification Reference

- Targeted make-based suite: 50 passed


---


## SPRINT_20_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_20_TASKS.md`


## Sprint 20 Task Board

**Sprint**: 20  
**Theme**: Builder Adoption + Library Usability  
**Status**: COMPLETE

### Cycles

| Cycle | Stories | Status |
|-------|---------|--------|
| 1 | S20-1 shared CLI/builder construction seam | Complete |
| 2 | S20-2 builder docs/examples + regression pass | Complete |

### Notes

- Gate 1 approved by Smith
- Architecture completed by Morpheus
- Sprint remains bounded: builder adoption + docs, not executor redesign
- Exit criteria: CLI regressions green, builder/library behavior preserved, docs/examples aligned with exports, QA parity pass, lead review pass
- Verification baseline achieved: 50 targeted tests passed through `make test`


---


## SPRINT_20_Summary_2026-04-08T21-58.md

**Original Location**: `agents/neo.docs/SPRINT_20_Summary_2026-04-08T21-58.md`


## Sprint 20 Summary

**Author**: Neo  
**Date**: 2026-04-08T21:58

### Delivered

- Added `via/pipeline/stage_builder.py` as the shared match-stage construction seam for parser and builder callers
- Migrated `via/pipeline/parser.py` to the shared stage-builder helpers instead of hand-building relationship filters and final match-stage shape
- Migrated `via/api/query_builder.py` to the same seam so builder and CLI-backed parsing compile the same match stage structure
- Documented `ViaQueryBuilder` and `ViaRunner` as the supported Python API in `README.md` and `docs/USER_GUIDE.md`
- Added focused parity coverage in `tests/unit/test_sprint20_c1.py`

### Files Changed

- `via/pipeline/stage_builder.py`
- `via/pipeline/parser.py`
- `via/api/query_builder.py`
- `README.md`
- `docs/USER_GUIDE.md`
- `tests/unit/test_sprint20_c1.py`

### Verification

- `make test FILE=tests/unit/test_sprint20_c1.py` → 3 passed
- `make test FILE=tests/unit/test_pipeline_parser.py` → 44 passed
- `make test FILE=tests/unit/test_sprint19_c1.py` → 3 passed
- Targeted baseline for Sprint 20 signoff: 50 passed


---


## SPRINT_20_UAT_Summary_2026-04-08T21-58.md

**Original Location**: `agents/trin.docs/SPRINT_20_UAT_Summary_2026-04-08T21-58.md`


## Sprint 20 UAT Summary

**Author**: Trin  
**Date**: 2026-04-08T21:58

### Verdict

PASS

### Verified

- CLI-side parsing and `ViaQueryBuilder` now share the same match-stage construction seam
- Relationship query construction still preserves existing semantics and validations
- Python API docs/examples align with the exported builder surface

### Regression Coverage

- Sprint 20 seam parity tests
- Existing pipeline parser suite
- Existing Sprint 19 builder suite

### Verification Baseline

- Targeted make-based suite: 50 passed


---
