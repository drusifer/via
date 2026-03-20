# Morpheus Current Task - Sprint 7 Architecture

## Task: Sprint 7 Architecture Design (MCP Mode)
**Status**: COMPLETE (100%)
**Date**: 2026-03-20

## Outcome: DESIGN READY

Full design in `SPRINT_7_ARCHITECTURE.md`. Three areas:
1. `JsonRenderer` + `RenderType.JSON` + `MatchRecord.to_dict()` — follows existing renderer arch exactly
2. Watch + JSON-RPC concurrency — WatchService background thread, add `handle_signals` param
3. `install`/`status`/`uninstall` polymorphism — `InstallTarget` ABC + `INSTALL_TARGETS` registry

**TD-1 from Sprint 6 must be done first** — `reindex_file()` + `delete_file_completely()` — correctness issue now that watch is always-on.

Neo implementation order specified in doc.
