# Product Backlog & Roadmap

**Author**: Cypher (PM)
**Last Updated**: 2026-07-01

## Product Backlog

### Features & Capabilities
1. **Boolean operators in queries**
   - *Description*: Support boolean logic (AND, OR, NOT) across pipeline stages to allow complex filtering patterns.
   - *Status*: Open backlog item.
2. **Interactive TUI**
   - *Description*: An interactive terminal user interface (TUI) to browse, filter, and view symbol source code.
   - *Status*: Open backlog item (deferred from Sprint 2).
3. **Git integration**
   - *Description*: Query codebase based on history (`git blame`, time of last change, commit ranges).
   - *Status*: Open backlog item.
4. **Cross-project queries**
   - *Description*: Ability to register and query across multiple index databases (`.via/index.db`).
   - *Status*: Open backlog item.
5. **Broader link extraction / auto route resolution**
   - *Description*: Automatically index relationships between JavaScript/TypeScript call sites and REST route entrypoints.
   - *Status*: Open backlog item (from Sprint 17).
6. **Additional languages**
   - *Description*: AST parsers for Go, Rust, Java/Kotlin, or Swift.
   - *Status*: Open backlog item.
7. **Per-test coverage & test quality analysis**
   - *Description*: Run tests one at a time, capture per-test coverage data plus
     metadata (last run, status, duration), to enable measuring test quality and
     efficiency (redundancy, coverage-per-second, uncovered symbols despite a
     green suite). Phase 1 (capture) requirements: `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`.
     Phase 2 (analysis) intentionally unscoped until Phase 1 data exists.
   - *Status*: Open backlog item — candidate for Sprint 27, pending Morpheus feasibility (OQ-1..3).
8. **Sankey view: test-suite-to-code-area flow**
   - *Description*: A Sankey diagram showing flow from test directories/suites
     to the code areas (package/module) they exercise, aggregated at
     directory granularity (raw test-id/symbol granularity hairballs past
     ~30 nodes — same problem flagged for the earlier redundancy-view idea).
     Answers a different question than the Sprint 27 Phase 2 hierarchy
     heatmap: not "how well is this code tested" but "which parts of the
     test suite are entangled with which parts of the app" — useful before
     reorganizing tests or splitting a module. Edge thickness should be
     configurable/toggleable between two weightings: **by coverage** (count
     of symbols in that code area exercised by that test group — shows
     where test effort concentrates structurally) or **by time** (total
     `test_runs.duration_seconds` for tests in that group flowing into that
     code area — shows where test *cost* concentrates, which can surface a
     different hotspot, e.g. a small module that's expensive to test only
     because it shares a slow test directory).
   - *Status*: Open backlog item — parked until after Sprint 27 Phase 2
     (hierarchy heatmap) ships and is actually used; revisit if the
     test-organization-vs-code-structure question comes up for real.

### Technical Debt & Code Quality
1. **Unified executor strategy & CLI parser replacement**
   - *Description*: Refactor query executor and replace argparse with handler objects to unify CLI and programmatic interfaces.
   - *Status*: Open backlog item (from Sprint 18).
2. **Performance optimization**
   - *Description*: Performance polish for very large chained relationship filters.
   - *Status*: Open backlog item.
3. **`_js_body` unit tests**
   - *Description*: Add dedicated unit tests if body parsing logic continues to diverge from parser internals.
   - *Status*: Open backlog item (from Sprint 21).

## Next Sprint Recommendations
- **Option A (HCI Focus)**: Boolean operators in queries (AND, OR, NOT) to enhance composability.
- **Option B (QA Focus)**: Focused regression sprint to resolve the 3 failing tests from the current baseline.
- **Option C (UX Focus)**: Basic Interactive TUI / browse results command.
