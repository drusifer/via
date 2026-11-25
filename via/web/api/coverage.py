"""
GET /api/coverage/hierarchy, GET /api/coverage/test-efficiency, and
GET /api/coverage/symbol handlers.

TLDR:
    Aggregates Sprint 27 Phase 1's per-test `covered-by` data into a
    hierarchical test-coverage-intensity tree (package -> module -> class ->
    method/function) for the web UI's D3 zoomable-icicle view (leaves sized
    by lines of code, colored by coverage intensity), plus a flat per-test
    efficiency table and a per-leaf drill-down (qualified name + docstring +
    signature, re-parsed from source on demand). Outlier detection compares
    each leaf symbol against its own peer group (symbol_type + constructor-
    likeness by naming convention) so constructors aren't flagged just for
    having naturally higher fan-in.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
import ast
import os
from statistics import mean, pstdev
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from via.db.store import DatabaseStore

# Naming-convention check for "expected to run often" symbols (per user
# directive: constructors shouldn't be flagged as outliers just for being
# constructors). No new capture needed — this is a pure name comparison.
_CONSTRUCTOR_LIKE_NAMES = {'__init__', '__new__', '__post_init__', '__call__'}

# z-score above which a symbol is flagged as an outlier within its peer group.
_OUTLIER_Z_THRESHOLD = 2.0

# Minimum peer-group size before any outlier call is made. Leave-one-out
# stdev from very few "other" points is itself noisy — a tight cluster of
# fewer than ~10 values can produce a spurious z > threshold from sampling
# noise alone (a single point a bit above the rest looks "extreme" when the
# baseline variance estimate is built from only 4-8 other points). Below
# this size there simply aren't enough peers to judge "unusual" against, so
# nothing in the group is flagged.
_MIN_PEER_GROUP_SIZE = 10


def _is_constructor_like(symbol_name: str) -> bool:
    return symbol_name in _CONSTRUCTOR_LIKE_NAMES


def _compute_outliers(leaves: List[Dict[str, Any]]) -> None:
    """Flag `is_outlier` in place, comparing each leaf to its peer group.

    Peer group = (symbol_type, is_constructor_like) so a constructor with an
    unusually high fan-in is only flagged relative to *other* constructors,
    not against ordinary methods.

    Uses leave-one-out statistics (each leaf compared against its peer
    group's mean/stdev *excluding itself*), not a naive z-score against the
    whole group. Including the candidate in its own mean/stdev caps its
    z-score at sqrt(n-1) as its value grows — for a 5-member group that cap
    is exactly 2.0, so a plain z-score could never cross a >2.0 threshold no
    matter how extreme the outlier. Leave-one-out avoids that self-dampening.
    """
    peer_groups: Dict[Tuple[str, bool], List[Dict[str, Any]]] = {}
    for leaf in leaves:
        key = (leaf['symbol_type'], _is_constructor_like(leaf['symbol_name']))
        peer_groups.setdefault(key, []).append(leaf)

    for group in peer_groups.values():
        if len(group) < _MIN_PEER_GROUP_SIZE:
            for leaf in group:
                leaf['is_outlier'] = False
            continue
        counts = [leaf['covering_test_count'] for leaf in group]
        for i, leaf in enumerate(group):
            others = counts[:i] + counts[i + 1:]
            mu = mean(others)
            sigma = pstdev(others)
            if sigma == 0:
                leaf['is_outlier'] = counts[i] != mu
            else:
                z = (counts[i] - mu) / sigma
                leaf['is_outlier'] = z > _OUTLIER_Z_THRESHOLD


def _drop_redundant_class_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop a class's own row when it has method children.

    `covered-by` attaches to the class symbol too (its line range spans all
    its methods), so a class with methods would otherwise carry both its own
    directly-attached fan-in *and* be re-derived as the mean of its methods —
    two different numbers for the same node. Classes with no methods (e.g. a
    plain dataclass with only attributes) keep their own row since they have
    no method descendants to aggregate instead.
    """
    method_parents = {
        (row['file_path'], row['parent_name'])
        for row in rows
        if row['symbol_type'] == 'method' and row['parent_name']
    }
    return [
        row for row in rows
        if not (row['symbol_type'] == 'class' and (row['file_path'], row['symbol_name']) in method_parents)
    ]


def _compute_loc(line_number: int, line_end: Any) -> int:
    """Lines-of-code for a symbol, for D3 icicle leaf sizing (per user
    directive: size = LOC, color = coverage intensity — two independent
    dimensions). Falls back to 1 for symbols indexed before the `line_end`
    column existed (schema v8) — until the project is re-indexed, those
    leaves render at minimum width rather than crashing on a NULL.
    """
    if line_end is None:
        return 1
    return max(1, line_end - line_number + 1)


def build_coverage_hierarchy(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a nested package/module/class/method tree with intensity_pct + outlier flags.

    Args:
        rows: symbol rows as returned by DatabaseStore.get_symbol_coverage_counts()
              (id, symbol_name, symbol_type, file_path, parent_name,
              line_number, line_end, covering_test_count).

    Returns:
        A tree: {"name", "type", "intensity_pct", "children": [...]}. Leaves
        additionally carry "id" (for the drill-down detail lookup), "loc"
        (lines of code — the frontend sizes icicle leaves by this, colors
        by intensity_pct), "covering_test_count", and "is_outlier". Each
        ancestor's intensity_pct is the mean across *all* leaf descendants
        (not a mean-of-child-means), per the architecture doc.
    """
    rows = _drop_redundant_class_rows(rows)

    leaves: List[Dict[str, Any]] = [
        {
            'id': row['id'],
            'symbol_name': row['symbol_name'],
            'symbol_type': row['symbol_type'],
            'file_path': row['file_path'],
            'parent_name': row['parent_name'],
            'covering_test_count': row['covering_test_count'],
            'intensity_pct': row['covering_test_count'] * 100,
            'loc': _compute_loc(row['line_number'], row.get('line_end')),
        }
        for row in rows
    ]
    _compute_outliers(leaves)

    root: Dict[str, Any] = {'name': '', 'type': 'root', 'children': {}}
    for leaf in leaves:
        parts = leaf['file_path'].split('/')
        packages, module = parts[:-1], parts[-1]

        node = root
        for pkg in packages:
            node = node['children'].setdefault(
                pkg, {'name': pkg, 'type': 'package', 'children': {}}
            )
        node = node['children'].setdefault(
            module, {'name': module, 'type': 'module', 'children': {}}
        )
        if leaf['symbol_type'] == 'method' and leaf['parent_name']:
            node = node['children'].setdefault(
                leaf['parent_name'],
                {'name': leaf['parent_name'], 'type': 'class', 'children': {}},
            )
        leaf_node = {
            'id': leaf['id'],
            'name': leaf['symbol_name'],
            'type': leaf['symbol_type'],
            'intensity_pct': leaf['intensity_pct'],
            'covering_test_count': leaf['covering_test_count'],
            'is_outlier': leaf['is_outlier'],
            'loc': leaf['loc'],
        }
        # Tuple key avoids collisions with sibling package/module/class string keys.
        node['children'][('leaf', leaf['symbol_name'], id(leaf))] = leaf_node

    def _finalize(node: Dict[str, Any]) -> Tuple[Dict[str, Any], List[float]]:
        if 'children' not in node:
            return node, [node['intensity_pct']]
        finalized_children = []
        leaf_values: List[float] = []
        for child in node['children'].values():
            finalized_child, child_leaf_values = _finalize(child)
            finalized_children.append(finalized_child)
            leaf_values.extend(child_leaf_values)
        result = {
            'name': node['name'],
            'type': node['type'],
            'intensity_pct': (sum(leaf_values) / len(leaf_values)) if leaf_values else 0.0,
            'children': finalized_children,
        }
        return result, leaf_values

    finalized, _ = _finalize(root)
    return finalized


def get_coverage_hierarchy(db_store: "DatabaseStore") -> Dict[str, Any]:
    """Build the coverage-intensity hierarchy tree from the live index."""
    rows = db_store.get_symbol_coverage_counts()
    return build_coverage_hierarchy(rows)


_MOCK_CONSTRUCTORS = frozenset({
    'Mock',
    'MagicMock',
    'AsyncMock',
    'NonCallableMock',
    'NonCallableMagicMock',
    'PropertyMock',
    'create_autospec',
})
_PATCH_ATTRS = frozenset({'object', 'dict', 'multiple'})


def _is_mock_call(node: ast.Call) -> bool:
    """Return True if `node` is a static mock constructor or patch call."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in _MOCK_CONSTRUCTORS or func.id == 'patch'
    if isinstance(func, ast.Attribute):
        if func.attr in _MOCK_CONSTRUCTORS or func.attr == 'patch':
            return True
        if func.attr in _PATCH_ATTRS:
            parent = func.value
            return (isinstance(parent, ast.Name) and parent.id == 'patch') or (
                isinstance(parent, ast.Attribute) and parent.attr == 'patch'
            )
    return False


def _count_mock_calls(nodes: List[ast.AST]) -> int:
    """Count AST Call nodes matching mock/patch patterns across `nodes`."""
    total = 0
    for root in nodes:
        for child in ast.walk(root):
            if isinstance(child, ast.Call) and _is_mock_call(child):
                total += 1
    return total


def _parse_python_file(file_path: str) -> Optional[ast.Module]:
    """Read and AST-parse a Python file, returning None on I/O or syntax errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return ast.parse(f.read())
    except (IOError, OSError, SyntaxError, UnicodeDecodeError):
        return None


def _module_to_rel_candidates(dotted: str) -> List[str]:
    base = dotted.replace('.', '/')
    return [f'{base}.py', f'{base}/__init__.py']


def _extract_import_candidates(nodes: List[ast.AST]) -> Set[str]:
    """Extract candidate relative `.py` paths referenced by imports in `nodes`."""
    candidates: Set[str] = set()
    for root in nodes:
        for child in ast.walk(root):
            if isinstance(child, ast.Import):
                for alias in child.names:
                    candidates.update(_module_to_rel_candidates(alias.name))
            elif isinstance(child, ast.ImportFrom) and child.module and child.level == 0:
                candidates.update(_module_to_rel_candidates(child.module))
                for alias in child.names:
                    if alias.name != '*':
                        candidates.update(_module_to_rel_candidates(f'{child.module}.{alias.name}'))
    return candidates


def _resolve_project_imports(
    candidates: Set[str], index_root: Optional[str], exclude_file: str
) -> Set[str]:
    """Keep candidate paths that exist as non-test project files under `index_root`."""
    if not index_root or not candidates:
        return set()
    excluded = os.path.realpath(exclude_file)
    resolved_rels: Set[str] = set()
    for rel in candidates:
        parts = rel.split('/')
        if parts[0] == 'tests' or parts[-1] == 'conftest.py':
            continue
        full = _resolve_under_root(index_root, rel)
        if full and full != excluded and os.path.isfile(full):
            resolved_rels.add(rel)
    return resolved_rels


def _analyze_test_file(
    file_path: str, index_root: Optional[str] = None
) -> Dict[Tuple[Optional[str], str], Tuple[int, Set[str]]]:
    """Single-pass AST analysis returning `(mock_count, imported_project_files)` per test."""
    tree = _parse_python_file(file_path)
    if tree is None:
        return {}

    top_level_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    module_imports = _resolve_project_imports(
        _extract_import_candidates(top_level_imports), index_root, file_path
    )

    analyzed: Dict[Tuple[Optional[str], str], Tuple[int, Set[str]]] = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_imports = _resolve_project_imports(
                _extract_import_candidates([stmt]), index_root, file_path
            )
            analyzed[(None, stmt.name)] = (_count_mock_calls([stmt]), module_imports | local_imports)
        elif isinstance(stmt, ast.ClassDef):
            class_mocks = _count_mock_calls(stmt.decorator_list)
            for item in stmt.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    local_imports = _resolve_project_imports(
                        _extract_import_candidates([item]), index_root, file_path
                    )
                    analyzed[(stmt.name, item.name)] = (
                        class_mocks + _count_mock_calls([item]),
                        module_imports | local_imports,
                    )
    return analyzed


def count_mock_usages_in_file(file_path: str) -> Dict[Tuple[Optional[str], str], int]:
    """Statically count unittest.mock / patch usages per function/method in a Python file."""
    return {key: count for key, (count, _) in _analyze_test_file(file_path).items()}


def _parse_test_nodeid(test_id: str) -> Optional[Tuple[str, Optional[str], str]]:
    """Parse a pytest nodeid into `(rel_file_path, class_name_or_None, func_name)`."""
    parts = test_id.split('::')
    if len(parts) < 2:
        return None
    rel_path = parts[0]
    func_name = parts[-1].split('[', 1)[0]
    class_name = parts[1] if len(parts) >= 3 else None
    return rel_path, class_name, func_name


def _resolve_under_root(index_root: str, rel_path: str) -> Optional[str]:
    """Resolve `rel_path` strictly inside `index_root`, rejecting path traversal."""
    root_real = os.path.realpath(index_root)
    candidate = os.path.realpath(os.path.join(root_real, rel_path))
    try:
        if os.path.commonpath([root_real, candidate]) != root_real:
            return None
    except ValueError:
        return None
    return candidate


def get_test_efficiency(db_store: "DatabaseStore") -> List[Dict[str, Any]]:
    """Return per-test efficiency rows with symbols_per_second, mock_call_count,
    imported_module_covered_count, and mocks_only.

    `imported_module_covered_count` sums `covered-by` symbols belonging to the
    project modules imported by that test (None when no project module imports
    can be resolved). `mocks_only` is True when a test uses mocks
    (`mock_call_count > 0`) and covers 0 symbols in its imported project modules.
    """
    rows = db_store.get_test_efficiency_data()
    covered_by_file = db_store.get_test_covered_file_counts()
    file_cache: Dict[str, Dict[Tuple[Optional[str], str], Tuple[int, Set[str]]]] = {}
    results = []
    for row in rows:
        duration = row['duration_seconds']
        covered = row['covered_symbol_count']
        symbols_per_second = (covered / duration) if duration > 0 else None
        mock_call_count, imported_covered = _lookup_test_mock_and_import_coverage(
            row['test_id'], db_store.index_root, covered_by_file.get(row['test_id'], {}), file_cache
        )
        mocks_only = bool(mock_call_count and imported_covered == 0)
        results.append({
            **row,
            'symbols_per_second': symbols_per_second,
            'mock_call_count': mock_call_count,
            'imported_module_covered_count': imported_covered,
            'mocks_only': mocks_only,
        })
    return results


def _lookup_test_mock_and_import_coverage(
    test_id: str,
    index_root: str,
    test_file_counts: Dict[str, int],
    file_cache: Dict[str, Dict[Tuple[Optional[str], str], Tuple[int, Set[str]]]],
) -> Tuple[Optional[int], Optional[int]]:
    parsed = _parse_test_nodeid(test_id)
    if parsed is None:
        return None, None
    rel_path, class_name, func_name = parsed
    resolved = _resolve_under_root(index_root, rel_path)
    if resolved is None:
        return None, None
    if resolved not in file_cache:
        file_cache[resolved] = _analyze_test_file(resolved, index_root)
    entry = file_cache[resolved].get((class_name, func_name))
    if entry is None:
        return None, None
    mock_count, imported_files = entry
    if not imported_files:
        return mock_count, None
    imported_covered = sum(test_file_counts.get(f, 0) for f in imported_files)
    return mock_count, imported_covered


def _extract_signature_and_docstring(
    file_path: str, line_number: int, symbol_name: str
) -> Dict[str, Optional[str]]:
    """Re-parse a Python source file to get one symbol's docstring + signature.

    Mirrors `via/renderers/usage.py`'s `UsageRenderer._extract_docstring`
    approach (match by line number, fall back to name-only) rather than
    persisting docstring/args at index time — this is a drill-down-only,
    on-demand lookup, not something every query needs to pay for.

    Returns:
        dict with keys 'signature' and 'docstring' (either may be None —
        e.g. a non-Python symbol, an unreadable/unparseable file, or a
        match that couldn't be located).
    """
    tree = _parse_python_file(file_path)
    if tree is None:
        return {'signature': None, 'docstring': None}

    target_node = None
    for node in ast.walk(tree):
        if not hasattr(node, 'lineno'):
            continue
        is_matching_type = isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        if is_matching_type and node.lineno == line_number and node.name == symbol_name:
            target_node = node
            break
    if target_node is None:
        # Fallback: name-only match anywhere in the file (source may have
        # shifted a line or two since the last index).
        for node in ast.walk(tree):
            is_matching_type = isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            if is_matching_type and getattr(node, 'name', None) == symbol_name:
                target_node = node
                break
    if target_node is None:
        return {'signature': None, 'docstring': None}

    docstring = ast.get_docstring(target_node)
    signature = None
    if isinstance(target_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        signature = f"{target_node.name}({_format_args(target_node.args)})"
    return {'signature': signature, 'docstring': docstring}


def _format_args(args: "ast.arguments") -> str:
    """Render an ast.arguments node as a comma-joined signature string."""
    parts = []
    for arg in args.args:
        part = arg.arg
        if arg.annotation is not None and hasattr(ast, 'unparse'):
            part += f": {ast.unparse(arg.annotation)}"
        parts.append(part)
    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    for arg in args.kwonlyargs:
        part = arg.arg
        if arg.annotation is not None and hasattr(ast, 'unparse'):
            part += f": {ast.unparse(arg.annotation)}"
        parts.append(part)
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")
    return ', '.join(parts)


def get_symbol_detail(db_store: "DatabaseStore", symbol_id: int) -> Optional[Dict[str, Any]]:
    """Drill-down detail for one coverage-heatmap leaf (Cypher AC7, per user
    directive 2026-07-02): qualified name + docstring + signature for
    functions/methods, or just qualified name/location for other types
    (e.g. classes, or non-Python languages where AST re-parsing doesn't
    apply — degrades gracefully rather than erroring).
    """
    symbol = db_store.get_symbol_detail(symbol_id)
    if symbol is None:
        return None

    detail = {**symbol, 'signature': None, 'docstring': None}
    if symbol['language'] == 'python' and symbol['symbol_type'] in ('function', 'method', 'class'):
        extracted = _extract_signature_and_docstring(
            symbol['file_path'], symbol['line_number'], symbol['symbol_name']
        )
        detail.update(extracted)
    return detail
