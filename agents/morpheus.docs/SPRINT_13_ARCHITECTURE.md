# Sprint 13 Architecture: CLI Relationship Flag Redesign

_Author: Morpheus | Date: 2026-03-23_

## Summary

Replace `-V<rel>`, `--invert`, and `--ref-type` with three clean, self-documenting flags:
- `--via <rel>` / `-V <rel>` — positive relationship filter
- `--sans <rel>` / `-S <rel>` — negative (NOT EXISTS) relationship filter
- `--not` — negate immediately following match pattern

**Breaking change: no backward compatibility. Zero deprecated aliases.**

---

## Files Changing

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

## Direction Semantics (PRESERVED FROM OLD DESIGN)

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

## S13-1: Flag Parsing Changes

### `flag_groups.py`
- Remove `FlagGroup.RELATIONSHIP = 'V'`
- Remove `RELATIONSHIP_FLAGS: List[Flag]`
- Remove `get_relationship_short_flags()`
- Update `get_all_flags()` to exclude relationship flags
- Keep `FlagGroup.MATCH`, `FlagGroup.TYPE`, `FlagGroup.OUTPUT`, `FlagGroup.FORMAT`

### `relationship_types.py`
- Keep `ReferenceType` enum (values used in DB queries)
- Remove `short_flag`, `cli_short`, `from_short_flag`, `get_flag_map()` (CLI flag → enum mapping, no longer needed)
- Keep `from_value()`, `get_value_map()` (string → enum, still needed for validation)

### `relationship_filter.py`
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

### `parser.py` — `_find_relationship_split()`
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

### `parser.py` — `_split_on_via()`
Current `_split_on_via` checks `if arg == '--via'` to determine whether it's a pipeline separator or a relationship flag. This logic needs updating:
- `--via <rel-type>` → relationship flag (keep in segment)
- `--via` alone → pipeline separator

Current code already handles this correctly by checking `if argv[i + 1] in value_map`. Keep this logic, but also handle `-V` short form.

### `parser.py` — `--not` flag
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

## S13-2: `--sans` NOT EXISTS Execution

### `store.py` — New method `query_negative_relationships()`

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

### `executor.py` — Route `is_negative=True` to new method

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

## S13-3: `--not` Match Pattern Negation

In `executor.py`, `_execute_match_stage` and `_execute_filter_stage`:
```python
negated = getattr(args, 'negate_pattern', False)

# In DB query (match_stage):
results = self.db.match(..., negated=negated)

# In filter stage:
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

## S13-4: Help Text

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

## S13-5: Test Updates

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

## Dependency Order

```
S13-1 (flag_groups + relationship_filter + parser)
  └─► S13-2 (executor + store: --sans NOT EXISTS)
  └─► S13-3 (executor + store: --not negation)
        └─► S13-4 (help text — after all flags exist)
              └─► S13-5 (tests — sweep all old flag names)
```

S13-2 and S13-3 independent after S13-1. Implement in one cycle: S13-1 → S13-2 → S13-3 → S13-4 → S13-5.

---

## Open Questions for Neo

**OQ-1**: The old `invert=True` path in `executor.py` returned `select_from="t"` (targets). With `--invert` removed, are there any relationship queries (other than `--sans`) that need to return targets? Check test suite for all `--invert` usage.

**OQ-2**: `_split_on_via()` in parser.py currently treats `--via <non-rel-type>` as a pipeline separator. With `-V` as the new short form for `--via`, `-V` alone (or `-V` without a relationship arg) should raise a parse error (not be treated as a separator). Ensure short form handling is correct.

**OQ-3**: For `--sans`, the `result_stale` filter is probably not meaningful (NOT EXISTS returns symbols that have NO relationship). Confirm: `--stale` with `--sans` should raise a `PipelineParseError`.
