# Morpheus Next Steps

## Resume Point: Sprint 24 Cycle 2 approved

### On Resume
1. Read bottom 20 lines of `agents/CHAT.md`.
2. Check whether Mouse closed Sprint 24 or assigned another cycle.
3. If another cycle is assigned, review it against `agents/morpheus.docs/SPRINT_24_ARCHITECTURE.md`.

### Key Decisions (Sprint 24)
- Result-stage-first: first stage = returned results, --via/--sans = filters.
- Inverse relationship types: `called-by`, `inherited-by`, `imported-by`, `referenced-by`, `declared-in`, `covers`, `http-called-by`.
- Rename RelationshipFilter fields: object_* → filter_*, add `inverted: bool`.
- Swap subject/object in executor; pass `invert=True`/`invert_join=True` for inverse types.
- Canned queries are transparent argv — no hidden behavior.
- Multi-filter chaining: parser preserves ordered filters; executor applies first as primary and later filters as sequential post-filters.
- No DB schema changes.
- No backward compatibility.
- 3 cycles: inverse types + executor swap + tests → canned/MCP/help → integration/UAT/docs.
