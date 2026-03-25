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
