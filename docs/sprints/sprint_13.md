# Sprint 13 Consolidated Documentation

This document consolidates all documentation for Sprint 13.

## Table of Contents

- [SPRINT_13_PRD.md](#sprint-13-prdmd) (originally `agents/cypher.docs/SPRINT_13_PRD.md`)

- [SPRINT_13_ARCHITECTURE.md](#sprint-13-architecturemd) (originally `agents/morpheus.docs/SPRINT_13_ARCHITECTURE.md`)

- [SPRINT_13_GATE1_REVIEW.md](#sprint-13-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_13_GATE1_REVIEW.md`)

- [SPRINT_13_TEST_REPORT.md](#sprint-13-test-reportmd) (originally `agents/smith.docs/SPRINT_13_TEST_REPORT.md`)

- [SPRINT_13_TASKS.md](#sprint-13-tasksmd) (originally `agents/mouse.docs/SPRINT_13_TASKS.md`)


---


## SPRINT_13_PRD.md

**Original Location**: `agents/cypher.docs/SPRINT_13_PRD.md`


## Sprint 13 PRD: CLI Relationship Flag Redesign

_Author: Cypher | Date: 2026-03-23_
_Reference: agents/smith.docs/CLI_DESIGN_VIA_SANS_FLAGS.md_

---

### Goal

Replace the current relationship flag system (`-Vinh`, `-Vca`, `--invert`, etc.) with a clean, symmetric, self-documenting interface:

- `--via <rel>` — positive relationship filter ("has this relationship")
- `--sans <rel>` — negative relationship filter ("does NOT have this relationship")
- `--not` — match pattern negation ("symbol name does NOT match")

**No backward compatibility. The old flags are removed, not deprecated.**

---

### Out of Scope

- Web UI changes (relationship types are passed as JSON values, not CLI flags — unaffected)
- New relationship types (separate sprint)
- `--intersect` compound AND queries (separate sprint)

---

### Stories

---

#### S13-1: Replace `-V<rel>` flags with `--via <rel>` / `--sans <rel>`

**As a** CLI user,
**I want** to write `via --match-glob "Base*" --via inherits-from --match-glob "*"`,
**so that** my relationship queries are self-documenting and don't require me to memorise flag suffixes.

**Acceptance Criteria:**

- `--via <rel>` accepted as a CLI flag where `<rel>` is one of: `inherits-from`, `calls`, `imports`, `references`, `has`, `declares`
- `--sans <rel>` accepted with the same `<rel>` values
- Short forms `-V <rel>` and `-S <rel>` work as aliases
- All `-V<rel>` compound flags removed: `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas` are gone — using them produces "unknown flag" error
- `--ref-type` removed — superseded by `--via`
- `--invert` / `-iv` removed — gone entirely, no alias
- Direction is encoded by argument order (anchor left, results right) — documented in `--help`
- Invalid `<rel>` value produces a clear error: `"Unknown relationship type 'foo'. Valid: inherits-from, calls, imports, references, has, declares"`
- `RelationshipFilter` data structure gains `is_negative: bool` field (`True` for `--sans`)
- All existing relationship query behaviour is preserved under the new flags

**Files expected to change:**
- `via/core/flag_groups.py` — remove `RELATIONSHIP_FLAGS`, add `--via`/`--sans` definitions
- `via/__main__.py` — remove `-V<rel>` arg parsing, remove `--invert`, add `--via`/`--sans`, update help text and examples
- `via/pipeline/executor.py` — remove `--invert` direction-flip logic
- `via/mcp/schema.py` — update relationship flag references

---

#### S13-2: Implement `--sans` NOT-EXISTS execution

**As a** CLI user,
**I want** `via --match-glob "*" --type-function --sans calls --match-glob "*"` to return functions that are never called,
**so that** I can find dead code without external tooling.

**Acceptance Criteria:**

- `--sans <rel>` executes as a NOT EXISTS subquery on the relationships table
- `via --match-glob "*" --type-function --sans calls --match-glob "*"` returns functions with no outgoing `calls` edges
- `via --match-glob "*" --type-class --sans inherits-from --match-glob "*"` returns classes with no `inherits-from` relationship
- `via --match-glob "test_*" --type-function --sans has --match-glob "*/tests/*" --type-filepath` returns test_ functions outside `tests/` — no error (this was the `--invert` error case)
- The result pattern after `--sans` correctly constrains the NOT EXISTS subquery (e.g. `--sans calls --match-glob "external_*"` means "not called by anything matching `external_*`", not "not called by anything at all")
- `--sans` combined with `--stale` behaves correctly
- Error message if `--sans` is used without a `<rel>` argument

---

#### S13-3: Implement `--not` match pattern negation

**As a** CLI user,
**I want** `via --not --match-glob "_*" --type-method` to return methods whose names do NOT start with underscore,
**so that** I can filter to public symbols without writing an inverse regex.

**Acceptance Criteria:**

- `--not` negates the immediately following `--match-glob` / `--match-regex` / `--match-sql` pattern
- `via --not --match-glob "_*" --type-method` returns methods not starting with `_`
- `via --not --match-glob "test_*" --type-function` returns functions not named `test_*`
- `--not` without a following `--match-*` flag produces a clear error: `"--not must precede a match flag (--match-glob, --match-regex, --match-sql)"`
- `--not` and `--sans` are orthogonal and can be combined in one command
- `--not` applies only to the match stage it precedes — does not affect relationship patterns
- Short form: none (long form only, to avoid `-n` conflicts)

---

#### S13-4: Update `--help`, examples, and error messages

**As a** CLI user,
**I want** `via --help` to show only the new flag syntax,
**so that** I learn the correct interface from first contact and never see the old flags.

**Acceptance Criteria:**

- `--help` output contains no references to `-Vinh`, `-Vca`, `--invert`, `-iv`, `--ref-type`
- `--help` documents `--via <rel>` and `--sans <rel>` with the direction convention (anchor left, results right)
- `--help` documents `--not` and its orthogonality to `--sans`
- All inline examples in `__main__.py` use long-form flags (`--match-glob`, `--type-class`, `--via`, `--sans`, `--not`)
- Valid `<rel>` values are listed in `--help`
- `via --help` passes a manual review: a developer reading it cold can write a relationship query without consulting external docs

---

#### S13-5: Update all tests

**As a** developer,
**I want** the test suite to cover only the new flag interface,
**so that** there are no tests that pass by relying on removed flags.

**Acceptance Criteria:**

- All unit and integration tests using `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`, `--invert`, `--ref-type` are updated to use `--via`/`--sans`
- Tests added for `--sans` NOT EXISTS behaviour (at minimum: uncalled functions, classes with no parent, misplaced test_ functions)
- Tests added for `--not` match negation (at minimum: exclude private methods, exclude test_ functions)
- Tests added for invalid `<rel>` error message
- Tests added for `--not` without a match flag error message
- All 1121 Python tests pass
- No test references old flag names in assertions, parametrize values, or docstrings

---

### Dependency Order

```
S13-1 (flag parsing + RelationshipFilter)
  └─► S13-2 (--sans executor logic)
  └─► S13-3 (--not executor logic)
        └─► S13-4 (--help update — after all flags exist)
              └─► S13-5 (tests — after implementation complete)
```

S13-2 and S13-3 can be implemented in parallel after S13-1.

---

### Definition of Done

- All 5 stories complete
- `via --help` shows no old flags
- `via -Vinh "Base" --match-glob "*"` returns "unknown flag" error
- `via --match-glob "*" --type-function --sans calls --match-glob "*"` returns results
- `via --not --match-glob "_*" --type-method` returns results
- All tests pass


---


## SPRINT_13_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_13_ARCHITECTURE.md`


## Sprint 13 Architecture: CLI Relationship Flag Redesign

_Author: Morpheus | Date: 2026-03-23_

### Summary

Replace `-V<rel>`, `--invert`, and `--ref-type` with three clean, self-documenting flags:
- `--via <rel>` / `-V <rel>` — positive relationship filter
- `--sans <rel>` / `-S <rel>` — negative (NOT EXISTS) relationship filter
- `--not` — negate immediately following match pattern

**Breaking change: no backward compatibility. Zero deprecated aliases.**

---

### Files Changing

| File | Change |
|------|--------|
| `via/core/flag_groups.py` | Remove `FlagGroup.RELATIONSHIP`, `RELATIONSHIP_FLAGS`, `get_relationship_short_flags()` |
| `via/core/relationship_types.py` | Remove `short_flag`, `cli_short`, `from_short_flag`, `get_flag_map()` — no longer needed |
| `via/pipeline/relationship_filter.py` | Replace `invert: bool` with `is_negative: bool` |
| `via/pipeline/parser.py` | Replace `-V<rel>` parsing + `--invert` + `--ref-type` with `--via`/`--sans`/`--not` |
| `via/pipeline/executor.py` | Remove invert direction-flip logic; add NOT EXISTS path for `is_negative=True` |
| `via/db/store.py` | Add `query_negative_relationships()` for `--sans` NOT EXISTS semantics |
| `via/__main__.py` | Update help text, examples, remove old flag references |
| `via/mcp/schema.py` | Update relationship flag references in tool description |

---

### Direction Semantics (PRESERVED FROM OLD DESIGN)

The `--via` flag preserves the existing direction convention from old `invert=False`:

```
BEFORE --via = object pattern  (what you're filtering the "known" side on)
AFTER --via  = subject pattern (filter on subjects = what gets returned)
Returns: subjects (sources) that have the relationship TO the object
```

Examples:
- `via --match-glob "BaseHandler" --via inherits-from --match-glob "*"` — subclasses of BaseHandler
  (BEFORE=BaseHandler=parent filter, AFTER=*=child filter, returns children)
- `via --match-glob "*" --via calls --match-glob "get_counts"` — callers of get_counts
  (BEFORE=*=callee filter=get_counts, AFTER=*=caller filter, returns callers)

**The old `--invert` is gone.** Queries that previously required `--invert` must be restructured:
- Old "what does main() call?": `via -mg "main" -Vca -mg "*" --invert`
- New equivalent: no direct equivalent in `--via` alone — use `--sans calls --match-glob "uncalled_*"` for the negative case, or restructure the query.

> **Note for Neo**: `invert=True` logic (select_from="t") is REMOVED. Only `select_from="s"` (subjects/sources) is used. Test all relationship queries in the existing test suite to confirm expected behavior is preserved under the new flag names.

---

### S13-1: Flag Parsing Changes

#### `flag_groups.py`
- Remove `FlagGroup.RELATIONSHIP = 'V'`
- Remove `RELATIONSHIP_FLAGS: List[Flag]`
- Remove `get_relationship_short_flags()`
- Update `get_all_flags()` to exclude relationship flags
- Keep `FlagGroup.MATCH`, `FlagGroup.TYPE`, `FlagGroup.OUTPUT`, `FlagGroup.FORMAT`

#### `relationship_types.py`
- Keep `ReferenceType` enum (values used in DB queries)
- Remove `short_flag`, `cli_short`, `from_short_flag`, `get_flag_map()` (CLI flag → enum mapping, no longer needed)
- Keep `from_value()`, `get_value_map()` (string → enum, still needed for validation)

#### `relationship_filter.py`
```python
@dataclass
class RelationshipFilter:
    relationship_type: ReferenceType
    object_pattern: str
    object_match_syntax: str = 'glob'
    object_types: List[str] = field(default_factory=list)
    is_negative: bool = False          # NEW: True for --sans (NOT EXISTS)
    result_newerthan_seconds: Optional[float] = None
    result_olderthan_seconds: Optional[float] = None
    result_stale: bool = False
    # REMOVED: invert: bool
```

#### `parser.py` — `_find_relationship_split()`
Remove:
- Loop scanning for `-Vinh`, `-Vca`, etc. (`flag_map` lookup)
- `--invert`/`-iv` extraction (`_extract_invert_flag`)
- `--ref-type` parsing

Add:
```python
def _find_relationship_split(self, args):
    value_map = ReferenceType.get_value_map()
    valid_rels = sorted(value_map.keys())

    # --via <rel> (positive)
    for i, arg in enumerate(args):
        if arg in ('--via', '-V') and i + 1 < len(args):
            rel_str = args[i + 1]
            if rel_str not in value_map:
                raise PipelineParseError(
                    f"Unknown relationship type '{rel_str}'.\n"
                    f"Valid: {', '.join(valid_rels)}"
                )
            rel_type = value_map[rel_str]
            subject_args = args[:i]
            object_args = args[i + 2:]
            return (subject_args, rel_type, object_args, False)  # is_negative=False

    # --sans <rel> (negative / NOT EXISTS)
    for i, arg in enumerate(args):
        if arg in ('--sans', '-S') and i + 1 < len(args):
            rel_str = args[i + 1]
            if rel_str not in value_map:
                raise PipelineParseError(
                    f"Unknown relationship type '{rel_str}'.\n"
                    f"Valid: {', '.join(valid_rels)}"
                )
            rel_type = value_map[rel_str]
            subject_args = args[:i]
            object_args = args[i + 2:]
            return (subject_args, rel_type, object_args, True)  # is_negative=True

    return None
```

#### `parser.py` — `_split_on_via()`
Current `_split_on_via` checks `if arg == '--via'` to determine whether it's a pipeline separator or a relationship flag. This logic needs updating:
- `--via <rel-type>` → relationship flag (keep in segment)
- `--via` alone → pipeline separator

Current code already handles this correctly by checking `if argv[i + 1] in value_map`. Keep this logic, but also handle `-V` short form.

#### `parser.py` — `--not` flag
Add `--not` to the match_parser:
```python
parser.add_argument('--not', dest='negate_pattern', action='store_true', default=False,
                    help='Negate the following match pattern')
```

But `--not` must be a pre-parse sentinel, not an argparse flag, since it must precede the match flag positionally. Parse it in `_parse_match_stage` before calling `match_parser.parse_args()`:

```python
def _extract_not_flag(self, args: List[str]) -> Tuple[List[str], bool]:
    """Extract --not from args."""
    filtered = []
    negated = False
    for i, arg in enumerate(args):
        if arg == '--not':
            # Verify next arg is a match flag
            next_args = [a for a in args[i+1:] if not a.startswith('-') or a in ('-mg', '-mr', '-ms')]
            if not any(a in ('--match-glob', '-mg', '--match-regex', '-mr', '--match-sql', '-ms')
                       for a in args[i+1:]):
                raise PipelineParseError(
                    "--not must precede a match flag (--match-glob, --match-regex, --match-sql)"
                )
            negated = True
        else:
            filtered.append(arg)
    return filtered, negated
```

Store `negated` on the parsed namespace: `parsed_args.negate_pattern = negated`.

---

### S13-2: `--sans` NOT EXISTS Execution

#### `store.py` — New method `query_negative_relationships()`

```python
def query_negative_relationships(
    self,
    relationship_type: str,
    subject_pattern: str = '*',
    object_pattern: str = '*',
    subject_type: Optional[str] = None,
    object_type: Optional[str] = None,
    match_op: MatchOp = MatchOp.GLOB,
    case_sensitive: bool = True,
    limit: int = 100,
    result_newerthan_seconds: Optional[float] = None,
    result_olderthan_seconds: Optional[float] = None,
) -> Iterator[MatchRecord]:
    """Return symbols that do NOT have the specified relationship.

    Used by --sans flag. Executes NOT EXISTS subquery.

    Example: functions with no outgoing 'calls' edges:
        query_negative_relationships('calls', subject_pattern='*',
                                     subject_type='function', object_pattern='*')
    """
    # Build main WHERE clause for subject (the anchor side)
    where_parts = []
    params = []

    if subject_pattern and subject_pattern != '*':
        col = 's.symbol_name' if case_sensitive else 'LOWER(s.symbol_name)'
        pat = subject_pattern if case_sensitive else subject_pattern.lower()
        where_parts.append(f"{col} {match_op.sql_op} ?")
        params.append(pat)

    if subject_type:
        where_parts.append("s.symbol_type = ?")
        params.append(subject_type)

    # Temporal filters on subjects
    now = time.time()
    if result_newerthan_seconds is not None:
        where_parts.append("s.mtime > ?")
        params.append(now - result_newerthan_seconds)
    if result_olderthan_seconds is not None:
        where_parts.append("s.mtime < ?")
        params.append(now - result_olderthan_seconds)

    # NOT EXISTS subquery
    not_exists_parts = ["r2.from_symbol_id = s.id",
                        "r2.reference_type = ?"]
    not_exists_params = [relationship_type]

    if object_pattern and object_pattern != '*':
        col = 't2.symbol_name' if case_sensitive else 'LOWER(t2.symbol_name)'
        pat = object_pattern if case_sensitive else object_pattern.lower()
        not_exists_parts.append(f"{col} {match_op.sql_op} ?")
        not_exists_params.append(pat)

    if object_type:
        not_exists_parts.append("t2.symbol_type = ?")
        not_exists_params.append(object_type)

    where_clause = (" AND ".join(where_parts) + " AND " if where_parts else "") + \
        f"NOT EXISTS (SELECT 1 FROM symbol_references r2 " \
        f"JOIN symbols t2 ON r2.to_symbol_id = t2.id " \
        f"WHERE {' AND '.join(not_exists_parts)})"

    all_params = params + not_exists_params + [limit]

    query = f"""
        SELECT
            s.symbol_name, s.symbol_type, s.file_path, s.line_number,
            s.byte_offset, s.byte_length, s.qualified_name, s.parent_name,
            s.mtime, NULL AS anchor_mtime, b.base_names
        FROM symbols s
        LEFT JOIN (
            SELECT sr2.from_symbol_id,
                   GROUP_CONCAT(s2.symbol_name, ',') as base_names
            FROM symbol_references sr2
            JOIN symbols s2 ON sr2.to_symbol_id = s2.id
            WHERE sr2.reference_type = 'inherits-from'
            GROUP BY sr2.from_symbol_id
        ) b ON b.from_symbol_id = s.id
        WHERE {where_clause}
        ORDER BY s.file_path, s.line_number
        LIMIT ?
    """
    cursor = self.conn.execute(query, all_params)
    for row in cursor:
        row_dict = {
            'symbol_name': row[0], 'symbol_type': row[1], 'file_path': row[2],
            'line_number': row[3], 'byte_offset': row[4], 'byte_length': row[5],
            'qualified_name': row[6], 'parent_name': row[7], 'mtime': row[8],
            'base_names': row[10],
        }
        record = self._record_factory.create_from_row(row_dict)
        record.anchor_mtime = None
        yield record
```

#### `executor.py` — Route `is_negative=True` to new method

In `_execute_relationship_query`:
```python
if rel.is_negative:
    return self._execute_negative_relationship_query(stage)
```

`_execute_negative_relationship_query` extracts subject_pattern (BEFORE `--sans`), object_pattern (AFTER `--sans`), types, and calls `db.query_negative_relationships()`.

Remove:
- `_VHAS_CONTAINER_TYPES` and `_VHAS_CONTAINER_FLAGS` validation block (the `--invert` error for DECLARES)
- The `if not rel.invert: / else:` direction-flip logic

---

### S13-3: `--not` Match Pattern Negation

In `executor.py`, `_execute_match_stage` and `_execute_filter_stage`:
```python
negated = getattr(args, 'negate_pattern', False)

## In DB query (match_stage):
results = self.db.match(..., negated=negated)

## In filter stage:
if negated:
    if not self._pattern_matches(...):
        yield record
else:
    if self._pattern_matches(...):
        yield record
```

In `store.py`, `match()`:
```python
def match(self, ..., negated: bool = False) -> Iterator[MatchRecord]:
    # Where the pattern WHERE clause is built:
    not_prefix = "NOT " if negated else ""
    where_parts.append(f"{not_prefix}{column} {match_op.sql_op} ?")
```

---

### S13-4: Help Text

Update `__main__.py` `_build_help()`:
- Remove all references to `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`, `--invert`, `-iv`, `--ref-type`
- Add `--via <rel>`, `--sans <rel>`, `--not` sections
- Include constrained `--sans` example (Smith Gate 1 requirement):
  ```
  via --match-glob "*" --type-function --sans calls --match-glob "external_*"
  ```
  ("functions that are not called by anything named `external_*`")
- List valid `<rel>` values in help
- All examples use long-form flags

---

### S13-5: Test Updates

All tests referencing `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`, `--invert`, `-iv`, `--ref-type` must be updated to use `--via`/`--sans`. Use `grep` to find all affected files:
```bash
grep -r "Vinh\|Vca\|Vimp\|Vhas\|--invert\|-iv\|ref.type" tests/ --include="*.py" -l
```

New tests required:
- `--sans calls` (uncalled functions)
- `--sans inherits-from` (classes with no parent)
- `--not --match-glob` (exclude private methods)
- Invalid `<rel>` error message
- `--not` without match flag error message
- E2E tests: verify no old flag references in Playwright test fixture commands

---

### Dependency Order

```
S13-1 (flag_groups + relationship_filter + parser)
  └─► S13-2 (executor + store: --sans NOT EXISTS)
  └─► S13-3 (executor + store: --not negation)
        └─► S13-4 (help text — after all flags exist)
              └─► S13-5 (tests — sweep all old flag names)
```

S13-2 and S13-3 independent after S13-1. Implement in one cycle: S13-1 → S13-2 → S13-3 → S13-4 → S13-5.

---

### Open Questions for Neo

**OQ-1**: The old `invert=True` path in `executor.py` returned `select_from="t"` (targets). With `--invert` removed, are there any relationship queries (other than `--sans`) that need to return targets? Check test suite for all `--invert` usage.

**OQ-2**: `_split_on_via()` in parser.py currently treats `--via <non-rel-type>` as a pipeline separator. With `-V` as the new short form for `--via`, `-V` alone (or `-V` without a relationship arg) should raise a parse error (not be treated as a separator). Ensure short form handling is correct.

**OQ-3**: For `--sans`, the `result_stale` filter is probably not meaningful (NOT EXISTS returns symbols that have NO relationship). Confirm: `--stale` with `--sans` should raise a `PipelineParseError`.


---


## SPRINT_13_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_13_GATE1_REVIEW.md`


## Sprint 13 Gate 1 Review — CLI Relationship Redesign

_Author: Smith | Date: 2026-03-23_

### Decision: APPROVED WITH NOTES

The Sprint 13 PRD directly reflects the design work in `smith.docs/CLI_DESIGN_VIA_SANS_FLAGS.md` and `smith.docs/USE_CASES_20_QUESTIONS.md`. I am the origin of this design — it reflects real user needs and gaps I documented personally. Stories are well-formed. Proceeding with two required fixes and one note for Morpheus.

---

### Required Fixes (before arch)

#### Fix 1: Resolve deprecated-alias discrepancy
`CLI_DESIGN_VIA_SANS_FLAGS.md` says: "Short aliases retained as deprecated aliases for one release."
PRD says: "No backward compatibility. Old flags are removed."

**PRD wins** — hard removal is cleaner and avoids a future cleanup sprint. Confirm: old `-V<rel>` flags produce `"unknown flag"` error, never silently pass through. The PRD AC already states this. Just ensuring we're aligned — no code should silently accept old flags.

**Action**: Morpheus ensure parser gives ArgParse `error()` for any `-V<rel>` pattern — do not alias them at all.

#### Fix 2: S13-2 `--sans` semantics need a concrete example in --help
AC says: "the result pattern after `--sans` correctly constrains the NOT EXISTS subquery". This is correct but will confuse users if not shown in `--help`. The distinction is subtle:
- `--sans calls --match-glob "*"` = "not called by anything"
- `--sans calls --match-glob "external_*"` = "not called by anything matching `external_*`"

**Action**: S13-4 `--help` must include a concrete example of constrained `--sans` (not just the unconstrained case).

---

### Notes for Morpheus

- **S13-3 `--not` position**: AC says "`--not` applies only to the match stage it precedes". Make sure the parser enforces this positionally, not just logically.
- **S13-5 scope**: E2E Playwright tests in `tests/e2e/app.spec.js` don't test CLI flags directly (they go through the API), but any relationship query tests there should use updated syntax. Include in S13-5 scope if needed.
- **`--ref-type` removal**: S13-1 AC says `--ref-type` is removed (superseded by `--via`). Confirm web API (`/api/query`) is not affected — it uses `relationship_type` JSON field, not the CLI flag. This is Out of Scope per PRD and should stay that way.

---

### Story-by-Story Sign-off

| Story | Status | Notes |
|-------|--------|-------|
| S13-1: `--via`/`--sans` flag parsing | ✅ AC clear | Short forms `-V`/`-S` confirmed |
| S13-2: `--sans` NOT EXISTS execution | ✅ AC clear | Add constrained example to --help (Fix 2) |
| S13-3: `--not` match negation | ✅ AC clear | No short form is correct |
| S13-4: --help update | ✅ AC clear | Fix 2 adds one required example |
| S13-5: Test updates | ✅ AC clear | Add E2E scope check per note above |

**Gate 1: APPROVED.** Proceed to Morpheus arch with notes above.


---


## SPRINT_13_TEST_REPORT.md

**Original Location**: `agents/smith.docs/SPRINT_13_TEST_REPORT.md`


## Sprint 13 User Test Report

_Author: Smith | Date: 2026-03-24_

### Feature Tests: PASS

| Command | Result |
|---------|--------|
| `via -mg "*" -tc --via inherits-from -mg "*" -tc` | ✅ Returns subclasses |
| `via -mg "DatabaseStore" -tc --via inherits-from -mg "*" -tc` | ✅ Empty (no subclasses) |
| `via -mg "*" -tc --sans inherits-from -mg "*" -tc` | ✅ Returns root classes |
| `via -mg "*" -tf --sans calls -mg "*" -tf` | ✅ Returns uncalled functions |
| `via --not -mg "_*" -tm` | ✅ Returns non-underscore methods |
| `via -mg "*" -tc -V inherits-from -mg "*" -tc` | ✅ Short form works |
| `via -mg "*" -tc -V foobar -mg "*"` | ✅ Error: "Unknown relationship type 'foobar'. Valid: calls, declares, imports, inherits-from, references" |
| `via -Vinh "BaseHandler" -mg "*"` | ✅ Error: old flag rejected |

### Bug: Stale Agent SKILL.md Files (HIGH PRIORITY)

**Affected files:**
- `agents/neo.docs/SKILL.md` — uses `-Vca`, `-iv`, `-Vimp`, `-Vinh`
- `agents/trin.docs/SKILL.md` — uses `-Vca`, `-iv`, `-Vinh`, `-Vr`
- `agents/morpheus.docs/SKILL.md` — uses `-Vinh`, `-iv`, `-Vimp`, `-Vr`, `-Vca`
- `agents/oracle.docs/SKILL.md` — uses `-Vr`, `-iv`, `-Vimp`, `-Vinh`
- `agents/smith.docs/USE_CASES_20_QUESTIONS.md` — uses `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`, `--invert`

**Impact**: Every agent that consults its SKILL.md for via query examples will generate broken commands that return "Error: Invalid match stage arguments". This silently breaks codebase navigation for all agents.

**Fix needed**: Update all via-query example tables in affected SKILL.md files to use new flags:
- `-Vinh` → `--via inherits-from`
- `-Vca` → `--via calls`
- `-Vimp` → `--via imports`
- `-Vr` → `--via references`
- `-Vhas` → `--via has`
- `--invert` / `-iv` → restructure query (no direct replacement)

**Routing**: @Bob *prompt — this is a SKILL.md reprompt task.


---


## SPRINT_13_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_13_TASKS.md`


## Sprint 13 Task Board: CLI Relationship Flag Redesign

_Author: Mouse | Date: 2026-03-23_
_Baseline: 1121 Python + 74 JS + 22 E2E tests_

### Phases

#### Phase 1 — Core Flag Parsing (S13-1) [4 tasks]

**Goal**: Remove old flags, add `--via`/`-V`, `--sans`/`-S`, `--not`. All existing tests still pass.

| # | Task | File(s) | Done? |
|---|------|---------|-------|
| P1-1 | Remove `RELATIONSHIP_FLAGS`, `FlagGroup.RELATIONSHIP`, `get_relationship_short_flags()` | `flag_groups.py` | ☐ |
| P1-2 | Remove `short_flag`, `cli_short`, `from_short_flag`, `get_flag_map()` from `ReferenceType` | `relationship_types.py` | ☐ |
| P1-3 | Replace `invert: bool` with `is_negative: bool` in `RelationshipFilter` | `relationship_filter.py` | ☐ |
| P1-4 | Rewrite `_find_relationship_split()`: `--via/-V`, `--sans/-S`, `--not`; remove `--invert`, `--ref-type`, `-Vinh` etc. | `parser.py` | ☐ |

Exit criteria: `make test` still passes (updated all references to `is_negative`).

---

#### Phase 2 — `--sans` NOT EXISTS + `--not` Negation (S13-2 + S13-3) [3 tasks]

**Goal**: `--sans` returns symbols with NO matching relationship. `--not` negates match pattern.

| # | Task | File(s) | Done? |
|---|------|---------|-------|
| P2-1 | Add `query_negative_relationships()` to `DatabaseStore` | `store.py` | ☐ |
| P2-2 | Add `--sans` NOT EXISTS path in executor; remove `invert` direction-flip logic | `executor.py` | ☐ |
| P2-3 | Add `negated: bool` to `DatabaseStore.match()`; handle `--not` in executor filter stages | `store.py`, `executor.py` | ☐ |

Exit criteria: `make test` passes. Manual check: `via --match-glob "*" --type-function --sans calls --match-glob "*"` returns results.

---

#### Phase 3 — Help Text + Tests (S13-4 + S13-5) [3 tasks]

**Goal**: `--help` shows no old flags. All tests updated. New tests cover `--sans`, `--not`, error messages.

| # | Task | File(s) | Done? |
|---|------|---------|-------|
| P3-1 | Update `--help` text + examples; update `mcp/schema.py` | `__main__.py`, `mcp/schema.py` | ☐ |
| P3-2 | Update all existing tests: replace `-Vinh/-Vca/-Vimp/-Vr/-Vhas/--invert/-iv/--ref-type` | `tests/` | ☐ |
| P3-3 | Add new tests: `--sans` (3 cases), `--not` (2 cases), invalid `<rel>` error, `--not` without match error | `tests/` | ☐ |

Exit criteria: `make test` passes at ≥1121 (all old tests pass + new tests added). `make test-js` passes. `make test-e2e` passes.

---

### Notes for Neo

- Start with Phase 1 — breaking changes to flag infrastructure
- Use `grep -r "Vinh\|Vca\|Vimp\|Vhas\|--invert\|-iv\|ref.type\|rel\.invert\|rel_type" via/ tests/ --include="*.py"` to find all affected code
- Remove the `_VHAS_CONTAINER_TYPES` validation block in executor.py (was for `--invert` with DECLARES)
- OQ-3: `--stale` with `--sans` should raise `PipelineParseError`
- OQ-2: Short form `-V` must not be confused with pipeline separator; test `-V inherits-from` explicitly

### Definition of Done

- `via -Vinh "Base" --match-glob "*"` produces "unknown option" error
- `via --match-glob "*" --type-function --sans calls --match-glob "*"` returns results
- `via --not --match-glob "_*" --type-method` returns results
- `via --help` contains no old flag names
- All tests pass


---
