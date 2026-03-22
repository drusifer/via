# Morpheus Next Steps

## Resume Point: Sprint 9 Implementation (after Drew review of arch doc)

### Immediate on Resume
1. Read `agents/morpheus.docs/SPRINT_9_ARCHITECTURE.md` — Sprint 9 arch spec
2. Check CHAT.md for Drew's answers to the 5 open questions in the arch doc
3. Update arch doc with any Drew corrections
4. Hand off to Neo for implementation in Phase order

### Implementation Phase Order
- Phase 1: TD-REVIEW-2, TD-REVIEW-5, TD-REVIEW-3, TD-REVIEW-4, TD-REVIEW-1
- Phase 2: Stories 3, 4, 5 (no blockers)
- Phase 3: Story 1 (after TD-REVIEW-2 + TD-REVIEW-5)
- Phase 4: Story 2a (schema migration)

---

## Previous Resume Point: Sprint 9 Planning

Sprint 8 SHIPPED. Code review complete. 837 tests passing.

### Immediate on Resume
1. Read `agents/CHAT.md` for latest
2. Read `agents/morpheus.docs/CODE_REVIEW_2026_03_21.md` for tech debt backlog
3. Plan Sprint 9 stories with Cypher

### Sprint 9 Candidates
- TD-REVIEW-1: Remove `_get_match_metadata()` — DB/render decoupling (P1 priority)
- TD-REVIEW-2: Add `DatabaseStore.get_symbol_id()` — clean abstraction violation
- TD-REVIEW-4: Extract `_upsert_raw_file()` — easy DRY win
- TD-WATCH-1: Extract `PathFilter` from `FileDiscovery`
- Any new user stories from Cypher

### Architecture Invariants to Enforce
- DB layer must NOT know about rendering (column widths, render types)
- Service layer must NOT access `db_store.conn` directly
- FK CASCADE handles symbol/reference deletion — no manual deletes
- `resolve_pending_relationships()` must be called after every indexing operation

### via MCP Query Rule (VERIFIED 2026-03-21)
KNOWN anchor LEFT (before -Vxxx), `*` RIGHT (after -Vxxx).
No -iv: returns relators TO anchor. With -iv: returns what anchor relates TO.
