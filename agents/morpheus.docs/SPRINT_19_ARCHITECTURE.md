# Sprint 19 Architecture — ViaQueryBuilder

**Author**: Morpheus  
**Date**: 2026-04-08  
**Sprint**: Sprint 19 — ViaQueryBuilder  
**Input**: `agents/cypher.docs/SPRINT_19_USER_STORIES.md`, `agents/smith.docs/SPRINT_19_GATE1_REVIEW.md`, `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21:22.md`

## Verdict

Proceed with a new API layer that compiles into the existing `PipelineStage` model, then prove it by migrating `via/web/api/query.py`.

## Design Goals

1. Add a readable Python-facing query-construction API.
2. Preserve all current query semantics.
3. Avoid inventing a second execution path.
4. Remove web-layer `Namespace` fabrication.

## Chosen Shape

### New package

Create:

- `via/api/__init__.py`
- `via/api/query_builder.py`

### Public classes

- `ViaQueryBuilder`
- `RelationshipQueryBuilder`
- `ViaQuery`
- `ViaRunner`

### Internal rule

The builder collects typed state, then compiles once at the compatibility seam into `PipelineStage(StageType.MATCH, Namespace(...))`.

That keeps Sprint 19 additive and avoids rewriting `PipelineExecutor`.

## Builder Surface

### Plain match methods

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

### Relationship methods

- `via(relationship_type)`
- `sans(relationship_type)`

These should return a `RelationshipQueryBuilder`, which sets the object-side query and returns to the parent with `.done()`.

## Execution Model

`ViaRunner` is a thin wrapper over `PipelineExecutor`.

```python
records = ViaRunner(db_store).run(builder.build())
```

No hidden execution during build.

## Web API Adoption

`via/web/api/query.py` should:

1. translate JSON body fields into builder calls
2. build a `ViaQuery`
3. execute it with `ViaRunner`
4. keep existing HTTP response shaping logic

The web layer remains an adapter, but not a place that knows `Namespace` field wiring.

## Explicit Non-Goals

1. Do not migrate CLI parsing to the builder in Sprint 19.
2. Do not redesign `PipelineExecutor`.
3. Do not change response payload formats.
4. Do not introduce validation rules beyond existing via semantics.

## Risks

1. Relationship builder chaining becoming order-sensitive or unclear.
2. Builder defaults drifting from current web defaults.
3. Public API leaking raw argparse concepts.

## Mitigations

1. Keep `RelationshipQueryBuilder` narrow and explicit.
2. Reuse existing enum/string values for symbol types, relationships, and render types.
3. Prove parity through existing web query tests plus direct builder tests.

## Implementation Handoff

Mouse should plan this in two short cycles:

1. builder core + execution + builder tests
2. web API migration + regression pass
