"""Smoke test: Sprint 27 Phase 2 coverage endpoints, real stack end-to-end.

TLDR:
    Exercises the full real stack for the coverage-visualization feature —
    real IndexingService parsing a temp project, real per-test `covered-by`
    edges and `test_runs` rows via DatabaseStore, a real WebServer bound to
    an OS-assigned port, and real HTTP GET requests against
    /api/coverage/hierarchy and /api/coverage/test-efficiency. Unlike the
    fixture-driven unit tests in tests/unit/test_web_coverage.py, this test
    builds its data through the real indexing path (PythonParser +
    IndexingService) rather than hand-rolled DatabaseStore.insert_symbol()
    calls, so a regression in how indexing produces symbol_type/parent_name/
    file_path (the fields the hierarchy build depends on) would show up here
    even if the unit tests' synthetic rows didn't happen to exercise it.

    Rerun anytime with: make test FILE=tests/integration/test_coverage_web_smoke.py
"""
import http.client
import json

import pytest

from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService
from via.web.server import WebServer


def _get_json(port: int, path: str):
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, json.loads(body)


@pytest.fixture
def project(tmp_path):
    """A small real project: a package with a class + function, two tests."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "mod.py").write_text(
        "class Widget:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "\n"
        "    def render(self):\n"
        "        return 'ok'\n"
        "\n"
        "def helper():\n"
        "    return 42\n"
    )
    return tmp_path


@pytest.fixture
def db_store(project):
    db_path = project / ".via" / "index.db"
    db_path.parent.mkdir()
    store = DatabaseStore(str(db_path), str(project))
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


@pytest.fixture
def indexed(project, db_store):
    """Index the real project through the public IndexingService API."""
    registry = ParserRegistry()
    registry.register(PythonParser())
    IndexingService(db_store, registry).index(str(project))
    return db_store


def _find_symbol_id(store, symbol_name, symbol_type):
    row = store.conn.execute(
        "SELECT id FROM symbols WHERE symbol_name = ? AND symbol_type = ?",
        (symbol_name, symbol_type),
    ).fetchone()
    assert row is not None, f"expected indexing to have produced {symbol_type} {symbol_name!r}"
    return row[0]


def _link_test_coverage(store, symbol_id, test_id):
    test_sym_id = store.insert_symbol(
        symbol_name=test_id, symbol_type='test', file_path='<test>',
        line_number=0, qualified_name=test_id,
    )
    store.insert_relationship(symbol_id, test_sym_id, 'covered-by')


class TestCoverageWebSmoke:
    def test_hierarchy_and_efficiency_endpoints_over_real_http(self, project, indexed):
        # Simulate two tests covering the real, indexed `render` method —
        # so its intensity should be 200% (covered by 2 distinct tests) —
        # and one test covering `helper`.
        render_id = _find_symbol_id(indexed, 'render', 'method')
        helper_id = _find_symbol_id(indexed, 'helper', 'function')
        _link_test_coverage(indexed, render_id, 'tests/test_widget.py::test_render_a')
        _link_test_coverage(indexed, render_id, 'tests/test_widget.py::test_render_b')
        _link_test_coverage(indexed, helper_id, 'tests/test_helper.py::test_helper')
        indexed.upsert_test_run(
            'tests/test_widget.py::test_render_a', 'pass', 0.5, '2026-07-01T00:00:00+00:00'
        )
        indexed.close()

        db_path = str(project / ".via" / "index.db")
        srv = WebServer(port=0, db_path=db_path, index_root=str(project))
        srv.start()
        try:
            status, tree = _get_json(srv.port, "/api/coverage/hierarchy")
            assert status == 200

            # Walk down to the real 'render' leaf via the real package/module/
            # class nesting that indexing actually produced.
            pkg_node = next(c for c in tree["children"] if c["name"] == "pkg")
            mod_node = next(c for c in pkg_node["children"] if c["name"] == "mod.py")
            widget_node = next(c for c in mod_node["children"] if c["name"] == "Widget")
            render_leaf = next(c for c in widget_node["children"] if c["name"] == "render")
            helper_leaf = next(c for c in mod_node["children"] if c["name"] == "helper")

            assert render_leaf["intensity_pct"] == 200.0
            assert helper_leaf["intensity_pct"] == 100.0
            # __init__ was never covered by a test in this scenario.
            init_leaf = next(c for c in widget_node["children"] if c["name"] == "__init__")
            assert init_leaf["intensity_pct"] == 0.0

            status, efficiency = _get_json(srv.port, "/api/coverage/test-efficiency")
            assert status == 200
            rows = {r["test_id"]: r for r in efficiency["results"]}
            assert rows["tests/test_widget.py::test_render_a"]["covered_symbol_count"] == 1
            assert rows["tests/test_widget.py::test_render_a"]["symbols_per_second"] == 2.0
        finally:
            srv.stop()
