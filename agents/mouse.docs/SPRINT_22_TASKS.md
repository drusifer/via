# Sprint 22 Task Plan — Query Confidence And Error Recovery

**Author**: Mouse  
**Date**: 2026-04-12  
**Stories**: `agents/cypher.docs/SPRINT_22_24_HCI_UX_USER_STORIES.md`  
**Architecture**: `agents/morpheus.docs/SPRINT_22_ARCHITECTURE.md`  
**Smith Gate 2**: `agents/smith.docs/SPRINT_22_GATE2_REVIEW.md`

---

## Sprint Goal

Make VIA query failures explicit and teach the result-stage-first command model without adding new query semantics.

**Final Status**: COMPLETE  
**Closeout**: `agents/mouse.docs/SPRINT_22_CLOSEOUT.md`

## Scope

### In Scope

- Structured MCP query errors
- Parser-level matcher validation
- Regex validation and docs
- Correct misleading `declares` quick-reference docs
- CLI/MCP help/schema updates for result stage + filter stage model

### Out Of Scope

- Relationship shortcut syntax
- Inverse `declares` / "symbols declared in file" implementation
- Executor strategy refactor
- Full CLI parser replacement

---

## Cycle Plan

| Cycle | Phase | Stories | Owner Flow | Status |
|-------|-------|---------|------------|--------|
| 1 | Error Contract | S22-1 | Neo → Trin → Morpheus | Complete |
| 2 | Stage Validation | S22-2, S22-3 | Neo → Trin → Morpheus | Complete |
| 3 | Docs/Schema Corrections | S22-4 + doc portions of S22-2/S22-3 | Neo → Trin → Morpheus → Smith | Complete |

---

## Cycle 1 — Structured Error Contract

**Goal**: Expected parse/query failures return structured MCP errors and clean CLI errors.

### Neo Tasks

- [x] Add shared query error shape, recommended `via/pipeline/errors.py`.
- [x] Update `PipelineParseError` to carry `code`, `message`, and optional `hint`.
- [x] Convert parser expected failures to structured `PipelineParseError`.
- [x] Update `via/mcp/server.py` to return:
  - `output_type: "error"`
  - `result: []`
  - `total: 0`
  - `shown: 0`
  - `error: {code, message, hint}`
- [x] Preserve internal logging for unexpected exceptions.
- [x] Add focused tests for MCP invalid args and CLI clean stderr.

### Trin Verification

- [x] Run targeted parser/MCP tests through Makefile.
- [x] Verify invalid flags do not return valid empty result shape.
- [x] Verify valid empty searches still return normal empty results.

### Morpheus Review Focus

- [x] Error contract is shared and not duplicated per caller.
- [x] No broad parser/executor refactor sneaks into Cycle 1.

---

## Cycle 2 — Match Stage And Regex Validation

**Goal**: Ambiguous match syntax and invalid regex are diagnosed before execution.

### Neo Tasks

- [x] Add one-matcher-per-stage validation before argparse stores values.
- [x] Validate result stage and relationship filter stage separately.
- [x] Preserve multi-type OR behavior (`-tf -tm -tc`).
- [x] Validate `-mr` regex patterns at parse time.
- [x] Add tests for:
  - repeated `-mg`
  - mixed `-mg` + `-mr`
  - repeated matcher in filter stage
  - valid result-stage + filter-stage matchers
  - invalid regex
  - valid regex
  - regex with no matches
  - valid multi-type query

### Trin Verification

- [x] Run targeted parser/query tests through Makefile.
- [x] Verify invalid regex is not reported as no matches.
- [x] Verify multi-type query remains a supported token-saving workflow.

### Morpheus Review Focus

- [x] "Stage" validation matches architecture.
- [x] Relationship syntax behavior is unchanged except for clearer invalid inputs.

---

## Cycle 3 — Docs, Schema, And Help Corrections

**Goal**: User-facing docs teach the correct command model and stop recommending misleading `declares` behavior.

### Neo Tasks

- [x] Update `agents/PROJECT.md` quick reference.
- [x] Update `via/mcp/schema.py` examples and description.
- [x] Update `via --help` text where relevant.
- [x] Update `docs/USER_GUIDE.md` if it contains outdated relationship or `declares` examples.
- [x] Add tests asserting:
  - result-stage/filter-stage model appears in help/schema
  - one-matcher-per-stage rule appears in help/schema
  - regex example appears
  - misleading "find all symbols in a file" quick reference is removed or corrected

### Trin Verification

- [x] Run targeted docs/schema/help tests through Makefile.
- [x] Smoke-check `via mcp schema` and `via --help` output.
- [x] Confirm docs do not imply inverse `declares` behavior.

### Morpheus Review Focus

- [x] Docs match architecture.
- [x] No new query power is introduced in docs-only cycle.

### Smith Review Focus

- [x] Confirm wording supports HCI goals:
  - first stage returns results
  - relationship stages filter results
  - invalid input is recoverable

---

## Definition Of Done

- [x] All Sprint 22 acceptance criteria are met.
- [x] All cycle-level targeted tests pass through Makefile.
- [x] Smith confirms HCI wording after Cycle 3.
- [x] No new relationship semantics shipped.
- [x] Sprint closeout records the final targeted test baseline.

---

## First Handoff

@Neo: Start Cycle 1, structured error contract.
