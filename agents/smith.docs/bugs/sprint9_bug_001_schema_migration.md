# Bug S9-001: Schema Migration Crash on Existing Databases

**Severity**: P0 — Blocks all existing users from running `via index` after upgrade
**Filed by**: Smith
**Route to**: Trin → Neo

---

## Reproduction

```bash
# On a machine with a pre-Sprint-9 via database (schema version < 5):
via index .
```

**Error:**
```
sqlite3.OperationalError: no such column: mtime
Error: Indexing failed: no such column: mtime
```

## Expected

`via index .` completes successfully, applying the v4→v5 schema migration transparently.

## Actual

Hard crash. The index is unusable. No data loss message, no recovery guidance, no workaround shown.

## Root Cause

In `via/db/store.py` `initialize_schema()`, the execution order is:

1. CREATE tables (IF NOT EXISTS — old symbols table stays without `mtime`)
2. **`CREATE_INDEXES` loop runs** ← includes `idx_symbols_mtime ON symbols(mtime)`
3. v5 migration runs (tries to `ALTER TABLE symbols ADD COLUMN mtime`)

Step 2 crashes because `symbols.mtime` doesn't exist yet — the migration in step 3 never runs.

**Fix**: `idx_symbols_mtime` must be created inside the `current_version < 5` migration block, not in the shared `CREATE_INDEXES` loop. Or, migrations must run before `CREATE_INDEXES`.

## UX Impact

- Any user upgrading from Sprint 8 → Sprint 9 hits this immediately on first `via index`
- No helpful error message — raw SQLite exception exposed to user
- No recovery instructions in the error output
- Workaround (delete `.via/index.db`) is not documented anywhere

## Workaround (for testing)

```bash
rm .via/index.db && via index .
```
