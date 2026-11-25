# Product Backlog & Roadmap

**Author**: Cypher (PM)
**Last Updated**: 2026-11-24 (post Sprint 27 launch & retro)

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
7. **Sankey view: test-suite-to-code-area flow**
   - *Description*: Directory-level Sankey diagram showing flow from test directories/suites to the code areas (package/module) they exercise, toggleable between **coverage weight** (symbol count) and **time weight** (`test_runs.duration_seconds`).
   - *Status*: Open backlog item — parked after Sprint 27 until the hierarchy heatmap is used in practice.
8. **Lambda / anonymous-function own-leaf coverage** *(from Sprint 27 Phase 2)*
   - *Description*: Index Python lambdas as distinct symbols if standalone leaf visibility in the coverage heatmap is ever needed (currently rolled into the enclosing function/method).
   - *Status*: Open backlog item.

### UX Polish & Hygiene (from Sprint 27 Retro)
1. **Coverage Efficiency table empty-state hint** *(Smith retro, UX)*
   - *Description*: Show a concise empty-state message in `#coverage-efficiency-wrap` when zero `test_runs` rows exist, guiding the user to run `make test-coverage` (matching Heatmap's empty state).
   - *Status*: Open.
2. **Coverage heatmap legend contrast** *(Smith Cycle 1 note)*
   - *Description*: Increase contrast of the `"Adequate (100%)"` neutral-gray legend swatch so it is visually distinct against the light card background.
   - *Status*: Open.
3. **CI, security scans & lint hygiene** *(Tank / Switch / Neo retro)*
   - *Description*: Add GitHub Actions push/PR CI workflow (`test`, `test-js`, `gitleaks`), add `security-scan-python` / `security-scan-npm` targets to `Makefile`, resolve the 5 pre-existing Ruff lint warnings, untrack `node_modules/.vite/vitest/.../results.json`, and resolve/rotate Switch's pre-existing gitleaks finding at `.continue/agents/config.yaml:10`.
   - *Status*: Open.

## Recently Shipped (Archived from Backlog)
- **Sprint 26**: Unified CLI/executor registries, CTE chained relationship performance optimization, `FunctionBodyAnalyzer` unit tests, polymorphic relationship type hierarchy (`any-ref`/`upstream-ref`/`downstream-ref`, `blast`).
- **Sprint 27 (Phase 1 & Phase 2)**: Per-test coverage capture (`via coverage import-contexts`, `test_runs`), D3 zoomable-icicle intensity heatmap (LOC sizing, outlier markers, leaf drill-down), test efficiency table + static AST `Mocks` count (`mock_call_count`), `docs/SDLC.md`, PyPI `via-index 0.1.0` trusted publishing.

## Next Sprint Recommendations
- **Option A (Hygiene / Tech Debt — Tier 2)**: Resolve Sprint 27 retro items (Efficiency empty-state, legend contrast, PR CI + security scans, 5 Ruff findings, `.continue/agents/config.yaml:10`).
- **Option B (HCI Focus)**: Boolean operators in queries (`AND`, `OR`, `NOT`).
- **Option C (Developer Productivity)**: Git history integration (`git blame` / commit ranges) or Cross-project queries.
