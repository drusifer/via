# Product Backlog & Roadmap

**Author**: Cypher (PM)
**Last Updated**: 2026-11-24 (post Sprint 28 launch & retro)

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

### Security & Architecture Tech Debt (from Sprint 28 Retro & `docs/DOMAIN.md`)
1. **Resolve pre-existing gitleaks history finding** *(Switch / Tank — owner action)*
   - *Description*: Verify/rotate the key in `.continue/agents/config.yaml:10` (commit `9817f24`) and decide on git history remediation so `make security-scan-secrets` exits 0 cleanly.
   - *Status*: Open — awaits repo owner action.
2. **Domain drift remediation (optional Architecture Sprint)** *(Morpheus — tracked in `docs/DOMAIN.md` §3)*
   - *Description*: Split `DatabaseStore` (~2,240 lines) by bounded context (`Indexing` / `Querying` / `Test Quality`), align `SymbolType` enum with DB-stored `'test'`/`'external_class'`/`'module'` kinds, decouple CLI/rendering mixins from `MatchRecord`, and unify `Relation` vs `ReferenceType` in `ViaQueryBuilder` & Web API.
   - *Status*: Open backlog item (captured in `docs/DOMAIN.md`).

## Recently Shipped (Archived from Backlog)
- **Sprint 26**: Unified CLI/executor registries, CTE chained relationship performance optimization, `FunctionBodyAnalyzer` unit tests, polymorphic relationship type hierarchy (`any-ref`/`upstream-ref`/`downstream-ref`, `blast`).
- **Sprint 27 (Phase 1 & Phase 2)**: Per-test coverage capture (`via coverage import-contexts`, `test_runs`), D3 zoomable-icicle intensity heatmap (LOC sizing, outlier markers, leaf drill-down), test efficiency table + imported-module coverage & `mocks_only` signal, `docs/SDLC.md`, PyPI `via-index 0.1.0` trusted publishing.
- **Sprint 28**: `security-scan-python` / `security-scan-npm` / `security-scan` targets + 0 Python & 0 npm advisories (Vitest 5), `ruff check via/` at 0 errors, `node_modules/` gitignored & untracked, Coverage Efficiency empty-state hint & `#legend-mid` contrast, canonical `docs/DOMAIN.md`.

## Next Sprint Recommendations
- **Option A (HCI Focus)**: Boolean operators in queries (`AND`, `OR`, `NOT`).
- **Option B (Architecture Tech Debt — Tier 2)**: Address `docs/DOMAIN.md` §3 drifts (`DatabaseStore` split, `SymbolType` alignment, `MatchRecord` decoupling, unified `Relation` API).
- **Option C (Developer Productivity)**: Git history integration (`git blame` / commit ranges) or Cross-project queries.
