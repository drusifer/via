# Polymorphic Refactor Plan

**Author**: Morpheus  
**Date**: 2026-04-08T20:52

## Trigger

Bob guidance in `agents/CHAT.md`:

- prefer polymorphic classes over large `if` / `else` blocks
- keep it DRY
- push branching into type-specific behavior only where the abstraction is stable

## Executive Read

Do **not** do a blanket anti-`if` rewrite.

The repo already has good polymorphic seams in:

- `MatchRecord` subclasses
- `MatchRecordFactory`
- renderer classes

The remaining refactor value is in places where branching is both:

1. repeated across multiple methods, and
2. actually modeling stable type-specific behavior rather than syntax-tree walking or orchestration

## Good Targets

### P1: `via/parsers/javascript_parser.py`

#### Why

- Multiple long `if/elif` chains dispatch on node type across several passes:
  - symbol extraction
  - call extraction
  - HTTP-call extraction
  - string-constant extraction
- The duplication is structural, not incidental.

#### Refactor Direction

Introduce small extractor objects or a registry-based visitor layer:

- `TopLevelNodeExtractor`
- handler per node family:
  - import
  - function
  - class
  - declaration/export wrapper

Goal: one traversal contract, multiple behaviors plugged into handlers.

#### Constraint

Do not over-abstract raw tree-sitter mechanics. The aim is to remove repeated node-type branching, not hide the AST behind a leaky framework.

---

### P1: `via/pipeline/executor.py`

#### Why

- `_execute_match_stage()` is accumulating multiple policy branches:
  - plain match
  - multi-type match
  - relationship query
  - negative relationship query
  - post-match `--contains`
  - line slicing / render follow-up elsewhere
- This is turning into command-policy orchestration in one class.

#### Refactor Direction

Split stage execution strategy by query mode:

- `PlainMatchStrategy`
- `RelationshipMatchStrategy`
- `NegativeRelationshipStrategy`
- `PostMatchFilter` objects for body filtering / line slicing

Goal: executor becomes orchestration over strategy objects instead of owning every branch.

#### Constraint

Keep the current pipeline public behavior exactly stable. This is an internal decomposition refactor, not a query-language redesign.

---

### P2: `via/renderers/factory.py`

#### Why

- The current `if render_type == ...` chain is small and understandable, so it is not urgent.
- But it is a clean candidate for a registry lookup if more renderer types keep arriving.

#### Refactor Direction

Replace the branch ladder with a registry map:

- `RenderType -> renderer builder`

This is only worth doing if the renderer matrix keeps growing.

#### Constraint

This is lower priority because the current code is readable and already centralized.

---

## Bad Targets

### `via/core/match_record.py`

Leave it alone. This is already the right kind of polymorphism.

### `via/services/indexing.py`

Some duplication is worth reducing, but most of the current branches are procedural storage steps, not type hierarchies. Prefer helper extraction before introducing more classes here.

### Every AST `if child.type == ...`

Some node-type branching is the nature of parser code. Converting all of it to classes would be ceremony, not design improvement.

## Proposed Sequence

1. Refactor `javascript_parser.py` first
   - highest duplication
   - most obvious stable dispatch seams
2. Refactor `pipeline/executor.py` second
   - strategy extraction around query modes
3. Revisit `renderers/factory.py` only if more render types are planned

## Definition of Done

- Fewer repeated node-type branch ladders in JS parser
- Fewer mode-switch branches in executor
- No user-visible query behavior changes
- Existing Sprint 15-17 regression suites remain green

## Recommendation

Treat this as a technical-debt planning item for the next sprint or a bounded refactor cycle, not an opportunistic in-flight rewrite.
