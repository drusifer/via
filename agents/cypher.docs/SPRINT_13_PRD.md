# Sprint 13 PRD: CLI Relationship Flag Redesign

_Author: Cypher | Date: 2026-03-23_
_Reference: agents/smith.docs/CLI_DESIGN_VIA_SANS_FLAGS.md_

---

## Goal

Replace the current relationship flag system (`-Vinh`, `-Vca`, `--invert`, etc.) with a clean, symmetric, self-documenting interface:

- `--via <rel>` — positive relationship filter ("has this relationship")
- `--sans <rel>` — negative relationship filter ("does NOT have this relationship")
- `--not` — match pattern negation ("symbol name does NOT match")

**No backward compatibility. The old flags are removed, not deprecated.**

---

## Out of Scope

- Web UI changes (relationship types are passed as JSON values, not CLI flags — unaffected)
- New relationship types (separate sprint)
- `--intersect` compound AND queries (separate sprint)

---

## Stories

---

### S13-1: Replace `-V<rel>` flags with `--via <rel>` / `--sans <rel>`

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

### S13-2: Implement `--sans` NOT-EXISTS execution

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

### S13-3: Implement `--not` match pattern negation

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

### S13-4: Update `--help`, examples, and error messages

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

### S13-5: Update all tests

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

## Dependency Order

```
S13-1 (flag parsing + RelationshipFilter)
  └─► S13-2 (--sans executor logic)
  └─► S13-3 (--not executor logic)
        └─► S13-4 (--help update — after all flags exist)
              └─► S13-5 (tests — after implementation complete)
```

S13-2 and S13-3 can be implemented in parallel after S13-1.

---

## Definition of Done

- All 5 stories complete
- `via --help` shows no old flags
- `via -Vinh "Base" --match-glob "*"` returns "unknown flag" error
- `via --match-glob "*" --type-function --sans calls --match-glob "*"` returns results
- `via --not --match-glob "_*" --type-method` returns results
- All tests pass
