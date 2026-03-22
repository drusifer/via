# Trin Next Steps

## Immediate: Sprint 9 Cycle 3 UAT
After Neo implements Story 1 (-Vhas / DECLARES):
- Verify `RelationshipType` → `ReferenceType` rename — all imports updated project-wide
- Verify `DECLARES` enum value added
- Verify `-Vhas`/`--via-has` flag appears in `--help`
- Verify `_store_declares_relationships()` in IndexingService:
  - file→symbol relationships: all symbols in a file declared by the filepath symbol
  - class→method/inner-class relationships
  - function→nested-function relationships
- Verify container type validation with precise error messages
- Verify `via -mg 'store.py' -tN -Vhas -tc` returns classes in store.py
- Verify `via -mg '*service*' -tF -Vhas -tf -n 0` returns functions in service files
- Verify `--invert` gives clear error message

## Sprint 9 UAT Queue
- Cycle 4: Story 2a (temporal matcher) — write UAT for `--newerthan`/`--olderthan`

## Process Rule
- Always use `make` skill (not raw Bash) for all test runs
- Baseline: 893 passed, 1 xfailed (Sprint 9 Cycle 2 complete)

## Archived Plans
- `archive/CLI_TEST_PLAN.md` - Sprint 1
- `archive/SPRINT_2_TEST_PLAN.md` - Sprint 2
- `archive/SPRINT_3_TEST_PLAN.md` - Sprint 3
- `archive/UAT_REPORT_SPRINT_4.md` - Sprint 4
- `SPRINT_5_UAT_PLAN.md` - Sprint 5 (25/25 pass)
- `tests/uat/test_sprint6_uat.py` - Sprint 6 (17/17 pass)
