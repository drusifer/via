# Sprint 20 Architecture — Builder Adoption + Library Usability

**Author**: Morpheus  
**Date**: 2026-04-08  
**Sprint**: Sprint 20 — Builder Adoption + Library Usability  
**Input**: `agents/cypher.docs/SPRINT_20_USER_STORIES.md`, `agents/smith.docs/SPRINT_20_GATE1_REVIEW.md`, `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21:22.md`

## Verdict

Proceed with a shared query-compilation seam and documentation pass. Do not replace the CLI parser or redesign the executor.

## Design Goals

1. Reduce duplicated query-construction logic between CLI and programmatic callers.
2. Keep CLI behavior unchanged.
3. Keep `ViaQueryBuilder` as the public programmatic surface.
4. Make the public Python API discoverable in docs.

## Chosen Shape

### Shared internal seam

Introduce a small internal query-spec/compiler seam that both sources can use:

- builder path: fluent API -> query spec -> `PipelineStage`
- CLI path: parsed argparse namespace -> query spec or direct compiler input -> `PipelineStage`

The important design point is that the seam is about construction, not execution.

### Keep current roles intact

- `PipelineParser` still parses argv
- `ViaQueryBuilder` still owns fluent programmatic construction
- `PipelineExecutor` still executes stages

Sprint 20 is about centralizing stage construction rules, not flattening those roles into one object.

## Recommended Module Direction

Prefer one of these two bounded options:

1. Add a small compiler/helper module under `via/api/` or `via/pipeline/` that owns `Namespace`/`PipelineStage` compatibility assembly.
2. Extract the existing stage-compilation logic inside `ViaQueryBuilder` into reusable helpers that the CLI adapter can also call.

Either is acceptable. The key rule is:

No new semantics layer, and no second executor.

## Public API Direction

Sprint 20 should treat these as the supported Python query surface:

- `ViaQueryBuilder`
- `ViaRunner`
- `ViaQuery`

`RelationshipQueryBuilder` is public only insofar as it is part of fluent chaining, but the docs should emphasize `ViaQueryBuilder` as the entrypoint.

## Documentation Scope

Minimum required doc updates:

1. one plain builder example
2. one relationship builder example
3. one note that the builder preserves normal via semantics rather than creating a new query language
4. one import example showing the supported public path

Best locations:

- `README.md`
- `docs/USER_GUIDE.md`
- top-level package docs if needed

## Explicit Non-Goals

1. No full parser replacement with fluent calls.
2. No executor strategy refactor.
3. No change to match defaults, relationship direction, or render semantics.
4. No broad package reorganization beyond the shared seam needed for Sprint 20.

## Risks

1. The shared seam could accidentally become a shadow parser.
2. CLI and builder callers could still diverge if the seam is too shallow.
3. Documentation could drift from exports or real behavior.

## Mitigations

1. Keep the seam narrow: compile known query state into the existing stage shape.
2. Protect current CLI behavior with regression tests.
3. Add at least one doc-backed verification point or focused smoke coverage.

## Implementation Handoff

Mouse should plan this in two short cycles:

1. shared query-construction seam for CLI/builder parity
2. docs/examples plus final regression pass
