"""Unit tests for Sprint 27 Phase 2 coverage visualization — Cycle 1.

TLDR:
    Tests DatabaseStore.get_symbol_coverage_counts()/get_test_efficiency_data()/
    get_symbol_detail() against a real in-memory-backed SQLite DB, the pure
    hierarchy-build + outlier-detection + LOC-sizing logic in
    via/web/api/coverage.py, the docstring/signature re-extraction used by
    the leaf drill-down (AC7), and the three /api/coverage/* routes
    end-to-end over real HTTP (catches wiring/typo bugs a pure
    function-level test wouldn't). Role: protects the data layer feeding
    the D3 intensity-heatmap view.
"""
import http.client
import itertools
import json
import os

import pytest

from via.db.store import DatabaseStore
from via.web.api.coverage import (
    build_coverage_hierarchy,
    get_coverage_hierarchy,
    get_symbol_detail,
    get_test_efficiency,
)
from via.web.server import WebServer


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    root = str(tmp_path)
    store = DatabaseStore(db_path, root)
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


def _insert_test_symbol(store: DatabaseStore, test_id: str) -> int:
    return store.insert_symbol(
        symbol_name=test_id, symbol_type='test', file_path='<test>',
        line_number=0, qualified_name=test_id,
    )


def _insert_code_symbol(store, name, symbol_type, file_path, parent_name=None,
                         line_number=1, line_end=None, language='python'):
    # symbols.file_path is stored absolute in real usage (see
    # core/discovery.py FileInfo.path) and get_symbol_coverage_counts()
    # relativizes it against store.index_root — so tests must insert a real
    # absolute path under index_root for that round-trip to reproduce the
    # given relative-looking `file_path`, same as the real indexing path.
    qualified = f"{parent_name}.{name}" if parent_name else name
    abs_file_path = os.path.join(store.index_root, file_path)
    return store.insert_symbol(
        symbol_name=name, symbol_type=symbol_type, file_path=abs_file_path,
        line_number=line_number, line_end=line_end, qualified_name=qualified,
        parent_name=parent_name, language=language,
    )


def _cover(store, symbol_id, test_symbol_id):
    store.insert_relationship(symbol_id, test_symbol_id, 'covered-by')


# ---------------------------------------------------------------------------
# DatabaseStore.get_symbol_coverage_counts()
# ---------------------------------------------------------------------------

class TestGetSymbolCoverageCounts:
    def test_empty_db_returns_empty_list(self, tmp_db):
        assert tmp_db.get_symbol_coverage_counts() == []

    def test_uncovered_symbol_has_zero_count(self, tmp_db):
        _insert_code_symbol(tmp_db, 'foo', 'function', 'pkg/mod.py')
        rows = tmp_db.get_symbol_coverage_counts()
        assert len(rows) == 1
        assert rows[0]['covering_test_count'] == 0

    def test_counts_distinct_covering_tests(self, tmp_db):
        sym_id = _insert_code_symbol(tmp_db, 'foo', 'function', 'pkg/mod.py')
        t1 = _insert_test_symbol(tmp_db, 'tests/test_a.py::test_1')
        t2 = _insert_test_symbol(tmp_db, 'tests/test_a.py::test_2')
        _cover(tmp_db, sym_id, t1)
        _cover(tmp_db, sym_id, t2)
        rows = tmp_db.get_symbol_coverage_counts()
        assert rows[0]['covering_test_count'] == 2

    def test_excludes_test_symbols_themselves(self, tmp_db):
        _insert_test_symbol(tmp_db, 'tests/test_a.py::test_1')
        rows = tmp_db.get_symbol_coverage_counts()
        assert rows == []

    def test_includes_class_and_method_and_function(self, tmp_db):
        _insert_code_symbol(tmp_db, 'Foo', 'class', 'pkg/mod.py')
        _insert_code_symbol(tmp_db, 'bar', 'method', 'pkg/mod.py', parent_name='Foo')
        _insert_code_symbol(tmp_db, 'baz', 'function', 'pkg/mod.py')
        rows = tmp_db.get_symbol_coverage_counts()
        types = {row['symbol_type'] for row in rows}
        assert types == {'class', 'method', 'function'}


# ---------------------------------------------------------------------------
# DatabaseStore.get_test_efficiency_data()
# ---------------------------------------------------------------------------

class TestGetTestEfficiencyData:
    def test_empty_db_returns_empty_list(self, tmp_db):
        assert tmp_db.get_test_efficiency_data() == []

    def test_joins_duration_and_covered_count(self, tmp_db):
        sym_id = _insert_code_symbol(tmp_db, 'foo', 'function', 'pkg/mod.py')
        test_id = 'tests/test_a.py::test_1'
        t_sym = _insert_test_symbol(tmp_db, test_id)
        _cover(tmp_db, sym_id, t_sym)
        tmp_db.upsert_test_run(test_id, 'pass', 1.5, '2026-07-01T00:00:00+00:00')

        rows = tmp_db.get_test_efficiency_data()
        assert len(rows) == 1
        assert rows[0]['test_id'] == test_id
        assert rows[0]['duration_seconds'] == 1.5
        assert rows[0]['covered_symbol_count'] == 1

    def test_test_with_no_coverage_has_zero_count(self, tmp_db):
        test_id = 'tests/test_a.py::test_1'
        _insert_test_symbol(tmp_db, test_id)
        tmp_db.upsert_test_run(test_id, 'pass', 0.1, '2026-07-01T00:00:00+00:00')
        rows = tmp_db.get_test_efficiency_data()
        assert rows[0]['covered_symbol_count'] == 0


# ---------------------------------------------------------------------------
# build_coverage_hierarchy() — pure logic
# ---------------------------------------------------------------------------

_row_id_counter = itertools.count(1)


def _row(symbol_name, symbol_type, file_path, parent_name=None, covering_test_count=0,
         line_number=1, line_end=None, id=None):  # noqa: A002 - matches DB column name
    return {
        'id': id if id is not None else next(_row_id_counter),
        'symbol_name': symbol_name, 'symbol_type': symbol_type,
        'file_path': file_path, 'parent_name': parent_name,
        'covering_test_count': covering_test_count,
        'line_number': line_number, 'line_end': line_end,
    }


class TestBuildCoverageHierarchy:
    def test_empty_rows_yields_zero_intensity_root(self):
        tree = build_coverage_hierarchy([])
        assert tree['intensity_pct'] == 0.0
        assert tree['children'] == []

    def test_single_function_becomes_leaf_under_package_and_module(self):
        rows = [_row('foo', 'function', 'pkg/mod.py', covering_test_count=1)]
        tree = build_coverage_hierarchy(rows)
        pkg = tree['children'][0]
        assert pkg['name'] == 'pkg'
        assert pkg['type'] == 'package'
        mod = pkg['children'][0]
        assert mod['name'] == 'mod.py'
        assert mod['type'] == 'module'
        leaf = mod['children'][0]
        assert leaf['name'] == 'foo'
        assert leaf['intensity_pct'] == 100.0
        assert leaf['covering_test_count'] == 1

    def test_leaf_carries_id_for_drill_down_lookup(self):
        rows = [_row('foo', 'function', 'mod.py', id=42)]
        tree = build_coverage_hierarchy(rows)
        leaf = tree['children'][0]['children'][0]
        assert leaf['id'] == 42

    def test_leaf_loc_computed_from_line_span(self):
        rows = [_row('foo', 'function', 'mod.py', line_number=10, line_end=19)]
        tree = build_coverage_hierarchy(rows)
        leaf = tree['children'][0]['children'][0]
        assert leaf['loc'] == 10

    def test_leaf_loc_defaults_to_one_when_line_end_missing(self):
        # Symbols indexed before the line_end column existed (schema v8)
        # have line_end=NULL until re-indexed — must not crash, size to 1.
        rows = [_row('foo', 'function', 'mod.py', line_number=10, line_end=None)]
        tree = build_coverage_hierarchy(rows)
        leaf = tree['children'][0]['children'][0]
        assert leaf['loc'] == 1

    def test_leaf_loc_is_at_least_one_for_single_line_symbol(self):
        rows = [_row('foo', 'function', 'mod.py', line_number=5, line_end=5)]
        tree = build_coverage_hierarchy(rows)
        leaf = tree['children'][0]['children'][0]
        assert leaf['loc'] == 1

    def test_intensity_pct_scales_with_covering_test_count(self):
        rows = [_row('foo', 'function', 'mod.py', covering_test_count=3)]
        tree = build_coverage_hierarchy(rows)
        leaf = tree['children'][0]['children'][0]
        assert leaf['intensity_pct'] == 300.0

    def test_uncovered_symbol_is_zero_percent(self):
        rows = [_row('foo', 'function', 'mod.py', covering_test_count=0)]
        tree = build_coverage_hierarchy(rows)
        leaf = tree['children'][0]['children'][0]
        assert leaf['intensity_pct'] == 0.0

    def test_method_nests_under_class_node(self):
        rows = [
            _row('Foo', 'class', 'mod.py', covering_test_count=0),
            _row('bar', 'method', 'mod.py', parent_name='Foo', covering_test_count=1),
        ]
        tree = build_coverage_hierarchy(rows)
        module = tree['children'][0]
        cls = module['children'][0]
        assert cls['name'] == 'Foo'
        assert cls['type'] == 'class'
        assert cls['children'][0]['name'] == 'bar'

    def test_class_own_row_dropped_when_it_has_methods(self):
        # Class's own directly-attached fan-in (5) would double-count against
        # its method's fan-in (1) — the class node should reflect only the
        # method's rollup (100%), not its own row.
        rows = [
            _row('Foo', 'class', 'mod.py', covering_test_count=5),
            _row('bar', 'method', 'mod.py', parent_name='Foo', covering_test_count=1),
        ]
        tree = build_coverage_hierarchy(rows)
        cls = tree['children'][0]['children'][0]
        assert len(cls['children']) == 1
        assert cls['children'][0]['name'] == 'bar'
        assert cls['intensity_pct'] == 100.0

    def test_class_with_no_methods_keeps_own_row(self):
        rows = [_row('Foo', 'class', 'mod.py', covering_test_count=2)]
        tree = build_coverage_hierarchy(rows)
        module = tree['children'][0]
        assert len(module['children']) == 1
        assert module['children'][0]['name'] == 'Foo'
        assert module['children'][0]['intensity_pct'] == 200.0

    def test_ancestor_intensity_is_mean_of_all_leaf_descendants_not_mean_of_children(self):
        # package/mod_a.py has 1 leaf at 100%; package/mod_b.py has 3 leaves
        # at 100/100/700%. A naive mean-of-child-means would average
        # (100 + 300) / 2 = 200 at the package level; the correct flattened
        # mean across all 4 leaves is (100+100+100+700)/4 = 250.
        rows = [
            _row('f1', 'function', 'package/mod_a.py', covering_test_count=1),
            _row('f2', 'function', 'package/mod_b.py', covering_test_count=1),
            _row('f3', 'function', 'package/mod_b.py', covering_test_count=1),
            _row('f4', 'function', 'package/mod_b.py', covering_test_count=7),
        ]
        tree = build_coverage_hierarchy(rows)
        pkg = tree['children'][0]
        assert pkg['intensity_pct'] == 250.0

    def test_arbitrary_directory_depth_is_preserved(self):
        rows = [_row('f', 'function', 'a/b/c/d.py', covering_test_count=1)]
        tree = build_coverage_hierarchy(rows)
        node = tree
        names = []
        while node.get('children'):
            node = node['children'][0]
            names.append(node['name'])
        assert names == ['a', 'b', 'c', 'd.py', 'f']

    def test_constructor_high_fan_in_not_flagged_among_ordinary_methods(self):
        # __init__ with high fan-in shouldn't be flagged just for being a
        # constructor when compared against a peer group of *other*
        # constructors with similarly high fan-in. 10 members — realistic
        # peer-group size (a project has many classes) and above
        # _MIN_PEER_GROUP_SIZE, so this exercises real leave-one-out stats
        # rather than trivially passing via the too-small-to-judge path.
        counts = [48, 49, 50, 51, 52, 48, 49, 50, 51, 52]
        rows = [
            _row('__init__', 'method', f'{chr(97 + i)}.py', parent_name=chr(65 + i),
                 covering_test_count=count)
            for i, count in enumerate(counts)
        ]
        tree = build_coverage_hierarchy(rows)
        leaves = _collect_leaves(tree)
        assert all(not leaf['is_outlier'] for leaf in leaves)

    def test_planted_outlier_is_flagged_within_its_peer_group(self):
        # 9 identical baseline methods + 1 genuine outlier — above
        # _MIN_PEER_GROUP_SIZE so real leave-one-out detection applies.
        rows = [
            _row(f'ordinary_{i}', 'method', f'{chr(97 + i)}.py', parent_name=chr(65 + i),
                 covering_test_count=1)
            for i in range(9)
        ]
        rows.append(
            _row('outlier_method', 'method', 'j.py', parent_name='J', covering_test_count=40)
        )
        tree = build_coverage_hierarchy(rows)
        leaves = _collect_leaves(tree)
        outliers = [leaf for leaf in leaves if leaf['is_outlier']]
        assert len(outliers) == 1
        assert outliers[0]['name'] == 'outlier_method'

    def test_single_member_peer_group_is_never_flagged(self):
        rows = [_row('only_one', 'function', 'mod.py', covering_test_count=999)]
        tree = build_coverage_hierarchy(rows)
        leaf = tree['children'][0]['children'][0]
        assert leaf['is_outlier'] is False


def _collect_leaves(node):
    if not node.get('children'):
        return [node] if 'is_outlier' in node else []
    leaves = []
    for child in node['children']:
        leaves.extend(_collect_leaves(child))
    return leaves


# ---------------------------------------------------------------------------
# get_coverage_hierarchy() / get_test_efficiency() — wrapper wiring
# ---------------------------------------------------------------------------

class TestGetCoverageHierarchyWrapper:
    def test_wraps_store_data_into_tree(self, tmp_db):
        sym_id = _insert_code_symbol(tmp_db, 'foo', 'function', 'pkg/mod.py')
        t_sym = _insert_test_symbol(tmp_db, 'tests/test_a.py::test_1')
        _cover(tmp_db, sym_id, t_sym)
        tree = get_coverage_hierarchy(tmp_db)
        leaf = tree['children'][0]['children'][0]['children'][0]
        assert leaf['name'] == 'foo'
        assert leaf['intensity_pct'] == 100.0


class TestGetTestEfficiencyWrapper:
    def test_computes_symbols_per_second(self, tmp_db):
        sym_id = _insert_code_symbol(tmp_db, 'foo', 'function', 'mod.py')
        test_id = 'tests/test_a.py::test_1'
        t_sym = _insert_test_symbol(tmp_db, test_id)
        _cover(tmp_db, sym_id, t_sym)
        tmp_db.upsert_test_run(test_id, 'pass', 2.0, '2026-07-01T00:00:00+00:00')

        results = get_test_efficiency(tmp_db)
        assert results[0]['symbols_per_second'] == 0.5

    def test_zero_duration_gives_none_not_infinity(self, tmp_db):
        test_id = 'tests/test_a.py::test_1'
        _insert_test_symbol(tmp_db, test_id)
        tmp_db.upsert_test_run(test_id, 'pass', 0.0, '2026-07-01T00:00:00+00:00')
        results = get_test_efficiency(tmp_db)
        assert results[0]['symbols_per_second'] is None


# ---------------------------------------------------------------------------
# GET /api/coverage/hierarchy and GET /api/coverage/test-efficiency — real HTTP
# ---------------------------------------------------------------------------

def _get(port: int, path: str) -> http.client.HTTPResponse:
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    resp.body = resp.read()
    conn.close()
    return resp


class TestCoverageEndpointsHTTP:
    def test_hierarchy_endpoint_returns_tree(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        sym_id = _insert_code_symbol(store, 'foo', 'function', 'pkg/mod.py')
        t_sym = _insert_test_symbol(store, 'tests/test_a.py::test_1')
        _cover(store, sym_id, t_sym)
        store.close()

        srv = WebServer(port=0, db_path=db_path, index_root=str(tmp_path))
        srv.start()
        try:
            resp = _get(srv.port, "/api/coverage/hierarchy")
            assert resp.status == 200
            tree = json.loads(resp.body)
            leaf = tree['children'][0]['children'][0]['children'][0]
            assert leaf['name'] == 'foo'
            assert leaf['intensity_pct'] == 100.0
        finally:
            srv.stop()

    def test_test_efficiency_endpoint_returns_results(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        test_id = 'tests/test_a.py::test_1'
        _insert_test_symbol(store, test_id)
        store.upsert_test_run(test_id, 'pass', 2.0, '2026-07-01T00:00:00+00:00')
        store.close()

        srv = WebServer(port=0, db_path=db_path, index_root=str(tmp_path))
        srv.start()
        try:
            resp = _get(srv.port, "/api/coverage/test-efficiency")
            assert resp.status == 200
            data = json.loads(resp.body)
            assert data['results'][0]['test_id'] == test_id
        finally:
            srv.stop()


# ---------------------------------------------------------------------------
# get_symbol_detail() — leaf drill-down (Cypher AC7)
# ---------------------------------------------------------------------------

class TestDatabaseStoreGetSymbolDetail:
    def test_returns_none_for_unknown_id(self, tmp_db):
        assert tmp_db.get_symbol_detail(999) is None

    def test_returns_identifying_fields(self, tmp_db):
        sym_id = _insert_code_symbol(tmp_db, 'foo', 'function', 'mod.py')
        detail = tmp_db.get_symbol_detail(sym_id)
        assert detail['symbol_name'] == 'foo'
        assert detail['symbol_type'] == 'function'
        assert detail['qualified_name'] == 'foo'
        assert detail['language'] == 'python'

    def test_file_path_is_absolute_not_relativized(self, tmp_db):
        # Unlike get_symbol_coverage_counts(), this needs the real absolute
        # path so the caller can actually open the file on disk.
        sym_id = _insert_code_symbol(tmp_db, 'foo', 'function', 'pkg/mod.py')
        detail = tmp_db.get_symbol_detail(sym_id)
        assert detail['file_path'] == os.path.join(tmp_db.index_root, 'pkg/mod.py')


class TestExtractSignatureAndDocstring:
    def test_extracts_function_docstring_and_signature(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "mod.py"
        src.write_text(
            "def greet(name: str, times: int = 1) -> str:\n"
            "    '''Say hello.'''\n"
            "    return f'hi {name}' * times\n"
        )
        result = _extract_signature_and_docstring(str(src), 1, 'greet')
        assert result['docstring'] == 'Say hello.'
        # No default values shown, matching python_parser.py's _extract_args
        # convention (names + annotations only).
        assert result['signature'] == 'greet(name: str, times: int)'

    def test_extracts_class_docstring_with_no_signature(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "mod.py"
        src.write_text(
            "class Foo:\n"
            "    '''A foo.'''\n"
            "    def bar(self):\n"
            "        pass\n"
        )
        result = _extract_signature_and_docstring(str(src), 1, 'Foo')
        assert result['docstring'] == 'A foo.'
        assert result['signature'] is None

    def test_no_docstring_returns_none_not_empty_string(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "mod.py"
        src.write_text("def bare():\n    return 1\n")
        result = _extract_signature_and_docstring(str(src), 1, 'bare')
        assert result['docstring'] is None
        assert result['signature'] == 'bare()'

    def test_signature_includes_varargs_and_kwargs(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "mod.py"
        src.write_text("def f(a, *args, b=1, **kwargs):\n    pass\n")
        result = _extract_signature_and_docstring(str(src), 1, 'f')
        # Matches the argument-listing convention already used elsewhere in
        # this codebase (python_parser.py's _extract_args): names +
        # annotations, no default values shown.
        assert result['signature'] == 'f(a, *args, b, **kwargs)'

    def test_falls_back_to_name_only_match_if_line_shifted(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "mod.py"
        src.write_text(
            "\n\n\n"  # 3 leading blank lines shift 'greet' off line 1
            "def greet():\n"
            "    '''Hi.'''\n"
            "    pass\n"
        )
        result = _extract_signature_and_docstring(str(src), 1, 'greet')
        assert result['docstring'] == 'Hi.'

    def test_symbol_not_found_even_by_name_returns_none_none(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "mod.py"
        src.write_text("def other():\n    pass\n")
        result = _extract_signature_and_docstring(str(src), 1, 'does_not_exist')
        assert result == {'signature': None, 'docstring': None}

    def test_signature_includes_annotated_kwonly_arg(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "mod.py"
        src.write_text("def f(*, b: int):\n    pass\n")
        result = _extract_signature_and_docstring(str(src), 1, 'f')
        assert result['signature'] == 'f(b: int)'

    def test_unreadable_file_returns_none_none_not_raise(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        result = _extract_signature_and_docstring(str(tmp_path / "does_not_exist.py"), 1, 'x')
        assert result == {'signature': None, 'docstring': None}

    def test_unparseable_file_returns_none_none_not_raise(self, tmp_path):
        from via.web.api.coverage import _extract_signature_and_docstring

        src = tmp_path / "broken.py"
        src.write_text("def (:::not valid python")
        result = _extract_signature_and_docstring(str(src), 1, 'x')
        assert result == {'signature': None, 'docstring': None}


class TestGetSymbolDetailWrapper:
    def test_python_function_gets_full_detail(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        src = tmp_path / "mod.py"
        src.write_text(
            "def greet(name: str) -> str:\n"
            "    '''Say hello.'''\n"
            "    return name\n"
        )
        sym_id = store.insert_symbol(
            symbol_name='greet', symbol_type='function', file_path=str(src),
            line_number=1, qualified_name='mod.greet', language='python',
        )
        detail = get_symbol_detail(store, sym_id)
        store.close()

        assert detail['qualified_name'] == 'mod.greet'
        assert detail['docstring'] == 'Say hello.'
        assert detail['signature'] == 'greet(name: str)'

    def test_non_python_symbol_degrades_gracefully(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        sym_id = store.insert_symbol(
            symbol_name='greet', symbol_type='function', file_path='mod.js',
            line_number=1, qualified_name='mod.greet', language='javascript',
        )
        detail = get_symbol_detail(store, sym_id)
        store.close()

        assert detail['qualified_name'] == 'mod.greet'
        assert detail['docstring'] is None
        assert detail['signature'] is None

    def test_unknown_id_returns_none(self, tmp_db):
        assert get_symbol_detail(tmp_db, 999) is None


class TestCoverageSymbolEndpointHTTP:
    def test_returns_detail_for_valid_id(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        src = tmp_path / "mod.py"
        src.write_text("def greet():\n    '''Hi.'''\n    pass\n")
        sym_id = store.insert_symbol(
            symbol_name='greet', symbol_type='function', file_path=str(src),
            line_number=1, qualified_name='mod.greet', language='python',
        )
        store.close()

        srv = WebServer(port=0, db_path=db_path, index_root=str(tmp_path))
        srv.start()
        try:
            resp = _get(srv.port, f"/api/coverage/symbol?id={sym_id}")
            assert resp.status == 200
            data = json.loads(resp.body)
            assert data['docstring'] == 'Hi.'
        finally:
            srv.stop()

    def test_missing_id_returns_400(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        store.close()

        srv = WebServer(port=0, db_path=db_path, index_root=str(tmp_path))
        srv.start()
        try:
            resp = _get(srv.port, "/api/coverage/symbol")
            assert resp.status == 400
        finally:
            srv.stop()

    def test_unknown_id_returns_404(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        store.close()

        srv = WebServer(port=0, db_path=db_path, index_root=str(tmp_path))
        srv.start()
        try:
            resp = _get(srv.port, "/api/coverage/symbol?id=999")
            assert resp.status == 404
        finally:
            srv.stop()
