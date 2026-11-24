# ViaQueryBuilder Architecture

**Author**: Morpheus  
**Date**: 2026-04-08T21:22  
**Trigger**: Bob chat request: make the via API easier to use in code with a fluent `ViaQueryBuilder`

## Problem

The current code-level query surface is awkward because it is still shaped around CLI parsing:

- CLI callers go through `PipelineParser.parse(argv)`
- Web callers manually assemble `argparse.Namespace` in `via/web/api/query.py`
- Internal execution expects `PipelineStage` plus argparse-flavored fields

That means programmatic callers either:

1. construct fake argv, or
2. construct fake `Namespace` objects, or
3. bypass the pipeline and couple directly to `DatabaseStore`

None of those is a clean application-facing API.

## Decision

Add a fluent query-construction layer:

- primary entrypoint: `ViaQueryBuilder`
- keep `PipelineExecutor` as the execution engine
- do not replace the CLI parser
- do not create a second query engine

The builder should compile into the same internal `PipelineStage` model already used by the CLI and web API.

## Goals

1. Make code-level query construction readable and discoverable.
2. Reuse the existing pipeline executor rather than inventing parallel logic.
3. Eliminate hand-written `Namespace` assembly outside the parser layer.
4. Preserve support for current query semantics:
   - match syntax
   - symbol types
   - `--via` / `--sans`
   - `--not`
   - `--lang`
   - `--subtype`
   - `--contains`
   - limits and slices
   - render type

## Explicit Non-Goals

1. No attempt to redesign the database query model in the same slice.
2. No attempt to unify CLI parsing and builder construction immediately.
3. No magic ORM-style API that hides via's actual query semantics.
4. No mixed mutable/executable object that both builds and runs implicitly.

## Proposed Shape

### Public API

Create a new module:

- `via/api/query_builder.py`

Primary classes:

- `ViaQueryBuilder`
- `RelationshipQueryBuilder`
- `ViaQuery`
- `ViaRunner`

### Fluent Example

```python
from via.api.query_builder import ViaQueryBuilder, ViaRunner

query = (
    ViaQueryBuilder()
    .glob("*Controller")
    .classes()
    .contains("rate_limit")
    .limit(20)
    .build()
)

records = ViaRunner(db_store).run(query)
```

Relationship example:

```python
query = (
    ViaQueryBuilder()
    .glob("Base")
    .classes()
    .via("inherits-from")
        .glob("*")
        .classes()
    .done()
    .build()
)
```

### Separation of Responsibilities

#### `ViaQueryBuilder`

Owns the fluent write API for one match stage and optional relationship chaining.

Methods should be semantic, not flag-shaped, but one-to-one with current capabilities:

- `glob(pattern)`
- `regex(pattern)`
- `sql(pattern)`
- `exact(pattern)` if Morpheus later wants first-class exact matching
- `types(*symbol_types)`
- convenience aliases:
  - `classes()`
  - `functions()`
  - `methods()`
  - `files()`
  - `headers()`
  - `strings()`
  - `links()`
- `case_insensitive()`
- `qualified()`
- `negate()`
- `language(name)`
- `subtype(name)`
- `contains(pattern)`
- `limit(n)`
- `slice(start, end=None)`
- `render(render_type)`
- `via(relationship_type)`
- `sans(relationship_type)`
- `build()`

#### `RelationshipQueryBuilder`

Represents the right-hand side of a relationship query. It should collect the object-side pattern/type constraints and then return control to the parent builder via `.done()`.

This is cleaner than flattening relationship state into one mutable bag with order-sensitive method calls.

#### `ViaQuery`

An immutable compiled query object.

It should contain:

- `stages: list[PipelineStage]`
- optional convenience methods:
  - `to_stages()`
  - `to_cli_args()` for debugging/transparency only

#### `ViaRunner`

Thin execution adapter around `PipelineExecutor`.

```python
runner = ViaRunner(db_store)
records = runner.run(query)
```

This keeps the builder from needing a database handle and prevents hidden side effects during construction.

## Internal Compilation Strategy

The builder should compile directly to the current pipeline representation:

1. collect builder state in typed dataclasses, not `Namespace`
2. translate those dataclasses into `PipelineStage`
3. only at the final compatibility seam, emit the `Namespace` shape expected by `PipelineExecutor`

That gives us an incremental migration path:

- phase 1: builder outputs `PipelineStage(Namespace(...))`
- phase 2: introduce typed stage args if we later refactor executor/parser internals

## Key Architectural Rule

The builder is a new construction API, not a new semantics layer.

If a CLI query cannot express something, `ViaQueryBuilder` should not invent it.

## Best Integration Targets

### First adopters

1. `via/web/api/query.py`
   Replace manual `Namespace` construction with builder compilation.
2. MCP server internals where code wants structured non-argv query assembly.
3. Future library-facing programmatic integrations.

### Leave unchanged initially

1. `PipelineParser`
2. CLI argv parsing in `via/__main__.py`
3. `PipelineExecutor` query semantics

## Risks

1. Fluent APIs can become order-sensitive and ambiguous if not bounded carefully.
2. Convenience methods can drift from actual symbol/relationship names.
3. If `ViaQueryBuilder` is too magical, users will not understand how it maps to CLI behavior.

## Mitigations

1. Keep method names close to existing semantics.
2. Provide `to_cli_args()` for transparency and debugging.
3. Keep relationship sub-builder explicit with `.done()`.
4. Reuse enum/string constants from existing core types where possible.

## Recommended Implementation Slice

Deliver this in short increments:

1. `ViaQueryBuilder` for plain match queries only
2. add relationship chaining with `via()` / `sans()`
3. migrate `via/web/api/query.py` to the builder
4. optionally expose the API in package docs and `__init__`

## Handoff

Cypher should package this as a bounded sprint rather than mixing it into unrelated executor refactors.
