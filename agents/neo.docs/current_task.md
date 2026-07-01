# Neo Current Task

**Task**: Sprint 26 Cycle 4 — Class-Based Relationship Type Hierarchy Design
**Status**: IN PROGRESS (50% complete)
**Updated**: 2026-06-21

## Completed
- [x] Resumed context and reviewed user request regarding "blast radius" query.
- [x] Clarified the design requirements for upstream (dependent) and downstream (dependency) relationship matching.
- [x] Created design proposal artifact `relationship_hierarchy_design.md` detailing the relationship hierarchy categories (Any, UpstreamRef, DownstreamRef, ReaderRef, WriterRef).
- [x] Wrote formal design document at `docs/DESIGN_RELATIONSHIP_HIERARCHY.md` for team review.

## In Progress
- [ ] Implement the class-based hierarchy in `via/core/relationship_types.py`.
- [ ] Adapt `PipelineParser` and `DatabaseStore` to parse and compile hierarchical queries.
