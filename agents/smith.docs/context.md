# Smith Context

**Last updated**: 2026-04-08

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

## Via MCP Expert Review (2026-04-08)
Full report: `agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md`

### Bugs Found
- **BUG-1**: `--lang py -tF` returns empty. Use `*.py -tF` as workaround.
- **BUG-2**: `declares` relationship does not work for markdown file → headers.
- **BUG-3**: Output format flags (`-oD`, `-oR`, `-oF`) silently ignored via MCP (always returns JSON).
- **BUG-4**: Hard result cap (10), no pagination, no `total_count` in response.

### Top Wishlist
1. `--path-glob` / `--path-contains` for directory-scoped queries
2. Pagination with `total_count`
3. Mermaid output via MCP
4. `declares` for markdown sections

## Sprint 16 Reviews (2026-04-08)
- Gate 1 APPROVED: `agents/cypher.docs/SPRINT_16_USER_STORIES.md`
- Gate 2 APPROVED: `agents/morpheus.docs/SPRINT_16_ARCHITECTURE.md`
- Key guidance carried forward:
  - `-ts` must remain structured string-symbol indexing, not generic source search
  - Coverage import should start with `coverage.xml` only
  - `--canned` must stay transparent and expand into normal via queries

## Sprint 17 Gate 1 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_17_GATE1_REVIEW.md`
- Key guidance carried forward:
  - `link`, `-ts`, and `--contains` must remain distinct mental models
  - HTTP bridge must be framed as primitive call-site visibility, not automatic route resolution
  - `--contains` is approved only as symbol-body filtering that still returns symbols

## Sprint 17 Gate 2 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_17_GATE2_REVIEW.md`
- Verified implementation stayed within the approved user mental model boundaries

## Sprint 18 Gate 1 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_18_GATE1_REVIEW.md`
- Key guidance carried forward:
  - this remains a structure-only sprint with no new user-visible semantics
  - exported declarations and TS-only declarations are the highest-risk parity areas
  - executor refactors stay out of Sprint 18

## Sprint 18 Gate 2 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_18_GATE2_REVIEW.md`
- Architecture kept the sprint local to parser-internal dispatch and preserved the no-new-semantics rule

## Sprint 19 Gate 1 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_19_GATE1_REVIEW.md`
- Key guidance carried forward:
  - builder vocabulary must stay recognizable to existing via users
  - web adoption should preserve behavior exactly
  - no quiet semantics changes under the guise of API cleanup

## Sprint 19 Gate 2 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_19_GATE2_REVIEW.md`
- Architecture preserved via’s existing semantics and kept the change additive

## Sprint 20 Gate 1 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_20_GATE1_REVIEW.md`
- Key guidance carried forward:
  - keep Sprint 20 bounded to builder adoption and docs
  - CLI behavior must remain unchanged
  - docs must not overstate builder capabilities

## Sprint 20 Gate 2 Review (2026-04-08)
- APPROVED: `agents/smith.docs/SPRINT_20_GATE2_REVIEW.md`
- Architecture preserved current roles while reducing query-construction drift

## Known Codebase Context
- `via/db/store.py:initialize_schema()` — migration ordering resolved (Sprint 9)
- `via/pipeline/executor.py` — container type validation for DECLARES added (Sprint 9)
- `-tH` is uppercase; `-th` lowercase is not aliased (documented behavior)
- `agents/tools/prep_tldr.py` — uses `sys.argv[1]` for root; needs argparse for Sprint 10
