# Sprint 9 Beta Test Report

**Tester**: Smith (Expert User)
**Date**: 2026-03-22
**Sprint Theme**: `-Vhas`, Temporal Matching, Expanded `-Vr`, Class Anchor Fix, `-Q` Path Matching, Tech Debt Phase 1

---

## Summary

| Category | Count |
|----------|-------|
| P0 Blocker bugs | 1 |
| P1 Correctness bugs | 2 |
| P2 UX issues | 2 |
| Features passed | 5/5 |
| UAT tests | 81 passed, 1 xfailed |

**Verdict: NOT READY TO LAUNCH** — P0 and P1 bugs must be fixed first.

---

## Bugs

### S9-001 — P0: Schema migration crashes `via index` on existing databases

**Full report**: `agents/smith.docs/bugs/sprint9_bug_001_schema_migration.md`

```
CMD:  via index .   (with pre-Sprint-9 .via/index.db present)
EXPECTED: transparent migration, indexing completes
ACTUAL:   sqlite3.OperationalError: no such column: mtime
          Error: Indexing failed: no such column: mtime
```

**Root cause**: `CREATE_INDEXES` loop runs before the v5 migration in `initialize_schema()`.
`idx_symbols_mtime ON symbols(mtime)` fails because `mtime` column doesn't exist yet.

**UX Impact**: Any user upgrading from Sprint 8 → Sprint 9 is immediately blocked.
Zero recovery guidance shown. Raw SQLite exception exposed.

**Fix**: Move `idx_symbols_mtime` creation into the `current_version < 5` migration block.

---

### S9-002 — P1: `-Vr` returns every result exactly twice

```
CMD:  via -mg 'require_connection' -tf -Vr
EXPECTED: each referenced method appears once
ACTUAL:   each result is duplicated (confirmed in both list and table output)
```

Example:
```
method | initialize_schema | store.py | 95
method | initialize_schema | store.py | 95   ← duplicate
method | begin_transaction | store.py | 544
method | begin_transaction | store.py | 544  ← duplicate
```

**UX Impact**: Doubles the apparent result count. Confusing and misleading.
Likely introduced when expanding reference tracking in Story 3 — the same reference may be
stored twice (e.g. once for function-body tracking, once for the new decorator/annotation path).

**Reproduce**: `via -mg 'require_connection' -tf -Vr`

---

### S9-003 — P1: Invalid `-Vhas` container type silently returns empty

```
CMD:  via -mg '*store*' -tc -Vhas -tm   (-tc is not a valid container for -Vhas)
EXPECTED: clear error — "Error: -Vhas stage 1 received '-tc' (class), which is not a container
          type. Valid containers: file (-tF), filename (-tN)."
ACTUAL:   empty output, exit code 0
```

**Acceptance criteria (from Sprint 9 stories)**: "Stage 1 must be a valid container type; clear error if not."

This was explicitly specified and not implemented. A silent no-results is far worse than an error —
the user assumes no matches exist, not that they used the wrong flag.

---

## UX Issues

### S9-004 — P2: Raw Python tracebacks shown on all pipeline errors

Every pipeline error prints `ERROR:root:Pipeline execution failed` followed by a full Python traceback
before the clean user-facing error message. Reproducible with:

```bash
via -mg '*' -tc --newerthan badvalue
via -mg '*store*' -tN -Vhas -tc --invert
```

The clean `Error: Pipeline failed: ...` message at the bottom is good. The traceback above it is noise
that exposes implementation internals to users. This should be suppressed unless `-v` verbose flag is set.

---

### S9-005 — P2 (Known): `-th` (lowercase) not accepted; only `-tH` works

Morpheus's `SKILL.md` documents `-th` (lowercase h) for header matching.
The actual flag is `-tH` (uppercase H). `via -mg '*pattern*' -th` returns an error.

1 xfail UAT test (`TestSkillMorpheus_HeaderSearch::test_documented_flag_th_lowercase`) confirms this is a known issue.

**Options**: Add `-th` as an alias, or update Morpheus SKILL.md to use `-tH`.

---

## Feature Test Results

### Story 1: `-Vhas` Has-A Relationship ✅ (core works, S9-003 aside)

```bash
via -mg '*store*' -tN -Vhas -tc        → ✅ DatabaseStore returned
via -mg 'executor.py' -tN -Vhas -tm   → ✅ all PipelineExecutor methods returned
via -mg '*service*' -tF -Vhas -tf      → ✅ functions in service files returned
via -mg '*store*' -tN -Vhas -tc --invert  → ✅ error message correct (but traceback shown — S9-004)
```

`-Vhas` appears in `--help` under Relationship Flags with correct description. ✅
Invalid container type: **silent empty** (S9-003). ❌

---

### Story 2a: Temporal Matching ✅

```bash
via -mg '*' -tc --newerthan 1d   → ✅ 47 classes returned (recently modified)
via -mg '*' -tf --olderthan 1w   → ✅ filtered result returned
via -mg '*' -tc --newerthan badvalue  → ✅ clear error: "Invalid duration 'badvalue'. Use format: 30s, 5m, 2h, 1d, 1w."
```

Duration error message is excellent. Temporal filtering is working correctly.
`--newerthan` and `--olderthan` appear in `--help` with examples. ✅

---

### Story 3: Expanded `-Vr` Reference Tracking ⚠️ (duplicates — S9-002)

```bash
via -mg 'require_connection' -tf -Vr       → ✅ decorator references returned (but doubled)
via -mg 'Optional' -ti -Vr                 → ✅ type annotation references returned (but doubled)
```

Class base references not testable — no classes in via codebase inherit from indexed symbols
(all base classes are either built-ins or external). Not a bug.

UAT xfail tests from Story 3 (Finding 5): **all now pass**. ✅

---

### Story 4: Fix Class Anchor Bug for `-Vca` ✅

```bash
via -mg 'PipelineExecutor' -tc -Vca -tf    → ✅ returns functions called by PipelineExecutor methods
```

Previously returned empty. Now correctly expands to include methods where `parent_name = class_name`. ✅

---

### Story 5: `-Q` Full-Path Matching for File Symbols ✅

```bash
via -mg 'via/core/*' -tF -Q    → ✅ 12 files under via/core/ returned
via -mg 'via/core/*' -tF       → ✅ empty (basename-only match — correct)
```

Full-path matching with `-Q` works correctly. No regression in basename-only behavior. ✅

---

## Overall Test Environment

- `via --version`: 0.1.0
- Index: fresh after `rm .via/index.db && via index .` (required due to S9-001)
- UAT suite: 81 passed, 1 xfailed (`-th` alias)
- All Sprint 9 story UAT acceptance tests pass (xfails resolved)

---

## Launch Readiness

| Issue | Severity | Block launch? |
|-------|----------|---------------|
| S9-001: Migration crash | P0 | YES |
| S9-002: `-Vr` duplicates | P1 | YES |
| S9-003: Silent invalid container | P1 | YES |
| S9-004: Traceback noise | P2 | No — fix in Sprint 10 |
| S9-005: `-th` alias | P2 | No — fix in Sprint 10 |

**3 bugs must be fixed before `*pm launch`.**
