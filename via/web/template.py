"""
HTML SPA template for the via Web UI.

TLDR:
    HTML_TEMPLATE is a single-file SPA served at GET /. Uses Material Design 3
    color tokens via Google Fonts/Icons CDN. Mermaid.js for diagram rendering.
    No build step required. All JS is vanilla ES2022 modules inline.
    CDN load failure shows a visible error banner instead of a blank page.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>via — Code Index</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap"
        onerror="document.getElementById('cdn-error').style.display='block'">
  <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
  <style>
    /* ------------------------------------------------------------------ */
    /* MD3 Colour Tokens (light scheme)                                    */
    /* ------------------------------------------------------------------ */
    :root {
      --md-sys-color-primary: #1a73e8;
      --md-sys-color-on-primary: #ffffff;
      --md-sys-color-primary-container: #d3e3fd;
      --md-sys-color-surface: #f8f9fa;
      --md-sys-color-surface-variant: #e8eaed;
      --md-sys-color-on-surface: #202124;
      --md-sys-color-on-surface-variant: #5f6368;
      --md-sys-color-outline: #dadce0;
      --md-sys-color-error: #d93025;
      --md-sys-color-success: #1e8e3e;
      --md-elevation-1: 0 1px 2px rgba(0,0,0,.1), 0 1px 3px rgba(0,0,0,.08);
      --md-elevation-2: 0 1px 2px rgba(0,0,0,.1), 0 2px 6px rgba(0,0,0,.1);
      --chip-fn: #1e8e3e; --chip-class: #1a73e8; --chip-method: #7b1fa2;
      --chip-import: #e8710a; --chip-global: #5f6368;
      --chip-filepath: #0d652d; --chip-filename: #137333;
      --chip-header: #c62828;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Roboto', sans-serif;
      background: var(--md-sys-color-surface);
      color: var(--md-sys-color-on-surface);
      min-height: 100vh;
    }

    /* ------------------------------------------------------------------ */
    /* Status bar                                                           */
    /* ------------------------------------------------------------------ */
    #status-bar {
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
      padding: 8px 16px;
      display: flex;
      align-items: center;
      gap: 16px;
      font-size: 13px;
      min-height: 40px;
    }
    #status-bar .watch-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: #69f0ae; flex-shrink: 0;
    }
    #status-bar .watch-dot.idle { background: #9aa0a6; }
    #status-title { font-weight: 500; font-size: 15px; margin-right: auto; }

    /* CDN error banner */
    #cdn-error {
      display: none;
      background: #fce8e6;
      color: var(--md-sys-color-error);
      padding: 10px 16px;
      font-size: 13px;
      border-bottom: 1px solid #f5c6c3;
    }

    /* Toast */
    #toast {
      position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
      background: #323232; color: #fff;
      padding: 12px 20px; border-radius: 8px;
      font-size: 14px; z-index: 9999;
      opacity: 0; transition: opacity .3s;
      pointer-events: none;
    }
    #toast.show { opacity: 1; }

    /* ------------------------------------------------------------------ */
    /* Main layout                                                          */
    /* ------------------------------------------------------------------ */
    #app {
      display: flex;
      gap: 0;
      height: calc(100vh - 40px);
    }
    #controls-panel {
      width: 340px;
      min-width: 280px;
      flex-shrink: 0;
      overflow-y: auto;
      padding: 16px;
      border-right: 1px solid var(--md-sys-color-outline);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    #results-panel {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
    }

    /* ------------------------------------------------------------------ */
    /* Cards                                                               */
    /* ------------------------------------------------------------------ */
    .card {
      background: #fff;
      border-radius: 12px;
      padding: 16px;
      box-shadow: var(--md-elevation-1);
    }
    .card h3 {
      font-size: 13px;
      font-weight: 500;
      color: var(--md-sys-color-on-surface-variant);
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 12px;
    }

    /* ------------------------------------------------------------------ */
    /* Form controls                                                        */
    /* ------------------------------------------------------------------ */
    .field { margin-bottom: 12px; }
    .field:last-child { margin-bottom: 0; }
    label {
      display: block;
      font-size: 12px;
      color: var(--md-sys-color-on-surface-variant);
      margin-bottom: 4px;
    }
    select, input[type="text"], input[type="number"] {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid var(--md-sys-color-outline);
      border-radius: 8px;
      font-size: 14px;
      font-family: inherit;
      background: #fff;
      color: var(--md-sys-color-on-surface);
      outline: none;
      transition: border-color .15s;
    }
    select:focus, input:focus { border-color: var(--md-sys-color-primary); }

    /* Toggle row */
    .toggle-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 14px;
      padding: 4px 0;
    }
    .toggle {
      position: relative; width: 36px; height: 20px;
      flex-shrink: 0;
    }
    .toggle input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; inset: 0;
      background: var(--md-sys-color-outline);
      border-radius: 10px;
      cursor: pointer;
      transition: background .2s;
    }
    .slider::before {
      content: ''; position: absolute;
      width: 14px; height: 14px;
      left: 3px; top: 3px;
      border-radius: 50%;
      background: #fff;
      transition: transform .2s;
    }
    .toggle input:checked + .slider { background: var(--md-sys-color-primary); }
    .toggle input:checked + .slider::before { transform: translateX(16px); }

    /* Symbol type chip group */
    .chip-group {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .chip {
      padding: 4px 10px;
      border-radius: 16px;
      font-size: 12px;
      font-weight: 500;
      border: 1.5px solid var(--md-sys-color-outline);
      background: transparent;
      color: var(--md-sys-color-on-surface-variant);
      cursor: pointer;
      transition: all .15s;
      user-select: none;
    }
    .chip.selected {
      background: var(--md-sys-color-primary-container);
      border-color: var(--md-sys-color-primary);
      color: var(--md-sys-color-primary);
    }

    /* Output format button group */
    .btn-group {
      display: flex;
      gap: 0;
      border: 1px solid var(--md-sys-color-outline);
      border-radius: 8px;
      overflow: hidden;
    }
    .btn-group button {
      flex: 1;
      padding: 8px;
      border: none;
      background: transparent;
      font-size: 13px;
      font-family: inherit;
      cursor: pointer;
      color: var(--md-sys-color-on-surface-variant);
      border-right: 1px solid var(--md-sys-color-outline);
      transition: background .15s, color .15s;
    }
    .btn-group button:last-child { border-right: none; }
    .btn-group button.active {
      background: var(--md-sys-color-primary-container);
      color: var(--md-sys-color-primary);
      font-weight: 500;
    }

    /* Action buttons */
    .actions { display: flex; gap: 8px; margin-top: 4px; }
    .btn-primary {
      flex: 1;
      padding: 10px;
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
      border: none;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      font-family: inherit;
      cursor: pointer;
      transition: opacity .15s;
    }
    .btn-primary:hover { opacity: .9; }
    .btn-primary:disabled { opacity: .5; cursor: not-allowed; }
    .btn-secondary {
      padding: 10px 16px;
      background: transparent;
      color: var(--md-sys-color-primary);
      border: 1px solid var(--md-sys-color-primary);
      border-radius: 8px;
      font-size: 14px;
      font-family: inherit;
      cursor: pointer;
    }

    /* Relationship target panel (hidden unless rel selected) */
    #target-card { display: none; }

    /* ------------------------------------------------------------------ */
    /* Results                                                             */
    /* ------------------------------------------------------------------ */
    #results-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    #results-header h2 { font-size: 15px; font-weight: 500; }
    #result-count { font-size: 13px; color: var(--md-sys-color-on-surface-variant); }

    /* Loading */
    #loading {
      display: none;
      text-align: center;
      padding: 40px;
      color: var(--md-sys-color-on-surface-variant);
    }
    .spinner {
      width: 32px; height: 32px;
      border: 3px solid var(--md-sys-color-outline);
      border-top-color: var(--md-sys-color-primary);
      border-radius: 50%;
      animation: spin .7s linear infinite;
      margin: 0 auto 12px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Empty / error state */
    #empty-state, #error-state {
      display: none;
      padding: 40px;
      text-align: center;
      color: var(--md-sys-color-on-surface-variant);
    }
    #error-state { color: var(--md-sys-color-error); }

    /* Result list */
    #result-list { display: flex; flex-direction: column; gap: 8px; }

    .result-card {
      background: #fff;
      border-radius: 10px;
      padding: 12px 16px;
      box-shadow: var(--md-elevation-1);
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }
    .result-card .type-badge {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 10px;
      color: #fff;
      flex-shrink: 0;
      margin-top: 2px;
      text-transform: uppercase;
    }
    .result-card .name {
      font-weight: 500;
      font-size: 14px;
      font-family: 'Roboto Mono', monospace;
    }
    .result-card .path {
      font-size: 12px;
      color: var(--md-sys-color-on-surface-variant);
      margin-top: 2px;
      font-family: 'Roboto Mono', monospace;
    }

    /* Table */
    #result-table-wrap { overflow-x: auto; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    thead { position: sticky; top: 0; background: var(--md-sys-color-surface-variant); }
    th {
      padding: 10px 12px;
      text-align: left;
      font-weight: 500;
      color: var(--md-sys-color-on-surface-variant);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }
    th:hover { background: var(--md-sys-color-outline); }
    td {
      padding: 8px 12px;
      border-bottom: 1px solid var(--md-sys-color-outline);
      font-family: 'Roboto Mono', monospace;
      font-size: 12px;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: var(--md-sys-color-surface-variant); }

    /* Diagram */
    #diagram-wrap { background: #fff; border-radius: 10px; padding: 16px; }
    #diagram-fallback {
      display: none;
      background: var(--md-sys-color-surface-variant);
      padding: 16px;
      border-radius: 8px;
      font-family: 'Roboto Mono', monospace;
      font-size: 12px;
      white-space: pre-wrap;
      overflow-x: auto;
    }

    /* Type badge colours */
    .badge-function { background: var(--chip-fn); }
    .badge-class    { background: var(--chip-class); }
    .badge-method   { background: var(--chip-method); }
    .badge-import   { background: var(--chip-import); }
    .badge-global   { background: var(--chip-global); }
    .badge-filepath { background: var(--chip-filepath); }
    .badge-filename { background: var(--chip-filename); }
    .badge-header   { background: var(--chip-header); }

    @media (max-width: 700px) {
      #app { flex-direction: column; height: auto; }
      #controls-panel { width: 100%; border-right: none; border-bottom: 1px solid var(--md-sys-color-outline); }
    }
  </style>
</head>
<body>

<!-- CDN error banner -->
<div id="cdn-error">
  ⚠ Could not load fonts from Google CDN — UI may look different. Functionality is unaffected.
</div>

<!-- Status bar -->
<div id="status-bar">
  <div class="watch-dot" id="watch-dot"></div>
  <span id="status-title">via</span>
  <span id="status-dir">—</span>
  <span id="status-files">— files</span>
  <span id="status-symbols">— symbols</span>
  <span id="status-time">—</span>
</div>

<div id="app">
  <!-- ---------------------------------------------------------------- -->
  <!-- Controls panel                                                    -->
  <!-- ---------------------------------------------------------------- -->
  <div id="controls-panel">

    <!-- Match card -->
    <div class="card">
      <h3>Match</h3>
      <div class="field">
        <label for="match-type">Match type</label>
        <select id="match-type">
          <option value="glob">Glob (* ?)</option>
          <option value="regex">Regex</option>
          <option value="sql">SQL LIKE (% _)</option>
        </select>
      </div>
      <div class="field">
        <label for="pattern">Pattern</label>
        <input type="text" id="pattern" placeholder="*service*" value="*">
      </div>
      <div class="toggle-row">
        <span>Case-insensitive (-I)</span>
        <label class="toggle"><input type="checkbox" id="case-insensitive"><span class="slider"></span></label>
      </div>
      <div class="toggle-row" style="margin-top:8px">
        <span>Qualified names (-Q)</span>
        <label class="toggle"><input type="checkbox" id="qualified"><span class="slider"></span></label>
      </div>
    </div>

    <!-- Symbol type card -->
    <div class="card">
      <h3>Symbol Types</h3>
      <div class="chip-group" id="type-chips">
        <span class="chip" data-type="class">Class</span>
        <span class="chip" data-type="function">Function</span>
        <span class="chip" data-type="method">Method</span>
        <span class="chip" data-type="import">Import</span>
        <span class="chip" data-type="global">Global</span>
        <span class="chip" data-type="filepath">File Path</span>
        <span class="chip" data-type="filename">File Name</span>
        <span class="chip" data-type="header">MD Header</span>
      </div>
    </div>

    <!-- Filters card -->
    <div class="card">
      <h3>Filters</h3>
      <div class="field">
        <label for="limit">Limit (0 = all)</label>
        <input type="number" id="limit" min="0" value="0" placeholder="0">
      </div>
      <div class="field">
        <label for="newerthan">Newer than (e.g. 1h, 2d)</label>
        <input type="text" id="newerthan" placeholder="1h">
      </div>
      <div class="field">
        <label for="olderthan">Older than (e.g. 2d)</label>
        <input type="text" id="olderthan" placeholder="2d">
      </div>
    </div>

    <!-- Relationship card -->
    <div class="card">
      <h3>Relationship</h3>
      <div class="field">
        <label for="relationship">Type</label>
        <select id="relationship">
          <option value="">(none)</option>
          <option value="inherits-from">inherits-from</option>
          <option value="calls">calls</option>
          <option value="imports">imports</option>
          <option value="references">references</option>
          <option value="has">has (declares)</option>
          <option value="declares">declares</option>
        </select>
      </div>
      <div class="toggle-row">
        <span>Invert direction (--invert)</span>
        <label class="toggle"><input type="checkbox" id="invert"><span class="slider"></span></label>
      </div>
      <div class="toggle-row" style="margin-top:8px">
        <span>Stale only (--stale)</span>
        <label class="toggle"><input type="checkbox" id="stale"><span class="slider"></span></label>
      </div>
    </div>

    <!-- Target pattern card (shown when relationship selected) -->
    <div class="card" id="target-card">
      <h3>Target Pattern</h3>
      <div class="field">
        <label for="target-match-type">Target match type</label>
        <select id="target-match-type">
          <option value="glob">Glob</option>
          <option value="regex">Regex</option>
          <option value="sql">SQL LIKE</option>
        </select>
      </div>
      <div class="field">
        <label for="target-pattern">Target pattern</label>
        <input type="text" id="target-pattern" placeholder="test_*" value="*">
      </div>
      <div class="field">
        <label>Target symbol types</label>
        <div class="chip-group" id="target-type-chips">
          <span class="chip" data-type="class">Class</span>
          <span class="chip" data-type="function">Function</span>
          <span class="chip" data-type="method">Method</span>
          <span class="chip" data-type="import">Import</span>
          <span class="chip" data-type="global">Global</span>
          <span class="chip" data-type="filepath">File Path</span>
          <span class="chip" data-type="filename">File Name</span>
          <span class="chip" data-type="header">MD Header</span>
        </div>
      </div>
    </div>

    <!-- Output format -->
    <div class="card">
      <h3>Output Format</h3>
      <div class="btn-group" id="output-format-group">
        <button data-fmt="list" class="active">List</button>
        <button data-fmt="table">Table</button>
        <button data-fmt="diagram">Diagram</button>
      </div>
    </div>

    <!-- Actions -->
    <div class="actions">
      <button class="btn-primary" id="run-btn">Run Query</button>
      <button class="btn-secondary" id="reset-btn">Reset</button>
    </div>

  </div><!-- /controls-panel -->

  <!-- ---------------------------------------------------------------- -->
  <!-- Results panel                                                     -->
  <!-- ---------------------------------------------------------------- -->
  <div id="results-panel">
    <div id="results-header">
      <h2>Results</h2>
      <span id="result-count"></span>
    </div>

    <div id="loading">
      <div class="spinner"></div>
      Running query…
    </div>

    <div id="empty-state">No results. Try broadening your pattern.</div>
    <div id="error-state"></div>

    <!-- List format -->
    <div id="result-list"></div>

    <!-- Table format -->
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

    <!-- Diagram format -->
    <div id="diagram-wrap" style="display:none">
      <div id="diagram-render"></div>
      <pre id="diagram-fallback"></pre>
    </div>

  </div><!-- /results-panel -->
</div><!-- /app -->

<div id="toast"></div>

<script type="module">
// -------------------------------------------------------------------------
// Mermaid CDN load
// -------------------------------------------------------------------------
let mermaidReady = false;
const mermaidScript = document.createElement('script');
mermaidScript.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
mermaidScript.onload = () => {
  mermaid.initialize({ startOnLoad: false, theme: 'default' });
  mermaidReady = true;
};
mermaidScript.onerror = () => {
  console.warn('Mermaid CDN unavailable — diagram text fallback active');
};
document.head.appendChild(mermaidScript);

// -------------------------------------------------------------------------
// State
// -------------------------------------------------------------------------
let outputFormat = 'list';
let lastStatus = null;
let tableData = [];
let sortCol = 'symbol_name';
let sortAsc = true;

// -------------------------------------------------------------------------
// DOM refs
// -------------------------------------------------------------------------
const $ = id => document.getElementById(id);

// -------------------------------------------------------------------------
// Chip toggling
// -------------------------------------------------------------------------
function initChips(groupId) {
  $$(groupId + ' .chip').forEach(chip => {
    chip.addEventListener('click', () => chip.classList.toggle('selected'));
  });
}
function $$(sel) { return Array.from(document.querySelectorAll(sel)); }
function selectedChips(groupId) {
  return $$('#' + groupId + ' .chip.selected').map(c => c.dataset.type);
}

initChips('type-chips');
initChips('target-type-chips');

// -------------------------------------------------------------------------
// Output format toggle
// -------------------------------------------------------------------------
$$('#output-format-group button').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('#output-format-group button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    outputFormat = btn.dataset.fmt;
  });
});

// -------------------------------------------------------------------------
// Relationship → show/hide target card
// -------------------------------------------------------------------------
$('relationship').addEventListener('change', () => {
  $('target-card').style.display = $('relationship').value ? 'block' : 'none';
});

// -------------------------------------------------------------------------
// Status bar polling
// -------------------------------------------------------------------------
async function updateStatus() {
  try {
    const r = await fetch('/api/status');
    if (!r.ok) return;
    const s = await r.json();

    $('status-dir').textContent = s.directory || '—';
    $('status-files').textContent = (s.file_count ?? '—') + ' files';
    $('status-symbols').textContent = (s.symbol_count ?? '—') + ' symbols';
    $('status-time').textContent = s.last_indexed ? relTime(s.last_indexed) : '—';
    $('watch-dot').className = 'watch-dot' + (s.watching ? '' : ' idle');

    // Toast on new reindex
    if (lastStatus && s.last_reindex_count > lastStatus.last_reindex_count) {
      showToast('Re-indexed ' + s.last_reindex_files + ' file' + (s.last_reindex_files === 1 ? '' : 's'));
    }
    lastStatus = s;
  } catch (_) { /* server not ready yet */ }
}

function relTime(iso) {
  const diff = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 5)  return 'just now';
  if (diff < 60) return diff + 's ago';
  if (diff < 3600) return Math.round(diff/60) + 'm ago';
  return Math.round(diff/3600) + 'h ago';
}

updateStatus();
setInterval(updateStatus, 5000);

// -------------------------------------------------------------------------
// Toast
// -------------------------------------------------------------------------
function showToast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

// -------------------------------------------------------------------------
// Badge colour helper
// -------------------------------------------------------------------------
function badgeClass(type) {
  const map = {
    function: 'badge-function', class: 'badge-class', method: 'badge-method',
    import: 'badge-import', global: 'badge-global',
    filepath: 'badge-filepath', filename: 'badge-filename', header: 'badge-header',
  };
  return map[type] || 'badge-global';
}

// -------------------------------------------------------------------------
// Run query
// -------------------------------------------------------------------------
$('run-btn').addEventListener('click', runQuery);
$('pattern').addEventListener('keydown', e => { if (e.key === 'Enter') runQuery(); });

async function runQuery() {
  showLoading();

  const rel = $('relationship').value || null;
  const body = {
    match_type:       $('match-type').value,
    pattern:          $('pattern').value || '*',
    symbol_types:     selectedChips('type-chips'),
    limit:            parseInt($('limit').value) || 0,
    case_insensitive: $('case-insensitive').checked,
    qualified:        $('qualified').checked,
    newerthan:        $('newerthan').value || null,
    olderthan:        $('olderthan').value || null,
    relationship:     rel,
    invert:           $('invert').checked,
    stale:            $('stale').checked,
    output_format:    outputFormat,
  };
  if (rel) {
    body.target_match_type  = $('target-match-type').value;
    body.target_pattern     = $('target-pattern').value || '*';
    body.target_symbol_types = selectedChips('target-type-chips');
  }

  try {
    const r = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Query failed');
    displayResults(data);
  } catch (err) {
    showError(err.message);
  }
}

// -------------------------------------------------------------------------
// Display results
// -------------------------------------------------------------------------
function showLoading() {
  $('loading').style.display = 'block';
  $('empty-state').style.display = 'none';
  $('error-state').style.display = 'none';
  $('result-list').innerHTML = '';
  $('result-table-wrap').style.display = 'none';
  $('diagram-wrap').style.display = 'none';
  $('result-count').textContent = '';
}

function showError(msg) {
  $('loading').style.display = 'none';
  $('error-state').textContent = '⚠ ' + msg;
  $('error-state').style.display = 'block';
}

function displayResults(data) {
  $('loading').style.display = 'none';

  const fmt = data.format;
  const elapsed = data.elapsed_ms ?? 0;

  if (fmt === 'diagram') {
    renderDiagram(data.mermaid_source || '');
    $('result-count').textContent = data.count + ' nodes (' + elapsed + 'ms)';
    return;
  }

  const results = data.results || [];
  $('result-count').textContent = results.length + ' results (' + elapsed + 'ms)';

  if (results.length === 0) {
    $('empty-state').style.display = 'block';
    return;
  }

  if (fmt === 'table') {
    renderTable(results);
  } else {
    renderList(results);
  }
}

// -------------------------------------------------------------------------
// List renderer
// -------------------------------------------------------------------------
function renderList(results) {
  const list = $('result-list');
  list.innerHTML = results.map(r => `
    <div class="result-card">
      <span class="type-badge ${badgeClass(r.symbol_type)}">${r.symbol_type}</span>
      <div>
        <div class="name">${esc(r.symbol_name)}</div>
        <div class="path">${esc(r.file_path)}:${r.line_number}</div>
      </div>
    </div>
  `).join('');
}

// -------------------------------------------------------------------------
// Table renderer
// -------------------------------------------------------------------------
function renderTable(results) {
  tableData = results;
  sortCol = 'symbol_name';
  sortAsc = true;
  $('result-table-wrap').style.display = 'block';
  renderTableBody();
}

function renderTableBody() {
  const sorted = [...tableData].sort((a, b) => {
    const av = String(a[sortCol] ?? '');
    const bv = String(b[sortCol] ?? '');
    return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
  });
  $('result-tbody').innerHTML = sorted.map(r => `
    <tr>
      <td>${esc(r.symbol_name)}</td>
      <td><span class="type-badge ${badgeClass(r.symbol_type)}" style="font-size:10px">${r.symbol_type}</span></td>
      <td>${esc(r.file_path)}</td>
      <td>${r.line_number}</td>
    </tr>
  `).join('');
}

$$('#result-table th[data-col]').forEach(th => {
  th.addEventListener('click', () => {
    if (sortCol === th.dataset.col) sortAsc = !sortAsc;
    else { sortCol = th.dataset.col; sortAsc = true; }
    $$('#result-table th').forEach(h => {
      h.textContent = h.textContent.replace(/ [▾▴]$/, '');
    });
    th.textContent += sortAsc ? ' ▾' : ' ▴';
    renderTableBody();
  });
});

// -------------------------------------------------------------------------
// Diagram renderer
// -------------------------------------------------------------------------
async function renderDiagram(src) {
  $('diagram-wrap').style.display = 'block';
  const renderEl = $('diagram-render');
  const fallback = $('diagram-fallback');

  if (!src) {
    renderEl.innerHTML = '<p style="color:var(--md-sys-color-on-surface-variant)">No diagram data.</p>';
    return;
  }

  if (mermaidReady) {
    try {
      const { svg } = await mermaid.render('via-diagram', src);
      renderEl.innerHTML = svg;
      fallback.style.display = 'none';
      return;
    } catch (_) { /* fall through to text fallback */ }
  }
  renderEl.innerHTML = '';
  fallback.textContent = src;
  fallback.style.display = 'block';
}

// -------------------------------------------------------------------------
// Reset
// -------------------------------------------------------------------------
$('reset-btn').addEventListener('click', () => {
  $('match-type').value = 'glob';
  $('pattern').value = '*';
  $('case-insensitive').checked = false;
  $('qualified').checked = false;
  $('limit').value = '0';
  $('newerthan').value = '';
  $('olderthan').value = '';
  $('relationship').value = '';
  $('target-card').style.display = 'none';
  $('invert').checked = false;
  $('stale').checked = false;
  $$('.chip.selected').forEach(c => c.classList.remove('selected'));
  $$('#output-format-group button').forEach(b => b.classList.remove('active'));
  $$('#output-format-group button')[0].classList.add('active');
  outputFormat = 'list';
  $('result-list').innerHTML = '';
  $('result-count').textContent = '';
  $('empty-state').style.display = 'none';
  $('error-state').style.display = 'none';
});

// -------------------------------------------------------------------------
// Escape HTML
// -------------------------------------------------------------------------
function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
</script>
</body>
</html>"""
