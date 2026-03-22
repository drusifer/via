# Trin Next Steps

## Resume Point: Sprint 10 Cycle 2 UAT

After Neo delivers Cycle 2 (S10-2 `--stale` + S10-3 `prep_tldr`):

### S10-2 `--stale` — what to verify
1. `--stale` appears in `via --help` with example
2. `via -mg '*' -tc -Vinh -mg '*' -tc --stale` → only returns results where result.mtime < anchor.mtime
3. Old index (no mtime) → clear error message
4. `--stale` + `--newerthan` combination works
5. For test fixture: use `os.utime()` to set known mtime differences

### S10-3 `prep_tldr` — what to verify
1. First run: creates `.via/prep_tldr_last_run`, regenerates all files
2. Second run (no changes): skips all files, prints "M skipped"
3. `--force`: ignores last-run, regenerates all
4. Modified file: gets reprocessed on second run

### Cycle 3: TD-WATCH-1 — what to verify
1. All existing FileDiscovery tests pass (regression)
2. `PathFilter` class exists in `via/core/path_filter.py`
3. WatchService no longer calls `_discovery._should_include_*`

## Sprint 10 Baseline
- 931 tests after Cycle 1 UAT (S10-1 --ref-type)
- Arch: `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md`
- Task board: `agents/mouse.docs/SPRINT_10_TASKS.md`

## Process Rules
- Always use `make` skill (not raw Bash) for test runs
- Bugs go to Neo to fix, then Trin re-verifies
