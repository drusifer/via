# Sprint 13 Task Board: CLI Relationship Flag Redesign

_Author: Mouse | Date: 2026-03-23_
_Baseline: 1121 Python + 74 JS + 22 E2E tests_

## Phases

### Phase 1 — Core Flag Parsing (S13-1) [4 tasks]

**Goal**: Remove old flags, add `--via`/`-V`, `--sans`/`-S`, `--not`. All existing tests still pass.

| # | Task | File(s) | Done? |
|---|------|---------|-------|
| P1-1 | Remove `RELATIONSHIP_FLAGS`, `FlagGroup.RELATIONSHIP`, `get_relationship_short_flags()` | `flag_groups.py` | ☐ |
| P1-2 | Remove `short_flag`, `cli_short`, `from_short_flag`, `get_flag_map()` from `ReferenceType` | `relationship_types.py` | ☐ |
| P1-3 | Replace `invert: bool` with `is_negative: bool` in `RelationshipFilter` | `relationship_filter.py` | ☐ |
| P1-4 | Rewrite `_find_relationship_split()`: `--via/-V`, `--sans/-S`, `--not`; remove `--invert`, `--ref-type`, `-Vinh` etc. | `parser.py` | ☐ |

Exit criteria: `make test` still passes (updated all references to `is_negative`).

---

### Phase 2 — `--sans` NOT EXISTS + `--not` Negation (S13-2 + S13-3) [3 tasks]

**Goal**: `--sans` returns symbols with NO matching relationship. `--not` negates match pattern.

| # | Task | File(s) | Done? |
|---|------|---------|-------|
| P2-1 | Add `query_negative_relationships()` to `DatabaseStore` | `store.py` | ☐ |
| P2-2 | Add `--sans` NOT EXISTS path in executor; remove `invert` direction-flip logic | `executor.py` | ☐ |
| P2-3 | Add `negated: bool` to `DatabaseStore.match()`; handle `--not` in executor filter stages | `store.py`, `executor.py` | ☐ |

Exit criteria: `make test` passes. Manual check: `via --match-glob "*" --type-function --sans calls --match-glob "*"` returns results.

---

### Phase 3 — Help Text + Tests (S13-4 + S13-5) [3 tasks]

**Goal**: `--help` shows no old flags. All tests updated. New tests cover `--sans`, `--not`, error messages.

| # | Task | File(s) | Done? |
|---|------|---------|-------|
| P3-1 | Update `--help` text + examples; update `mcp/schema.py` | `__main__.py`, `mcp/schema.py` | ☐ |
| P3-2 | Update all existing tests: replace `-Vinh/-Vca/-Vimp/-Vr/-Vhas/--invert/-iv/--ref-type` | `tests/` | ☐ |
| P3-3 | Add new tests: `--sans` (3 cases), `--not` (2 cases), invalid `<rel>` error, `--not` without match error | `tests/` | ☐ |

Exit criteria: `make test` passes at ≥1121 (all old tests pass + new tests added). `make test-js` passes. `make test-e2e` passes.

---

## Notes for Neo

- Start with Phase 1 — breaking changes to flag infrastructure
- Use `grep -r "Vinh\|Vca\|Vimp\|Vhas\|--invert\|-iv\|ref.type\|rel\.invert\|rel_type" via/ tests/ --include="*.py"` to find all affected code
- Remove the `_VHAS_CONTAINER_TYPES` validation block in executor.py (was for `--invert` with DECLARES)
- OQ-3: `--stale` with `--sans` should raise `PipelineParseError`
- OQ-2: Short form `-V` must not be confused with pipeline separator; test `-V inherits-from` explicitly

## Definition of Done

- `via -Vinh "Base" --match-glob "*"` produces "unknown option" error
- `via --match-glob "*" --type-function --sans calls --match-glob "*"` returns results
- `via --not --match-glob "_*" --type-method` returns results
- `via --help` contains no old flag names
- All tests pass
