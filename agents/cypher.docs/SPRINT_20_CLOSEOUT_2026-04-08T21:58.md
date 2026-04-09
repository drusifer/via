# Sprint 20 Closeout

**Author**: Cypher  
**Date**: 2026-04-08T21:58

## Outcome

Sprint 20 is SHIPPED.

### Delivered

- S20-1: shared CLI/programmatic query construction seam
- S20-2: documented `ViaQueryBuilder` and `ViaRunner` as the supported Python API

### Verification

- 50 targeted tests passed locally through `make test`
- Coverage included seam parity, pipeline parser regressions, and builder regressions

### Product Notes

- Sprint 20 reduces drift between CLI and programmatic query construction without changing query semantics
- Full CLI parser replacement and executor redesign remain explicit backlog items, not part of this ship decision
