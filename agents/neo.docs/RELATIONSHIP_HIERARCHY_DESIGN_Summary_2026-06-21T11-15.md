# Task Summary: Class-Based Relationship Hierarchy Design

**Task Name**: RELATIONSHIP_HIERARCHY_DESIGN
**Date**: 2026-06-21T11:15
**Persona**: Neo (Software Engineer)

## Accomplished
1. **Design Document**: Created [DESIGN_RELATIONSHIP_HIERARCHY.md](file:///home/drusifer/Projects/via/docs/DESIGN_RELATIONSHIP_HIERARCHY.md) describing the OOP-based class hierarchy design for relationship types in VIA.
2. **Artifact Definition**: Documented relationship categories (`Any`, `UpstreamRef`, `DownstreamRef`, `ReaderRef`, `WriterRef`) in `relationship_hierarchy_design.md` with visual Mermaid diagrams.
3. **SQL Strategy**: Formulated SQL `UNION` query compilation pattern for mixed-direction traversals (such as `blast` or `any`) to run in `DatabaseStore.query_relationships`.
4. **Canned Integration**: Outlined how `.via/canned/blast.json` will be dynamically configured using `any-ref` without code changes.

## Next Steps
1. Review design document with Morpheus (Tech Lead) and Smith (PM/User).
2. Code implementation: subclass definitions in `relationship_types.py`, parser updates in `parser.py`, and SQL compile updates in `store.py`.
