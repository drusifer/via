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
import { esc, relTime, badgeClass, intensityColor } from './utils.js';

// -------------------------------------------------------------------------
// Module-level state (no DOM access at declaration time)
// -------------------------------------------------------------------------
let mermaidReady = false;
let d3Ready = false;
let outputFormat = 'list';
let lastStatus = null;
let tableData = [];
let sortCol = 'symbol_name';
let sortAsc = true;

// Coverage view (Sprint 27 Phase 2) state
let coverageLoaded = false;
let efficiencyData = [];
let efficiencySortCol = 'duration_seconds';
let efficiencySortAsc = false;

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

// Return 'via' or 'sans' from the segmented control
function relMode() {
  const active = document.querySelector('#rel-mode .seg-btn.active');
  return active ? active.dataset.mode : 'via';
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
    mode:             relMode(),
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
// Coverage view (Sprint 27 Phase 2) — nav toggle
// -------------------------------------------------------------------------
function initViewNav() {
  $$('#view-nav button').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('#view-nav button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.view;
      $('app').style.display = view === 'query' ? 'flex' : 'none';
      $('coverage-view').style.display = view === 'coverage' ? 'block' : 'none';
      if (view === 'coverage' && !coverageLoaded) loadCoverageView();
    });
  });
}

function initCoverageSubnav() {
  $$('#coverage-subnav button').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('#coverage-subnav button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.covview;
      $('coverage-heatmap-wrap').style.display = view === 'heatmap' ? 'block' : 'none';
      $('coverage-efficiency-wrap').style.display = view === 'efficiency' ? 'block' : 'none';
    });
  });
}

// -------------------------------------------------------------------------
// Coverage view — data loading
// -------------------------------------------------------------------------
export async function loadCoverageView() {
  coverageLoaded = true;
  try {
    const [hierarchyResp, efficiencyResp] = await Promise.all([
      fetch('/api/coverage/hierarchy'),
      fetch('/api/coverage/test-efficiency'),
    ]);
    const tree = await hierarchyResp.json();
    const efficiency = await efficiencyResp.json();
    renderCoverageHeatmap(tree);
    renderEfficiencyTable(efficiency.results || []);
  } catch (err) {
    $('coverage-heatmap-fallback').style.display = 'block';
    $('coverage-heatmap-fallback').textContent = 'Failed to load coverage data: ' + err.message;
  }
}

// -------------------------------------------------------------------------
// Coverage view — hierarchy heatmap renderer
// -------------------------------------------------------------------------

// Flatten the hierarchy tree into "indent level + line" pairs for the
// no-D3 text fallback (mirrors the diagram text-fallback pattern below).
export function flattenHierarchyForFallback(node, depth = 0) {
  const label = node.name || '(root)';
  const pct = (node.intensity_pct ?? 0).toFixed(0);
  const outlierMark = node.is_outlier ? ' [OUTLIER]' : '';
  const line = '  '.repeat(depth) + label + ' — ' + pct + '%' + outlierMark;
  const lines = depth === 0 && !node.name ? [] : [line];
  for (const child of node.children || []) {
    lines.push(...flattenHierarchyForFallback(child, depth + 1));
  }
  return lines;
}

export function renderCoverageHeatmap(tree) {
  $('coverage-heatmap-svg').style.display = 'block';
  $('coverage-heatmap-fallback').style.display = 'none';

  if (!tree || !tree.children || tree.children.length === 0) {
    $('coverage-heatmap-svg').innerHTML = '';
    $('coverage-heatmap-fallback').style.display = 'block';
    $('coverage-heatmap-fallback').textContent = 'No coverage data yet — run `make test-coverage` first.';
    return;
  }

  if (d3Ready) {
    renderIcicleD3(tree);
    return;
  }

  // No-D3 fallback: indented text tree, still carries the intensity % and
  // the [OUTLIER] marker so the information is available even without the
  // charting library (mirrors the Mermaid diagram text-fallback pattern).
  $('coverage-heatmap-svg').style.display = 'none';
  $('coverage-heatmap-fallback').style.display = 'block';
  $('coverage-heatmap-fallback').textContent = flattenHierarchyForFallback(tree).join('\n');
}

// Real D3 zoomable-icicle rendering — only reachable once the D3 CDN script
// has loaded (browser only; never exercised by jsdom unit tests, which is
// why the fallback path above carries its own full test coverage instead).
function renderIcicleD3(tree) {
  const container = $('coverage-heatmap-svg');
  container.innerHTML = '';
  const width = container.clientWidth || 928;
  const nodeHeight = 28;

  // Size = lines of code (leaf.loc), color = coverage intensity — two
  // independent dimensions per user directive. `|| 1` guards symbols
  // indexed before the line_end column existed (loc defaults to 1 there).
  const root = d3.hierarchy(tree, d => d.children)
    .sum(d => (d.children && d.children.length ? 0 : (d.loc || 1)))
    .sort((a, b) => b.value - a.value);
  const height = (root.height + 1) * nodeHeight;

  d3.partition().size([width, height])(root);

  const svg = d3.select(container).append('svg')
    .attr('viewBox', [0, 0, width, height])
    .style('font', '11px Roboto, sans-serif');

  let focus = root;

  const g = svg.append('g');

  function rectX(d) { return xScale(d.x0); }
  function rectWidth(d) { return Math.max(0, xScale(d.x1) - xScale(d.x0)); }

  let xScale = d3.scaleLinear().domain([0, width]).range([0, width]);

  const cell = g.selectAll('g.node')
    .data(root.descendants())
    .join('g')
    .attr('class', d => 'node' + (d.data.is_outlier ? ' node-outlier' : ''))
    .attr('transform', d => `translate(${rectX(d)},${d.y0})`);

  cell.append('rect')
    .attr('width', rectWidth)
    .attr('height', d => d.y1 - d.y0 - 1)
    .attr('fill', d => intensityColor(d.data.intensity_pct ?? 0))
    .style('cursor', 'pointer')
    .on('click', (_event, d) => {
      // Leaves (no children) drill down to symbol detail (Cypher AC7);
      // ancestors (package/module/class) zoom instead, per user directive.
      if (!d.children) {
        showSymbolDetail(d.data.id);
      } else {
        zoomTo(d === focus ? root : d);
      }
    });

  cell.append('text')
    .attr('x', 4)
    .attr('y', 16)
    .attr('fill', '#202124')
    .text(d => d.data.name || '(root)')
    .style('pointer-events', 'none');

  cell.append('title')
    .text(d => `${d.data.name || '(root)'}\n${(d.data.intensity_pct ?? 0).toFixed(0)}%${d.data.is_outlier ? ' (outlier — unusual vs. peers)' : ''}`);

  function zoomTo(d) {
    focus = d;
    xScale = d3.scaleLinear().domain([d.x0, d.x1]).range([0, width]);
    cell.attr('transform', node => `translate(${rectX(node)},${node.y0})`);
    cell.select('rect').attr('width', rectWidth);
  }
}

// -------------------------------------------------------------------------
// Coverage view — leaf drill-down (Cypher AC7)
// -------------------------------------------------------------------------
export async function showSymbolDetail(symbolId) {
  const panel = $('coverage-symbol-detail');
  panel.style.display = 'block';
  panel.innerHTML = '<em>Loading…</em>';
  try {
    const r = await fetch('/api/coverage/symbol?id=' + encodeURIComponent(symbolId));
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Failed to load symbol detail');
    renderSymbolDetail(data);
  } catch (err) {
    panel.innerHTML = '<span style="color:var(--md-sys-color-error)">⚠ ' + esc(err.message) + '</span>';
  }
}

export function renderSymbolDetail(data) {
  const panel = $('coverage-symbol-detail');
  const parts = [
    `<div class="symbol-detail-name">${esc(data.signature || data.qualified_name)}</div>`,
    `<div class="symbol-detail-path">${esc(relPath(data.file_path))}:${data.line_number}</div>`,
  ];
  if (data.docstring) {
    parts.push(`<div class="symbol-detail-docstring">${esc(data.docstring)}</div>`);
  } else {
    parts.push('<div class="symbol-detail-docstring symbol-detail-empty">No docstring available.</div>');
  }
  parts.push('<button class="btn-secondary" id="symbol-detail-close">Close</button>');
  panel.innerHTML = parts.join('');
  $('symbol-detail-close').addEventListener('click', () => {
    panel.style.display = 'none';
  });
}

// -------------------------------------------------------------------------
// Coverage view — test efficiency table renderer
// -------------------------------------------------------------------------
export function renderEfficiencyTable(results) {
  efficiencyData = results;
  renderEfficiencyTableBody();
}

export function renderEfficiencyTableBody() {
  const sorted = [...efficiencyData].sort((a, b) => {
    const av = a[efficiencySortCol];
    const bv = b[efficiencySortCol];
    const an = av === null || av === undefined ? -Infinity : av;
    const bn = bv === null || bv === undefined ? -Infinity : bv;
    if (typeof an === 'string' || typeof bn === 'string') {
      return efficiencySortAsc
        ? String(an).localeCompare(String(bn))
        : String(bn).localeCompare(String(an));
    }
    return efficiencySortAsc ? an - bn : bn - an;
  });
  $('coverage-efficiency-tbody').innerHTML = sorted.map(r => `
    <tr>
      <td>${esc(r.test_id)}</td>
      <td>${esc(r.status)}</td>
      <td>${(r.duration_seconds ?? 0).toFixed(2)}</td>
      <td>${r.covered_symbol_count ?? 0}</td>
      <td>${r.symbols_per_second == null ? '—' : r.symbols_per_second.toFixed(2)}</td>
    </tr>
  `).join('');
}

function initEfficiencySort() {
  $$('#coverage-efficiency-table th[data-col]').forEach(th => {
    th.addEventListener('click', () => {
      if (efficiencySortCol === th.dataset.col) efficiencySortAsc = !efficiencySortAsc;
      else { efficiencySortCol = th.dataset.col; efficiencySortAsc = true; }
      $$('#coverage-efficiency-table th').forEach(h => {
        h.textContent = h.textContent.replace(/ [▾▴]$/, '');
      });
      th.textContent += efficiencySortAsc ? ' ▾' : ' ▴';
      renderEfficiencyTableBody();
    });
  });
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
    $('rel-mode-field').style.display = 'none';
    $$('#rel-mode .seg-btn').forEach((b, i) => b.classList.toggle('active', i === 0));
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

  // D3 CDN (Sprint 27 Phase 2 coverage heatmap — zoomable icicle)
  const d3Script = document.createElement('script');
  d3Script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
  d3Script.onload = () => { d3Ready = true; };
  d3Script.onerror = () => {
    console.warn('D3 CDN unavailable — coverage heatmap text fallback active');
  };
  document.head.appendChild(d3Script);

  initChips('type-chips');
  initChips('target-type-chips');
  initOutputFormat();
  initTableSort();
  initReset();
  initViewNav();
  initCoverageSubnav();
  initEfficiencySort();

  $('relationship').addEventListener('change', () => {
    const hasRel = Boolean($('relationship').value);
    $('target-card').style.display = hasRel ? 'block' : 'none';
    $('rel-mode-field').style.display = hasRel ? 'block' : 'none';
  });

  $$('#rel-mode .seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('#rel-mode .seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
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
