"""Standalone HTML Test Quality Report generator for VIA.

TLDR:
    Reads per-test coverage (`covered-by`) and execution metadata (`test_runs`)
    from `.via/index.db` (plus optional branch-arc contexts from `.coverage`),
    computes unique coverage, static AST assertion counts, and nearest-faster
    overlap neighbors, and writes a self-contained interactive HTML report to
    surface slow, low-coverage, and overlapping tests.
"""

import ast
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import coverage

from via.core.constants import EXIT_ERROR, EXIT_SUCCESS
from via.db.store import DatabaseStore
from via.web.api.coverage import (
    _parse_python_file,
    _parse_test_nodeid,
    _resolve_under_root,
    get_test_efficiency,
)

DEFAULT_REPORT_PATH = 'coverage/via-test-quality-report.html'
DEFAULT_SLOW_THRESHOLD = 0.5
_LOW_COV_SYMBOL_FLOOR = 15
_LOW_COV_SPS_FLOOR = 25.0
_HIGH_OVERLAP_PCT = 85.0
_ASSERT_CALL_NAMES = frozenset({'raises', 'warns', 'fail'})
_FLAG_RANK = {
    'slow-zero': 0,
    'slow-low': 1,
    'slow-overlap': 2,
    'slow-0uniq': 3,
    'mocks-only': 4,
    'ok': 5,
}


def _count_ast_assertions(node: ast.AST) -> int:
    """Count `assert` statements and pytest/unittest assertion calls in an AST subtree."""
    count = 0
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            count += 1
        elif isinstance(child, ast.Call):
            fn = child.func
            name = (
                fn.attr
                if isinstance(fn, ast.Attribute)
                else (fn.id if isinstance(fn, ast.Name) else '')
            )
            if name in _ASSERT_CALL_NAMES or name.startswith('assert_'):
                count += 1
    return count


def _analyze_assertions_in_file(file_path: str) -> Dict[Tuple[Optional[str], str], int]:
    """Map `(class_name_or_None, func_name)` -> assertion count for one Python test file."""
    tree = _parse_python_file(file_path)
    if tree is None:
        return {}
    counts: Dict[Tuple[Optional[str], str], int] = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            counts[(None, stmt.name)] = _count_ast_assertions(stmt)
        elif isinstance(stmt, ast.ClassDef):
            for item in stmt.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    counts[(stmt.name, item.name)] = _count_ast_assertions(item)
    return counts


def _lookup_assertion_count(
    test_id: str,
    index_root: str,
    cache: Dict[str, Dict[Tuple[Optional[str], str], int]],
) -> Optional[int]:
    parsed = _parse_test_nodeid(test_id)
    if parsed is None:
        return None
    rel_path, class_name, func_name = parsed
    resolved = _resolve_under_root(index_root, rel_path)
    if resolved is None or not os.path.isfile(resolved):
        return None
    if resolved not in cache:
        cache[resolved] = _analyze_assertions_in_file(resolved)
    return cache[resolved].get((class_name, func_name))


def _load_branch_arc_sets(data_file: str) -> Dict[str, Set[Tuple[int, int, int]]]:
    """Load per-test branch arc sets from a coverage.py file; fail if arcs are absent."""
    if not data_file or not os.path.isfile(data_file):
        raise ValueError(
            f"Coverage data file not found: {data_file}. "
            "Run pytest with --cov-branch --cov-context=test first."
        )
    cov_data = coverage.CoverageData(basename=data_file)
    cov_data.read()
    if not cov_data.has_arcs():
        raise ValueError(
            f"Branch coverage data required, but {data_file} has line-only data. "
            "Re-run pytest with --cov-branch (or set `branch = true` under [tool.coverage.run])."
        )
    arc_sets: Dict[str, Set[Tuple[int, int, int]]] = defaultdict(set)
    conn = sqlite3.connect(f"file:{data_file}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            """
            SELECT c.context, a.file_id, a.fromno, a.tono
            FROM arc a
            JOIN context c ON c.id = a.context_id
            WHERE c.context != ''
            """
        )
        for ctx, file_id, fromno, tono in rows:
            arc_sets[ctx.rsplit('|', 1)[0]].add((file_id, fromno, tono))
    finally:
        conn.close()
    return dict(arc_sets)


def _nearest_faster_overlap(
    tid: str,
    dur: float,
    overlap_sets: Dict[str, Set[Any]],
    fast_pool: List[Tuple[str, Set[Any], float]],
) -> Tuple[Optional[str], float, bool]:
    """Return `(faster_test_id, jaccard_pct, is_strict_subset)` for `tid`."""
    target = overlap_sets.get(tid)
    if not target:
        return None, 0.0, False
    best_j = 0.0
    best_other: Optional[str] = None
    best_sub = False
    for other_id, other_set, other_dur in fast_pool:
        if other_id == tid or other_dur >= dur:
            continue
        inter = len(target & other_set)
        if not inter:
            continue
        jaccard = inter / len(target | other_set)
        subsumed = target.issubset(other_set)
        if (subsumed and not best_sub) or (subsumed == best_sub and jaccard > best_j):
            best_sub = subsumed
            best_j = jaccard
            best_other = other_id
    if best_other is None:
        return None, 0.0, False
    return best_other, round(best_j * 100.0, 1), best_sub


def _classify_test(
    dur: float,
    cov: int,
    sps: Optional[float],
    uniq: int,
    subsumed: bool,
    overlap_pct: float,
    mocks_only: bool,
    slow_threshold: float,
) -> str:
    """Assign a quality signal flag to one test row."""
    if dur >= slow_threshold and cov == 0:
        return 'slow-zero'
    if dur >= slow_threshold and (
        cov <= _LOW_COV_SYMBOL_FLOOR or (sps is not None and sps < _LOW_COV_SPS_FLOOR)
    ):
        return 'slow-low'
    if dur >= slow_threshold and (subsumed or overlap_pct >= _HIGH_OVERLAP_PCT):
        return 'slow-overlap'
    if dur >= slow_threshold and uniq == 0:
        return 'slow-0uniq'
    if mocks_only:
        return 'mocks-only'
    return 'ok'


def _compute_unique_counts(cov_sets: Dict[str, Set[int]]) -> Dict[str, int]:
    """Return `{test_id: count_of_symbols_covered_only_by_this_test}`."""
    fanin: Dict[int, int] = defaultdict(int)
    for sids in cov_sets.values():
        for sid in sids:
            fanin[sid] += 1
    return {
        tid: sum(1 for sid in sids if fanin[sid] == 1)
        for tid, sids in cov_sets.items()
    }


def _summarize_kpis(tests: List[Dict[str, Any]], slow_threshold: float) -> Dict[str, Any]:
    total_dur = sum(t['dur'] for t in tests)
    slow_tests = [t for t in tests if t['dur'] >= slow_threshold]
    slow_dur = sum(t['dur'] for t in slow_tests)

    def _bucket(flag: str) -> Tuple[int, float]:
        items = [t for t in tests if t['flag'] == flag]
        return len(items), round(sum(t['dur'] for t in items), 1)

    sz_n, sz_d = _bucket('slow-zero')
    sl_n, sl_d = _bucket('slow-low')
    so_n, so_d = _bucket('slow-overlap')
    su_n, su_d = _bucket('slow-0uniq')
    return {
        'total_tests': len(tests),
        'total_dur': round(total_dur, 1),
        'slow_threshold': slow_threshold,
        'slow_count': len(slow_tests),
        'slow_dur': round(slow_dur, 1),
        'slow_pct_time': round(100.0 * slow_dur / total_dur, 1) if total_dur else 0.0,
        'slow_zero_count': sz_n,
        'slow_zero_dur': sz_d,
        'slow_low_count': sl_n,
        'slow_low_dur': sl_d,
        'slow_overlap_count': so_n,
        'slow_overlap_dur': so_d,
        'slow_0uniq_count': su_n,
        'slow_0uniq_dur': su_d,
        'mocks_only_count': sum(1 for t in tests if t['mocks_only']),
    }


def build_test_quality_data(
    store: DatabaseStore,
    branch_data_file: str,
    slow_threshold: float = DEFAULT_SLOW_THRESHOLD,
) -> Dict[str, Any]:
    """Assemble test-quality metrics, branch-arc overlaps, and file rollups."""
    eff = get_test_efficiency(store)
    cov_sets = store.get_test_covered_symbol_ids()
    unique_by_test = _compute_unique_counts(cov_sets)

    overlap_sets: Dict[str, Set[Any]] = _load_branch_arc_sets(branch_data_file)
    overlap_mode = 'branches'

    dur_by_id = {t['test_id']: float(t['duration_seconds'] or 0.0) for t in eff}
    fast_pool = [
        (tid, s, dur_by_id[tid])
        for tid, s in overlap_sets.items()
        if s and tid in dur_by_id
    ]

    assert_cache: Dict[str, Dict[Tuple[Optional[str], str], int]] = {}
    file_rollup: Dict[str, Dict[str, Any]] = {}
    tests: List[Dict[str, Any]] = []

    for row in eff:
        tid = row['test_id']
        dur = float(row['duration_seconds'] or 0.0)
        cov = int(row['covered_symbol_count'] or 0)
        sps = (cov / dur) if dur > 0 else None
        uniq = int(unique_by_test.get(tid, 0))
        mocks_only = bool(row['mocks_only'])
        asserts = _lookup_assertion_count(tid, store.index_root, assert_cache)
        tfile = tid.split('::', 1)[0]

        if dur >= slow_threshold and cov > 0:
            peer, overlap_pct, subsumed = _nearest_faster_overlap(tid, dur, overlap_sets, fast_pool)
        else:
            peer, overlap_pct, subsumed = None, 0.0, False

        flag = _classify_test(
            dur, cov, sps, uniq, subsumed, overlap_pct, mocks_only, slow_threshold
        )
        tests.append({
            'test_id': tid,
            'file': tfile,
            'status': row['status'],
            'dur': round(dur, 4),
            'cov': cov,
            'imp': row['imported_module_covered_count'],
            'uniq': uniq,
            'sps': round(sps, 1) if sps is not None else None,
            'asserts': asserts,
            'mocks': row['mock_call_count'],
            'mocks_only': mocks_only,
            'overlap_pct': overlap_pct,
            'subsumed': subsumed,
            'peer': peer,
            'flag': flag,
        })
        fr = file_rollup.setdefault(
            tfile,
            {
                'file': tfile,
                'tests': 0,
                'dur': 0.0,
                'cov_sum': 0,
                'unique_sum': 0,
                'zero_cov': 0,
                'slow_low': 0,
            },
        )
        fr['tests'] += 1
        fr['dur'] += dur
        fr['cov_sum'] += cov
        fr['unique_sum'] += uniq
        if cov == 0:
            fr['zero_cov'] += 1
        if flag in ('slow-zero', 'slow-low', 'slow-overlap'):
            fr['slow_low'] += 1

    tests.sort(key=lambda r: (_FLAG_RANK[r['flag']], -r['dur'], r['cov']))
    files = sorted(
        [
            {
                **fr,
                'dur': round(fr['dur'], 2),
                'avg_cov': round(fr['cov_sum'] / fr['tests'], 1) if fr['tests'] else 0.0,
            }
            for fr in file_rollup.values()
        ],
        key=lambda x: -x['dur'],
    )
    return {
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'overlap_mode': overlap_mode,
        'kpis': _summarize_kpis(tests, slow_threshold),
        'tests': tests,
        'files': files,
    }


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VIA Test Quality Report — Slow, Low-Coverage &amp; Overlapping Tests</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 0;
    font-family: var(--font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    color: var(--foreground, #0f172a);
    font-size: 13px;
    line-height: 1.45;
  }
  .wrap {
    width: 100%;
    max-width: 1120px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .header-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
  }
  .header-row h1 { margin: 0; font-size: 16px; font-weight: 700; }
  .meta { font-size: 11.5px; color: var(--muted-foreground, #64748b); }
  .kpis {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
  }
  .card {
    background: var(--card, #ffffff);
    border: 1px solid var(--border, #e2e8f0);
    border-radius: var(--radius, 8px);
    padding: 14px 16px;
  }
  .kpi-label {
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted-foreground, #64748b);
    margin-bottom: 4px;
  }
  .kpi-val {
    font-size: 21px;
    font-weight: 700;
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
  }
  .kpi-val.danger { color: var(--destructive, #dc2626); }
  .kpi-val.warn { color: var(--warning, #d97706); }
  .kpi-val.ok { color: var(--success, #16a34a); }
  .kpi-sub { font-size: 11px; color: var(--muted-foreground, #64748b); margin-top: 4px; }
  .section-head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
  }
  .section-head h2 { margin: 0; font-size: 13.5px; font-weight: 600; }
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 11px;
    color: var(--muted-foreground, #64748b);
  }
  .legend-item { display: inline-flex; align-items: center; gap: 5px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
  .scatter-box { position: relative; width: 100%; }
  #scatter-tip {
    display: none;
    position: absolute;
    pointer-events: none;
    z-index: 10;
    max-width: 360px;
    background: var(--popover, #0f172a);
    color: var(--popover-foreground, #f8fafc);
    border: 1px solid var(--border, #334155);
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 11.5px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.28);
  }
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
    margin-bottom: 10px;
  }
  input[type="search"] {
    background: var(--background, transparent);
    color: var(--foreground, #0f172a);
    border: 1px solid var(--border, #cbd5e1);
    border-radius: var(--radius, 6px);
    padding: 5px 9px;
    font-size: 12px;
    min-width: 180px;
  }
  .chip {
    border: 1px solid var(--border, #cbd5e1);
    background: transparent;
    color: var(--foreground, #334155);
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 11px;
    cursor: pointer;
  }
  .chip.active {
    background: var(--primary, #1565c0);
    color: var(--primary-foreground, #ffffff);
    border-color: var(--primary, #1565c0);
  }
  .tbl-wrap {
    overflow-x: auto;
    max-height: 390px;
    overflow-y: auto;
    border: 1px solid var(--border, #e2e8f0);
    border-radius: var(--radius, 6px);
  }
  table { width: 100%; border-collapse: collapse; font-size: 11.5px; table-layout: fixed; }
  th, td {
    padding: 6px 6px;
    text-align: left;
    border-bottom: 1px solid var(--border, #e2e8f0);
    vertical-align: top;
    overflow-wrap: anywhere;
  }
  th {
    position: sticky;
    top: 0;
    background: var(--card, #f8fafc);
    font-weight: 600;
    font-size: 10.5px;
    color: var(--muted-foreground, #475569);
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }
  th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .mono { font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace); font-size: 10.5px; overflow-wrap: anywhere; word-break: break-word; }
  .peer-hint { font-size: 10px; color: var(--muted-foreground, #64748b); margin-top: 2px; overflow-wrap: anywhere; word-break: break-word; }
  .badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    white-space: nowrap;
  }
  .b-zero { background: rgba(220,38,38,0.18); color: var(--destructive, #dc2626); }
  .b-low { background: rgba(234,88,12,0.18); color: var(--warning, #ea580c); }
  .b-ov { background: rgba(168,85,247,0.18); color: #a855f7; }
  .b-red { background: rgba(202,138,4,0.18); color: var(--warning, #ca8a04); }
  .b-ok { background: rgba(22,163,74,0.15); color: var(--success, #16a34a); }
  .note { font-size: 11px; color: var(--muted-foreground, #64748b); margin-top: 6px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="header-row">
    <h1>VIA Test Quality Report — Slow, Low-Coverage &amp; Overlapping Tests</h1>
    <span class="meta" id="gen-meta"></span>
  </div>

  <div class="kpis" id="kpi-grid"></div>

  <div class="card">
    <div class="section-head">
      <h2>Duration vs. Symbols Covered (Bottom-Right = Slow + Low Coverage)</h2>
      <div class="legend">
        <span class="legend-item"><span class="dot" style="background:#ef4444"></span>Slow + 0 cov</span>
        <span class="legend-item"><span class="dot" style="background:#f97316"></span>Slow + Low cov</span>
        <span class="legend-item"><span class="dot" style="background:#a855f7"></span>Slow + High overlap</span>
        <span class="legend-item"><span class="dot" style="background:#eab308"></span>Slow + 0 unique</span>
        <span class="legend-item"><span class="dot" style="background:#3b82f6"></span>Healthy</span>
      </div>
    </div>
    <div class="scatter-box" id="scatter-box">
      <div id="scatter-tip"></div>
    </div>
    <div class="note">X-axis uses log scale (1ms &rarr; 10s). Hover any dot to inspect; click to filter the audit table below.</div>
  </div>

  <div class="card">
    <div class="section-head">
      <h2>Ranked Test Quality Audit</h2>
      <span class="meta" id="shown-count"></span>
    </div>
    <div class="controls">
      <input type="search" id="search-input" placeholder="Filter by test name or file...">
      <button class="chip active" data-filter="flagged">Flagged (<span id="c-flagged">0</span>)</button>
      <button class="chip" data-filter="slow-low">Slow + Low Cov (<span id="c-sl">0</span>)</button>
      <button class="chip" data-filter="slow-overlap">Slow + High Overlap (<span id="c-so">0</span>)</button>
      <button class="chip" data-filter="slow-0uniq">Slow + 0 Unique (<span id="c-su">0</span>)</button>
      <button class="chip" data-filter="slow-all">All Slow (<span id="c-sa">0</span>)</button>
      <button class="chip" data-filter="all">All Tests (<span id="c-all">0</span>)</button>
    </div>
    <div class="tbl-wrap">
      <table>
        <colgroup>
          <col style="width:96px">
          <col>
          <col style="width:52px">
          <col style="width:42px">
          <col style="width:38px">
          <col style="width:46px">
          <col style="width:48px">
          <col style="width:62px">
        </colgroup>
        <thead>
          <tr>
            <th data-sort="flag">Signal</th>
            <th data-sort="test_id">Test (and closest faster overlap)</th>
            <th class="num" data-sort="dur">Dur (s)</th>
            <th class="num" data-sort="cov">Syms</th>
            <th class="num" data-sort="uniq">Uniq</th>
            <th class="num" data-sort="sps">Sym/s</th>
            <th class="num" data-sort="asserts">Asserts</th>
            <th class="num" data-sort="overlap_pct">Overlap</th>
          </tr>
        </thead>
        <tbody id="tests-tbody"></tbody>
      </table>
    </div>
    <div class="note" id="overlap-note"></div>
  </div>

  <div class="card">
    <div class="section-head">
      <h2>Slowest Test Files — Time Budget vs. Coverage Yield</h2>
      <span class="meta">Top 25 files by wall-clock time</span>
    </div>
    <div class="tbl-wrap">
      <table>
        <colgroup>
          <col>
          <col style="width:82px">
          <col style="width:46px">
          <col style="width:66px">
          <col style="width:76px">
          <col style="width:48px">
          <col style="width:56px">
        </colgroup>
        <thead>
          <tr>
            <th>Test File</th>
            <th class="num">Total Time (s)</th>
            <th class="num">Tests</th>
            <th class="num">Avg Syms</th>
            <th class="num">Unique Syms</th>
            <th class="num">0-Cov</th>
            <th class="num">Flagged</th>
          </tr>
        </thead>
        <tbody id="files-tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const DATA = __REPORT_DATA__;
const k = DATA.kpis;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

document.getElementById('gen-meta').textContent = `Generated ${DATA.generated_at} • ${k.total_tests.toLocaleString()} tests • ${k.total_dur}s total • overlap: ${DATA.overlap_mode}`;
document.getElementById('overlap-note').innerHTML = `<strong>Overlap (${esc(DATA.overlap_mode)})</strong> = highest Jaccard similarity (or strict subset <code>SUB</code>) against a <em>faster</em> test. Check <strong>Asserts</strong> &amp; the named faster neighbor before deleting — high overlap with distinct assertions is a fixture-sharing candidate.`;
document.getElementById('c-flagged').textContent = k.slow_zero_count + k.slow_low_count + k.slow_overlap_count + k.slow_0uniq_count + k.mocks_only_count;
document.getElementById('c-sl').textContent = k.slow_low_count;
document.getElementById('c-so').textContent = k.slow_overlap_count;
document.getElementById('c-su').textContent = k.slow_0uniq_count;
document.getElementById('c-sa').textContent = k.slow_count;
document.getElementById('c-all').textContent = k.total_tests;

const kpis = [
  { label: 'Slow + 0 Covered', val: `${k.slow_zero_count}`, cls: k.slow_zero_count ? 'danger' : 'ok', sub: `${k.slow_zero_dur}s spent (≥${k.slow_threshold}s, 0 syms)` },
  { label: 'Slow + Low Coverage', val: `${k.slow_low_count}`, cls: k.slow_low_count ? 'warn' : 'ok', sub: `${k.slow_low_dur}s spent (<25 sym/s or ≤15 syms)` },
  { label: 'Slow + High Overlap', val: `${k.slow_overlap_count}`, cls: k.slow_overlap_count ? 'warn' : 'ok', sub: `${k.slow_overlap_dur}s subsumed or ≥85% overlap` },
  { label: 'Slow Suite Share', val: `${k.slow_pct_time}%`, cls: '', sub: `${k.slow_count} tests ≥${k.slow_threshold}s take ${k.slow_dur}s / ${k.total_dur}s` },
];
document.getElementById('kpi-grid').innerHTML = kpis.map(x => `
  <div class="card">
    <div class="kpi-label">${esc(x.label)}</div>
    <div class="kpi-val ${x.cls}">${esc(x.val)}</div>
    <div class="kpi-sub">${esc(x.sub)}</div>
  </div>`).join('');

const FLAG_META = {
  'slow-zero': { label: 'SLOW + 0 COV', cls: 'b-zero', color: '#ef4444' },
  'slow-low': { label: 'SLOW + LOW', cls: 'b-low', color: '#f97316' },
  'slow-overlap': { label: 'SLOW + OVERLAP', cls: 'b-ov', color: '#a855f7' },
  'slow-0uniq': { label: 'SLOW + 0 UNIQ', cls: 'b-red', color: '#eab308' },
  'mocks-only': { label: 'MOCKS ONLY', cls: 'b-low', color: '#f97316' },
  'ok': { label: 'OK', cls: 'b-ok', color: '#3b82f6' },
};

(function renderScatter() {
  const W = 680, H = 265, padL = 48, padR = 20, padT = 16, padB = 34;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const maxDur = Math.max(10, ...DATA.tests.map(t => t.dur));
  const minLogX = Math.log10(0.001), maxLogX = Math.log10(maxDur);
  const maxY = Math.max(100, ...DATA.tests.map(t => t.cov));
  const sx = d => padL + ((Math.log10(Math.max(0.001, d)) - minLogX) / (maxLogX - minLogX)) * plotW;
  const sy = c => padT + plotH - (c / maxY) * plotH;
  const xSlow = sx(k.slow_threshold), yLow = sy(20);

  const xTicks = [0.001, 0.01, 0.1, 0.5, 1, 5, 10].filter(v => Math.log10(v) <= maxLogX + 0.05);
  const yTicks = [0, Math.round(maxY * 0.25), Math.round(maxY * 0.5), Math.round(maxY * 0.75), maxY];
  const gridX = xTicks.map(v => {
    const x = sx(v), lbl = v < 1 ? `${v * 1000}ms` : `${v}s`;
    return `<line x1="${x}" y1="${padT}" x2="${x}" y2="${padT + plotH}" stroke="rgba(148,163,184,0.22)" stroke-dasharray="${v === k.slow_threshold ? '4,3' : ''}"/>
            <text x="${x}" y="${H - 12}" text-anchor="middle" font-size="10" fill="var(--muted-foreground,#64748b)">${lbl}</text>`;
  }).join('');
  const gridY = yTicks.map(v => {
    const y = sy(v);
    return `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="rgba(148,163,184,0.18)"/>
            <text x="${padL - 6}" y="${y + 3}" text-anchor="end" font-size="10" fill="var(--muted-foreground,#64748b)">${v}</text>`;
  }).join('');

  const ordered = [...DATA.tests].sort((a, b) => (a.flag === 'ok' ? 0 : 1) - (b.flag === 'ok' ? 0 : 1));
  const dots = ordered.map((t, i) => {
    const x = sx(t.dur).toFixed(1), y = sy(t.cov).toFixed(1);
    const r = t.flag === 'ok' ? 2.6 : 4.2;
    const op = t.flag === 'ok' ? 0.36 : 0.9;
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="${FLAG_META[t.flag].color}" fill-opacity="${op}" data-idx="${i}" style="cursor:pointer"/>`;
  }).join('');

  const box = document.getElementById('scatter-box');
  const tip = document.getElementById('scatter-tip');
  const svgWrap = document.createElement('div');
  svgWrap.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" role="img" aria-label="Test duration vs symbols covered scatter plot">
      <rect x="${xSlow}" y="${yLow}" width="${Math.max(0, W - padR - xSlow)}" height="${padT + plotH - yLow}" fill="rgba(239,68,68,0.09)" stroke="rgba(239,68,68,0.35)" stroke-dasharray="4,3"/>
      <text x="${W - padR - 6}" y="${yLow - 5}" text-anchor="end" font-size="10" font-weight="600" fill="#ef4444">Slow + Low Coverage Zone</text>
      ${gridX}${gridY}
      <text x="${padL + plotW / 2}" y="${H - 1}" text-anchor="middle" font-size="10" fill="var(--muted-foreground,#64748b)">Test Duration (log scale)</text>
      <text x="12" y="${padT + plotH / 2}" text-anchor="middle" font-size="10" fill="var(--muted-foreground,#64748b)" transform="rotate(-90 12 ${padT + plotH / 2})">Symbols Covered</text>
      ${dots}
    </svg>`;
  box.insertBefore(svgWrap, tip);

  svgWrap.querySelectorAll('circle').forEach(c => {
    const t = ordered[Number(c.dataset.idx)];
    c.addEventListener('mouseenter', e => {
      const rect = box.getBoundingClientRect();
      tip.innerHTML = `<div class="mono" style="margin-bottom:4px"><strong>${esc(t.test_id)}</strong></div>
        <div>Dur: <strong>${t.dur.toFixed(3)}s</strong> &bull; Syms: <strong>${t.cov}</strong> &bull; Uniq: <strong>${t.uniq}</strong> &bull; Asserts: <strong>${t.asserts ?? '—'}</strong></div>
        ${t.peer ? `<div style="margin-top:3px;opacity:0.85">Overlap: <strong>${t.subsumed ? 'SUB ' : ''}${t.overlap_pct}%</strong> vs <span class="mono">${esc(t.peer)}</span></div>` : ''}`;
      tip.style.display = 'block';
      tip.style.left = Math.min(rect.width - 370, Math.max(8, e.clientX - rect.left + 12)) + 'px';
      tip.style.top = Math.max(8, e.clientY - rect.top - 72) + 'px';
    });
    c.addEventListener('mouseleave', () => { tip.style.display = 'none'; });
    c.addEventListener('click', () => {
      document.getElementById('search-input').value = t.test_id;
      activeFilter = 'all';
      document.querySelectorAll('.chip').forEach(x => x.classList.toggle('active', x.dataset.filter === 'all'));
      renderTests();
    });
  });
})();

let activeFilter = 'flagged';
let sortState = { col: 'dur', dir: -1 };
const flagRank = { 'slow-zero': 0, 'slow-low': 1, 'slow-overlap': 2, 'slow-0uniq': 3, 'mocks-only': 4, 'ok': 5 };

function renderTests() {
  const q = (document.getElementById('search-input').value || '').toLowerCase();
  let rows = DATA.tests.filter(t => {
    if (q && !t.test_id.toLowerCase().includes(q)) return false;
    if (activeFilter === 'flagged') return t.flag !== 'ok';
    if (activeFilter === 'slow-all') return t.dur >= k.slow_threshold;
    if (activeFilter === 'all') return true;
    return t.flag === activeFilter;
  });
  rows.sort((a, b) => {
    if (sortState.col === 'flag') return (flagRank[a.flag] - flagRank[b.flag]) * sortState.dir || (b.dur - a.dur);
    const av = a[sortState.col], bv = b[sortState.col];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (typeof av === 'string') return av.localeCompare(bv) * sortState.dir;
    return (av - bv) * sortState.dir;
  });
  const limit = 250;
  document.getElementById('shown-count').textContent = rows.length > limit
    ? `Showing top ${limit} of ${rows.length} matching tests`
    : `${rows.length} matching tests`;
  document.getElementById('tests-tbody').innerHTML = rows.slice(0, limit).map(t => {
    const fm = FLAG_META[t.flag];
    const ov = t.overlap_pct ? `${t.subsumed ? 'SUB ' : ''}${Math.round(t.overlap_pct)}%` : '—';
    const peerHtml = t.peer ? `<div class="peer-hint">&approx; ${esc(t.peer)}</div>` : '';
    return `<tr>
      <td><span class="badge ${fm.cls}">${fm.label}</span></td>
      <td><div class="mono">${esc(t.test_id)}</div>${peerHtml}</td>
      <td class="num"><strong>${t.dur.toFixed(3)}</strong></td>
      <td class="num">${t.cov}</td>
      <td class="num">${t.uniq}</td>
      <td class="num">${t.sps == null ? '—' : t.sps.toFixed(1)}</td>
      <td class="num">${t.asserts == null ? '—' : t.asserts}</td>
      <td class="num">${ov}</td>
    </tr>`;
  }).join('') || '<tr><td colspan="8">No matching tests.</td></tr>';
}

document.getElementById('search-input').addEventListener('input', renderTests);
document.querySelectorAll('.chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    renderTests();
  });
});
document.querySelectorAll('th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.sort;
    sortState = sortState.col === col ? { col, dir: -sortState.dir } : { col, dir: col === 'test_id' || col === 'flag' ? 1 : -1 };
    renderTests();
  });
});
renderTests();

document.getElementById('files-tbody').innerHTML = DATA.files.slice(0, 25).map(f => `
  <tr>
    <td class="mono">${esc(f.file)}</td>
    <td class="num"><strong>${f.dur.toFixed(2)}</strong></td>
    <td class="num">${f.tests}</td>
    <td class="num">${f.avg_cov}</td>
    <td class="num">${f.unique_sum}</td>
    <td class="num">${f.zero_cov > 0 ? `<span class="badge b-zero">${f.zero_cov}</span>` : '0'}</td>
    <td class="num">${f.slow_low > 0 ? `<span class="badge b-low">${f.slow_low}</span>` : '0'}</td>
  </tr>`).join('');
</script>
</body>
</html>
"""


def render_test_quality_html(payload: Dict[str, Any]) -> str:
    """Render a self-contained HTML test quality report from a structured payload."""
    data_json = json.dumps(payload).replace('</', '<\\/')
    return _HTML_TEMPLATE.replace('__REPORT_DATA__', data_json)


def generate_coverage_report(
    project_root: str,
    output_path: str = DEFAULT_REPORT_PATH,
    slow_threshold: float = DEFAULT_SLOW_THRESHOLD,
    coverage_file: str = '.coverage',
) -> int:
    """Generate a standalone HTML test quality report from `.via/index.db` and branch `.coverage`."""
    root = Path(project_root).resolve()
    db_path = root / '.via' / 'index.db'
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        return EXIT_ERROR

    candidate = Path(coverage_file)
    resolved_cov = str(candidate if candidate.is_absolute() else root / candidate)

    try:
        with DatabaseStore(str(db_path), str(root)) as store:
            store.initialize_schema()
            payload = build_test_quality_data(
                store, branch_data_file=resolved_cov, slow_threshold=slow_threshold
            )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    out = Path(output_path)
    out = out if out.is_absolute() else root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_test_quality_html(payload), encoding='utf-8')

    k = payload['kpis']
    flagged = (
        k['slow_zero_count']
        + k['slow_low_count']
        + k['slow_overlap_count']
        + k['slow_0uniq_count']
        + k['mocks_only_count']
    )
    print(
        f"Wrote test quality report: {out} "
        f"({k['total_tests']} tests, {flagged} flagged, overlap={payload['overlap_mode']})"
    )
    return EXIT_SUCCESS
