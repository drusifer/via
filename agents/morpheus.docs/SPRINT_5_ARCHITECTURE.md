# Sprint 5 - Relationships Architecture

**Author**: Morpheus (SE)
**Date**: 2026-01-24

## 1. Overview

 document outlines the technical architecture for implementing the "Symbol Relationships" feature, as defined in `agents/cypher.docs/SPRINT_5_RELATIONSHIPS_SCOPE.md`. The goal is to create a flexible and extensible system for indexing and querying relationships between symbols in the codebase.

## 2. Database Schema

 new table, `relationships`, will be added to the database schema.

**`relationships` table:**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary key. |
| `source_id` | INTEGER | Foreign key to `symbols.id`. The symbol that is the source of the relationship. |
| `target_id` | INTEGER | Foreign key to `symbols.id`. The symbol that is the target of the relationship. |
| `type` | TEXT | The type of relationship (e.g., 'inherits-from', 'calls', 'imports', 'references'). |

 index will be created on `(source_id, type)` and `(target_id, type)` to optimize queries.

## 3. Indexing Process

 indexing process will be enhanced to populate the new `relationships` table. This will require modifications to the AST parser.

### 3.1. Two-Pass Indexing Strategy

 two-pass indexing strategy will be employed to handle symbol resolution for call relationships:

*   **Pass 1: Symbol Indexing:** The existing parser will be used to index all symbols (classes, functions, methods, etc.) and populate the `symbols` table. This pass will also extract and store "unresolved" relationships, where the target of the relationship is a string (e.g., the name of a function being called).

*   **Pass 2: Relationship Resolution:** After all symbols have been indexed, a second pass will resolve the unresolved relationships. For each unresolved relationship, we will query the `symbols` table to find the `id` of the target symbol. Once resolved, the relationship will be inserted into the `relationships` table.

### 3.2. Parser Modifications

 `PythonParser` will be updated to extract the following information:

*   **Inheritance:** For each class, extract the names of its base classes.

*   **Function/Method Calls:** For each function and method, traverse the AST to find all `ast.Call` nodes and extract the name of the function being called.

*   **Imports:** The parser already extracts this information. We will now store it in the `relationships` table.
*   **References:** For now, a "reference" will be considered any `ast.Name` node that is not a definition. This will be a generic relationship that can be refined later.

## 4. Querying and CLI

### 4.1. Query Semantics

The CLI uses a user-friendly mental model for relationship queries:

*   **Pattern BEFORE `--via`**: What you're **relating TO** (the "known" thing)
*   **Pattern AFTER `--via`** (optional): Filter on **results** (defaults to `*` = all)
*   **`--invert` flag**: Flips the relationship direction

**Examples:**

*   `via -mg 'BaseClass' -tc --via inherits-from` → Find all children of BaseClass
*   `via -mg 'MyClass' -tc --via inherits-from --invert` → Find parents of MyClass
*   `via -mg 'helper' -tf --via calls` → Find all callers of helper
*   `via -mg 'main' -tf --via calls --invert` → Find all functions called by main

### 4.2. DatabaseStore

The `DatabaseStore` will be updated with a new method for querying relationships:

```python
def query_relationships(
    self,
    relationship_type: str,
    subject_pattern: str = None,  # Filters source symbols
    object_pattern: str = None,   # Filters target symbols
    subject_type: str = None,
    object_type: str = None,
    invert: bool = False,
    ...
) -> Iterator[MatchRecord]:
```

The method performs a `JOIN` between the `symbols` and `symbol_references` tables. The `invert` flag changes which symbols are returned (sources vs targets).

### 4.3. Executor Mapping

The `PipelineExecutor` maps CLI semantics to database query parameters:

*   **Without `--invert`**: CLI pattern → filters targets (parents/callees), returns sources (children/callers)
*   **With `--invert`**: CLI pattern → filters sources (children/callers), returns targets (parents/callees)

### 4.4. CLI Flags

The `via` command supports the new relationship query syntax:

*   `--via <relationship>` or short forms: `-Vinh`, `-Vca`, `-Vimp`, `-Vr`
*   `--invert` / `-iv` to reverse relationship direction
*   The pipeline parser handles the relationship query structure

## 5. Implementation Plan

 feature will be implemented incrementally, one relationship type at a time.

.  **Phase 1: Schema and Basic Querying:**
    *   Implement the `relationships` table in the database schema.
    *   Update `DatabaseStore` with the basic `query_relationships` method.
    *   Update the CLI to support the new syntax, initially with no-op relationship types.

.  **Phase 2: Inheritance:**
    *   Update the parser to extract inheritance information.
    *   Implement the logic for indexing and querying the `inherits-from` relationship.

.  **Phase 3: Imports:**
    *   Update the parser to store import information in the `relationships` table.
    *   Implement the logic for indexing and querying the `imports` relationship.

.  **Phase 4: Calls and References (Most Complex):**
    *   Implement the two-pass indexing strategy.
    *   Update the parser to extract call and reference information.
    *   Implement the symbol resolution logic.
    *   Implement the logic for indexing and querying the `calls` and `references` relationships.

 phased approach will allow us to deliver value incrementally and manage the complexity of the feature.
