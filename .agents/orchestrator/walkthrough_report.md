# VIA Custom Judge Skill Walkthrough Report

**Date**: 2026-06-20  
**Author**: Project Orchestrator (`sub_orch`)  
**Objective**: Optimize the Trace Effectiveness Score (TES) for the `via` query tool to >= 90 through a closed-loop judge workflow.

---

## 1. Score History

| Iteration | Date | Trin Run ID | Smith Eval ID | Trace Effectiveness Score (TES) | Status | Key Actions Taken |
|-----------|------|-------------|---------------|--------------------------------|--------|-------------------|
| **1** | 2026-06-20 | `6a5cb982-b48d-4cd4-95ba-2141edce3bab` | `c6ee4221-83a3-476e-80ee-cae55867b541` | **85 / 100** | Fail (<90) | Identified 2 codebase bugs (BUG-1, BUG-2); cataloged by Smith; handed off to Neo. |
| **2** | 2026-06-20 | `45aef610-3e0b-4405-9ee3-db4758b88d51` | `6e688a87-61d2-458c-b79b-c3220263b932` | **100 / 100** | **Pass** (Optimal) | Verified fixes for BUG-1 & BUG-2; optimized prompts (Bob); verified all 14 gauntlet scenarios pass. |

---

## 2. Bug Findings & Resolutions

### BUG-1: Inverted Declares Validation & Type Mapping
- **Symptom**: Scenario 3 (`via -mg '*' -tf --via declares -mg 'via/core/*' -tF -Q -n 5`) returned empty output due to type mismatch and validation crash.
- **Root Cause**: Inverted declares queries mapped container types incorrectly, causing `symbol_type` checks to evaluate against member types. This mismatch resulted in 0 rows matched.
- **Resolution (Neo)**: Swapped declares writes/joins in `store.py` and implemented `_get_actual_inverted()` in the executor to dynamically detect container types, ensuring proper inversion validation and query generation.

### BUG-2: Transitive Imports Resolution
- **Symptom**: Scenarios 7 and 14 returned empty outputs because `'imports'` relationships are stored between import symbols and target modules, not directly between files.
- **Root Cause**: Filename/filepath symbols had no direct imports relationship in the DB schema, causing file-level import queries to fail.
- **Resolution (Neo)**: Implemented transitive import resolution for file-like types in `query_relationships` and `query_negative_relationships` in `via/db/store.py`. This connects `filepath` or `filename` symbols to their child import statements. Added verification unit tests under `tests/unit/test_import_relationships.py`.

---

## 3. Prompt & Skill Optimization

### Universal `via` Skill (`agents/skills/via/SKILL.md`)
- Updated syntax instructions for `--via declares` / `--via declared-in` and `--via imports` to reflect correct directions.
- Explicitly forbade all specialist personas from performing fallback file-reading (`view_file` or `cat`) or `grep` searches when looking up symbols/relationships, enforcing the exclusive use of `via`.

### Persona Instructions
- Updated specialist persona files (`morpheus.docs/SKILL.md`, `neo.docs/SKILL.md`, `oracle.docs/SKILL.md`, `trin.docs/SKILL.md`) to reference the universal skill and strictly forbid file-read/grep fallbacks.
- Ran `setup_agent_links.py` to register and synchronize these prompt refinements.

---

## 4. Verification Results

In Iteration 2:
- Trin executed the 14 gauntlet scenarios using the updated queries.
- **Scenario 3** returned function declarations in `via/core/` (correctly omitting tests).
- **Scenario 7** returned files importing `sqlite3` (correctly resolving transitive imports).
- **Scenario 14** returned test files importing `executor` (correctly resolving transitive imports).
- **Final TES**: **100/100** (Correctness: 100/100, Fallback Penalties: 0, Efficiency Bonuses: +10 capped).
- All unit and integration tests are green.

---

## 5. Conclusion
The closed-loop judge workflow is successfully complete. The query engine bugs are resolved, prompts are hardened against token-waste fallbacks, and the `via` tool achieves 100% effectiveness across all 14 gauntlet scenarios.
