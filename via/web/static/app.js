/**
 * via Web UI — SPA application logic.
 *
 * TLDR:
 *   Vanilla ES2022 module. Pure utility functions live in utils.js.
 *   All DOM interaction and fetch calls are in this file. Event listeners
 *   are attached by initApp() — called automatically in a browser but
 *   skipped in test environments (import.meta.env?.TEST).
 *   Pure-ish functions (renderList, renderTable, showLoading, etc.) are
 *   exported for unit testing with jsdom.
 *
 * Author: Drew Gutstein
 * License: GPL-3.0
 */
import { esc, relTime, badgeClass } from './utils.js';

// -------------------------------------------------------------------------
// Module-level state (no DOM access at declaration time)
// -------------------------------------------------------------------------
let mermaidReady = false;
let outputFormat = 'list';
let lastStatus = null;
let tableData = [];
let sortCol = 'symbol_name';
let sortAsc = true;

// -------------------------------------------------------------------------
// DOM helpers
// -------------------------------------------------------------------------
const $ = id => document.getElementById(id);
function $$(sel) { return Array.from(document.querySelectorAll(sel)); }

// -------------------------------------------------------------------------
// Chip helpers
// -------------------------------------------------------------------------
function initChips(groupId) {
  $$('#' + groupId + ' .chip').forEach(chip => {
    chip.addEventListener('click', () => chip.classList.toggle('selected'));
  });
}

export function selectedChips(groupId) {
  return $$('#' + groupId + ' .chip.selected').map(c => c.dataset.type);
}

// -------------------------------------------------------------------------
// Output format toggle
// -------------------------------------------------------------------------
function initOutputFormat() {
  $$('#output-format-group button').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('#output-format-group button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      outputFormat = btn.dataset.fmt;
    });
  });
}

// -------------------------------------------------------------------------
// Show / hide states
// -------------------------------------------------------------------------
export function showLoading() {
  $('loading').style.display = 'block';
  $('initial-state').style.display = 'none';
  $('empty-state').style.display = 'none';
  $('error-state').style.display = 'none';
  $('result-list').innerHTML = '';
  $('result-table-wrap').style.display = 'none';
  $('diagram-wrap').style.display = 'none';
  $('result-count').textContent = '';
}

export function showError(msg) {
  $('loading').style.display = 'none';
  $('error-state').textContent = '⚠ ' + msg;
  $('error-state').style.display = 'block';
}

// -------------------------------------------------------------------------
// Build query request body from current form state
// -------------------------------------------------------------------------
export function buildQueryBody() {
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
    body.target_match_type   = $('target-match-type').value;
    body.target_pattern      = $('target-pattern').value || '*';
    body.target_symbol_types = selectedChips('target-type-chips');
  }
  return body;
}

// -------------------------------------------------------------------------
// Run query
// -------------------------------------------------------------------------
export async function runQuery() {
  showLoading();
  try {
    const r = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildQueryBody()),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Query failed');
    displayResults(data);
  } catch (err) {
    showError(err.message);
  }
}

// -------------------------------------------------------------------------
// Display results (dispatcher)
// -------------------------------------------------------------------------
export function displayResults(data) {
  $('loading').style.display = 'none';

  const fmt = data.format;
  const elapsed = data.elapsed_ms ?? 0;

  if (fmt === 'diagram') {
    renderDiagram(data.mermaid_source || '');
    $('result-count').textContent = data.count + ' nodes (' + elapsed + 'ms)';
    return;
  }

  const results = data.results || [];
  const count = results.length;
  $('result-count').textContent = count + ' result' + (count === 1 ? '' : 's') + ' (' + elapsed + 'ms)';

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
// Path helper — strip indexed root for display
// -------------------------------------------------------------------------
function relPath(p) {
  const root = lastStatus?.directory;
  if (root && p.startsWith(root)) {
    return p.slice(root.endsWith('/') ? root.length : root.length + 1);
  }
  return p;
}

// -------------------------------------------------------------------------
// List renderer
// -------------------------------------------------------------------------
export function renderList(results) {
  const list = $('result-list');
  list.innerHTML = results.map(r => `
    <div class="result-card">
      <span class="type-badge ${badgeClass(r.symbol_type)}">${r.symbol_type}</span>
      <div>
        <div class="name">${esc(r.symbol_name)}</div>
        <div class="path">${esc(relPath(r.file_path))}:${r.line_number}</div>
      </div>
    </div>
  `).join('');
}

// -------------------------------------------------------------------------
// Table renderer
// -------------------------------------------------------------------------
export function renderTable(results) {
  tableData = results;
  sortCol = 'symbol_name';
  sortAsc = true;
  $('result-table-wrap').style.display = 'block';
  renderTableBody();
}

export function renderTableBody() {
  const sorted = [...tableData].sort((a, b) => {
    const av = String(a[sortCol] ?? '');
    const bv = String(b[sortCol] ?? '');
    return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
  });
  $('result-tbody').innerHTML = sorted.map(r => `
    <tr>
      <td>${esc(r.symbol_name)}</td>
      <td><span class="type-badge ${badgeClass(r.symbol_type)}" style="font-size:10px">${r.symbol_type}</span></td>
      <td>${esc(relPath(r.file_path))}</td>
      <td>${r.line_number}</td>
    </tr>
  `).join('');
}

function initTableSort() {
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
}

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
// Status bar polling
// -------------------------------------------------------------------------
export async function updateStatus() {
  try {
    const r = await fetch('/api/status');
    if (!r.ok) return;
    const s = await r.json();

    $('status-dir').textContent = s.directory || '—';
    $('status-files').textContent = (s.file_count ?? '—') + ' files';
    $('status-symbols').textContent = (s.symbol_count ?? '—') + ' symbols';
    $('status-time').textContent = s.last_indexed ? relTime(s.last_indexed) : '—';
    $('watch-dot').className = 'watch-dot' + (s.watching ? '' : ' idle');

    if (lastStatus && s.last_reindex_count > lastStatus.last_reindex_count) {
      showToast('Re-indexed ' + s.last_reindex_files + ' file' + (s.last_reindex_files === 1 ? '' : 's'));
    }
    lastStatus = s;
  } catch (_) { /* server not ready yet */ }
}

// -------------------------------------------------------------------------
// Toast
// -------------------------------------------------------------------------
export function showToast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

// -------------------------------------------------------------------------
// Reset
// -------------------------------------------------------------------------
function initReset() {
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
}

// -------------------------------------------------------------------------
// App initialisation — attaches all event listeners and starts polling.
// Called automatically in browser; skipped in test environments.
// -------------------------------------------------------------------------
export function initApp() {
  // Mermaid CDN
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

  initChips('type-chips');
  initChips('target-type-chips');
  initOutputFormat();
  initTableSort();
  initReset();

  $('relationship').addEventListener('change', () => {
    $('target-card').style.display = $('relationship').value ? 'block' : 'none';
  });

  $('run-btn').addEventListener('click', runQuery);
  $('pattern').addEventListener('keydown', e => { if (e.key === 'Enter') runQuery(); });

  updateStatus();
  setInterval(updateStatus, 5000);
}

// Auto-init in browser only (not in Vitest / Node)
if (!import.meta.env?.TEST) {
  initApp();
}
