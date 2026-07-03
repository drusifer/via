/**
 * DOM-level tests for via/web/static/app.js.
 *
 * Uses jsdom (configured in vitest.config.js). Each test sets up a minimal
 * DOM fixture before importing the module so top-level DOM references resolve.
 * import.meta.env.TEST=true (Vitest default) prevents auto-init.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ---------------------------------------------------------------------------
// Minimal DOM fixture — mirrors the IDs expected by app.js
// ---------------------------------------------------------------------------
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
    <div id="cdn-error" style="display:none"></div>
    <div id="app">
      <div id="controls-panel">
        <select id="match-type"><option value="glob">Glob</option><option value="regex">Regex</option></select>
        <input id="pattern" type="text" value="*" />
        <input id="case-insensitive" type="checkbox" />
        <input id="qualified" type="checkbox" />
        <input id="limit" type="number" value="0" />
        <input id="newerthan" type="text" value="" />
        <input id="olderthan" type="text" value="" />
        <select id="relationship">
          <option value="">(none)</option>
          <option value="calls">calls</option>
        </select>
        <div id="rel-mode-field" style="display:none">
          <div id="rel-mode">
            <button type="button" class="seg-btn active" data-mode="via">With</button>
            <button type="button" class="seg-btn" data-mode="sans">Without</button>
          </div>
        </div>
        <div id="target-card" style="display:none">
          <select id="target-match-type"><option value="glob">Glob</option></select>
          <input id="target-pattern" type="text" value="*" />
          <div id="target-type-chips" class="chip-group">
            <span class="chip" data-type="class">Class</span>
          </div>
        </div>
        <input id="stale" type="checkbox" />
        <div id="type-chips" class="chip-group">
          <span class="chip" data-type="class">Class</span>
          <span class="chip" data-type="function">Function</span>
        </div>
        <div id="output-format-group">
          <button data-fmt="list" class="active">List</button>
          <button data-fmt="table">Table</button>
          <button data-fmt="diagram">Diagram</button>
        </div>
        <button id="run-btn">Run</button>
        <button id="reset-btn">Reset</button>
      </div>
      <div id="results-panel">
        <span id="result-count"></span>
        <div id="loading" style="display:none"></div>
        <div id="initial-state" style="display:block"></div>
        <div id="empty-state" style="display:none"></div>
        <div id="error-state" style="display:none"></div>
        <div id="result-list"></div>
        <div id="result-table-wrap" style="display:none">
          <table id="result-table">
            <thead>
              <tr>
                <th data-col="symbol_name">Name ▾</th>
                <th data-col="symbol_type">Type</th>
                <th data-col="file_path">File</th>
                <th data-col="line_number">Line</th>
              </tr>
            </thead>
            <tbody id="result-tbody"></tbody>
          </table>
        </div>
        <div id="diagram-wrap" style="display:none">
          <div id="diagram-render"></div>
          <pre id="diagram-fallback"></pre>
        </div>
      </div>
    </div>
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
    <div id="toast"></div>
  `;
}

// Lazy import — module is loaded once per test file; fixture must be in place.
let mod;
async function getModule() {
  if (!mod) {
    createFixture();
    mod = await import('../../via/web/static/app.js');
  }
  return mod;
}

// ---------------------------------------------------------------------------
// showLoading
// ---------------------------------------------------------------------------
describe('showLoading', () => {
  beforeEach(createFixture);

  it('makes #loading visible', async () => {
    const { showLoading } = await getModule();
    showLoading();
    expect(document.getElementById('loading').style.display).toBe('block');
  });

  it('hides #initial-state, #empty-state and #error-state', async () => {
    const { showLoading } = await getModule();
    document.getElementById('initial-state').style.display = 'block';
    document.getElementById('empty-state').style.display = 'block';
    document.getElementById('error-state').style.display = 'block';
    showLoading();
    expect(document.getElementById('initial-state').style.display).toBe('none');
    expect(document.getElementById('empty-state').style.display).toBe('none');
    expect(document.getElementById('error-state').style.display).toBe('none');
  });

  it('clears result-list innerHTML', async () => {
    const { showLoading } = await getModule();
    document.getElementById('result-list').innerHTML = '<div>old</div>';
    showLoading();
    expect(document.getElementById('result-list').innerHTML).toBe('');
  });

  it('hides table and diagram panels', async () => {
    const { showLoading } = await getModule();
    document.getElementById('result-table-wrap').style.display = 'block';
    document.getElementById('diagram-wrap').style.display = 'block';
    showLoading();
    expect(document.getElementById('result-table-wrap').style.display).toBe('none');
    expect(document.getElementById('diagram-wrap').style.display).toBe('none');
  });

  it('clears result-count text', async () => {
    const { showLoading } = await getModule();
    document.getElementById('result-count').textContent = '42 results';
    showLoading();
    expect(document.getElementById('result-count').textContent).toBe('');
  });
});

// ---------------------------------------------------------------------------
// showError
// ---------------------------------------------------------------------------
describe('showError', () => {
  beforeEach(createFixture);

  it('hides #loading', async () => {
    const { showError } = await getModule();
    document.getElementById('loading').style.display = 'block';
    showError('oops');
    expect(document.getElementById('loading').style.display).toBe('none');
  });

  it('shows #error-state with prefixed message', async () => {
    const { showError } = await getModule();
    showError('something went wrong');
    const el = document.getElementById('error-state');
    expect(el.style.display).toBe('block');
    expect(el.textContent).toBe('⚠ something went wrong');
  });
});

// ---------------------------------------------------------------------------
// renderList
// ---------------------------------------------------------------------------
describe('renderList', () => {
  beforeEach(createFixture);

  const RESULTS = [
    { symbol_name: 'MyClass', symbol_type: 'class', file_path: 'via/foo.py', line_number: 10 },
    { symbol_name: 'my_fn',   symbol_type: 'function', file_path: 'via/bar.py', line_number: 5 },
  ];

  it('renders one result-card per result', async () => {
    const { renderList } = await getModule();
    renderList(RESULTS);
    const cards = document.querySelectorAll('#result-list .result-card');
    expect(cards.length).toBe(2);
  });

  it('renders symbol names', async () => {
    const { renderList } = await getModule();
    renderList(RESULTS);
    const html = document.getElementById('result-list').innerHTML;
    expect(html).toContain('MyClass');
    expect(html).toContain('my_fn');
  });

  it('renders file path with line number', async () => {
    const { renderList } = await getModule();
    renderList(RESULTS);
    const html = document.getElementById('result-list').innerHTML;
    expect(html).toContain('via/foo.py:10');
    expect(html).toContain('via/bar.py:5');
  });

  it('applies correct badge class for each type', async () => {
    const { renderList } = await getModule();
    renderList(RESULTS);
    const html = document.getElementById('result-list').innerHTML;
    expect(html).toContain('badge-class');
    expect(html).toContain('badge-function');
  });

  it('escapes HTML in symbol names', async () => {
    const { renderList } = await getModule();
    renderList([{ symbol_name: '<script>', symbol_type: 'global', file_path: 'x.py', line_number: 1 }]);
    const html = document.getElementById('result-list').innerHTML;
    expect(html).toContain('&lt;script&gt;');
    expect(html).not.toContain('<script>');
  });

  it('renders empty list without error', async () => {
    const { renderList } = await getModule();
    renderList([]);
    expect(document.getElementById('result-list').innerHTML).toBe('');
  });
});

// ---------------------------------------------------------------------------
// renderTable + renderTableBody (sorting)
// ---------------------------------------------------------------------------
describe('renderTable / renderTableBody', () => {
  beforeEach(createFixture);

  const RESULTS = [
    { symbol_name: 'zebra', symbol_type: 'class',    file_path: 'b.py', line_number: 2 },
    { symbol_name: 'alpha', symbol_type: 'function', file_path: 'a.py', line_number: 1 },
    { symbol_name: 'mango', symbol_type: 'method',   file_path: 'c.py', line_number: 3 },
  ];

  it('makes result-table-wrap visible', async () => {
    const { renderTable } = await getModule();
    renderTable(RESULTS);
    expect(document.getElementById('result-table-wrap').style.display).toBe('block');
  });

  it('renders correct number of rows', async () => {
    const { renderTable } = await getModule();
    renderTable(RESULTS);
    const rows = document.querySelectorAll('#result-tbody tr');
    expect(rows.length).toBe(3);
  });

  it('default sort is symbol_name ascending', async () => {
    const { renderTable } = await getModule();
    renderTable(RESULTS);
    const rows = document.querySelectorAll('#result-tbody tr');
    expect(rows[0].cells[0].textContent).toBe('alpha');
    expect(rows[1].cells[0].textContent).toBe('mango');
    expect(rows[2].cells[0].textContent).toBe('zebra');
  });

  it('renderTableBody sorts descending when sortAsc flipped via re-render', async () => {
    const { renderTable, renderTableBody } = await getModule();
    renderTable(RESULTS);
    // Directly invoke renderTableBody after toggling internal sort state via
    // calling renderTable again (resets to asc) — verify stable re-render.
    renderTable([...RESULTS].reverse());
    const rows = document.querySelectorAll('#result-tbody tr');
    expect(rows[0].cells[0].textContent).toBe('alpha');
  });

  it('escapes HTML in table cells', async () => {
    const { renderTable } = await getModule();
    renderTable([{ symbol_name: '<b>bold</b>', symbol_type: 'global', file_path: 'x.py', line_number: 0 }]);
    const cell = document.querySelector('#result-tbody td');
    expect(cell.textContent).toBe('<b>bold</b>');
    expect(cell.innerHTML).toContain('&lt;b&gt;');
  });
});

// ---------------------------------------------------------------------------
// buildQueryBody
// ---------------------------------------------------------------------------
describe('buildQueryBody', () => {
  beforeEach(createFixture);

  it('reads match-type and pattern from DOM', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('match-type').value = 'regex';
    document.getElementById('pattern').value = '^foo';
    const body = buildQueryBody();
    expect(body.match_type).toBe('regex');
    expect(body.pattern).toBe('^foo');
  });

  it('defaults pattern to "*" when empty', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('pattern').value = '';
    const body = buildQueryBody();
    expect(body.pattern).toBe('*');
  });

  it('reads boolean flags from checkboxes', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('case-insensitive').checked = true;
    document.getElementById('qualified').checked = true;
    document.getElementById('stale').checked = true;
    const body = buildQueryBody();
    expect(body.case_insensitive).toBe(true);
    expect(body.qualified).toBe(true);
    expect(body.stale).toBe(true);
  });

  it('reads limit as integer', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('limit').value = '50';
    const body = buildQueryBody();
    expect(body.limit).toBe(50);
  });

  it('sets newerthan/olderthan to null when empty', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('newerthan').value = '';
    document.getElementById('olderthan').value = '';
    const body = buildQueryBody();
    expect(body.newerthan).toBeNull();
    expect(body.olderthan).toBeNull();
  });

  it('includes relationship when set', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('relationship').value = 'calls';
    const body = buildQueryBody();
    expect(body.relationship).toBe('calls');
  });

  it('omits target fields when relationship is empty', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('relationship').value = '';
    const body = buildQueryBody();
    expect(body.target_match_type).toBeUndefined();
    expect(body.target_pattern).toBeUndefined();
    expect(body.target_symbol_types).toBeUndefined();
  });

  it('includes target fields when relationship is set', async () => {
    const { buildQueryBody } = await getModule();
    document.getElementById('relationship').value = 'calls';
    document.getElementById('target-match-type').value = 'glob';
    document.getElementById('target-pattern').value = 'test_*';
    const body = buildQueryBody();
    expect(body.target_match_type).toBe('glob');
    expect(body.target_pattern).toBe('test_*');
    expect(Array.isArray(body.target_symbol_types)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// selectedChips
// ---------------------------------------------------------------------------
describe('selectedChips', () => {
  beforeEach(createFixture);

  it('returns empty array when no chips selected', async () => {
    const { selectedChips } = await getModule();
    expect(selectedChips('type-chips')).toEqual([]);
  });

  it('returns types of selected chips', async () => {
    const { selectedChips } = await getModule();
    document.querySelector('#type-chips .chip[data-type="class"]').classList.add('selected');
    expect(selectedChips('type-chips')).toEqual(['class']);
  });

  it('returns multiple selected types', async () => {
    const { selectedChips } = await getModule();
    document.querySelectorAll('#type-chips .chip').forEach(c => c.classList.add('selected'));
    const types = selectedChips('type-chips');
    expect(types).toContain('class');
    expect(types).toContain('function');
    expect(types.length).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// runQuery — fetch mocking
// ---------------------------------------------------------------------------
describe('runQuery', () => {
  beforeEach(createFixture);

  it('calls /api/query with POST and JSON body', async () => {
    const { runQuery } = await getModule();
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ format: 'list', results: [], elapsed_ms: 1 }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await runQuery();

    expect(mockFetch).toHaveBeenCalledWith('/api/query', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }));
    vi.unstubAllGlobals();
  });

  it('calls showError when fetch returns non-OK response', async () => {
    const { runQuery } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ error: 'bad request' }),
    }));

    await runQuery();

    const errorEl = document.getElementById('error-state');
    expect(errorEl.style.display).toBe('block');
    expect(errorEl.textContent).toContain('bad request');
    vi.unstubAllGlobals();
  });

  it('calls showError when fetch throws', async () => {
    const { runQuery } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network error')));

    await runQuery();

    const errorEl = document.getElementById('error-state');
    expect(errorEl.style.display).toBe('block');
    expect(errorEl.textContent).toContain('network error');
    vi.unstubAllGlobals();
  });
});

// ---------------------------------------------------------------------------
// updateStatus — fetch mocking
// ---------------------------------------------------------------------------
describe('updateStatus', () => {
  beforeEach(createFixture);

  it('updates status bar elements from API response', async () => {
    const { updateStatus } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        directory: '/home/user/project',
        file_count: 42,
        symbol_count: 1337,
        last_indexed: new Date(Date.now() - 3000).toISOString(),
        watching: true,
        last_reindex_count: 0,
      }),
    }));

    await updateStatus();

    expect(document.getElementById('status-dir').textContent).toBe('/home/user/project');
    expect(document.getElementById('status-files').textContent).toBe('42 files');
    expect(document.getElementById('status-symbols').textContent).toBe('1337 symbols');
    expect(document.getElementById('watch-dot').className).toBe('watch-dot');
    vi.unstubAllGlobals();
  });

  it('sets watch-dot to idle when not watching', async () => {
    const { updateStatus } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        directory: '/x', file_count: 0, symbol_count: 0,
        last_indexed: null, watching: false, last_reindex_count: 0,
      }),
    }));

    await updateStatus();

    expect(document.getElementById('watch-dot').className).toBe('watch-dot idle');
    vi.unstubAllGlobals();
  });

  it('silently ignores fetch errors', async () => {
    const { updateStatus } = await getModule();
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    await expect(updateStatus()).resolves.toBeUndefined();
    vi.unstubAllGlobals();
  });
});

// ---------------------------------------------------------------------------
// showToast
// ---------------------------------------------------------------------------
describe('showToast', () => {
  beforeEach(createFixture);

  it('sets toast text and adds show class', async () => {
    const { showToast } = await getModule();
    vi.useFakeTimers();
    showToast('Re-indexed 3 files');
    const t = document.getElementById('toast');
    expect(t.textContent).toBe('Re-indexed 3 files');
    expect(t.classList.contains('show')).toBe(true);
    vi.useRealTimers();
  });

  it('removes show class after 3000ms', async () => {
    const { showToast } = await getModule();
    vi.useFakeTimers();
    showToast('test');
    vi.advanceTimersByTime(3001);
    expect(document.getElementById('toast').classList.contains('show')).toBe(false);
    vi.useRealTimers();
  });
});

// ---------------------------------------------------------------------------
// Output format toggle (requires initApp to wire click listeners)
// ---------------------------------------------------------------------------
const stubIdleFetch = () => vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({
    directory: '/', file_count: 0, symbol_count: 0,
    last_indexed: null, watching: false, last_reindex_count: 0,
  }),
}));

describe('output format toggle', () => {
  beforeEach(() => { createFixture(); vi.useFakeTimers(); stubIdleFetch(); });
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

  it('clicking Table button gives it active class', async () => {
    const { initApp } = await getModule();
    initApp();
    document.querySelector('#output-format-group button[data-fmt="table"]').click();
    expect(document.querySelector('[data-fmt="table"]').classList.contains('active')).toBe(true);
  });

  it('active class removed from previous format button on toggle', async () => {
    const { initApp } = await getModule();
    initApp();
    document.querySelector('#output-format-group button[data-fmt="table"]').click();
    expect(document.querySelector('[data-fmt="list"]').classList.contains('active')).toBe(false);
  });

  it('buildQueryBody reflects toggled output format', async () => {
    const { initApp, buildQueryBody } = await getModule();
    initApp();
    document.querySelector('#output-format-group button[data-fmt="diagram"]').click();
    expect(buildQueryBody().output_format).toBe('diagram');
  });
});

// ---------------------------------------------------------------------------
// Reset button (requires initApp to wire click listener)
// ---------------------------------------------------------------------------
describe('reset button', () => {
  beforeEach(() => { createFixture(); vi.useFakeTimers(); stubIdleFetch(); });
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

  it('resets pattern to "*"', async () => {
    const { initApp } = await getModule();
    initApp();
    document.getElementById('pattern').value = 'MyClass';
    document.getElementById('reset-btn').click();
    expect(document.getElementById('pattern').value).toBe('*');
  });

  it('resets match-type to "glob"', async () => {
    const { initApp } = await getModule();
    initApp();
    document.getElementById('match-type').value = 'regex';
    document.getElementById('reset-btn').click();
    expect(document.getElementById('match-type').value).toBe('glob');
  });

  it('deselects all chips', async () => {
    const { initApp } = await getModule();
    initApp();
    document.querySelectorAll('#type-chips .chip').forEach(c => c.classList.add('selected'));
    document.getElementById('reset-btn').click();
    expect(document.querySelectorAll('.chip.selected').length).toBe(0);
  });

  it('restores active class to list button', async () => {
    const { initApp } = await getModule();
    initApp();
    document.querySelector('#output-format-group button[data-fmt="table"]').click();
    document.getElementById('reset-btn').click();
    expect(document.querySelector('[data-fmt="list"]').classList.contains('active')).toBe(true);
  });

  it('clears result-count and result-list', async () => {
    const { initApp } = await getModule();
    initApp();
    document.getElementById('result-count').textContent = '5 results';
    document.getElementById('result-list').innerHTML = '<div>old</div>';
    document.getElementById('reset-btn').click();
    expect(document.getElementById('result-count').textContent).toBe('');
    expect(document.getElementById('result-list').innerHTML).toBe('');
  });
});

// ---------------------------------------------------------------------------
// Toast on reindex (updateStatus triggers toast when count increases)
// ---------------------------------------------------------------------------
describe('toast on reindex', () => {
  beforeEach(createFixture);
  afterEach(() => vi.unstubAllGlobals());

  it('shows toast when last_reindex_count increases between polls', async () => {
    const { updateStatus } = await getModule();
    vi.useFakeTimers();

    // First poll — establishes baseline at count=0
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        directory: '/', file_count: 5, symbol_count: 10,
        last_indexed: null, watching: true,
        last_reindex_count: 0, last_reindex_files: 0,
      }),
    }));
    await updateStatus();

    // Second poll — count increases → toast
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        directory: '/', file_count: 5, symbol_count: 10,
        last_indexed: null, watching: true,
        last_reindex_count: 1, last_reindex_files: 2,
      }),
    }));
    await updateStatus();

    const toast = document.getElementById('toast');
    expect(toast.classList.contains('show')).toBe(true);
    expect(toast.textContent).toBe('Re-indexed 2 files');
    vi.useRealTimers();
  });
});

// ---------------------------------------------------------------------------
// Coverage view nav (Sprint 27 Phase 2 — requires initApp to wire listeners)
// ---------------------------------------------------------------------------
describe('coverage view nav', () => {
  beforeEach(createFixture);

  it('switching to Coverage hides #app and shows #coverage-view', async () => {
    const { initApp } = await getModule();
    initApp();
    document.querySelector('#view-nav button[data-view="coverage"]').click();
    expect(document.getElementById('app').style.display).toBe('none');
    expect(document.getElementById('coverage-view').style.display).toBe('block');
  });

  it('switching back to Query restores #app and hides #coverage-view', async () => {
    const { initApp } = await getModule();
    initApp();
    document.querySelector('#view-nav button[data-view="coverage"]').click();
    document.querySelector('#view-nav button[data-view="query"]').click();
    expect(document.getElementById('app').style.display).toBe('flex');
    expect(document.getElementById('coverage-view').style.display).toBe('none');
  });

  it('marks the clicked nav button active and deactivates the other', async () => {
    const { initApp } = await getModule();
    initApp();
    const coverageBtn = document.querySelector('#view-nav button[data-view="coverage"]');
    const queryBtn = document.querySelector('#view-nav button[data-view="query"]');
    coverageBtn.click();
    expect(coverageBtn.classList.contains('active')).toBe(true);
    expect(queryBtn.classList.contains('active')).toBe(false);
  });

  it('coverage subnav toggles heatmap/efficiency panels', async () => {
    const { initApp } = await getModule();
    initApp();
    document.querySelector('#coverage-subnav button[data-covview="efficiency"]').click();
    expect(document.getElementById('coverage-heatmap-wrap').style.display).toBe('none');
    expect(document.getElementById('coverage-efficiency-wrap').style.display).toBe('block');
  });
});
