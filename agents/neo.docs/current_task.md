# Neo Current Task

**Task**: Sprint 12 Phase 1 — WebServer scaffold
**Status**: COMPLETE — awaiting Trin UAT
**Updated**: 2026-03-22

## Done
- `via/web/__init__.py` — exports WebServer
- `via/web/server.py` — WebServer (ThreadingHTTPServer, port auto-select, notify_reindex)
- `via/web/handler.py` — ViaRequestHandler (GET /api/health, CORS, route stubs)
- `via/web/api/__init__.py`
- `tests/unit/test_web_server.py` — 18 tests, all pass

## Next (after Trin UAT + Morpheus review)
- Phase 2: Status API + DatabaseStore.get_counts() / get_last_indexed_iso()
