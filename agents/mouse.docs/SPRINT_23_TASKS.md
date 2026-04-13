# Sprint 23 Task Plan — Recognition Over Recall

**Author**: Mouse  
**Date**: 2026-04-12  
**Stories**: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`  
**Architecture**: `agents/morpheus.docs/SPRINT_23_ARCHITECTURE.md`  
**Smith Gate 1**: `agents/smith.docs/SPRINT_23_GATE1_REVIEW.md`  
**Smith Gate 2**: `agents/smith.docs/SPRINT_23_GATE2_REVIEW.md`

---

## Sprint Goal

Make common VIA workflows discoverable without requiring users or agents to memorize relationship direction, output flags, or token-saving sequences.

## Scope

### In Scope

- `--canned` built-in audit and result-stage-first corrections
- `--show-expanded` for shortcut transparency
- Compact task-oriented MCP schema examples
- Compact CLI help HCI pass
- Diagram fallback response preservation

### Out Of Scope

- Direct shortcut flags like `--callers`
- New relationship model
- Hidden inverse `declares`
- Executor strategy refactor
- Full recipe section (Sprint 24)

---

## Cycle Plan

| Cycle | Phase | Stories | Owner Flow | Status |
|-------|-------|---------|------------|--------|
| 1 | Canned Shortcut Surface | S23-1 | Neo → Trin → Morpheus | Approved |
| 2 | Task Examples And CLI Help | S23-2, S23-4 | Neo → Trin → Morpheus → Smith | Approved |
| 3 | Diagram Fallback Preservation | S23-3 | Neo → Trin → Morpheus | Approved |

---

## Cycle 1 — Canned Shortcut Surface

**Goal**: Make `--canned` the transparent recognition shortcut path.

### Neo Tasks

- [x] Audit existing built-in canned queries in `via/canned.py`.
- [x] Correct built-ins to current task-correct runtime semantics.
- [x] Add supported built-ins from architecture:
  - `callers`
  - `methods-calling`
  - `inheritors`
  - `docs-headers`
  - `symbol-body`
  - `paged-scan`
- [x] Keep or remove existing built-ins based on whether their semantics remain correct.
- [x] Add `--show-expanded` for `--canned`.
- [x] Ensure `--show-expanded` prints a copyable full `via ...` command.
- [x] Do not add runnable `callees` or `declared-in-file` unless cleanly implemented and tested.
- [x] Add focused unit tests in `tests/unit/test_sprint23_c1.py`.

### Trin Verification

- [x] Verify supported canned shortcuts return same results as expanded queries.
- [x] Verify `--show-expanded` does not execute the query.
- [x] Verify missing canned args still produce actionable errors.
- [x] Verify deferred shortcut names are not advertised as runnable built-ins.

### Morpheus Review Focus

- [x] `--canned` remains a template expander, not a second query engine.
- [x] No new relationship semantics shipped.

---

## Cycle 2 — Task Examples And CLI Help

**Goal**: Make common tasks discoverable in MCP schema and CLI help without bloat.

### Neo Tasks

- [x] Add compact "Common tasks" section to `via/mcp/schema.py`.
- [x] Include examples for:
  - find symbol
  - read symbol body
  - find callers
  - docs headers
  - regex naming search
  - multi-type search
  - paged broad scan
- [x] Update `via --help` with compact task examples.
- [x] Add uppercase `-tH` / invalid lowercase `-th` guidance.
- [x] Preserve one-matcher-per-stage guidance and use runtime-correct relationship examples.
- [x] Add tests in `tests/unit/test_sprint23_c2.py`.

### Trin Verification

- [x] Run schema/help tests through Makefile.
- [x] Smoke-check `.venv/bin/python -m via --help`.
- [x] Smoke-check `.venv/bin/python -m via mcp schema`.
- [x] Confirm help growth is at most 25 lines from Sprint 22 baseline.

### Morpheus Review Focus

- [x] Help/schema examples match approved shortcut names and expansions.
- [x] No unsupported shortcut appears as runnable.

### Smith Review Focus

- [x] Final HCI wording gate for examples and help density.

---

## Cycle 3 — Diagram Fallback Preservation

**Goal**: Preserve useful MCP data when diagram output cannot render edges.

### Neo Tasks

- [x] Update MCP output handling in `via/mcp/server.py`.
- [x] Preserve useful JSON result data for unsupported diagram shapes.
- [x] Add a clear `note` for no-relationship and unsupported-shape fallbacks.
- [x] Keep valid diagram responses as `output_type: "diagram"`.
- [x] Add tests in `tests/unit/test_sprint23_c3.py`.

### Trin Verification

- [x] Verify no-edge diagram fallback.
- [x] Verify unsupported-shape fallback preserves results.
- [x] Verify valid-edge diagram response remains diagram output.
- [x] Run existing MCP output regression tests.

### Morpheus Review Focus

- [x] Response-shape fix stays in MCP wrapper layer where possible.
- [x] Renderer API is not broadened unless necessary.

---

## Definition Of Done

- [x] All Sprint 23 acceptance criteria are met.
- [x] All cycle-level targeted tests pass through Makefile.
- [x] Smith approves Cycle 2 HCI wording.
- [x] No direct shortcut flags added.
- [x] No hidden inverse `declares` shipped.
- [ ] Sprint closeout records final targeted baseline.

---

## First Handoff

@Neo: Start Cycle 1, canned shortcut surface.
