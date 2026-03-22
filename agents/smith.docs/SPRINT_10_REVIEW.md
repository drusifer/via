# Smith — Sprint 10 User Story Review

**Date**: 2026-03-22
**Reviewer**: Smith (Expert User)
**Stories**: agents/cypher.docs/SPRINT_10_USER_STORIES.md
**Verdict**: **APPROVED WITH NOTES**

---

## Story-by-Story Review

### S10-1: `--ref-type` CLI Unification — APPROVED ✅

**User perspective**: This is the right move. The `-V<X>` flags feel like magic runes. `--ref-type inherits-from` is self-documenting. Power users will love being able to query any reference type without memorizing flags.

**AC quality**: Solid. Error message in AC 4 is correct (lists valid values). Temporal flag combination in AC 5 is important to test.

**Note for Morpheus (not a blocker)**: The `--help` text MUST list valid `--ref-type` values inline (e.g., `choices: inherits-from, calls, imports, references, declares`). If a user has to go to the docs to find valid values, the flag is half-baked. Add this to the implementation spec.

**AC 1 example is correct**: `--ref-type declares` positioned between `-mg` stages, same as `-Vinh`. This is the right UX.

---

### S10-2: `--stale` Cross-Stage Temporal — APPROVED ✅

**User perspective**: The "find tests older than the source they test" use case is real and powerful. The flag name `--stale` is exactly right — short, semantic, immediately understandable.

**AC quality**: Good. AC 5 error message is correct. The AC 3 `MatchRecord.mtime` change is well-specified.

**Note for Morpheus (not a blocker)**: The `--help` description for `--stale` must include a one-line example showing the semantic: `"Filter: result is older than its anchor (e.g. find stale tests)"`. Without this, users won't know what "stale" means in context.

**AC 2 semantic**: Confirmed correct — `result.mtime < anchor.mtime` per pair is the right comparison.

---

### S10-3: `prep_tldr` Incremental — APPROVED WITH CORRECTION ⚠️

**User perspective**: This is a needed quality-of-life improvement. Running prep_tldr during active dev sessions and waiting for a full reindex is wasteful.

**AC quality**: Well-specified. The file-list-always-regenerated rule (AC 5) is important — good catch.

**Correction needed (not a blocker, fix in implementation)**:
- AC 1 says `os.time()` — Python doesn't have `os.time()`. The correct call is `time.time()`. Neo should use `time.time()` when writing the implementation.

**Timestamp comparison correctness**: Verified — `symbols.mtime` (OS file mtime) compared against `time.time()` at last prep_tldr run is correct. Files changed after last run will have higher mtime → they get reprocessed. ✅

**One UX request**: The `--force` flag should also be listed in `--help` (or argparse help text). The script needs proper argparse support (currently only accepts a positional `root`). Make sure the argparse help is informative.

---

### TD-WATCH-1: PathFilter Extraction — APPROVED ✅

**User perspective**: Transparent refactor. Completely invisible to end users. The `PathFilter.should_index()` API is clean and well-named.

**AC quality**: Solid. AC 5 (behavior unchanged, existing tests pass) is the correct definition of done for a refactor.

---

## Summary

| Story | Verdict | Notes |
|-------|---------|-------|
| S10-1 `--ref-type` | ✅ Approved | Add valid-values list to `--help` text |
| S10-2 `--stale` | ✅ Approved | Add example to `--help` text |
| S10-3 prep_tldr incr | ✅ Approved | Fix `os.time()` → `time.time()` in impl |
| TD-WATCH-1 PathFilter | ✅ Approved | No notes |

**Sprint scope**: 8pts is reasonable for Sprint 10. Cycle plan (1 story per cycle, smallest last) is good sequencing.

**Gate 1 result**: **APPROVED** — sprint proceeds to Morpheus architecture.

---

## Carry-forward from Sprint 9

Note to Morpheus: Sprint 9 left S9-004 open (traceback noise on errors — raw Python tracebacks shown, should suppress unless `-v`). If Neo has bandwidth, fold this into Sprint 10 as a 0.5pt cleanup. Not a blocker.
