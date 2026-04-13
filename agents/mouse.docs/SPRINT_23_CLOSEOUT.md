# Sprint 23 Closeout — Recognition Over Recall

**Persona**: Mouse  
**Date**: 2026-04-12  
**Status**: COMPLETE

## Sprint Goal

Make common VIA workflows discoverable without requiring users or agents to memorize relationship direction, output flags, or token-saving sequences.

## Delivered

### Cycle 1 — Canned Shortcut Surface

- Added/verified Sprint 23 canned shortcuts: `methods-calling`, `docs-headers`, `symbol-body`, `paged-scan`.
- Added `--show-expanded`.
- Kept unsupported `callees` and `declared-in-file` out of built-ins.
- Morpheus approved the template-expander architecture.

### Cycle 2 — Task Examples And CLI Help

- Added compact CLI `Common Tasks`.
- Added task-oriented MCP schema examples.
- Added `--show-expanded` help discoverability.
- Added uppercase `-tH` guidance.
- Kept unsupported shortcut names out of help/schema.
- Smith approved the HCI wording gate with a future wording note.

### Cycle 3 — Diagram Fallback Preservation

- MCP diagram fallback now preserves useful JSON result records when diagram output cannot render.
- Empty diagram fallback returns JSON with a clear note.
- Valid diagram output remains `output_type: "diagram"`.
- Renderer API was not broadened.

## Verification Baseline

Targeted Makefile verification passed:

- Cycle 1: 9 tests
- Cycle 2: 30 tests
- Cycle 3: 28 tests

Total targeted Sprint 23 verification baseline: **67 passing tests**.

## Reviews And Gates

- Cycle 1 UAT: `agents/trin.docs/SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18:21.md`
- Cycle 1 review: `agents/morpheus.docs/SPRINT_23_CYCLE_1_REVIEW.md`
- Cycle 2 UAT: `agents/trin.docs/SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18:27.md`
- Cycle 2 review: `agents/morpheus.docs/SPRINT_23_CYCLE_2_REVIEW.md`
- Cycle 2 HCI review: `agents/smith.docs/SPRINT_23_CYCLE_2_HCI_REVIEW.md`
- Cycle 3 UAT: `agents/trin.docs/SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18:32.md`
- Cycle 3 review: `agents/morpheus.docs/SPRINT_23_CYCLE_3_REVIEW.md`

## Follow-Up Risk

Sprint 23 exposed that runtime relationship orientation still differs from the Sprint 22 result-stage-first documentation direction. Sprint 23 handled this by leading users toward canned task shortcuts and labeling raw relationship syntax as advanced current-runtime behavior. A future sprint should reconcile the runtime and documentation model so the command structure can be simplified again.
