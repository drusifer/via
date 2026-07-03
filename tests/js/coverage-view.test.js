/**
 * DOM-level tests for the Sprint 27 Phase 2 coverage view in
 * via/web/static/app.js — nav toggle, hierarchy heatmap (text fallback path,
 * since D3 never loads in jsdom/CI), and the test-efficiency table.
 *
 * Uses jsdom (configured in vitest.config.js). Each test sets up a minimal
 * DOM fixture before importing the module so top-level DOM references
 * resolve. import.meta.env.TEST=true (Vitest default) prevents auto-init.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

function createFixture() {
  document.body.innerHTML = `
    <div id="status-bar">
      <div class="watch-dot" id="watch-dot"></div>
      <span id="status-title">via</span>
      <span id="status-dir">—</span>
      <span id="status-files">—</span>
      <span id="status-symbols">—</span>
      <span id="status-time">—</span>
      <div id="view-nav">
        <button data-view="query" class="active">Query</button>
        <button data-view="coverage">Coverage</button>
      </div>
    </div>
    <div id="app" style="display:flex"></div>
    <div id="coverage-view" style="display:none">
      <div id="coverage-subnav">
        <button data-covview="heatmap" class="active">Heatmap</button>
        <button data-covview="efficiency">Efficiency</button>
      </div>
      <div id="coverage-heatmap-wrap">
        <div id="coverage-heatmap-svg"></div>
        <pre id="coverage-heatmap-fallback" style="display:none"></pre>
        <div id="coverage-symbol-detail" style="display:none"></div>
      </div>
      <div id="coverage-efficiency-wrap" style="display:none">
        <table id="coverage-efficiency-table">
          <thead>
            <tr>
              <th data-col="test_id">Test ▾</th>
              <th data-col="status">Status</th>
              <th data-col="duration_seconds">Duration (s)</th>
              <th data-col="covered_symbol_count">Symbols Covered</th>
              <th data-col="symbols_per_second">Symbols/sec</th>
            </tr>
          </thead>
          <tbody id="coverage-efficiency-tbody"></tbody>
        </table>
      </div>
    </div>
  `;
}

let mod;
async function getModule() {
  if (!mod) {
    createFixture();
    mod = await import('../../via/web/static/app.js');
  }
  return mod;
}

// ---------------------------------------------------------------------------
// flattenHierarchyForFallback
// ---------------------------------------------------------------------------
describe('flattenHierarchyForFallback', () => {
  beforeEach(createFixture);

  it('skips the unnamed root node', async () => {
    const { flattenHierarchyForFallback } = await getModule();
    const tree = { name: '', type: 'root', intensity_pct: 50, children: [] };
    expect(flattenHierarchyForFallback(tree)).toEqual([]);
  });

  it('includes intensity percentage in each line', async () => {
    const { flattenHierarchyForFallback } = await getModule();
    const tree = {
      name: '', type: 'root', intensity_pct: 0,
      children: [{ name: 'pkg', type: 'package', intensity_pct: 150, children: [] }],
    };
    const lines = flattenHierarchyForFallback(tree);
    expect(lines[0]).toContain('pkg');
    expect(lines[0]).toContain('150%');
  });

  it('marks outlier leaves with [OUTLIER]', async () => {
    const { flattenHierarchyForFallback } = await getModule();
    const tree = {
      name: '', type: 'root', intensity_pct: 0,
      children: [{ name: 'hot_method', type: 'method', intensity_pct: 900, is_outlier: true, children: [] }],
    };
    const lines = flattenHierarchyForFallback(tree);
    expect(lines[0]).toContain('[OUTLIER]');
  });

  it('does not mark non-outlier leaves', async () => {
    const { flattenHierarchyForFallback } = await getModule();
    const tree = {
      name: '', type: 'root', intensity_pct: 0,
      children: [{ name: 'normal', type: 'method', intensity_pct: 100, is_outlier: false, children: [] }],
    };
    const lines = flattenHierarchyForFallback(tree);
    expect(lines[0]).not.toContain('[OUTLIER]');
  });

  it('indents nested children by depth', async () => {
    const { flattenHierarchyForFallback } = await getModule();
    const tree = {
      name: '', type: 'root', intensity_pct: 0,
      children: [{
        name: 'pkg', type: 'package', intensity_pct: 100,
        children: [{ name: 'mod.py', type: 'module', intensity_pct: 100, children: [] }],
      }],
    };
    const lines = flattenHierarchyForFallback(tree);
    const indentOf = line => line.match(/^ */)[0].length;
    expect(indentOf(lines[1])).toBeGreaterThan(indentOf(lines[0]));
  });
});

// ---------------------------------------------------------------------------
// renderCoverageHeatmap — text fallback path (D3 never loads in jsdom)
// ---------------------------------------------------------------------------
describe('renderCoverageHeatmap (no-D3 fallback)', () => {
  beforeEach(createFixture);

  it('shows a message for an empty tree', async () => {
    const { renderCoverageHeatmap } = await getModule();
    renderCoverageHeatmap({ name: '', type: 'root', intensity_pct: 0, children: [] });
    const fallback = document.getElementById('coverage-heatmap-fallback');
    expect(fallback.style.display).toBe('block');
    expect(fallback.textContent).toContain('make test-coverage');
  });

  it('renders the flattened tree as fallback text', async () => {
    const { renderCoverageHeatmap } = await getModule();
    const tree = {
      name: '', type: 'root', intensity_pct: 0,
      children: [{ name: 'foo', type: 'function', intensity_pct: 200, is_outlier: false, children: [] }],
    };
    renderCoverageHeatmap(tree);
    const fallback = document.getElementById('coverage-heatmap-fallback');
    expect(fallback.style.display).toBe('block');
    expect(fallback.textContent).toContain('foo — 200%');
  });
});

// ---------------------------------------------------------------------------
// renderEfficiencyTable / renderEfficiencyTableBody
// ---------------------------------------------------------------------------
describe('renderEfficiencyTable', () => {
  beforeEach(createFixture);

  const rows = [
    { test_id: 'tests/a.py::test_1', status: 'pass', duration_seconds: 2.5, covered_symbol_count: 10, symbols_per_second: 4.0 },
    { test_id: 'tests/b.py::test_2', status: 'fail', duration_seconds: 0.5, covered_symbol_count: 20, symbols_per_second: 40.0 },
  ];

  it('renders one row per test', async () => {
    const { renderEfficiencyTable } = await getModule();
    renderEfficiencyTable(rows);
    const trs = document.querySelectorAll('#coverage-efficiency-tbody tr');
    expect(trs.length).toBe(2);
  });

  it('renders a dash for null symbols_per_second (not "Infinity")', async () => {
    const { renderEfficiencyTable } = await getModule();
    renderEfficiencyTable([
      { test_id: 't', status: 'pass', duration_seconds: 0, covered_symbol_count: 0, symbols_per_second: null },
    ]);
    const tbody = document.getElementById('coverage-efficiency-tbody');
    expect(tbody.textContent).toContain('—');
    expect(tbody.textContent).not.toContain('Infinity');
  });

  it('escapes test_id to prevent XSS', async () => {
    const { renderEfficiencyTable } = await getModule();
    renderEfficiencyTable([
      { test_id: '<img src=x onerror=alert(1)>', status: 'pass', duration_seconds: 1, covered_symbol_count: 1, symbols_per_second: 1 },
    ]);
    const tbody = document.getElementById('coverage-efficiency-tbody');
    expect(tbody.innerHTML).not.toContain('<img');
    expect(tbody.innerHTML).toContain('&lt;img');
  });
});

// Note: nav-toggle wiring (view-nav, coverage-subnav) is tested in
// dom.test.js's "coverage view nav" describe block, since initApp() wires
// the *entire* app (query controls, reset button, etc.) and needs the full
// fixture dom.test.js already maintains — duplicating that fixture here
// would just be a second copy to keep in sync.

// ---------------------------------------------------------------------------
// loadCoverageView — fetch mocking
// ---------------------------------------------------------------------------
describe('loadCoverageView', () => {
  beforeEach(createFixture);

  it('fetches both endpoints and renders both views', async () => {
    const { loadCoverageView } = await getModule();
    const tree = { name: '', type: 'root', intensity_pct: 0, children: [] };
    const mockFetch = vi.fn()
      .mockResolvedValueOnce({ json: async () => tree })
      .mockResolvedValueOnce({ json: async () => ({ results: [] }) });
    vi.stubGlobal('fetch', mockFetch);

    await loadCoverageView();

    expect(mockFetch).toHaveBeenCalledWith('/api/coverage/hierarchy');
    expect(mockFetch).toHaveBeenCalledWith('/api/coverage/test-efficiency');
    vi.unstubAllGlobals();
  });

  it('shows a fallback message when fetch fails', async () => {
    const { loadCoverageView } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    await loadCoverageView();

    const fallback = document.getElementById('coverage-heatmap-fallback');
    expect(fallback.style.display).toBe('block');
    expect(fallback.textContent).toContain('offline');
    vi.unstubAllGlobals();
  });
});

// ---------------------------------------------------------------------------
// renderSymbolDetail / showSymbolDetail — leaf drill-down (Cypher AC7)
// ---------------------------------------------------------------------------
describe('renderSymbolDetail', () => {
  beforeEach(createFixture);

  it('shows signature, path, and docstring when all present', async () => {
    const { renderSymbolDetail } = await getModule();
    renderSymbolDetail({
      qualified_name: 'mod.greet', signature: 'greet(name: str)',
      docstring: 'Say hello.', file_path: '/abs/mod.py', line_number: 3,
    });
    const panel = document.getElementById('coverage-symbol-detail');
    expect(panel.textContent).toContain('greet(name: str)');
    expect(panel.textContent).toContain('Say hello.');
    expect(panel.textContent).toContain('/abs/mod.py:3');
  });

  it('falls back to qualified_name when no signature (e.g. a class)', async () => {
    const { renderSymbolDetail } = await getModule();
    renderSymbolDetail({
      qualified_name: 'mod.Foo', signature: null,
      docstring: 'A foo.', file_path: '/abs/mod.py', line_number: 1,
    });
    const panel = document.getElementById('coverage-symbol-detail');
    expect(panel.textContent).toContain('mod.Foo');
  });

  it('shows a placeholder, not blank, when there is no docstring', async () => {
    const { renderSymbolDetail } = await getModule();
    renderSymbolDetail({
      qualified_name: 'mod.bare', signature: 'bare()',
      docstring: null, file_path: '/abs/mod.py', line_number: 1,
    });
    const panel = document.getElementById('coverage-symbol-detail');
    expect(panel.textContent).toContain('No docstring available.');
  });

  it('escapes docstring content to prevent XSS', async () => {
    const { renderSymbolDetail } = await getModule();
    renderSymbolDetail({
      qualified_name: 'mod.x', signature: 'x()',
      docstring: '<img src=x onerror=alert(1)>', file_path: '/abs/mod.py', line_number: 1,
    });
    const panel = document.getElementById('coverage-symbol-detail');
    expect(panel.innerHTML).not.toContain('<img');
    expect(panel.innerHTML).toContain('&lt;img');
  });

  it('close button hides the panel', async () => {
    const { renderSymbolDetail } = await getModule();
    renderSymbolDetail({
      qualified_name: 'mod.x', signature: 'x()',
      docstring: null, file_path: '/abs/mod.py', line_number: 1,
    });
    const panel = document.getElementById('coverage-symbol-detail');
    panel.style.display = 'block';
    document.getElementById('symbol-detail-close').click();
    expect(panel.style.display).toBe('none');
  });
});

describe('showSymbolDetail', () => {
  beforeEach(createFixture);

  it('fetches the symbol endpoint with the given id and renders it', async () => {
    const { showSymbolDetail } = await getModule();
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        qualified_name: 'mod.greet', signature: 'greet()',
        docstring: 'Hi.', file_path: '/abs/mod.py', line_number: 1,
      }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await showSymbolDetail(42);

    expect(mockFetch).toHaveBeenCalledWith('/api/coverage/symbol?id=42');
    const panel = document.getElementById('coverage-symbol-detail');
    expect(panel.style.display).toBe('block');
    expect(panel.textContent).toContain('Hi.');
    vi.unstubAllGlobals();
  });

  it('shows an error message when the fetch fails', async () => {
    const { showSymbolDetail } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));

    await showSymbolDetail(42);

    const panel = document.getElementById('coverage-symbol-detail');
    expect(panel.textContent).toContain('network down');
    vi.unstubAllGlobals();
  });

  it('shows an error message when the server returns a non-OK response', async () => {
    const { showSymbolDetail } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ error: 'symbol not found' }),
    }));

    await showSymbolDetail(999);

    const panel = document.getElementById('coverage-symbol-detail');
    expect(panel.textContent).toContain('symbol not found');
    vi.unstubAllGlobals();
  });
});
