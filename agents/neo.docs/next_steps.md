# Neo Next Steps

## Resume Point: Sprint 9 planning (stories TBD)

Sprint 8 SHIPPED (2026-03-21). 837 tests passing.

### Before Starting Sprint 9
1. Read `agents/CHAT.md` for latest assignments
2. Read `agents/cypher.docs/SPRINT_9_USER_STORIES.md` for stories
3. Ask Morpheus for architecture review if needed
4. TDD: write tests first, see red, implement, see green

### Tech Debt Available (pick up anytime)
- TD-REVIEW-2: Add `DatabaseStore.get_symbol_id()`, remove `.conn` direct access in indexing.py (small, clean)
- TD-REVIEW-4: Extract `_upsert_raw_file()`, merge 3 near-identical file-storage methods
- TD-REVIEW-5: Merge `_store_call_relationships` + `_store_reference_relationships`
- TD-WATCH-1: Extract `PathFilter` from `FileDiscovery` (low urgency)
- TD-REVIEW-1: Remove `_get_match_metadata()` from store.py (medium effort)
- TD-REVIEW-3: Simplify `delete_file_completely` (verify FK CASCADE first)
