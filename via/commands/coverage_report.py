"""Standalone HTML Test Quality Report generator for VIA.

TLDR:
    Reads per-test coverage (`covered-by`) and execution metadata (`test_runs`)
    from `.via/index.db` (plus optional branch-arc contexts from `.coverage`),
    computes unique coverage, static AST assertion counts, and nearest-faster
    overlap neighbors, and writes a self-contained interactive HTML report to
    surface slow, low-coverage, and overlapping tests.
"""

import ast
import hashlib
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import coverage
from coverage.results import Numbers

from via.core.constants import EXIT_ERROR, EXIT_SUCCESS
from via.db.store import DatabaseStore
from via.web.api.coverage import (
    _drop_redundant_class_rows,
    _parse_python_file,
    _parse_test_nodeid,
    _resolve_under_root,
    get_test_efficiency,
)

DEFAULT_REPORT_PATH = 'coverage/via-test-quality-report.html'
DEFAULT_SLOW_THRESHOLD = 0.5
_LOW_MODULE_COV_THRESHOLD = 85.0
_COVERAGE_HISTORY_FILE = 'coverage_history.json'
_LOW_COV_SYMBOL_FLOOR = 15
_LOW_COV_SPS_FLOOR = 25.0
_HIGH_OVERLAP_PCT = 85.0
_ASSERT_CALL_NAMES = frozenset({'raises', 'warns', 'fail'})
_MOCK_ASSERT_PREFIXES = (
    'assert_called',
    'assert_not_called',
    'assert_any_call',
    'assert_has_calls',
)
_FLAG_RANK = {
    'slow-zero': 0,
    'slow-low': 1,
    'slow-overlap': 2,
    'slow-0uniq': 3,
    'mocks-only': 4,
    'smelly-assert': 5,
    'ok': 6,
}


def _call_name(call: ast.Call) -> str:
    fn = call.func
    if isinstance(fn, ast.Attribute):
        return fn.attr
    if isinstance(fn, ast.Name):
        return fn.id
    return ''


_SHARED_FIXTURE_SCOPES = frozenset({'class', 'module', 'package', 'session'})


def _fixture_scope(fn: ast.AST) -> Optional[str]:
    """Return pytest fixture scope (`'function'`, `'class'`, `'module'`, ...) or None."""
    for dec in getattr(fn, 'decorator_list', ()):
        if isinstance(dec, ast.Name) and dec.id == 'fixture':
            return 'function'
        if isinstance(dec, ast.Attribute) and dec.attr == 'fixture':
            return 'function'
        if isinstance(dec, ast.Call) and _call_name(dec) == 'fixture':
            for kw in dec.keywords:
                if kw.arg == 'scope' and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    return kw.value.value
            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                return dec.args[0].value
            return 'function'
    return None


def _is_fixture_func(fn: ast.AST) -> bool:
    return _fixture_scope(fn) is not None


def _param_names(fn: ast.AST) -> Set[str]:
    args = getattr(fn, 'args', None)
    if args is None:
        return set()
    names = {a.arg for a in args.args + args.kwonlyargs}
    return names - {'self', 'cls'}


def _collect_fixture_graph(
    tree: ast.Module,
) -> Tuple[Dict[str, Tuple[str, Set[str]]], Dict[str, Dict[str, Tuple[str, Set[str]]]]]:
    """Map fixture names -> `(scope, param_names)` at module and class levels."""
    mod_fx: Dict[str, Tuple[str, Set[str]]] = {}
    cls_fx: Dict[str, Dict[str, Tuple[str, Set[str]]]] = defaultdict(dict)
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sc = _fixture_scope(stmt)
            if sc is not None:
                mod_fx[stmt.name] = (sc, _param_names(stmt))
        elif isinstance(stmt, ast.ClassDef):
            for item in stmt.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sc = _fixture_scope(item)
                    if sc is not None:
                        cls_fx[stmt.name][item.name] = (sc, _param_names(item))
    return mod_fx, cls_fx


def _resolve_shared_fixtures(
    params: Set[str], fixtures: Dict[str, Tuple[str, Set[str]]]
) -> Set[str]:
    """Return all transitive class/module/package/session fixture names used by `params`."""
    shared: Set[str] = set()
    seen: Set[str] = set()
    stack = list(params)
    while stack:
        name = stack.pop()
        if name in seen or name not in fixtures:
            continue
        seen.add(name)
        scope, deps = fixtures[name]
        if scope in _SHARED_FIXTURE_SCOPES:
            shared.add(name)
        stack.extend(deps - seen)
    return shared


def _detect_tautology(expr: ast.expr) -> Optional[str]:
    if isinstance(expr, ast.Constant) and bool(expr.value):
        return f"assert {expr.value!r}"
    if isinstance(expr, ast.Compare) and len(expr.ops) == 1 and len(expr.comparators) == 1:
        op, left, right = expr.ops[0], expr.left, expr.comparators[0]
        if isinstance(op, (ast.Eq, ast.Is, ast.LtE, ast.GtE)) and ast.dump(left) == ast.dump(right):
            return f"self-compare ({ast.unparse(expr)})"
        is_len_ge_zero = (
            isinstance(op, ast.GtE)
            and isinstance(left, ast.Call)
            and isinstance(left.func, ast.Name)
            and left.func.id == 'len'
            and isinstance(right, ast.Constant)
            and right.value == 0
        )
        if is_len_ge_zero:
            return f"always-true ({ast.unparse(expr)})"
    return None


def _is_broad_raises(call: ast.Call) -> bool:
    if _call_name(call) != 'raises' or not call.args:
        return False
    arg0 = call.args[0]
    if not (isinstance(arg0, ast.Name) and arg0.id in ('Exception', 'BaseException')):
        return False
    return not any(kw.arg == 'match' for kw in call.keywords)


def _try_swallows_assert(node: ast.Try) -> bool:
    for handler in node.handlers:
        catches_broad = handler.type is None or (
            isinstance(handler.type, ast.Name)
            and handler.type.id in ('Exception', 'BaseException', 'AssertionError')
        )
        if catches_broad and not any(isinstance(x, ast.Raise) for x in ast.walk(handler)):
            return True
    return False


def _has_direct_assertion(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
        if isinstance(child, ast.Call):
            name = _call_name(child)
            if name in _ASSERT_CALLS_OR_PREFIX or name.startswith('assert'):
                return True
    return False


_ASSERT_CALLS_OR_PREFIX = _ASSERT_CALL_NAMES


def _collect_assert_helpers(tree: ast.Module) -> Tuple[Set[str], Dict[str, Set[str]]]:
    file_helpers: Set[str] = set()
    class_helpers: Dict[str, Set[str]] = defaultdict(set)
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not stmt.name.startswith('test_') and _has_direct_assertion(stmt):
                file_helpers.add(stmt.name)
        elif isinstance(stmt, ast.ClassDef):
            for item in stmt.body:
                if (
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not item.name.startswith('test_')
                    and _has_direct_assertion(item)
                ):
                    class_helpers[stmt.name].add(item.name)
    return file_helpers, class_helpers


def _record_assert(
    node: ast.Assert, state: Dict[str, Any], in_cf: bool, in_swallow: bool
) -> None:
    state['total'] += 1
    if not in_cf:
        state['top'] += 1
    taut = _detect_tautology(node.test)
    if taut:
        state['smells'].append(('tautology', taut))
    if in_swallow:
        state['smells'].append(('swallowed-assert', ast.unparse(node)[:60]))


def _record_call_check(
    node: ast.Call, helpers: Set[str], state: Dict[str, Any], in_cf: bool
) -> None:
    name = _call_name(node)
    if name in _ASSERT_CALL_NAMES or name.startswith('assert_') or name in helpers:
        state['total'] += 1
        if not in_cf:
            state['top'] += 1
        if name.startswith(_MOCK_ASSERT_PREFIXES):
            state['mock_asserts'] += 1
        if _is_broad_raises(node):
            state['smells'].append(('broad-raises', ast.unparse(node)[:60]))


def _walk_try_node(
    node: ast.Try, helpers: Set[str], state: Dict[str, Any], in_cf: bool, in_swallow: bool
) -> None:
    swallows = in_swallow or _try_swallows_assert(node)
    for s in node.body:
        _walk_test_checks(s, helpers, state, in_cf=in_cf, in_swallow=swallows)
    for h in node.handlers:
        for s in h.body:
            _walk_test_checks(s, helpers, state, in_cf=True, in_swallow=in_swallow)
    for s in node.orelse + node.finalbody:
        _walk_test_checks(s, helpers, state, in_cf=in_cf, in_swallow=in_swallow)


def _is_nonempty_literal_iter(expr: ast.expr) -> bool:
    if isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
        return len(expr.elts) > 0
    if isinstance(expr, ast.Dict):
        return len(expr.keys) > 0
    return False


def _walk_test_checks(
    node: ast.AST,
    helpers: Set[str],
    state: Dict[str, Any],
    in_cf: bool = False,
    in_swallow: bool = False,
) -> None:
    if isinstance(node, ast.Assert):
        _record_assert(node, state, in_cf, in_swallow)
        return
    if isinstance(node, ast.Call):
        _record_call_check(node, helpers, state, in_cf)
    if isinstance(node, (ast.For, ast.AsyncFor)):
        child_cf = in_cf or not _is_nonempty_literal_iter(node.iter)
        for ch in ast.iter_child_nodes(node):
            _walk_test_checks(ch, helpers, state, in_cf=child_cf, in_swallow=in_swallow)
        return
    if isinstance(node, (ast.If, ast.While)):
        for ch in ast.iter_child_nodes(node):
            _walk_test_checks(ch, helpers, state, in_cf=True, in_swallow=in_swallow)
        return
    if isinstance(node, ast.Try):
        _walk_try_node(node, helpers, state, in_cf, in_swallow)
        return
    for ch in ast.iter_child_nodes(node):
        _walk_test_checks(ch, helpers, state, in_cf=in_cf, in_swallow=in_swallow)


def _inspect_test_ast(fn: ast.AST, helpers: Set[str]) -> Tuple[int, List[str], str]:
    """Return `(assert_count, smell_codes, concise_detail)` for one test function."""
    state: Dict[str, Any] = {'total': 0, 'top': 0, 'mock_asserts': 0, 'smells': []}
    for stmt in getattr(fn, 'body', ()):
        _walk_test_checks(stmt, helpers, state)

    smell_pairs: List[Tuple[str, str]] = list(state['smells'])
    if state['total'] == 0 and not _is_fixture_func(fn):
        smell_pairs.append(('no-asserts', '0 assertions, raises, or assert helpers'))
    elif state['total'] > 0:
        if state['top'] == 0:
            smell_pairs.append(
                ('conditional-only', f"all {state['total']} assertion(s) inside if/for/except")
            )
        if state['mock_asserts'] == state['total']:
            smell_pairs.append(
                ('mock-only-asserts', f"{state['mock_asserts']} mock assert(s) only (no value checks)")
            )

    codes: List[str] = []
    details: List[str] = []
    for code, detail in smell_pairs:
        if code not in codes:
            codes.append(code)
            details.append(detail)
    return state['total'], codes, '; '.join(details)


def _analyze_test_file_ast(
    file_path: str,
) -> Dict[Tuple[Optional[str], str], Tuple[int, List[str], str, Set[str]]]:
    """Map `(class_name_or_None, func_name)` -> `(asserts, smells, detail, shared_fixtures)`."""
    tree = _parse_python_file(file_path)
    if tree is None:
        return {}
    file_helpers, class_helpers = _collect_assert_helpers(tree)
    mod_fx, cls_fx = _collect_fixture_graph(tree)
    info: Dict[Tuple[Optional[str], str], Tuple[int, List[str], str, Set[str]]] = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cnt, smells, detail = _inspect_test_ast(stmt, file_helpers)
            shared = _resolve_shared_fixtures(_param_names(stmt), mod_fx)
            info[(None, stmt.name)] = (cnt, smells, detail, shared)
        elif isinstance(stmt, ast.ClassDef):
            helpers = file_helpers | class_helpers[stmt.name]
            fixtures = {**mod_fx, **cls_fx[stmt.name]}
            for item in stmt.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cnt, smells, detail = _inspect_test_ast(item, helpers)
                    shared = _resolve_shared_fixtures(_param_names(item), fixtures)
                    info[(stmt.name, item.name)] = (cnt, smells, detail, shared)
    return info


def _lookup_test_ast_info(
    test_id: str,
    index_root: str,
    cache: Dict[str, Dict[Tuple[Optional[str], str], Tuple[int, List[str], str, Set[str]]]],
) -> Tuple[Optional[int], List[str], str, Set[str]]:
    parsed = _parse_test_nodeid(test_id)
    if parsed is None:
        return None, [], '', set()
    rel_path, class_name, func_name = parsed
    resolved = _resolve_under_root(index_root, rel_path)
    if resolved is None or not os.path.isfile(resolved):
        return None, [], '', set()
    if resolved not in cache:
        cache[resolved] = _analyze_test_file_ast(resolved)
    found = cache[resolved].get((class_name, func_name))
    if found is None:
        return None, [], '', set()
    return found


def _resolve_shared_fixture_attribution(
    eff: List[Dict[str, Any]],
    ast_by_tid: Dict[str, Tuple[Optional[int], List[str], str, Set[str]]],
) -> Dict[str, str]:
    """Map `cov == 0` tests sharing a module/class fixture with a `cov > 0` sibling to provenance."""
    best_owner: Dict[Tuple[str, str], Tuple[str, int]] = {}
    for row in eff:
        tid = row['test_id']
        cov = int(row['covered_symbol_count'] or 0)
        if cov <= 0:
            continue
        tfile = tid.split('::', 1)[0]
        for fx in ast_by_tid[tid][3]:
            prev = best_owner.get((tfile, fx))
            if prev is None or cov > prev[1]:
                best_owner[(tfile, fx)] = (tid, cov)

    attributed: Dict[str, str] = {}
    for row in eff:
        tid = row['test_id']
        cov = int(row['covered_symbol_count'] or 0)
        asserts, smells, _, shared_fx = ast_by_tid[tid]
        if cov > 0 or smells or not asserts or not shared_fx:
            continue
        tfile = tid.split('::', 1)[0]
        matches = [
            (fx, best_owner[(tfile, fx)])
            for fx in sorted(shared_fx)
            if (tfile, fx) in best_owner
        ]
        if matches:
            fx, (owner_tid, owner_cov) = max(matches, key=lambda item: item[1][1])
            owner_short = owner_tid.split('::', 1)[-1]
            attributed[tid] = f"{fx} → {owner_short} ({owner_cov} syms)"
    return attributed


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
    has_smell: bool = False,
    shared_fixture_cov: bool = False,
) -> str:
    """Assign a quality signal flag to one test row."""
    if dur >= slow_threshold and cov == 0:
        if shared_fixture_cov:
            return 'smelly-assert' if has_smell else 'ok'
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
    if has_smell:
        return 'smelly-assert'
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
    smell_counts: Dict[str, int] = defaultdict(int)
    smelly_count = 0
    for t in tests:
        sm = t.get('smells') or ()
        if sm:
            smelly_count += 1
            for code in sm:
                smell_counts[code] += 1
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
        'smelly_flag_count': sum(1 for t in tests if t['flag'] == 'smelly-assert'),
        'flagged_count': sum(1 for t in tests if t['flag'] != 'ok'),
        'smelly_count': smelly_count,
        'smell_counts': dict(smell_counts),
    }


def _compute_module_coverage(data_file: str, index_root: str) -> Dict[str, Any]:
    """Compute statement+branch coverage summary and modules below 85% from `.coverage`."""
    cov = coverage.Coverage(data_file=data_file)
    cov.load()
    data = cov.get_data()
    root_real = os.path.realpath(index_root)
    total = Numbers()
    low_modules: List[Dict[str, Any]] = []
    for path in sorted(data.measured_files()):
        try:
            nums = cov._analyze(path).numbers
        except Exception:
            continue
        total += nums
        if nums.n_statements == 0 or nums.pc_covered >= _LOW_MODULE_COV_THRESHOLD:
            continue
        rel = os.path.relpath(os.path.realpath(path), root_real).replace('\\', '/')
        low_modules.append({
            'file': rel,
            'cover_pct': round(nums.pc_covered, 1),
            'stmts': nums.n_statements,
            'miss_stmts': nums.n_missing,
            'branches': nums.n_branches,
            'miss_branches': nums.n_missing_branches,
        })
    low_modules.sort(key=lambda m: (m['cover_pct'], -m['miss_stmts']))
    return {
        'cov_pct': round(total.pc_covered, 1),
        'stmts': total.n_statements,
        'miss_stmts': total.n_missing,
        'branches': total.n_branches,
        'miss_branches': total.n_missing_branches,
        'low_modules': low_modules,
    }


def _compute_symbol_safety_net(store: DatabaseStore) -> Dict[str, Any]:
    """Summarize production symbol coverage and top 15 uncovered symbols by LOC."""
    raw_rows = store.get_symbol_coverage_counts()
    prod_rows = [
        r
        for r in _drop_redundant_class_rows(raw_rows)
        if not r['file_path'].startswith('tests/')
        and not r['file_path'].endswith('conftest.py')
        and r['file_path'] not in ('<test>', '<coverage>', '<external>')
    ]
    all_keys: Set[str] = set()
    covered_keys: Set[str] = set()
    uncovered: List[Dict[str, Any]] = []
    for r in prod_rows:
        sym_label = (
            f"{r['parent_name']}.{r['symbol_name']}"
            if r.get('parent_name')
            else r['symbol_name']
        )
        key = f"{r['file_path']}:{sym_label}"
        all_keys.add(key)
        if r['covering_test_count'] > 0:
            covered_keys.add(key)
        else:
            line_start = r['line_number'] or 0
            line_end = r['line_end'] or line_start
            loc = max(1, line_end - line_start + 1)
            uncovered.append({
                'symbol': key,
                'type': r['symbol_type'],
                'loc': loc,
            })
    uncovered.sort(key=lambda x: (-x['loc'], x['symbol']))
    return {
        'total_symbols': len(all_keys),
        'covered_symbols': len(covered_keys),
        'uncovered_symbols': len(all_keys) - len(covered_keys),
        'all_keys': all_keys,
        'covered_keys': covered_keys,
        'uncovered_top': uncovered[:15],
        'prod_rows': prod_rows,
    }


def _build_symbol_test_index(
    store: DatabaseStore,
    prod_rows: List[Dict[str, Any]],
    tests: List[Dict[str, Any]],
) -> List[List[Any]]:
    """Build compact `[symbol_key, symbol_type, [test_indices...]]` lookup rows."""
    test_idx = {t['test_id']: i for i, t in enumerate(tests)}
    edges_by_sym: Dict[int, List[int]] = defaultdict(list)
    rows = store.conn.execute(
        """
        SELECT sr.from_symbol_id, t.qualified_name
        FROM symbol_references sr
        JOIN symbols t ON t.id = sr.to_symbol_id
        WHERE sr.reference_type = 'covered-by'
        """
    ).fetchall()
    for sym_id, tname in rows:
        idx = test_idx.get(tname)
        if idx is not None:
            edges_by_sym[sym_id].append(idx)

    entries: List[List[Any]] = []
    for r in prod_rows:
        sym_label = (
            f"{r['parent_name']}.{r['symbol_name']}"
            if r.get('parent_name')
            else r['symbol_name']
        )
        key = f"{r['file_path']}:{sym_label}"
        tids = sorted(set(edges_by_sym.get(r['id'], ())))
        entries.append([key, r['symbol_type'], tids])
    entries.sort(key=lambda e: (-len(e[2]), e[0]))
    return entries


def _file_fingerprint(data_file: str) -> str:
    h = hashlib.sha256()
    with open(data_file, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


def _build_comparison(
    prev: Dict[str, Any],
    cov_pct: float,
    kpis: Dict[str, Any],
    flagged_count: int,
    file_durs: Dict[str, float],
    all_keys: Set[str],
    covered_keys: Set[str],
) -> Dict[str, Any]:
    """Compute before/after deltas and symbol coverage regressions against `prev`."""
    prev_cov_set = set(prev.get('covered_keys', ()))
    # Only flag symbols that still exist in the codebase (avoid false alarms on deleted code)
    newly_uncovered = sorted((prev_cov_set & all_keys) - covered_keys)
    prev_files = prev.get('file_durations') or {}
    file_deltas = []
    for fname in set(prev_files) | set(file_durs):
        before = float(prev_files.get(fname, 0.0))
        after = float(file_durs.get(fname, 0.0))
        delta = round(after - before, 2)
        if abs(delta) >= 0.5:
            file_deltas.append({
                'file': fname,
                'before': round(before, 2),
                'after': round(after, 2),
                'delta': delta,
            })
    file_deltas.sort(key=lambda x: -abs(x['delta']))

    prev_dur = float(prev.get('total_dur', kpis['total_dur']))
    prev_cov = float(prev.get('cov_pct', cov_pct))
    prev_slow_dur = float(prev.get('slow_dur', kpis['slow_dur']))
    prev_flagged = int(prev.get('flagged_count', flagged_count))
    prev_covered = int(prev.get('covered_symbols', len(prev_cov_set)))
    return {
        'has_previous': True,
        'cov_delta_pct': round(cov_pct - prev_cov, 1),
        'dur_delta_s': round(kpis['total_dur'] - prev_dur, 1),
        'newly_uncovered': newly_uncovered,
        'newly_covered_count': len(covered_keys - prev_cov_set),
        'comparison': {
            'total_dur': {'before': prev_dur, 'after': kpis['total_dur'], 'delta': round(kpis['total_dur'] - prev_dur, 1)},
            'slow_dur': {'before': prev_slow_dur, 'after': kpis['slow_dur'], 'delta': round(kpis['slow_dur'] - prev_slow_dur, 1)},
            'flagged_count': {'before': prev_flagged, 'after': flagged_count, 'delta': flagged_count - prev_flagged},
            'cov_pct': {'before': prev_cov, 'after': cov_pct, 'delta': round(cov_pct - prev_cov, 1)},
            'covered_symbols': {'before': prev_covered, 'after': len(covered_keys), 'delta': len(covered_keys) - prev_covered},
            'file_deltas': file_deltas[:8],
            'prev_scatter': prev.get('scatter_points') or [],
        },
    }


def _update_coverage_history(
    root: Path,
    fingerprint: str,
    cov_pct: float,
    kpis: Dict[str, Any],
    tests: List[Dict[str, Any]],
    files: List[Dict[str, Any]],
    all_keys: Set[str],
    covered_keys: Set[str],
) -> Dict[str, Any]:
    """Compare against prior run idempotently (rotates snapshot only when `.coverage` changes)."""
    hist_path = root / '.via' / _COVERAGE_HISTORY_FILE
    state: Dict[str, Any] = {}
    if hist_path.is_file():
        try:
            state = json.loads(hist_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            state = {}

    flagged_count = int(
        kpis.get(
            'flagged_count',
            kpis['slow_zero_count']
            + kpis['slow_low_count']
            + kpis['slow_overlap_count']
            + kpis['slow_0uniq_count']
            + kpis['mocks_only_count']
            + kpis.get('smelly_flag_count', 0),
        )
    )
    file_durs = {f['file']: round(float(f['dur']), 2) for f in files}
    scatter_pts = [[t['test_id'], t['dur'], t['cov'], t['flag']] for t in tests]
    snapshot = {
        'cov_pct': cov_pct,
        'total_dur': kpis['total_dur'],
        'slow_dur': kpis['slow_dur'],
        'slow_count': kpis['slow_count'],
        'flagged_count': flagged_count,
        'total_tests': kpis['total_tests'],
        'covered_symbols': len(covered_keys),
        'covered_keys': sorted(covered_keys),
        'file_durations': file_durs,
        'scatter_points': scatter_pts,
    }
    prev = state.get('previous')
    cur = state.get('current')
    if state.get('current_hash') != fingerprint:
        if cur:
            prev = cur
        state = {
            'current_hash': fingerprint,
            'current': snapshot,
            'previous': prev,
        }
        hist_path.parent.mkdir(parents=True, exist_ok=True)
        hist_path.write_text(json.dumps(state), encoding='utf-8')
    elif not (cur and cur.get('scatter_points') and cur.get('file_durations')):
        state['current'] = snapshot
        hist_path.parent.mkdir(parents=True, exist_ok=True)
        hist_path.write_text(json.dumps(state), encoding='utf-8')

    if not prev:
        return {
            'has_previous': False,
            'cov_delta_pct': None,
            'dur_delta_s': None,
            'newly_uncovered': [],
            'newly_covered_count': 0,
            'comparison': None,
        }
    return _build_comparison(prev, cov_pct, kpis, flagged_count, file_durs, all_keys, covered_keys)


def build_test_quality_data(
    store: DatabaseStore,
    branch_data_file: str,
    slow_threshold: float = DEFAULT_SLOW_THRESHOLD,
    update_history: bool = True,
) -> Dict[str, Any]:
    """Assemble test-quality metrics, branch-arc overlaps, coverage safety net, and file rollups."""
    eff = get_test_efficiency(store)
    cov_sets = store.get_test_covered_symbol_ids()
    unique_by_test = _compute_unique_counts(cov_sets)

    overlap_sets: Dict[str, Set[Any]] = _load_branch_arc_sets(branch_data_file)
    overlap_mode = 'branches'
    mod_cov = _compute_module_coverage(branch_data_file, store.index_root)
    sym_net = _compute_symbol_safety_net(store)

    dur_by_id = {t['test_id']: float(t['duration_seconds'] or 0.0) for t in eff}
    fast_pool = [
        (tid, s, dur_by_id[tid])
        for tid, s in overlap_sets.items()
        if s and tid in dur_by_id
    ]

    assert_cache: Dict[str, Dict[Tuple[Optional[str], str], Tuple[int, List[str], str, Set[str]]]] = {}
    ast_by_tid = {
        row['test_id']: _lookup_test_ast_info(row['test_id'], store.index_root, assert_cache)
        for row in eff
    }
    shared_attr = _resolve_shared_fixture_attribution(eff, ast_by_tid)
    file_rollup: Dict[str, Dict[str, Any]] = {}
    tests: List[Dict[str, Any]] = []

    for row in eff:
        tid = row['test_id']
        dur = float(row['duration_seconds'] or 0.0)
        cov = int(row['covered_symbol_count'] or 0)
        sps = (cov / dur) if dur > 0 else None
        uniq = int(unique_by_test.get(tid, 0))
        mocks_only = bool(row['mocks_only'])
        asserts, smells, smell_detail, _ = ast_by_tid[tid]
        shared_fixture = shared_attr.get(tid)
        tfile = tid.split('::', 1)[0]

        if dur >= slow_threshold and cov > 0:
            peer, overlap_pct, subsumed = _nearest_faster_overlap(tid, dur, overlap_sets, fast_pool)
        else:
            peer, overlap_pct, subsumed = None, 0.0, False

        flag = _classify_test(
            dur,
            cov,
            sps,
            uniq,
            subsumed,
            overlap_pct,
            mocks_only,
            slow_threshold,
            has_smell=bool(smells),
            shared_fixture_cov=bool(shared_fixture),
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
            'smells': smells,
            'smell_detail': smell_detail,
            'shared_fixture': shared_fixture,
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
        if cov == 0 and not shared_fixture:
            fr['zero_cov'] += 1
        if flag != 'ok':
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
    kpis = _summarize_kpis(tests, slow_threshold)
    if update_history:
        diff = _update_coverage_history(
            Path(store.index_root),
            _file_fingerprint(branch_data_file),
            mod_cov['cov_pct'],
            kpis,
            tests,
            files,
            sym_net['all_keys'],
            sym_net['covered_keys'],
        )
    else:
        diff = {
            'has_previous': False,
            'cov_delta_pct': None,
            'dur_delta_s': None,
            'newly_uncovered': [],
            'newly_covered_count': 0,
            'comparison': None,
        }
    coverage_summary = {
        'cov_pct': mod_cov['cov_pct'],
        'stmts': mod_cov['stmts'],
        'miss_stmts': mod_cov['miss_stmts'],
        'branches': mod_cov['branches'],
        'miss_branches': mod_cov['miss_branches'],
        'total_symbols': sym_net['total_symbols'],
        'covered_symbols': sym_net['covered_symbols'],
        'uncovered_symbols': sym_net['uncovered_symbols'],
        'low_modules': mod_cov['low_modules'],
        'uncovered_top': sym_net['uncovered_top'],
        **diff,
    }
    symbol_index = _build_symbol_test_index(store, sym_net['prod_rows'], tests)
    return {
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'overlap_mode': overlap_mode,
        'kpis': kpis,
        'coverage': coverage_summary,
        'tests': tests,
        'files': files,
        'symbols': symbol_index,
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
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
  }
  .kpi-row {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 6px;
  }
  .kpi-delta {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .b-neutral { background: rgba(148,163,184,0.16); color: var(--muted-foreground, #64748b); }
  .seg-toggle {
    display: inline-flex;
    border: 1px solid var(--border, #cbd5e1);
    border-radius: var(--radius, 6px);
    overflow: hidden;
  }
  .seg-btn {
    appearance: none;
    border: none;
    border-right: 1px solid var(--border, #cbd5e1);
    background: transparent;
    color: var(--muted-foreground, #64748b);
    padding: 3px 9px;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
  }
  .seg-btn:last-child { border-right: none; }
  .seg-btn.active {
    background: var(--primary, #1565c0);
    color: var(--primary-foreground, #ffffff);
  }
  .reg-banner {
    display: none;
    background: rgba(220,38,38,0.10);
    border: 1px solid var(--destructive, #dc2626);
    border-radius: var(--radius, 8px);
    padding: 12px 16px;
  }
  .reg-banner h2 {
    margin: 0 0 6px 0;
    font-size: 13px;
    color: var(--destructive, #dc2626);
  }
  .reg-banner ul {
    margin: 6px 0 0 18px;
    padding: 0;
    max-height: 160px;
    overflow-y: auto;
  }
  .gaps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 12px;
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
  .b-smell { background: rgba(236,72,153,0.18); color: #ec4899; }
  .b-ok { background: rgba(22,163,74,0.15); color: var(--success, #16a34a); }
  .note { font-size: 11px; color: var(--muted-foreground, #64748b); margin-top: 6px; }
  .playbook ol { margin: 6px 0 10px 18px; padding: 0; }
  .playbook li { margin: 4px 0; }
  .playbook h3 { margin: 10px 0 4px 0; font-size: 12px; font-weight: 600; }
  .playbook code {
    font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace);
    font-size: 11px;
    background: var(--secondary, rgba(148,163,184,0.16));
    padding: 1px 4px;
    border-radius: 3px;
  }
  .copy-btn {
    border: 1px solid var(--border, #cbd5e1);
    background: var(--secondary, transparent);
    color: var(--foreground, #334155);
    border-radius: var(--radius, 6px);
    padding: 4px 10px;
    font-size: 11px;
    cursor: pointer;
  }
  .copy-btn:hover { border-color: var(--primary, #1565c0); }
  .sym-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 10px;
  }
  .sym-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border: 1px solid var(--border, #cbd5e1);
    background: transparent;
    color: var(--foreground, #334155);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace);
    font-size: 10.5px;
    cursor: pointer;
    max-width: 100%;
    overflow-wrap: anywhere;
  }
  .sym-pill.active {
    background: var(--primary, #1565c0);
    color: var(--primary-foreground, #ffffff);
    border-color: var(--primary, #1565c0);
  }
  .sym-pill.active .badge {
    background: rgba(255,255,255,0.22);
    color: #ffffff;
  }
  .sym-summary {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 11.5px;
  }
  .clickable-row { cursor: pointer; }
  .clickable-row:hover td { background: rgba(148,163,184,0.08); }
</style>
</head>
<body>
<div class="wrap">
  <div class="header-row">
    <h1>VIA Test Quality Report — Slow, Low-Coverage &amp; Overlapping Tests</h1>
    <span class="meta" id="gen-meta"></span>
  </div>

  <div class="reg-banner" id="reg-banner">
    <h2 id="reg-title"></h2>
    <div class="meta">These symbols were covered in the previous run and dropped to 0 coverage in this run:</div>
    <ul id="reg-list" class="mono"></ul>
  </div>

  <div class="kpis" id="kpi-grid"></div>

  <div class="card">
    <div class="section-head">
      <h2>Duration vs. Symbols Covered (Bottom-Right = Slow + Low Coverage)</h2>
      <div class="seg-toggle" id="scatter-mode-toggle" style="display:none" role="group" aria-label="Scatter view mode">
        <button class="seg-btn" type="button" data-mode="before">Before</button>
        <button class="seg-btn active" type="button" data-mode="after">After</button>
      </div>
    </div>
    <div class="legend" style="margin-bottom:8px">
      <span class="legend-item"><span class="dot" style="background:#ef4444"></span>Slow + 0 cov</span>
      <span class="legend-item"><span class="dot" style="background:#f97316"></span>Slow + Low cov</span>
      <span class="legend-item"><span class="dot" style="background:#a855f7"></span>Slow + High overlap</span>
      <span class="legend-item"><span class="dot" style="background:#eab308"></span>Slow + 0 unique</span>
      <span class="legend-item"><span class="dot" style="background:#ec4899"></span>Smelly assert</span>
      <span class="legend-item"><span class="dot" style="background:#3b82f6"></span>Healthy</span>
    </div>
    <div class="scatter-box" id="scatter-box">
      <div id="scatter-tip"></div>
    </div>
    <div class="note">X-axis uses log scale (1ms &rarr; 10s) shared across Before/After. Toggle Before/After to animate dot movement; hover any dot to inspect; click to filter the audit table.</div>
  </div>

  <div class="card" id="before-after-card" style="display:none">
    <div class="section-head">
      <h2>Before vs. After (vs. Previous Run)</h2>
      <span class="meta" id="ba-meta"></span>
    </div>
    <div class="gaps-grid">
      <div>
        <div class="kpi-label" style="margin-bottom:6px">Suite Metrics</div>
        <div class="tbl-wrap">
          <table>
            <colgroup>
              <col>
              <col style="width:64px">
              <col style="width:64px">
              <col style="width:78px">
            </colgroup>
            <thead>
              <tr><th>Metric</th><th class="num">Before</th><th class="num">After</th><th class="num">Delta</th></tr>
            </thead>
            <tbody id="ba-metrics-tbody"></tbody>
          </table>
        </div>
      </div>
      <div>
        <div class="kpi-label" style="margin-bottom:6px">Biggest Per-File Runtime Changes</div>
        <div class="tbl-wrap">
          <table>
            <colgroup>
              <col>
              <col style="width:54px">
              <col style="width:54px">
              <col style="width:64px">
            </colgroup>
            <thead>
              <tr><th>Test File</th><th class="num">Before</th><th class="num">After</th><th class="num">Delta</th></tr>
            </thead>
            <tbody id="ba-files-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="section-head">
      <h2>Ranked Test Quality Audit</h2>
      <span class="meta" id="shown-count"></span>
    </div>
    <div class="controls">
      <input type="search" id="search-input" placeholder="Filter by test name or file...">
      <button class="chip active" data-filter="flagged">Flagged (<span id="c-flagged">0</span>)</button>
      <button class="chip" data-filter="smelly">Smelly Asserts (<span id="c-smell">0</span>)</button>
      <button class="chip" data-filter="slow-low">Slow + Low Cov (<span id="c-sl">0</span>)</button>
      <button class="chip" data-filter="slow-overlap">Slow + High Overlap (<span id="c-so">0</span>)</button>
      <button class="chip" data-filter="slow-0uniq">Slow + 0 Unique (<span id="c-su">0</span>)</button>
      <button class="chip" data-filter="slow-all">All Slow (<span id="c-sa">0</span>)</button>
      <button class="chip" data-filter="all">All Tests (<span id="c-all">0</span>)</button>
    </div>
    <div class="tbl-wrap">
      <table>
        <colgroup>
          <col style="width:108px">
          <col>
          <col style="width:50px">
          <col style="width:40px">
          <col style="width:36px">
          <col style="width:44px">
          <col style="width:46px">
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

  <div class="card" id="symbol-lookup-card">
    <div class="section-head">
      <h2>Symbol &rarr; Covering Tests Lookup</h2>
      <span class="meta" id="sym-match-meta"></span>
    </div>
    <div class="controls">
      <input type="search" id="sym-search" style="flex:1;min-width:220px" placeholder="Type a symbol, Class.method, or file path (e.g. get_symbol_coverage_counts, DatabaseStore.connect)...">
      <button class="copy-btn" id="copy-via-cmd-btn" type="button" style="display:none">Copy via CLI</button>
    </div>
    <div class="sym-pills" id="sym-pills"></div>
    <div class="sym-summary" id="sym-summary"></div>
    <div class="tbl-wrap" style="max-height:280px">
      <table>
        <colgroup>
          <col style="width:108px">
          <col>
          <col style="width:54px">
          <col style="width:44px">
          <col style="width:50px">
        </colgroup>
        <thead>
          <tr>
            <th>Signal</th>
            <th>Covering Test (click row to filter audit table)</th>
            <th class="num">Dur (s)</th>
            <th class="num">Syms</th>
            <th class="num">Asserts</th>
          </tr>
        </thead>
        <tbody id="sym-tests-tbody"></tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="section-head">
      <h2>Coverage Safety Net — Risky Gaps</h2>
      <span class="meta" id="cov-net-meta"></span>
    </div>
    <div class="gaps-grid">
      <div>
        <div class="kpi-label" style="margin-bottom:6px">Modules Under 85% (Stmt + Branch)</div>
        <div class="tbl-wrap" style="max-height:280px">
          <table>
            <colgroup>
              <col>
              <col style="width:54px">
              <col style="width:52px">
              <col style="width:52px">
            </colgroup>
            <thead>
              <tr><th>Module</th><th class="num">Cover</th><th class="num">Miss St</th><th class="num">Miss Br</th></tr>
            </thead>
            <tbody id="low-mods-tbody"></tbody>
          </table>
        </div>
      </div>
      <div>
        <div class="kpi-label" style="margin-bottom:6px">Top 15 Uncovered Symbols (by LOC)</div>
        <div class="tbl-wrap" style="max-height:280px">
          <table>
            <colgroup>
              <col>
              <col style="width:60px">
              <col style="width:44px">
            </colgroup>
            <thead>
              <tr><th>Symbol</th><th>Type</th><th class="num">LOC</th></tr>
            </thead>
            <tbody id="uncov-syms-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="card playbook" id="agent-instructions">
    <div class="section-head">
      <h2>Agent Instructions — Resolving Slow, Overlapping &amp; Flaky Tests</h2>
      <button class="copy-btn" id="copy-playbook-btn" type="button">Copy Instructions</button>
    </div>
    <p class="note" style="margin-top:0">Follow this repeatable workflow when using this report to speed up and harden a test suite without losing validation coverage:</p>
    <h3>1. Triage by Signal (Worst ROI First)</h3>
    <ol>
      <li><strong><code>SLOW + 0 COV</code></strong> — Confirm whether the test spawns an uninstrumented subprocess (enable <code>coverage.py</code> <code>parallel = true</code>, <code>sigterm = true</code>, <code>patch = ["subprocess"]</code>, and per-test context propagation) or truly exercises no production code.</li>
      <li><strong><code>SLOW + LOW</code></strong> — Inspect for blind <code>time.sleep()</code> calls, slow server shutdown loops (e.g. <code>serve_forever(poll_interval=0.5)</code>), repeated heavy DB/index/HTTP setup, or unnecessary disk SQLite I/O.</li>
      <li><strong><code>SLOW + OVERLAP</code> / <code>SLOW + 0 UNIQ</code></strong> — Compare against the named faster neighbor and <strong>Asserts</strong> column. <em>Never delete a test solely because <code>Unique = 0</code></em>; different assertions on the same branches still validate distinct contracts.</li>
      <li><strong><code>MOCKS ONLY</code></strong> — Tests using mocks while covering <code>0</code> symbols in their imported project modules; check for hollow tests asserting only mock wiring.</li>
      <li><strong><code>Smelly Asserts</code></strong> — Static AST checks for false-green tests: <code>TAUTOLOGY</code> (<code>assert True</code> / <code>x == x</code>), <code>BROAD RAISES</code> (<code>pytest.raises(Exception)</code> without <code>match=</code>), <code>SWALLOWED ASSERT</code> (assert inside broad <code>try/except</code>), <code>CONDITIONAL ONLY</code> (all assertions inside <code>for</code>/<code>if</code> with no non-empty guard), <code>NO ASSERTS</code> (0 assertions), and <code>MOCK ASSERTS</code> (only <code>mock.assert_called*</code> with zero value checks).</li>
    </ol>
    <h3>2. Apply Fixes in Order of Preference</h3>
    <ol>
      <li><strong>Check symbol coverage before touching a test:</strong> Use the <em>Symbol &rarr; Covering Tests Lookup</em> above (or <code>via -mg '*' --via covers -mg '&lt;symbol&gt;' -n 0</code> / <code>--via covered-by -mg '*&lt;test&gt;*'</code>) to verify what another fast test already guards.</li>
      <li><strong>Harden smelly assertions (don't silence them):</strong> Add <code>assert len(items) &gt; 0</code> before dynamic loops (<code>LOOP/IF ONLY</code>); use <code>with pytest.raises(ConcreteError, match=...)</code> instead of <code>try/except</code> or bare <code>Exception</code> (<code>BROAD RAISES</code>); assert an observable post-condition (DB state, <code>caplog</code>, flag, or spy) even on <code>*_is_safe</code> / <code>*_does_not_raise</code> tests (<code>NO ASSERTS</code>); pair <code>assert_called*</code> with a real behavioral assertion (<code>MOCK ASSERTS</code>).</li>
      <li><strong>Prefer lower-resource equivalents:</strong> Test pure logic in-process with <code>:memory:</code> SQLite or direct function calls instead of booting HTTP servers or OS subprocesses when process boundaries are not under test.</li>
      <li><strong>Replace blind sleeps with event-driven waits:</strong> Launch subprocesses unbuffered (<code>python -u</code>) and wait on a condition/log line (e.g. <code>"Watching"</code>, <code>"Re-indexed:"</code>) rather than fixed delays. If faster signaling exposes a startup race (such as logging ready before installing signal handlers), fix the production race rather than re-adding sleeps.</li>
      <li><strong>Reuse expensive resources safely (prefer live sessions over pre-fetched snapshots):</strong> Share one <code>scope="class"</code> or <code>scope="module"</code> live server, session, indexed project, or daemon while keeping each test's actual request/operation inside the test body. Avoid pre-fetching multiple test responses into one snapshot dict in a fixture &mdash; snapshot fixtures attribute all coverage and setup failures to the first test and leave sibling tests with <code>0</code> covered symbols.</li>
      <li><strong>Prevent shared-resource flakiness (mandatory):</strong> Only share fixtures across strictly read-only tests, OR isolate side effects using disjoint target files plus output-buffer slicing (<code>mark()</code> / <code>output_since(mark)</code>) so no test can pass on an earlier test's output. Keep mutating, lifecycle, and shutdown tests isolated per test.</li>
      <li><strong>Don't mock away real production bottlenecks:</strong> If a single shared-fixture call stays slow (e.g. a multi-second query against a real index), profile the production code rather than faking it out.</li>
      <li><strong>Delete only proven duplicates:</strong> Remove a test only when a faster test already covers the same branch arcs <em>and</em> checks the same assertions (confirm via AST review or targeted mutation testing on the covered functions).</li>
    </ol>
    <h3>3. Verify Idempotently &amp; Know When to Stop</h3>
    <ol>
      <li>Run targeted modified files with <code>--durations=15</code> and confirm zero failures and zero pytest deprecation warnings (use <code>@classmethod</code> under <code>@pytest.fixture(scope="class")</code>).</li>
      <li>Re-run the full self-contained, idempotent coverage pipeline (<code>make test-coverage</code>: clean <code>.coverage*</code> shards &rarr; <code>via index .</code> &rarr; <code>pytest --cov-branch --cov-context=test</code> &rarr; <code>via coverage import-contexts</code> &rarr; <code>via coverage report</code>).</li>
      <li>Confirm wall-clock time and flagged test counts dropped with <strong>0% coverage loss</strong> and <strong>0 regressions</strong>. Once <code>Smelly Asserts = 0</code>, <code>Slow + 0 Cov = 0</code>, and the remaining slow tests are irreducible single-instance E2E boundaries (one daemon startup, one debounce window, one stdio handshake), stop optimizing and preserve E2E realism.</li>
    </ol>
  </div>
</div>

<script>
const DATA = __REPORT_DATA__;
const k = DATA.kpis;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

document.getElementById('gen-meta').textContent = `Generated ${DATA.generated_at} • ${k.total_tests.toLocaleString()} tests • ${k.total_dur}s total • overlap: ${DATA.overlap_mode}`;
document.getElementById('overlap-note').innerHTML = `<strong>Overlap (${esc(DATA.overlap_mode)})</strong> = highest Jaccard similarity (or strict subset <code>SUB</code>) against a <em>faster</em> test. Check <strong>Asserts</strong> &amp; the named faster neighbor before deleting — high overlap with distinct assertions is a fixture-sharing candidate.`;
const flaggedNow = k.flagged_count ?? (k.slow_zero_count + k.slow_low_count + k.slow_overlap_count + k.slow_0uniq_count + k.mocks_only_count + (k.smelly_flag_count || 0));
document.getElementById('c-flagged').textContent = flaggedNow;
document.getElementById('c-smell').textContent = k.smelly_count || 0;
document.getElementById('c-sl').textContent = k.slow_low_count;
document.getElementById('c-so').textContent = k.slow_overlap_count;
document.getElementById('c-su').textContent = k.slow_0uniq_count;
document.getElementById('c-sa').textContent = k.slow_count;
document.getElementById('c-all').textContent = k.total_tests;

const cov = DATA.coverage || {};
const regs = cov.newly_uncovered || [];
if (regs.length > 0) {
  document.getElementById('reg-banner').style.display = 'block';
  document.getElementById('reg-title').textContent = `Coverage Regression Alert: ${regs.length} symbol${regs.length === 1 ? '' : 's'} lost coverage vs. previous run`;
  document.getElementById('reg-list').innerHTML = regs.map(s => `<li>${esc(s)}</li>`).join('');
}
const cmp = cov.comparison;
const fmtDelta = (n, unit = '') => `${n > 0 ? '+' : ''}${n}${unit}`;
const durPctDelta = cmp && cmp.total_dur.before > 0
  ? Math.round((cmp.total_dur.delta / cmp.total_dur.before) * 100)
  : null;
const symDeltaText = cmp
  ? ` (${fmtDelta(cmp.covered_symbols.delta)})`
  : '';
const regText = regs.length > 0 ? `${regs.length} regressions` : (cov.has_previous ? '0 regressions' : 'baseline saved');
const kpis = [
  {
    label: 'Suite Duration',
    val: `${k.total_dur}s`,
    cls: cmp && cmp.total_dur.delta < 0 ? 'ok' : '',
    delta: cmp ? `${fmtDelta(cmp.total_dur.delta, 's')}${durPctDelta != null ? ` (${durPctDelta > 0 ? '+' : ''}${durPctDelta}%)` : ''}` : null,
    deltaCls: cmp ? (cmp.total_dur.delta < 0 ? 'b-ok' : cmp.total_dur.delta > 0 ? 'b-zero' : 'b-neutral') : '',
    sub: cmp ? `was ${cmp.total_dur.before}s • ${k.total_tests.toLocaleString()} tests` : `${k.total_tests.toLocaleString()} tests`,
  },
  {
    label: 'Slow Test Time',
    val: `${k.slow_dur}s`,
    cls: k.slow_count ? 'warn' : 'ok',
    delta: cmp ? fmtDelta(cmp.slow_dur.delta, 's') : null,
    deltaCls: cmp ? (cmp.slow_dur.delta < 0 ? 'b-ok' : cmp.slow_dur.delta > 0 ? 'b-zero' : 'b-neutral') : '',
    sub: `${k.slow_pct_time}% share • ${k.slow_count} slow (≥${k.slow_threshold}s)`,
  },
  {
    label: 'Flagged Tests',
    val: `${flaggedNow}`,
    cls: k.slow_zero_count ? 'danger' : flaggedNow ? 'warn' : 'ok',
    delta: cmp ? fmtDelta(cmp.flagged_count.delta) : null,
    deltaCls: cmp ? (cmp.flagged_count.delta < 0 ? 'b-ok' : cmp.flagged_count.delta > 0 ? 'b-zero' : 'b-neutral') : '',
    sub: `${k.slow_zero_count} zero • ${k.slow_low_count} low • ${k.slow_overlap_count} overlap${k.smelly_count ? ` • ${k.smelly_count} smelly` : ''}`,
  },
  {
    label: 'Coverage Safety Net',
    val: `${cov.cov_pct ?? 0}%`,
    cls: regs.length ? 'danger' : 'ok',
    delta: cmp ? fmtDelta(cmp.cov_pct.delta, '%') : null,
    deltaCls: cmp ? (regs.length > 0 || cmp.cov_pct.delta < -0.5 ? 'b-zero' : cmp.cov_pct.delta > 0 ? 'b-ok' : 'b-neutral') : '',
    sub: `${cov.covered_symbols ?? 0}/${cov.total_symbols ?? 0} syms${symDeltaText} • ${regText}`,
  },
];
document.getElementById('kpi-grid').innerHTML = kpis.map(x => `
  <div class="card">
    <div class="kpi-label">${esc(x.label)}</div>
    <div class="kpi-row">
      <div class="kpi-val ${x.cls}">${esc(x.val)}</div>
      ${x.delta != null ? `<span class="kpi-delta ${x.deltaCls}">${esc(x.delta)}</span>` : ''}
    </div>
    <div class="kpi-sub">${esc(x.sub)}</div>
  </div>`).join('');

const FLAG_META = {
  'slow-zero': { label: 'SLOW + 0 COV', cls: 'b-zero', color: '#ef4444' },
  'slow-low': { label: 'SLOW + LOW', cls: 'b-low', color: '#f97316' },
  'slow-overlap': { label: 'SLOW + OVERLAP', cls: 'b-ov', color: '#a855f7' },
  'slow-0uniq': { label: 'SLOW + 0 UNIQ', cls: 'b-red', color: '#eab308' },
  'mocks-only': { label: 'MOCKS ONLY', cls: 'b-low', color: '#f97316' },
  'smelly-assert': { label: 'SMELLY ASSERT', cls: 'b-smell', color: '#ec4899' },
  'ok': { label: 'OK', cls: 'b-ok', color: '#3b82f6' },
};

(function initScatter() {
  const prevPts = ((DATA.coverage && DATA.coverage.comparison && DATA.coverage.comparison.prev_scatter) || []).map(
    p => ({ test_id: p[0], dur: p[1], cov: p[2], flag: p[3] })
  );
  const hasPrev = prevPts.length > 0;
  const toggleEl = document.getElementById('scatter-mode-toggle');
  if (hasPrev) toggleEl.style.display = 'inline-flex';

  const W = 680, H = 265, padL = 48, padR = 20, padT = 16, padB = 34;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const allPts = hasPrev ? DATA.tests.concat(prevPts) : DATA.tests;
  const maxDur = Math.max(10, ...allPts.map(t => t.dur));
  const minLogX = Math.log10(0.001), maxLogX = Math.log10(maxDur);
  const maxY = Math.max(100, ...allPts.map(t => t.cov));
  const sx = d => padL + ((Math.log10(Math.max(0.001, d)) - minLogX) / (maxLogX - minLogX)) * plotW;
  const sy = c => padT + plotH - (c / maxY) * plotH;
  const xSlow = sx(k.slow_threshold), yLow = sy(20);

  const hexToRgb = hex => [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
  const rgbStr = c => `rgb(${Math.round(c[0])},${Math.round(c[1])},${Math.round(c[2])})`;
  const pointState = (t, fallback) => {
    const src = t || fallback;
    const isOk = src.flag === 'ok';
    const col = hexToRgb((FLAG_META[src.flag] || FLAG_META.ok).color);
    return {
      x: sx(src.dur),
      y: sy(src.cov),
      r: t ? (isOk ? 2.6 : 4.2) : 0,
      op: t ? (isOk ? 0.36 : 0.9) : 0,
      rgb: col,
      visible: Boolean(t),
    };
  };

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

  const afterById = new Map(DATA.tests.map(t => [t.test_id, t]));
  const beforeById = new Map(prevPts.map(t => [t.test_id, t]));
  const idSet = new Set([...afterById.keys(), ...beforeById.keys()]);
  const nodes = [...idSet].map(id => {
    const before = beforeById.get(id) || null;
    const after = afterById.get(id) || null;
    const stBefore = pointState(before, after);
    const stAfter = pointState(after, before);
    const priority = (before && before.flag !== 'ok') || (after && after.flag !== 'ok') ? 1 : 0;
    return {
      test_id: id,
      before,
      after,
      stBefore,
      stAfter,
      priority,
      cur: { x: stAfter.x, y: stAfter.y, r: stAfter.r, op: stAfter.op, rgb: [...stAfter.rgb] },
      el: null,
    };
  });
  nodes.sort((a, b) => a.priority - b.priority);

  const circlesSvg = nodes.map((n, idx) => {
    const c = n.cur;
    const pe = n.stAfter.visible ? 'auto' : 'none';
    return `<circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="${c.r.toFixed(2)}" fill="${rgbStr(c.rgb)}" fill-opacity="${c.op.toFixed(2)}" data-idx="${idx}" style="cursor:pointer;pointer-events:${pe}"/>`;
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
      ${circlesSvg}
    </svg>`;
  box.insertBefore(svgWrap, tip);

  let activeMode = 'after';
  let rafId = null;

  svgWrap.querySelectorAll('circle').forEach(c => {
    const n = nodes[Number(c.dataset.idx)];
    n.el = c;
    c.addEventListener('mouseenter', e => {
      const t = activeMode === 'before' ? n.before : n.after;
      if (!t) return;
      const rect = box.getBoundingClientRect();
      const tag = activeMode === 'before' ? ' <span class="badge b-low">BEFORE</span>' : '';
      const deltaLine = n.before && n.after
        ? `<div style="margin-top:2px;opacity:0.85">Before: ${n.before.dur.toFixed(3)}s (${n.before.cov} syms) &rarr; After: ${n.after.dur.toFixed(3)}s (${n.after.cov} syms)</div>`
        : '';
      tip.innerHTML = `<div class="mono" style="margin-bottom:4px"><strong>${esc(t.test_id)}</strong>${tag}</div>
        <div>Dur: <strong>${t.dur.toFixed(3)}s</strong> &bull; Syms: <strong>${t.cov}</strong>${t.uniq != null ? ` &bull; Uniq: <strong>${t.uniq}</strong> &bull; Asserts: <strong>${t.asserts ?? '—'}</strong>` : ''}</div>
        ${deltaLine}
        ${t.peer ? `<div style="margin-top:3px;opacity:0.85">Overlap: <strong>${t.subsumed ? 'SUB ' : ''}${t.overlap_pct}%</strong> vs <span class="mono">${esc(t.peer)}</span></div>` : ''}`;
      tip.style.display = 'block';
      tip.style.left = Math.min(rect.width - 370, Math.max(8, e.clientX - rect.left + 12)) + 'px';
      tip.style.top = Math.max(8, e.clientY - rect.top - 76) + 'px';
    });
    c.addEventListener('mouseleave', () => { tip.style.display = 'none'; });
    c.addEventListener('click', () => {
      document.getElementById('search-input').value = n.test_id;
      activeFilter = 'all';
      document.querySelectorAll('.chip').forEach(x => x.classList.toggle('active', x.dataset.filter === 'all'));
      renderTests();
    });
  });

  function applyNode(n, x, y, r, op, rgb, visible) {
    n.cur.x = x; n.cur.y = y; n.cur.r = r; n.cur.op = op; n.cur.rgb = rgb;
    n.el.setAttribute('cx', x.toFixed(1));
    n.el.setAttribute('cy', y.toFixed(1));
    n.el.setAttribute('r', r.toFixed(2));
    n.el.setAttribute('fill', rgbStr(rgb));
    n.el.setAttribute('fill-opacity', op.toFixed(2));
    n.el.style.pointerEvents = visible ? 'auto' : 'none';
  }

  function transitionTo(mode) {
    if (mode === activeMode) return;
    activeMode = mode;
    tip.style.display = 'none';
    if (rafId != null) cancelAnimationFrame(rafId);

    const targets = nodes.map(n => mode === 'before' ? n.stBefore : n.stAfter);
    const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) {
      nodes.forEach((n, i) => {
        const tg = targets[i];
        applyNode(n, tg.x, tg.y, tg.r, tg.op, [...tg.rgb], tg.visible);
      });
      return;
    }

    const starts = nodes.map(n => ({ x: n.cur.x, y: n.cur.y, r: n.cur.r, op: n.cur.op, rgb: [...n.cur.rgb] }));
    const duration = 650;
    const t0 = performance.now();
    const ease = u => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;

    function step(now) {
      const raw = Math.min(1, (now - t0) / duration);
      const e = ease(raw);
      for (let i = 0; i < nodes.length; i++) {
        const s = starts[i], tg = targets[i];
        const rgb = [
          s.rgb[0] + (tg.rgb[0] - s.rgb[0]) * e,
          s.rgb[1] + (tg.rgb[1] - s.rgb[1]) * e,
          s.rgb[2] + (tg.rgb[2] - s.rgb[2]) * e,
        ];
        applyNode(
          nodes[i],
          s.x + (tg.x - s.x) * e,
          s.y + (tg.y - s.y) * e,
          s.r + (tg.r - s.r) * e,
          s.op + (tg.op - s.op) * e,
          rgb,
          raw === 1 ? tg.visible : (s.op > 0 || tg.op > 0)
        );
      }
      if (raw < 1) {
        rafId = requestAnimationFrame(step);
      } else {
        rafId = null;
      }
    }
    rafId = requestAnimationFrame(step);
  }

  toggleEl.querySelectorAll('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      toggleEl.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      transitionTo(btn.dataset.mode);
    });
  });
})();

let activeFilter = 'flagged';
let sortState = { col: 'dur', dir: -1 };
const flagRank = { 'slow-zero': 0, 'slow-low': 1, 'slow-overlap': 2, 'slow-0uniq': 3, 'mocks-only': 4, 'smelly-assert': 5, 'ok': 6 };
const SMELL_META = {
  'tautology': { label: 'TAUTOLOGY', cls: 'b-zero', rank: 0 },
  'swallowed-assert': { label: 'SWALLOWED', cls: 'b-zero', rank: 1 },
  'broad-raises': { label: 'BROAD RAISES', cls: 'b-low', rank: 2 },
  'no-asserts': { label: 'NO ASSERTS', cls: 'b-low', rank: 3 },
  'conditional-only': { label: 'LOOP/IF ONLY', cls: 'b-red', rank: 4 },
  'mock-only-asserts': { label: 'MOCK ASSERTS', cls: 'b-smell', rank: 5 },
};
const bestSmellRank = t => {
  const sm = t.smells || [];
  return sm.length ? Math.min(...sm.map(s => (SMELL_META[s] ? SMELL_META[s].rank : 9))) : 9;
};

function renderTests() {
  const q = (document.getElementById('search-input').value || '').toLowerCase();
  let rows = DATA.tests.filter(t => {
    if (q && !t.test_id.toLowerCase().includes(q) && !(t.smell_detail || '').toLowerCase().includes(q)) return false;
    if (activeFilter === 'flagged') return t.flag !== 'ok';
    if (activeFilter === 'smelly') return (t.smells || []).length > 0;
    if (activeFilter === 'slow-all') return t.dur >= k.slow_threshold;
    if (activeFilter === 'all') return true;
    return t.flag === activeFilter;
  });
  rows.sort((a, b) => {
    if (activeFilter === 'smelly' && sortState.col === 'dur') {
      return (bestSmellRank(a) - bestSmellRank(b)) || (b.dur - a.dur);
    }
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
    const fm = FLAG_META[t.flag] || FLAG_META.ok;
    const ov = t.overlap_pct ? `${t.subsumed ? 'SUB ' : ''}${Math.round(t.overlap_pct)}%` : '—';
    const smells = t.smells || [];
    const primaryBadge = (t.flag === 'smelly-assert' && smells.length)
      ? ''
      : `<span class="badge ${fm.cls}">${fm.label}</span>`;
    const smellBadges = smells.map((s, idx) => {
      const sm = SMELL_META[s] || { label: s.toUpperCase(), cls: 'b-smell' };
      const top = primaryBadge || idx > 0 ? ' style="margin-top:3px"' : '';
      return `<div${top}><span class="badge ${sm.cls}">${sm.label}</span></div>`;
    }).join('');
    const smellHint = t.smell_detail ? `<div class="peer-hint">smell: ${esc(t.smell_detail)}</div>` : '';
    const sharedHint = t.shared_fixture ? `<div class="peer-hint">cov via shared fixture: ${esc(t.shared_fixture)}</div>` : '';
    const peerHtml = t.peer ? `<div class="peer-hint">&approx; ${esc(t.peer)}</div>` : '';
    return `<tr>
      <td>${primaryBadge}${smellBadges}</td>
      <td><div class="mono">${esc(t.test_id)}</div>${smellHint}${sharedHint}${peerHtml}</td>
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

if (cmp) {
  document.getElementById('before-after-card').style.display = 'block';
  const pctSaved = cmp.total_dur.before > 0 ? Math.round((-cmp.total_dur.delta / cmp.total_dur.before) * 100) : 0;
  document.getElementById('ba-meta').textContent = cmp.total_dur.delta < 0
    ? `${Math.abs(cmp.total_dur.delta)}s faster (${pctSaved}% reduction) • ${regs.length} coverage regressions`
    : `${cmp.total_dur.delta >= 0 ? '+' : ''}${cmp.total_dur.delta}s runtime change • ${regs.length} coverage regressions`;
  const fmtSigned = (n, unit='') => `${n > 0 ? '+' : ''}${n}${unit}`;
  const mRows = [
    { name: 'Total Test Duration', b: `${cmp.total_dur.before}s`, a: `${cmp.total_dur.after}s`, d: fmtSigned(cmp.total_dur.delta, 's'), good: cmp.total_dur.delta <= 0 },
    { name: `Slow Test Time (≥${k.slow_threshold}s)`, b: `${cmp.slow_dur.before}s`, a: `${cmp.slow_dur.after}s`, d: fmtSigned(cmp.slow_dur.delta, 's'), good: cmp.slow_dur.delta <= 0 },
    { name: 'Flagged Tests', b: `${cmp.flagged_count.before}`, a: `${cmp.flagged_count.after}`, d: fmtSigned(cmp.flagged_count.delta), good: cmp.flagged_count.delta <= 0 },
    { name: 'Coverage (Stmt + Branch)', b: `${cmp.cov_pct.before}%`, a: `${cmp.cov_pct.after}%`, d: fmtSigned(cmp.cov_pct.delta, '%'), good: cmp.cov_pct.delta >= -0.5 },
    { name: 'Covered Symbols', b: `${cmp.covered_symbols.before}`, a: `${cmp.covered_symbols.after}`, d: fmtSigned(cmp.covered_symbols.delta), good: cmp.covered_symbols.delta >= 0 && regs.length === 0 },
  ];
  document.getElementById('ba-metrics-tbody').innerHTML = mRows.map(r => `
    <tr>
      <td>${esc(r.name)}</td>
      <td class="num">${esc(r.b)}</td>
      <td class="num"><strong>${esc(r.a)}</strong></td>
      <td class="num"><span class="badge ${r.good ? 'b-ok' : 'b-zero'}">${esc(r.d)}</span></td>
    </tr>`).join('');
  document.getElementById('ba-files-tbody').innerHTML = (cmp.file_deltas || []).map(f => `
    <tr>
      <td class="mono">${esc(f.file)}</td>
      <td class="num">${f.before.toFixed(1)}s</td>
      <td class="num"><strong>${f.after.toFixed(1)}s</strong></td>
      <td class="num"><span class="badge ${f.delta <= 0 ? 'b-ok' : 'b-zero'}">${fmtSigned(f.delta.toFixed(1), 's')}</span></td>
    </tr>`).join('') || '<tr><td colspan="4">No per-file duration changes &ge; 0.5s.</td></tr>';
}

document.getElementById('cov-net-meta').textContent = `${cov.stmts ?? 0} stmts (${cov.miss_stmts ?? 0} missed) • ${cov.branches ?? 0} branches (${cov.miss_branches ?? 0} missed) • ${cov.uncovered_symbols ?? 0} uncovered symbols`;
document.getElementById('low-mods-tbody').innerHTML = (cov.low_modules || []).map(m => `
  <tr>
    <td class="mono">${esc(m.file)}</td>
    <td class="num"><span class="badge ${m.cover_pct < 60 ? 'b-zero' : 'b-low'}">${m.cover_pct}%</span></td>
    <td class="num">${m.miss_stmts}</td>
    <td class="num">${m.miss_branches}</td>
  </tr>`).join('') || '<tr><td colspan="4">All modules meet &ge;85% statement + branch coverage.</td></tr>';
document.getElementById('uncov-syms-tbody').innerHTML = (cov.uncovered_top || []).map(u => `
  <tr class="clickable-row" data-sym="${esc(u.symbol)}">
    <td class="mono">${esc(u.symbol)}</td>
    <td><span class="badge b-ok">${esc(u.type)}</span></td>
    <td class="num">${u.loc}</td>
  </tr>`).join('') || '<tr><td colspan="3">No uncovered production symbols.</td></tr>';

(function initSymbolLookup() {
  const syms = (DATA.symbols || []).map(s => {
    const key = s[0], colon = key.indexOf(':');
    const shortName = colon >= 0 ? key.slice(colon + 1) : key;
    const leafName = shortName.includes('.') ? shortName.slice(shortName.lastIndexOf('.') + 1) : shortName;
    return { key, shortName, leafName, lower: key.toLowerCase(), shortLower: shortName.toLowerCase(), leafLower: leafName.toLowerCase(), type: s[1], testIds: s[2] };
  });
  const searchEl = document.getElementById('sym-search');
  const metaEl = document.getElementById('sym-match-meta');
  const pillsEl = document.getElementById('sym-pills');
  const sumEl = document.getElementById('sym-summary');
  const tbodyEl = document.getElementById('sym-tests-tbody');
  const copyBtn = document.getElementById('copy-via-cmd-btn');
  if (!syms.length) {
    document.getElementById('symbol-lookup-card').style.display = 'none';
    return;
  }

  let selected = syms[0];
  let currentMatches = syms;

  function scoreMatch(s, q) {
    if (!q) return 0;
    if (s.leafLower === q || s.shortLower === q) return 0;
    if (s.leafLower.startsWith(q) || s.shortLower.startsWith(q)) return 1;
    if (s.shortLower.includes(q)) return 2;
    return 3;
  }

  function renderSelected() {
    if (!selected) {
      copyBtn.style.display = 'none';
      sumEl.innerHTML = '<span class="meta">No matching symbols.</span>';
      tbodyEl.innerHTML = '<tr><td colspan="5">No matching symbol selected.</td></tr>';
      return;
    }
    const covering = selected.testIds.map(i => DATA.tests[i]).filter(Boolean).sort((a, b) => a.dur - b.dur);
    copyBtn.style.display = 'inline-block';
    copyBtn.dataset.cmd = `via -mg '*' --via covers -mg '${selected.leafName}' -n 0`;
    const speedRange = covering.length
      ? ` &bull; fastest <strong>${covering[0].dur.toFixed(3)}s</strong> &bull; slowest <strong>${covering[covering.length - 1].dur.toFixed(3)}s</strong>`
      : '';
    const countBadge = covering.length
      ? `<span class="badge b-ok">${covering.length} test${covering.length === 1 ? '' : 's'}</span>`
      : '<span class="badge b-zero">0 tests (uncovered)</span>';
    sumEl.innerHTML = `<div><span class="mono"><strong>${esc(selected.key)}</strong></span> <span class="badge b-neutral">${esc(selected.type)}</span></div><div>${countBadge}${speedRange}</div>`;
    tbodyEl.innerHTML = covering.map(t => {
      const fm = FLAG_META[t.flag] || FLAG_META.ok;
      return `<tr class="clickable-row" data-tid="${esc(t.test_id)}">
        <td><span class="badge ${fm.cls}">${fm.label}</span></td>
        <td class="mono">${esc(t.test_id)}</td>
        <td class="num"><strong>${t.dur.toFixed(3)}</strong></td>
        <td class="num">${t.cov}</td>
        <td class="num">${t.asserts == null ? '—' : t.asserts}</td>
      </tr>`;
    }).join('') || '<tr><td colspan="5">No tests cover this symbol in the latest run.</td></tr>';
    tbodyEl.querySelectorAll('tr[data-tid]').forEach(tr => {
      tr.addEventListener('click', () => {
        document.getElementById('search-input').value = tr.dataset.tid;
        activeFilter = 'all';
        document.querySelectorAll('.chip').forEach(x => x.classList.toggle('active', x.dataset.filter === 'all'));
        renderTests();
      });
    });
  }

  function renderLookup() {
    const q = (searchEl.value || '').trim().toLowerCase();
    currentMatches = q
      ? syms.filter(s => s.lower.includes(q)).sort((a, b) => scoreMatch(a, q) - scoreMatch(b, q) || b.testIds.length - a.testIds.length || a.key.localeCompare(b.key))
      : syms;
    metaEl.textContent = q
      ? `${currentMatches.length} of ${syms.length} symbols match`
      : `${syms.length} production symbols (showing top 12 by test count)`;
    if (!currentMatches.includes(selected)) {
      selected = currentMatches[0] || null;
    }
    const topPills = currentMatches.slice(0, 12);
    pillsEl.innerHTML = topPills.map((s, idx) => `
      <button type="button" class="sym-pill${selected === s ? ' active' : ''}" data-pidx="${idx}" title="${esc(s.key)}">
        <span>${esc(s.shortName)}</span>
        <span class="badge ${s.testIds.length ? 'b-ok' : 'b-zero'}">${s.testIds.length}</span>
      </button>`).join('');
    pillsEl.querySelectorAll('.sym-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        selected = topPills[Number(btn.dataset.pidx)];
        pillsEl.querySelectorAll('.sym-pill').forEach(b => b.classList.toggle('active', b === btn));
        renderSelected();
      });
    });
    renderSelected();
  }

  searchEl.addEventListener('input', renderLookup);
  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(copyBtn.dataset.cmd || '');
      copyBtn.textContent = 'Copied!';
      setTimeout(() => { copyBtn.textContent = 'Copy via CLI'; }, 1500);
    } catch (_) {
      copyBtn.textContent = 'Copy unavailable';
    }
  });
  document.querySelectorAll('#uncov-syms-tbody tr[data-sym]').forEach(tr => {
    tr.addEventListener('click', () => {
      searchEl.value = tr.dataset.sym;
      renderLookup();
      document.getElementById('symbol-lookup-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  renderLookup();
})();

document.getElementById('copy-playbook-btn').addEventListener('click', async () => {
  const el = document.getElementById('agent-instructions');
  const btn = document.getElementById('copy-playbook-btn');
  const text = el.innerText.replace(/^Agent Instructions.*?Copy Instructions\\s*/s, 'Agent Instructions — Resolving Slow, Overlapping & Flaky Tests\\n\\n').trim();
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy Instructions'; }, 1500);
  } catch (_) {
    btn.textContent = 'Copy unavailable';
  }
});
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
    flagged = int(k.get('flagged_count', 0))
    print(
        f"Wrote test quality report: {out} "
        f"({k['total_tests']} tests, {flagged} flagged, overlap={payload['overlap_mode']})"
    )
    return EXIT_SUCCESS
