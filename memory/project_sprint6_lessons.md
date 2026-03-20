---
name: Sprint 6 lessons learned
description: Key bugs and architectural lessons from Sprint 6 Watch Mode implementation
type: project
---

Two bugs found in UAT (both fixed before ship):

**Bug 1: SQLite + threading = check_same_thread=False**
`DatabaseStore.connect()` now uses `check_same_thread=False`. Required because `WatchService` runs DB ops in `threading.Timer` threads. Without it: silent failures, "0 symbols" output, nothing actually committed.

**Bug 2: Symbols table not CASCADE-linked to files**
`symbols.file_path` is a plain TEXT column. Deleting a file record does NOT cascade. Must call `delete_symbols_by_file()` + `delete_file_by_path()`. TD item: add `DatabaseStore.delete_file_completely()`.

**Why:** These are non-obvious gotchas that could recur in Sprint 7/8.

**How to apply:** When writing any new service that uses DB from a non-main thread, verify `check_same_thread=False` is set. When deleting files from index, always use the deletion triad.
