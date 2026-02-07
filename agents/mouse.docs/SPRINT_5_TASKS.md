# Sprint 5 Task Breakdown - Symbol Relationships

**Version**: 1.0
**Date**: 2026-01-24
**Task Owner**: @Mouse
**Status**: Ready for Implementation

---

## Executive Summary

Sprint 5 introduces **symbol relationship queries** - the ability to understand and query how symbols relate to each other (inheritance, calls, imports, references). This is a major feature that enables powerful codebase navigation.

**Sprint Theme**: Understand the connections between code symbols

**Estimated Effort**: 34 story points, ~272 hours

---

## Architecture Summary

Based on `morpheus.docs/SPRINT_5_ARCHITECTURE.md`:

- **New Table**: `relationships` with `source_id`, `target_id`, `type`
- **Two-Pass Indexing**: Pass 1 indexes symbols + unresolved refs, Pass 2 resolves relationships
- **Query Syntax**: `<subject> --via <relationship> <object> [--invert]`

---

## Sprint 5 Scope

### Story Points Summary

| Story | Points | Priority | Phase |
|-------|--------|----------|-------|
| US-R1: Schema & Basic Querying | 5 | P0 | 1 |
| US-R2: Inheritance Relationships | 8 | P1 | 2 |
| US-R3: Import Relationships | 5 | P1 | 3 |
| US-R4: Call Relationships | 13 | P1 | 4 |
| US-R5: Integration & Polish | 3 | P2 | 5 |
| **Total** | **34** | | |

---

## Phase 1: Schema & Basic Querying (US-R1 - P0, 5pts)

**Dependencies**: None (BLOCKER for all other phases)
**Duration**: 5 days (40h)
**Assignee**: @Neo

### Task 1.1: Create Relationships Table (1 day, 8h)

**Files to Modify**:
- `via/db/schema.py`
- `via/db/store.py`

**Implementation Steps**:
1. Add `relationships` table to schema:
   ```sql
   CREATE TABLE IF NOT EXISTS relationships (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       source_id INTEGER NOT NULL,
       target_id INTEGER NOT NULL,
       type TEXT NOT NULL,
       FOREIGN KEY (source_id) REFERENCES symbols(id) ON DELETE CASCADE,
       FOREIGN KEY (target_id) REFERENCES symbols(id) ON DELETE CASCADE
   );
   ```
2. Create indexes for efficient queries:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_rel_source_type ON relationships(source_id, type);
   CREATE INDEX IF NOT EXISTS idx_rel_target_type ON relationships(target_id, type);
   CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(type);
   ```
3. Add to schema version management
4. Update `initialize_schema()` in store.py

**Acceptance Criteria**:
- AC1: Relationships table created on index
- AC2: Indexes exist for query optimization
- AC3: Foreign key constraints enforced
- AC4: ON DELETE CASCADE cleans up orphaned relationships

**Tests**:
- `test_relationships_table_exists()`
- `test_relationships_indexes_exist()`
- `test_relationships_cascade_delete()`

**Estimated**: 8h

---

### Task 1.2: Add RelationshipType Enum (0.5 days, 4h)

**Files to Create**:
- `via/core/relationship_types.py`

**Implementation Steps**:
1. Create `RelationshipType` enum:
   ```python
   class RelationshipType(Enum):
       INHERITS_FROM = 'inherits-from'
       CALLS = 'calls'
       IMPORTS = 'imports'
       REFERENCES = 'references'

       @property
       def short_flag(self) -> str:
           return {
               self.INHERITS_FROM: 'inh',
               self.CALLS: 'ca',
               self.IMPORTS: 'imp',
               self.REFERENCES: 'r',
           }[self]
   ```

**Acceptance Criteria**:
- AC1: All 4 relationship types defined
- AC2: Short flag mappings correct

**Tests**:
- `test_relationship_type_values()`
- `test_relationship_type_short_flags()`

**Estimated**: 4h

---

### Task 1.3: DatabaseStore Relationship Methods (1.5 days, 12h)

**Files to Modify**:
- `via/db/store.py`

**Implementation Steps**:
1. Add `insert_relationship()`:
   ```python
   def insert_relationship(self, source_id: int, target_id: int, rel_type: str) -> int:
       cursor = self.conn.execute(
           "INSERT INTO relationships (source_id, target_id, type) VALUES (?, ?, ?)",
           (source_id, target_id, rel_type)
       )
       return cursor.lastrowid
   ```
2. Add `query_relationships()`:
   ```python
   def query_relationships(
       self,
       relationship_type: str,
       subject_type: Optional[str] = None,
       subject_pattern: Optional[str] = None,
       object_type: Optional[str] = None,
       object_pattern: Optional[str] = None,
       invert: bool = False,
       match_op: MatchOp = MatchOp.GLOB,
       case_sensitive: bool = True,
       limit: int = 100
   ) -> Iterator[MatchRecord]:
       """Query symbols by relationship.

       When invert=False: Find subjects that have relationship TO objects matching pattern
       When invert=True: Find subjects that have relationship FROM objects matching pattern
       """
   ```
3. Add `delete_relationships_for_file()` for re-indexing
4. Add `get_symbol_id()` helper for resolution

**Acceptance Criteria**:
- AC1: Can insert relationships
- AC2: Can query relationships with subject/object filtering
- AC3: Invert flag swaps source/target correctly
- AC4: Returns MatchRecord iterator (streaming)

**Tests**:
- `test_insert_relationship()`
- `test_query_relationships_basic()`
- `test_query_relationships_with_patterns()`
- `test_query_relationships_inverted()`
- `test_delete_relationships_for_file()`

**Estimated**: 12h

---

### Task 1.4: CLI Relationship Flags (1 day, 8h)

**Files to Modify**:
- `via/pipeline/parser.py`
- `via/core/flag_groups.py`

**Implementation Steps**:
1. Add relationship flag group to parser:
   ```python
   # Relationship flags (--via <type> or -V<suffix>)
   rel_group = parser.add_mutually_exclusive_group()
   rel_group.add_argument('--via', dest='relationship_type',
                          choices=['inherits-from', 'calls', 'imports', 'references'])
   rel_group.add_argument('-Vinh', dest='relationship_type', action='store_const',
                          const='inherits-from', help='Inheritance relationship')
   rel_group.add_argument('-Vca', dest='relationship_type', action='store_const',
                          const='calls', help='Call relationship')
   rel_group.add_argument('-Vimp', dest='relationship_type', action='store_const',
                          const='imports', help='Import relationship')
   rel_group.add_argument('-Vr', dest='relationship_type', action='store_const',
                          const='references', help='Reference relationship')
   ```
2. Add `--invert` / `-iv` flag:
   ```python
   parser.add_argument('--invert', '-iv', action='store_true',
                       help='Invert relationship direction')
   ```
3. Update `_is_relationship_stage()` detection
4. Add help text for relationship queries

**Acceptance Criteria**:
- AC1: `--via inherits-from` parsed correctly
- AC2: `-Vinh`, `-Vca`, `-Vimp`, `-Vr` shortcuts work
- AC3: `--invert` flag recognized
- AC4: Relationship stages detected in pipeline

**Tests**:
- `test_parse_relationship_long_form()`
- `test_parse_relationship_short_form()`
- `test_parse_invert_flag()`
- `test_is_relationship_stage()`

**Estimated**: 8h

---

### Task 1.5: Pipeline Executor Relationship Stage (1 day, 8h)

**Files to Modify**:
- `via/pipeline/executor.py`
- `via/pipeline/types.py`

**Implementation Steps**:
1. Add `StageType.RELATIONSHIP` to types.py
2. Add `_execute_relationship_stage()` to executor:
   ```python
   def _execute_relationship_stage(
       self,
       stage: PipelineStage,
       prev_results: Optional[Iterator[MatchRecord]] = None
   ) -> Iterator[MatchRecord]:
       args = stage.args
       rel_type = args.relationship_type
       invert = getattr(args, 'invert', False)

       # Get object query from next stage or use prev_results as subject filter
       # ...
   ```
3. Wire into `execute()` main loop
4. Handle relationship + match stage combinations

**Acceptance Criteria**:
- AC1: Relationship stages execute correctly
- AC2: Results streamed as MatchRecord iterator
- AC3: Can chain with match stages

**Tests**:
- `test_execute_relationship_stage()`
- `test_relationship_with_match_stages()`

**Estimated**: 8h

---

**Phase 1 Total**: 40h (5 days)

---

## Phase 2: Inheritance Relationships (US-R2 - P1, 8pts)

**Dependencies**: Phase 1
**Duration**: 8 days (64h)
**Assignee**: @Neo

### Task 2.1: Extract Inheritance from AST (2 days, 16h)

**Files to Modify**:
- `via/parsers/python_parser.py`

**Implementation Steps**:
1. In `_parse_class()`, extract base class names:
   ```python
   def _parse_class(self, node: ast.ClassDef, ...) -> ParsedSymbol:
       # Existing class parsing...

       # Extract base classes
       base_classes = []
       for base in node.bases:
           if isinstance(base, ast.Name):
               base_classes.append(base.id)
           elif isinstance(base, ast.Attribute):
               # Handle module.Class
               base_classes.append(self._get_attribute_name(base))

       return ParsedSymbol(
           ...,
           extra={'base_classes': base_classes}
       )
   ```
2. Handle various base class syntaxes:
   - Simple: `class Foo(Bar):`
   - Module: `class Foo(module.Bar):`
   - Multiple: `class Foo(Bar, Baz):`
3. Store base class names in `extra` dict

**Acceptance Criteria**:
- AC1: Simple inheritance extracted
- AC2: Module-qualified bases extracted
- AC3: Multiple inheritance extracted
- AC4: No bases returns empty list

**Tests**:
- `test_extract_simple_inheritance()`
- `test_extract_module_inheritance()`
- `test_extract_multiple_inheritance()`
- `test_extract_no_inheritance()`

**Estimated**: 16h

---

### Task 2.2: Store Inheritance Relationships (1.5 days, 12h)

**Files to Modify**:
- `via/services/indexing.py`
- `via/db/store.py`

**Implementation Steps**:
1. Create pending relationships table for unresolved refs:
   ```sql
   CREATE TABLE IF NOT EXISTS pending_relationships (
       id INTEGER PRIMARY KEY,
       source_id INTEGER NOT NULL,
       target_name TEXT NOT NULL,
       type TEXT NOT NULL
   );
   ```
2. In `_store_parsed_file()`, after inserting class:
   ```python
   if entity.extra and 'base_classes' in entity.extra:
       for base_name in entity.extra['base_classes']:
           self.db.insert_pending_relationship(
               symbol_id, base_name, 'inherits-from'
           )
   ```
3. Add `resolve_pending_relationships()` to store:
   ```python
   def resolve_pending_relationships(self):
       """Resolve pending relationships after all symbols indexed."""
       pending = self.conn.execute(
           "SELECT id, source_id, target_name, type FROM pending_relationships"
       ).fetchall()

       for row in pending:
           target_id = self.find_symbol_by_name(row['target_name'])
           if target_id:
               self.insert_relationship(row['source_id'], target_id, row['type'])
           self.conn.execute(
               "DELETE FROM pending_relationships WHERE id = ?", (row['id'],)
           )
   ```
4. Call resolution at end of indexing

**Acceptance Criteria**:
- AC1: Pending relationships stored during parsing
- AC2: Resolution runs after all files indexed
- AC3: Resolved relationships in relationships table
- AC4: Unresolvable refs cleaned up

**Tests**:
- `test_store_pending_relationship()`
- `test_resolve_inheritance_relationship()`
- `test_resolve_cross_file_inheritance()`
- `test_unresolvable_relationship_handled()`

**Estimated**: 12h

---

### Task 2.3: Inheritance Query Implementation (1.5 days, 12h)

**Files to Modify**:
- `via/db/store.py`

**Implementation Steps**:
1. Implement inheritance-specific query in `query_relationships()`:
   ```sql
   -- Find classes that inherit from X (default)
   SELECT s.* FROM symbols s
   JOIN relationships r ON s.id = r.source_id
   JOIN symbols t ON r.target_id = t.id
   WHERE r.type = 'inherits-from'
   AND t.symbol_name GLOB ?

   -- Find parents of X (inverted)
   SELECT t.* FROM symbols t
   JOIN relationships r ON t.id = r.target_id
   JOIN symbols s ON r.source_id = s.id
   WHERE r.type = 'inherits-from'
   AND s.symbol_name GLOB ?
   ```
2. Add subject type filtering (only classes can inherit)
3. Support pattern matching on both sides

**Acceptance Criteria**:
- AC1: Find children of base class
- AC2: Find parents of child class (inverted)
- AC3: Pattern matching works
- AC4: Proper MatchRecord types returned

**Tests**:
- `test_query_inherits_from()`
- `test_query_inherits_from_inverted()`
- `test_query_inheritance_with_pattern()`

**Estimated**: 12h

---

### Task 2.4: Inheritance Integration Tests (1 day, 8h)

**Files to Create**:
- `tests/integration/test_inheritance_relationships.py`

**Test Cases**:
1. Index project with class hierarchy
2. `via -mg '*' -tc --via inherits-from -mg 'Base*' -tc` - Find children
3. `via -mg 'Child*' -tc --via inherits-from -mg '*' -tc --invert` - Find parents
4. Multiple inheritance chain
5. Cross-file inheritance

**Estimated**: 8h

---

### Task 2.5: Update ClassMatchRecord (1 day, 8h)

**Files to Modify**:
- `via/core/match_record.py`

**Implementation Steps**:
1. Add `base_classes` field:
   ```python
   @dataclass
   class ClassMatchRecord(MatchRecord):
       base_classes: Optional[List[str]] = None
   ```
2. Update factory to populate from extra data
3. Used by DiagramRenderer for inheritance arrows

**Acceptance Criteria**:
- AC1: base_classes available on ClassMatchRecord
- AC2: DiagramRenderer can show inheritance

**Tests**:
- `test_class_record_has_base_classes()`
- `test_diagram_shows_inheritance()`

**Estimated**: 8h

---

### Task 2.6: Documentation (0.5 days, 4h)

**Files to Modify**:
- `docs/USER_GUIDE.md`

**Content**:
- Inheritance query examples
- How to find class hierarchy
- Usage with diagram output

**Estimated**: 4h

---

**Phase 2 Total**: 64h (8 days)

---

## Phase 3: Import Relationships (US-R3 - P1, 5pts)

**Dependencies**: Phase 1
**Duration**: 5 days (40h)
**Assignee**: @Neo

### Task 3.1: Extract Import Targets (1 day, 8h)

**Files to Modify**:
- `via/parsers/python_parser.py`

**Implementation Steps**:
1. For `from X import Y`, store relationship: file -> module X
2. For `import X`, store relationship: file -> module X
3. Add `import_target` to extra dict:
   ```python
   ParsedSymbol(
       symbol_type='import',
       symbol_name='List',
       qualified_name='typing.List',
       extra={'import_module': 'typing'}
   )
   ```

**Acceptance Criteria**:
- AC1: Import module captured
- AC2: Works for `from X import Y`
- AC3: Works for `import X`
- AC4: Works for `import X.Y.Z`

**Tests**:
- `test_extract_from_import_module()`
- `test_extract_import_module()`
- `test_extract_nested_import_module()`

**Estimated**: 8h

---

### Task 3.2: Store Import Relationships (1 day, 8h)

**Files to Modify**:
- `via/services/indexing.py`

**Implementation Steps**:
1. After storing import symbol, create relationship:
   - Source: The file's filepath symbol ID
   - Target: The import symbol ID
   - Type: 'imports'
2. Handle module-level imports vs symbol imports

**Acceptance Criteria**:
- AC1: File -> import relationships stored
- AC2: Can query which files import what

**Tests**:
- `test_store_import_relationship()`
- `test_import_relationship_links_file_to_symbol()`

**Estimated**: 8h

---

### Task 3.3: Import Query Implementation (1 day, 8h)

**Files to Modify**:
- `via/db/store.py`

**Implementation Steps**:
1. Query: Find files that import module X
   ```sql
   SELECT f.* FROM symbols f
   JOIN relationships r ON f.id = r.source_id
   JOIN symbols i ON r.target_id = i.id
   WHERE r.type = 'imports'
   AND f.symbol_type = 'filepath'
   AND i.qualified_name GLOB ?
   ```
2. Inverted: Find what a file imports
   ```sql
   SELECT i.* FROM symbols i
   JOIN relationships r ON i.id = r.target_id
   JOIN symbols f ON r.source_id = f.id
   WHERE r.type = 'imports'
   AND f.file_path GLOB ?
   ```

**Acceptance Criteria**:
- AC1: Find files importing a module
- AC2: Find imports in a file (inverted)
- AC3: Pattern matching on module names

**Tests**:
- `test_query_imports()`
- `test_query_imports_inverted()`
- `test_query_imports_pattern()`

**Estimated**: 8h

---

### Task 3.4: Import Integration Tests (1 day, 8h)

**Files to Create**:
- `tests/integration/test_import_relationships.py`

**Test Cases**:
1. `via -mg '*' -tF --via imports -mg 'typing*' -ti` - Files importing typing
2. `via -mg 'test_*.py' -tF --via imports -mg '*' -ti --invert` - What test files import
3. Cross-file import tracking

**Estimated**: 8h

---

### Task 3.5: Documentation (0.5 days, 4h)

**Files to Modify**:
- `docs/USER_GUIDE.md`

**Content**:
- Import query examples
- Finding module dependencies
- Analyzing import patterns

**Estimated**: 4h

---

**Phase 3 Total**: 40h (5 days)

---

## Phase 4: Call Relationships (US-R4 - P1, 13pts)

**Dependencies**: Phase 1
**Duration**: 13 days (104h)
**Assignee**: @Neo

**Note**: This is the most complex phase due to symbol resolution challenges.

### Task 4.1: Extract Function/Method Calls from AST (3 days, 24h)

**Files to Modify**:
- `via/parsers/python_parser.py`

**Implementation Steps**:
1. Add call extraction visitor:
   ```python
   def _extract_calls(self, node: ast.FunctionDef) -> List[str]:
       calls = []
       for child in ast.walk(node):
           if isinstance(child, ast.Call):
               name = self._get_call_name(child)
               if name:
                   calls.append(name)
       return calls
   ```
2. Handle call types:
   - Simple: `func()` -> 'func'
   - Method: `obj.method()` -> 'method'
   - Chained: `obj.a.b()` -> 'b'
   - Module: `module.func()` -> 'module.func'
3. Store in extra dict:
   ```python
   ParsedSymbol(
       symbol_type='function',
       extra={'calls': ['helper', 'utils.process']}
   )
   ```

**Acceptance Criteria**:
- AC1: Simple function calls extracted
- AC2: Method calls extracted
- AC3: Module-qualified calls extracted
- AC4: Nested/chained calls handled

**Tests**:
- `test_extract_simple_call()`
- `test_extract_method_call()`
- `test_extract_module_call()`
- `test_extract_chained_call()`
- `test_extract_multiple_calls()`

**Estimated**: 24h

---

### Task 4.2: Two-Pass Indexing Infrastructure (2 days, 16h)

**Files to Modify**:
- `via/services/indexing.py`

**Implementation Steps**:
1. Modify indexing to run in two passes:
   ```python
   def index_directory(self, directory: str):
       # Pass 1: Index all symbols
       for file in files:
           self._index_file_symbols(file)

       # Pass 2: Resolve relationships
       self.db.resolve_pending_relationships()
   ```
2. Add progress tracking for second pass
3. Handle incremental updates (only re-resolve changed files)

**Acceptance Criteria**:
- AC1: Two-pass indexing works
- AC2: Relationships resolved after all symbols indexed
- AC3: Progress reported for both passes

**Tests**:
- `test_two_pass_indexing()`
- `test_incremental_relationship_update()`

**Estimated**: 16h

---

### Task 4.3: Symbol Resolution for Calls (3 days, 24h)

**Files to Modify**:
- `via/db/store.py`

**Implementation Steps**:
1. Implement smart symbol resolution:
   ```python
   def find_symbol_by_call_name(
       self,
       call_name: str,
       caller_file: str,
       caller_scope: Optional[str] = None
   ) -> Optional[int]:
       """Resolve a call name to a symbol ID.

       Resolution order:
       1. Local scope (same class for methods)
       2. Same file
       3. Imported symbols
       4. Global search by name
       """
   ```
2. Handle common patterns:
   - `self.method()` -> method in same class
   - `helper()` -> function in same file or imported
   - `module.func()` -> imported module's function

**Acceptance Criteria**:
- AC1: Local methods resolved
- AC2: Same-file functions resolved
- AC3: Imported functions resolved
- AC4: Ambiguous calls handled gracefully

**Tests**:
- `test_resolve_local_method()`
- `test_resolve_same_file_function()`
- `test_resolve_imported_function()`
- `test_resolve_ambiguous_call()`

**Estimated**: 24h

---

### Task 4.4: Store Call Relationships (1 day, 8h)

**Files to Modify**:
- `via/services/indexing.py`

**Implementation Steps**:
1. In `_store_parsed_file()`, for functions/methods with calls:
   ```python
   if entity.extra and 'calls' in entity.extra:
       for call_name in entity.extra['calls']:
           self.db.insert_pending_relationship(
               symbol_id, call_name, 'calls'
           )
   ```
2. Resolution handles call->symbol mapping

**Acceptance Criteria**:
- AC1: Call relationships stored
- AC2: Unresolvable calls tracked but not blocking

**Tests**:
- `test_store_call_relationship()`

**Estimated**: 8h

---

### Task 4.5: Call Query Implementation (1.5 days, 12h)

**Files to Modify**:
- `via/db/store.py`

**Implementation Steps**:
1. Query: Find functions that call X
   ```sql
   SELECT caller.* FROM symbols caller
   JOIN relationships r ON caller.id = r.source_id
   JOIN symbols callee ON r.target_id = callee.id
   WHERE r.type = 'calls'
   AND callee.symbol_name GLOB ?
   ```
2. Inverted: Find what X calls
   ```sql
   SELECT callee.* FROM symbols callee
   JOIN relationships r ON callee.id = r.target_id
   JOIN symbols caller ON r.source_id = caller.id
   WHERE r.type = 'calls'
   AND caller.symbol_name GLOB ?
   ```

**Acceptance Criteria**:
- AC1: Find callers of a function
- AC2: Find callees of a function (inverted)
- AC3: Works for methods too

**Tests**:
- `test_query_calls()`
- `test_query_calls_inverted()`
- `test_query_method_calls()`

**Estimated**: 12h

---

### Task 4.6: References Relationship (1 day, 8h)

**Files to Modify**:
- `via/parsers/python_parser.py`
- `via/db/store.py`

**Implementation Steps**:
1. Extract `ast.Name` nodes that are references (not definitions)
2. Store as 'references' relationship type
3. This is more general than 'calls' - includes variable references

**Note**: This may generate many relationships. Consider limiting to important refs.

**Acceptance Criteria**:
- AC1: Symbol references extracted
- AC2: Can query "what references X"

**Tests**:
- `test_extract_references()`
- `test_query_references()`

**Estimated**: 8h

---

### Task 4.7: Call Relationship Integration Tests (1 day, 8h)

**Files to Create**:
- `tests/integration/test_call_relationships.py`

**Test Cases**:
1. `via -mg '*' -tf --via calls -mg 'helper*' -tf` - Find callers
2. `via -mg 'main' -tf --via calls -mg '*' -tf --invert` - Find callees
3. Method call chains
4. Cross-file calls

**Estimated**: 8h

---

### Task 4.8: Documentation (0.5 days, 4h)

**Files to Modify**:
- `docs/USER_GUIDE.md`

**Content**:
- Call relationship examples
- Finding function dependencies
- Impact analysis workflows

**Estimated**: 4h

---

**Phase 4 Total**: 104h (13 days)

---

## Phase 5: Integration & Polish (US-R5 - P2, 3pts)

**Dependencies**: Phases 1-4
**Duration**: 3 days (24h)
**Assignee**: @Neo

### Task 5.1: Full Integration Tests (1 day, 8h)

**Files to Create**:
- `tests/integration/test_relationship_queries.py`

**Test Cases**:
1. Combined queries with output formats
2. Relationship queries with render stages
3. Performance with large codebases
4. Error handling for unresolved relationships

**Estimated**: 8h

---

### Task 5.2: CLI Help & Documentation (1 day, 8h)

**Files to Modify**:
- `via/__main__.py`
- `docs/USER_GUIDE.md`
- `README.md`

**Content**:
- Update --help with relationship examples
- Full relationship query documentation
- Agent workflow examples

**Estimated**: 8h

---

### Task 5.3: Performance Optimization (1 day, 8h)

**Implementation Steps**:
1. Analyze query performance with large relationship sets
2. Add query caching if needed
3. Optimize JOIN queries
4. Add EXPLAIN QUERY PLAN tests

**Estimated**: 8h

---

**Phase 5 Total**: 24h (3 days)

---

## Sprint 5 Summary

### Total Effort by Phase

| Phase | Story | Priority | Points | Hours | Status |
|-------|-------|----------|--------|-------|--------|
| 1 | Schema & Basic Querying | P0 | 5 | 40h | Ready |
| 2 | Inheritance Relationships | P1 | 8 | 64h | Ready |
| 3 | Import Relationships | P1 | 5 | 40h | Ready |
| 4 | Call Relationships | P1 | 13 | 104h | Ready |
| 5 | Integration & Polish | P2 | 3 | 24h | Ready |
| **Total** | | | **34** | **272h** | |

### Critical Path

```
Phase 1 (Schema) ──┬─► Phase 2 (Inheritance)
   [BLOCKER]       │
                   ├─► Phase 3 (Imports)
                   │
                   └─► Phase 4 (Calls)
                              │
                              ▼
                       Phase 5 (Polish)
```

### Parallelization Opportunities

After Phase 1 completes, Phases 2, 3, and 4 can run in parallel:
- **@Neo-1**: Inheritance (Phase 2) - 8 days
- **@Neo-2**: Imports (Phase 3) - 5 days
- **@Neo-3**: Calls (Phase 4) - 13 days

Sequential: ~34 days @ 8h/day

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Symbol resolution complexity | High | High | Start with simple cases, iterate |
| Performance with many relationships | Medium | Medium | Indexes, caching, limits |
| Cross-file resolution | Medium | Medium | Two-pass indexing |
| Ambiguous call resolution | High | Low | Best-effort matching, log unresolved |

### Success Criteria

**Sprint 5 Complete When**:
- [ ] `relationships` table created and indexed
- [ ] `--via inherits-from` queries work
- [ ] `--via imports` queries work
- [ ] `--via calls` queries work
- [ ] `--via references` queries work
- [ ] `--invert` flag reverses all relationship queries
- [ ] Two-pass indexing resolves cross-file relationships
- [ ] All queries return proper MatchRecord iterators
- [ ] Documentation with working examples
- [ ] 90%+ test coverage on new code

---

## Appendix: Query Reference

### After Sprint 5

| Query | Description |
|-------|-------------|
| `via -mg '*' -tc --via inherits-from -mg 'Base' -tc` | Classes inheriting from Base |
| `via -mg 'Child' -tc --via inherits-from -mg '*' -tc -iv` | Parents of Child |
| `via -mg '*' -tF --via imports -mg 'typing' -ti` | Files importing typing |
| `via -mg 'test.py' -tF --via imports -mg '*' -ti -iv` | What test.py imports |
| `via -mg '*' -tf --via calls -mg 'helper' -tf` | Functions calling helper |
| `via -mg 'main' -tf --via calls -mg '*' -tf -iv` | Functions main calls |

---

**Status**: Ready for Implementation
**Created**: 2026-01-24
**Author**: @Mouse (Scrum Master)
