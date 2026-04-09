# Sprint 20 — Builder Adoption + Library Usability

**Author**: Cypher (PM)  
**Date**: 2026-04-08  
**Theme**: turn `ViaQueryBuilder` from an internal success into a real library-facing surface by adopting it in the CLI path where appropriate and documenting how to use it from Python code.  
**Sources**: `agents/cypher.docs/SPRINT_19_CLOSEOUT_2026-04-08T21:37.md`, `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21:22.md`  
**Points**: ~5pt  
**Baseline**: Sprint 19 shipped with 30 targeted tests passing locally

---

## Sprint Goal

Sprint 19 proved that `ViaQueryBuilder` works as a real construction API and can replace hand-built `Namespace` wiring in the web layer. Sprint 20 should build on that by making the builder more central and more discoverable without turning the sprint into a parser or executor rewrite.

The product goal is simple: if a developer wants to use via from Python code, the supported path should be obvious and documented, and the CLI/query stack should have less duplicated construction logic.

---

## Stories

### S20-1: CLI/Programmatic Query Construction Shares the Builder Seam (P0, 3pt)

**As a** maintainer of via’s query stack,  
**I want** the CLI path to reuse the builder seam where it is safe to do so,  
**so that** programmatic and CLI query construction stop drifting apart.

#### Acceptance Criteria

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

### S20-2: Document `ViaQueryBuilder` as the Supported Python API (P0, 2pt)

**As a** Python developer embedding via,  
**I want** clear examples for plain and relationship queries using `ViaQueryBuilder`,  
**so that** I can adopt the library surface without reading internal code.

#### Acceptance Criteria

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

## Deferred Beyond Sprint 20

| Item | Reason Deferred |
|------|-----------------|
| Executor strategy refactor | separate architectural track from builder adoption |
| Full CLI parser replacement by fluent builder | too large for one bounded sprint |
| Query-engine redesign | explicitly out of scope |

---

## Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S20-1 | CLI/programmatic query construction shares the builder seam | 3 | P0 |
| S20-2 | Document `ViaQueryBuilder` as the supported Python API | 2 | P0 |
| **Total** | | **5pt** | |

---

## Recommended Planning Flow

1. Smith Gate 1 review of scope boundaries
2. Morpheus architecture for the shared construction seam
3. Mouse plans 2 short cycles:
   - Cycle 1: shared builder/CLI seam
   - Cycle 2: docs/examples + final regression pass
