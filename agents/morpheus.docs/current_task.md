# Morpheus Current Task

## Sprint 19 Review
**Status**: COMPLETE
**Date**: 2026-04-08

## Deliverables
- `agents/morpheus.docs/SPRINT_19_ARCHITECTURE.md`
- `agents/morpheus.docs/SPRINT_19_REVIEW_2026-04-08T21:37.md`

## Core Recommendation
- Add a fluent `ViaQueryBuilder` that compiles into the existing pipeline stage model
- Keep builder construction separate from execution via immutable `ViaQuery` and thin `ViaRunner`
- Adopt it first in `via/web/api/query.py`, then wider programmatic use

## Next
- Hand off to Cypher for sprint closeout
