# Smith Context

**Last updated**: 2026-03-22

## Sprint 9 Beta Test

Completed full end-to-end beta test of Sprint 9. Full report at `agents/smith.docs/SPRINT_9_BETA_TEST.md`.

### Bugs Filed
- **S9-001 (P0)**: Schema migration crashes `via index` on existing DBs — fixed and verified.
- **S9-002 (P1)**: `-Vr` duplicate results — fixed and verified.
- **S9-003 (P1)**: Invalid `-Vhas` container type silently returns empty — fixed and verified.

### UX Issues (carry-forward)
- **S9-004 (P2)**: Raw Python tracebacks shown on all pipeline errors — suppress unless `-v`. OPEN — deferred to Sprint 10 as optional 0.5pt cleanup.
- **S9-005 (P2)**: `-th` lowercase not accepted — resolved/documented.

## Sprint 10 Gate 1 Review (2026-03-22)

**Verdict**: APPROVED WITH NOTES
**Full review**: `agents/smith.docs/SPRINT_10_REVIEW.md`

### Story Verdicts
- S10-1 `--ref-type`: APPROVED — add valid-values list to `--help` text
- S10-2 `--stale`: APPROVED — add example to `--help` text
- S10-3 `prep_tldr` incremental: APPROVED — fix `os.time()` → `time.time()` in impl
- TD-WATCH-1 PathFilter: APPROVED — no notes

### Key UX Requirements for Morpheus
1. S10-1: `--help` must list `--ref-type` valid values inline
2. S10-2: `--help` for `--stale` must include one-line semantic example
3. S10-3: `prep_tldr` needs proper argparse (currently only accepts positional root)

## Known Codebase Context
- `via/db/store.py:initialize_schema()` — migration ordering resolved (Sprint 9)
- `via/pipeline/executor.py` — container type validation for DECLARES added (Sprint 9)
- `-tH` is uppercase; `-th` lowercase is not aliased (documented behavior)
- `agents/tools/prep_tldr.py` — uses `sys.argv[1]` for root; needs argparse for Sprint 10
