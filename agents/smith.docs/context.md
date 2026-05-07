# Smith Context

**Last updated**: 2026-05-06

## Sprint 25 Gate 1 Review (2026-05-06)

Full review: `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`

### Verdict
- APPROVED WITH NOTES.
- Dart/Flutter stories are valuable because they give Flutter developers normal VIA structural navigation without pretending to be a Flutter analyzer.
- Keep `--lang dart` as the user-facing language filter; do not introduce a separate `--lang flutter`.
- Avoid Flutter-specific flags in Sprint 25; use existing `-tc`, `-tm`, `--via`, and output surfaces.
- Morpheus must decide constructor representation and parser dependency quality.
- Docs must explain that `import` / `export` / `part` are directive strings, not resolved package dependencies.

## Sprint 25 Gate 2 Architecture Review (2026-05-06)

Full review: `agents/smith.docs/SPRINT_25_GATE2_REVIEW.md`

### Verdict
- APPROVED.
- Architecture preserves normal VIA surfaces and avoids Flutter-specific flags.
- Cycle 0 dependency spike is UX-positive because it prevents premature claims of Dart support.
- Required implementation notes: visible language filter is `--lang dart`; docs must state no widget tree, route graph, semantic analyzer, or package dependency resolution.
- If Cycle 0 fails, team must communicate the rescope plainly.

## Sprint 25 Cycle 2 HCI Review (2026-05-06)

Full review: `agents/smith.docs/SPRINT_25_CYCLE_2_HCI_REVIEW.md`

### Verdict
- APPROVED.
- README, user guide, and MCP schema now show Dart/Flutter examples through normal VIA surfaces.
- `--lang dart` is visible; no Flutter-only flags were added.
- Docs state Dart imports/exports/parts are directive strings, not resolved package dependencies.
- Docs state VIA does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.
- Residual risk: relationship syntax remains cognitively heavy; examples are acceptable for Sprint 25.

## VIA MCP Usability Evaluation (2026-04-12)

Full report: `agents/smith.docs/VIA_MCP_Usability_Summary_2026-04-12T13:25.md`

### Verdict
- APPROVED WITH USABILITY CONCERNS.
- VIA MCP is highly useful for token-efficient agent work when the user knows the query vocabulary.
- Strongest pattern: narrow JSON/list query → fetch one symbol with `-oR` → use relationship queries for impact analysis → page with `--slice`.

### Findings
- Invalid flags currently return empty results instead of structured errors.
- The documented file `declares` quick-reference pattern returned empty results for `via/mcp/server.py`.
- Relationship direction is useful but cognitively heavy; canned `--callers` / `--callees` style affordances would reduce recall burden.
- Diagram output fallback can discard useful relationship results.
- `-oL`, `-oT`, `-oU`, and `-oR` worked and are useful token-control surfaces.
- Regex search (`-mr`) needs explicit UX/test coverage as a power-user token-saving path.
- Multi-type queries work and are useful; multi-match semantics are ambiguous and should be rejected or documented.

## Sprint 22-24 HCI/UX Gate 1 Review (2026-04-12)

Full review: `agents/smith.docs/SPRINT_22_24_GATE1_REVIEW.md`

### Verdict
- APPROVED WITH NOTES.
- Sprint 22 should focus on query confidence and error recovery before any recognition shortcuts or docs recipes.
- S22-4 file `declares` must be decided by Morpheus as implementation vs documentation correction before Neo starts.
- S23 shortcuts must use task-language names and expand into existing `--via` / `--sans` semantics.

## Sprint 22 Gate 2 Architecture Review (2026-04-12)

Full review: `agents/smith.docs/SPRINT_22_GATE2_REVIEW.md`

### Verdict
- APPROVED.
- `output_type: "error"` is approved for MCP.
- "Result stage" / "filter stage" is approved user-facing vocabulary.
- S22-4 documentation correction is approved; true "symbols declared in file" belongs in Sprint 23 shortcut design.

## Sprint 22 Final HCI Review (2026-04-12)

Full review: `agents/smith.docs/SPRINT_22_FINAL_HCI_REVIEW.md`

### Verdict
- APPROVED.
- CLI help and MCP schema now teach result-stage/filter-stage consistently.
- Error paths for invalid regex and repeated match flags provide recovery hints.
- Multi-type query remains valid.
- Misleading inverse `declares` wording is removed from the project quick reference and user-facing docs.
- Live checks used `.venv/bin/python` because system `python` lacks project dependencies in this shell.

## Sprint 23 Gate 1 Review (2026-04-12)

Full review: `agents/smith.docs/SPRINT_23_GATE1_REVIEW.md`

### Verdict
- APPROVED WITH NOTES.
- Recognition-over-recall is the correct next HCI focus after Sprint 22.
- Shortcut vocabulary must remain task-language.
- Architecture should pick one coherent shortcut surface, not multiple competing systems.
- Do not ship fake support for `callees` or `declared-in-file`; support cleanly or defer visibly.
- Every supported shortcut should show the expanded ordinary VIA query.

## Sprint 23 Gate 2 Architecture Review (2026-04-12)

Full review: `agents/smith.docs/SPRINT_23_GATE2_REVIEW.md`

### Verdict
- APPROVED.
- `--canned` is approved as the single Sprint 23 shortcut surface.
- `--show-expanded` is approved for expansion visibility.
- `declared-in-file` and `callees` should be deferred unless implemented cleanly and tested.
- Full recipes remain Sprint 24; Sprint 23 schema/help examples should stay compact.

## Sprint 23 Cycle 2 HCI Review (2026-04-12)

Full review: `agents/smith.docs/SPRINT_23_CYCLE_2_HCI_REVIEW.md`

### Verdict
- APPROVED WITH NOTES.
- `Common Tasks` improves recognition over recall.
- Help and schema use progressive disclosure: task examples first, advanced relationships later.
- Uppercase `-tH` guidance helps prevent a known user error.
- Help remains compact at 121 lines.
- Future relationship-orientation work should replace "current runtime" language with a simpler stable model.

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
