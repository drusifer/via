# Sprint 16 — Task Board

**Sprint**: String Intelligence + Reusable Query Workflows
**Points**: 8pt (4 stories)
**Baseline**: 1235 passed, 1 skipped, 4 warnings
**Arch**: `morpheus.docs/SPRINT_16_ARCHITECTURE.md`
**Stories**: `cypher.docs/SPRINT_16_USER_STORIES.md`

---

## Cycle 1: Carry-Over Correctness (1pt) — S16-1

### S16-1: Fix `--slice` For OR'd Multi-Type Queries (1pt)
- [x] C1-1: Add regression test covering OR'd multi-type query with `--slice 10:20`
- [x] C1-2: Thread slice offset/limit through `_match_multiple_types` path
- [x] C1-3: Verify `total` / `shown` remain correct for paged OR queries
- [x] C1-4: Verify `--slice` + `-n` conflict behavior unchanged

**Exit criteria**: All relevant pagination tests pass. Hand to Trin UAT.

---

## Cycle 2: New Symbol Type (3pt) — S16-2

### S16-2: String Constants As `-ts` (3pt)
- [x] C2-1: Add `string_constant` symbol type and `-ts` flag support
- [x] C2-2: Extract conservative Python string constants
- [x] C2-3: Extract conservative JS/TS string constants
- [x] C2-4: Persist `string_constant` symbols with file/line/enclosing-symbol metadata
- [x] C2-5: Store `references` relationship from string constants to enclosing symbol/file anchor
- [x] C2-6: Add renderer coverage for list/table/json output
- [x] C2-7: Add unit/integration tests for Python and JS/TS fixtures

**Exit criteria**: `-ts` queries work end-to-end with stable output. Hand to Trin UAT.

---

## Cycle 3: Workflow Features (4pt) — S16-3 + S16-4

### S16-3: Coverage Import As `covered-by` (2pt)
- [x] C3-1: Add `via coverage import <coverage.xml>` CLI path
- [x] C3-2: Parse `coverage.xml` fixture and resolve covered symbols
- [x] C3-3: Store `covered-by` relationships
- [x] C3-4: Add query test for `--sans covered-by`
- [x] C3-5: Add clear error handling for malformed/unresolved coverage inputs

### S16-4: Canned Queries (`via --canned`) (2pt)
- [x] C3-6: Add canned-query loader for built-ins + `.via/canned/*.json`
- [x] C3-7: Add `--canned` and `--args` expansion path
- [x] C3-8: Ship built-ins: `unused`, `callers`, `inheritors`, `dead-docs`
- [x] C3-9: Add tests for custom canned queries, arg substitution, and invalid inputs

**Exit criteria**: Coverage import and canned queries both pass tests. Hand to Trin UAT.

---

## Post-Implementation

- [x] Trin UAT (per cycle)
- [x] Morpheus review (per cycle)
- [ ] Oracle doc groom
- [ ] Smith end-to-end user test
- [x] Cypher closeout
