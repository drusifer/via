# Neo Context

## Sprint 13 (2026-03-24)

### Problem Diagnosed (session 2)
Neo's Sprint 13 P1 build left 174 failures + 133 errors. Root causes found and fixed:
1. `_match_with_regex()` missing `negated` param → added with `(match is not None) != negated`
2. `test_relationship_executor.py` used old `invert=` → changed to `is_negative=`
3. Tests used `--sans` as if it meant inverted direction (like old `--invert`) — WRONG
   - `--sans` = NOT EXISTS (subjects with NO relationship)
   - Tests expecting targets (callees, parents, referenced symbols) needed rewriting
4. `--sans declares` needed "not yet supported" error
5. `--via declares` with non-container object type needed validation

### Key Design Decisions
- `--sans` = NOT EXISTS subquery (subjects with no relationship) — NOT inverted direction
- Inverted direction queries (find targets/callees/parents) are NOT supported in Sprint 13
  - "What does X inherit from?" → no direct equivalent with --via only
  - Tests for this were rewritten as "find root classes (no parent)" instead
- `--via calls` with class anchor expands to methods (subject_parent_pattern expansion)
- `--sans declares` raises ValueError "not yet supported"
- `--via declares` validates object_type must be file/class/filepath/filename

### Test Direction Convention (CRITICAL)
```
BEFORE --via/--sans = object_pattern (the anchor)
AFTER --via/--sans  = subject_pattern (what gets returned)
--via: returns subjects WITH relationship TO object
--sans: returns subjects with NO relationship TO object
```

### Test Count
- Baseline: 1121 (pre-Sprint 13)
- Current: 1115 passing (P3-3 new tests not yet added)
- Need: ≥1121 (add 6 new tests covering --sans, --not, error cases)

### Previous Sprint Context
Sprint 12: Web UI fixes (UX-001 to UX-005). 1121+74+22 tests.

## Sprint 17 (2026-04-08)

### Delivered
- `link` symbol type with markdown-first extraction
- `http-calls` primitive relationship for JS/TS outbound HTTP requests
- `--contains` as post-match symbol-body filtering

### Key Implementation Decisions
- Reused existing parser/indexer seams rather than adding a new store or query engine
- Reused symbol byte spans plus existing source-extraction utilities for `--contains`
- Reused existing relationship storage/query path for `http-calls`

## Sprint 18 (2026-04-08)

### Delivered
- Refactored JS/TS top-level symbol extraction in `via/parsers/javascript_parser.py` into module-private handler classes plus a dispatcher registry
- Reused the same dispatch path for exported declarations instead of maintaining separate export-specific extraction logic
- Added focused parity coverage in `tests/unit/test_sprint18_c1.py`

### Verification
- Targeted make-based regression suite: 96 passed

## Sprint 19 (2026-04-08)

### Delivered
- Added fluent programmatic query construction in `via/api/query_builder.py`
- Added thin execution adapter `ViaRunner` over `PipelineExecutor`
- Migrated `via/web/api/query.py` off manual `Namespace` construction

### Verification
- Targeted make-based builder and web-query regression suite: 30 passed
