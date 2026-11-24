# Polymorphic Refactor — Proposed Classes

**Author**: Morpheus  
**Date**: 2026-04-08T20:58

## Purpose

This is the class-level follow-up to `POLYMORPHIC_REFACTOR_PLAN_2026-04-08T20-52.md`.

The goal is to name the concrete abstractions we would introduce if the team prioritizes the polymorphic refactor, so the next sprint can scope implementation without reopening the architecture from scratch.

## Scope

Two modules are worth class extraction:

1. `via/parsers/javascript_parser.py`
2. `via/pipeline/executor.py`

Do not apply this plan outside those seams until the first pass proves the abstraction is paying for itself.

---

## 1. JavaScript Parser Class Plan

### Current Problem

`javascript_parser.py` repeats top-level node dispatch across several behaviors:

- symbol extraction
- call extraction
- HTTP-call extraction
- string-constant extraction

The code is drifting toward “same tree walk, different side effects.”

### Proposed Classes

#### `JavaScriptTopLevelHandler`

Abstract handler contract for a top-level node family.

Responsibilities:
- decide if it can handle a tree-sitter node
- contribute parsed entities to one or more collectors

Core methods:
- `matches(node) -> bool`
- `collect(node, content, sinks) -> None`

#### `ImportNodeHandler`

Handles:
- `import_statement`

Outputs:
- imports

#### `FunctionNodeHandler`

Handles:
- `function_declaration`
- exported function declarations

Outputs:
- functions
- calls
- http calls
- string constants

#### `ClassNodeHandler`

Handles:
- `class_declaration`
- exported class declarations

Outputs:
- classes
- methods
- method calls
- method HTTP calls
- method string constants

#### `VariableDeclarationHandler`

Handles:
- `lexical_declaration`
- `variable_declaration`

Outputs:
- globals
- arrow-function-backed functions
- calls/http calls/string constants from function-valued declarations

#### `TypeDeclarationHandler`

Handles:
- `interface_declaration`
- `enum_declaration`
- `type_alias_declaration`

Outputs:
- classes or globals with subtype metadata

#### `ExportWrapperHandler`

Handles:
- `export_statement`
- `export_default_declaration`

Role:
- unwrap and delegate to the inner handler instead of duplicating extraction logic

### Supporting Objects

#### `JavaScriptParseSinks`

Simple aggregation object passed to handlers instead of mutating `ParseResult` directly during every phase.

Fields:
- `functions`
- `classes`
- `imports`
- `globals`
- `calls`
- `http_calls`
- `string_constants`

This keeps handlers focused on extraction, while `JavaScriptParser.parse()` stays responsible for building the final `ParseResult`.

#### `FunctionBodyAnalyzer`

Shared helper for function/method/arrow-function bodies.

Responsibilities:
- collect normal calls
- collect HTTP calls
- collect string constants

This is the DRY center for body-level analysis and replaces the current parallel helper families.

### Assembly Model

`JavaScriptParser` keeps ownership of:
- parser initialization
- tree creation
- top-level traversal
- final `ParseResult` assembly

It delegates per-node behavior to a registry:

- `self._top_level_handlers = [...]`

This is composition, not inheritance-heavy complexity.

---

## 2. Pipeline Executor Class Plan

### Current Problem

`PipelineExecutor` still owns too many query-mode decisions:

- plain match flow
- OR-type flow
- positive relationship flow
- negative relationship flow
- `--contains` post-filtering
- line slicing/render follow-up

That is orchestration mixed with policy.

### Proposed Classes

#### `MatchExecutionStrategy`

Abstract contract for producing `Iterator[MatchRecord]` from a parsed stage.

Core method:
- `execute(stage, db) -> Iterator[MatchRecord]`

#### `PlainMatchStrategy`

Handles:
- non-relationship stage execution
- single-type and all-type matches

Notes:
- OR-type execution can stay inside this strategy initially, then split later if it keeps growing

#### `RelationshipMatchStrategy`

Handles:
- `--via <rel>` positive relationship queries

Responsibilities:
- resolve subject/object typing conventions
- delegate relationship queries to `DatabaseStore`
- apply result-side temporal/stale rules

#### `NegativeRelationshipStrategy`

Handles:
- `--sans <rel>` negative relationship queries

Responsibilities:
- build NOT-EXISTS semantics
- preserve current declares-specific inversion behavior

### Post-Query Filter Objects

These should be separate from match strategy because they operate on already-produced records.

#### `RecordFilter`

Abstract contract:
- `apply(records) -> Iterator[MatchRecord]`

#### `ContainsBodyFilter`

Handles:
- `--contains`

Responsibilities:
- read symbol body by byte span
- preserve symbol output contract
- skip/diagnose unsupported record types consistently

#### `LineSliceFilter`

Handles:
- `-mL`

Responsibilities:
- rewrite record byte spans according to requested line slice

### Optional Later Class

#### `RenderExecutionStep`

Not needed immediately, but if `_execute_render_stage()` keeps growing, make rendering its own orchestration object.

For now this remains lower priority than query-mode extraction.

---

## 3. Non-Goals

Do not introduce:

- a giant inheritance tree
- one class per tree-sitter node type
- a second parser framework layered on top of tree-sitter
- a separate query engine

The classes above are meant to reduce repeated branch policy, not hide the underlying system.

---

## 4. Recommended Implementation Order

1. Introduce `FunctionBodyAnalyzer`
2. Introduce top-level handler registry for `javascript_parser.py`
3. Introduce `MatchExecutionStrategy` + positive/negative/plain strategies in `executor.py`
4. Extract `ContainsBodyFilter`
5. Extract `LineSliceFilter`

This order gives maximum DRY payoff with the smallest public-surface risk.

---

## 5. Success Criteria

- `javascript_parser.py` no longer repeats the same top-level dispatch across multiple extraction passes
- `PipelineExecutor` becomes a coordinator over strategies/filters rather than the home of every query-mode branch
- Sprint 15-17 regression suites remain green
- No user-visible CLI semantic changes
