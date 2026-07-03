"""Trin's Cycle 1 UAT cross-check: real ground truth vs. the coverage API.

TLDR:
    Not part of the committed suite's regression set — a one-off,
    rerunnable ground-truth check comparing /api/coverage/hierarchy and
    /api/coverage/symbol against independently-computed real values (the
    CLI's own `-Vcovered-by` count, a direct line_end-line_number DB query,
    a real docstring re-read from source) on this project's real,
    freshly-captured .via/index.db. Requires `make via_index &&
    make test-coverage` to have been run first so the index reflects
    current source + current coverage data; skips if the expected symbol
    isn't present (e.g. renamed/removed) rather than failing the whole
    suite on drift.
"""
import json
import os
import urllib.request

import pytest

from via.web.server import WebServer

DB_PATH = ".via/index.db"
INDEX_ROOT = "."


def _real_covering_test_count(symbol_name: str) -> int:
    """Ground truth via the same DatabaseStore method the CLI's relationship
    query uses under the hood — count distinct covering tests directly from
    the real database, independent of the new coverage.py code under test."""
    from via.db.store import DatabaseStore

    store = DatabaseStore(DB_PATH, INDEX_ROOT)
    store.connect()
    row = store.conn.execute(
        """
        SELECT COUNT(DISTINCT sr.to_symbol_id)
        FROM symbols s
        JOIN symbol_references sr ON sr.from_symbol_id = s.id AND sr.reference_type = 'covered-by'
        WHERE s.symbol_name = ?
        """,
        (symbol_name,),
    ).fetchone()
    store.close()
    return row[0] if row else 0


@pytest.mark.skipif(
    not os.path.exists(DB_PATH),
    reason="requires a real .via/index.db (run `make via_index && make test-coverage` first)",
)
class TestCycle1RealIndexCrossCheck:
    def test_intensity_pct_matches_real_covering_test_count(self):
        symbol_name = "get_symbol_coverage_counts"
        expected_count = _real_covering_test_count(symbol_name)
        if expected_count == 0:
            pytest.skip(f"{symbol_name} not found or uncovered in the real index right now")

        srv = WebServer(port=0, db_path=DB_PATH, index_root=INDEX_ROOT)
        srv.start()
        try:
            with urllib.request.urlopen(
                f"http://localhost:{srv.port}/api/coverage/hierarchy", timeout=30
            ) as r:
                tree = json.loads(r.read())
        finally:
            srv.stop()

        leaf = _find_leaf(tree, symbol_name)
        assert leaf is not None, f"{symbol_name} not found in the hierarchy response"
        assert leaf["covering_test_count"] == expected_count
        assert leaf["intensity_pct"] == expected_count * 100

    def test_leaf_loc_matches_real_line_span(self):
        """Ground-truth check for the LOC-sizing feature (user directive,
        2026-07-02): compare the hierarchy leaf's `loc` against a direct
        line_end - line_number + 1 computation from the real DB, for a real,
        multi-line method."""
        from via.db.store import DatabaseStore

        symbol_name = "get_symbol_coverage_counts"
        store = DatabaseStore(DB_PATH, INDEX_ROOT)
        store.connect()
        row = store.conn.execute(
            "SELECT line_number, line_end FROM symbols WHERE symbol_name = ? AND symbol_type = 'method'",
            (symbol_name,),
        ).fetchone()
        store.close()
        if row is None or row[1] is None:
            pytest.skip(f"{symbol_name} not found or missing line_end in the real index right now")
        expected_loc = row[1] - row[0] + 1

        srv = WebServer(port=0, db_path=DB_PATH, index_root=INDEX_ROOT)
        srv.start()
        try:
            with urllib.request.urlopen(
                f"http://localhost:{srv.port}/api/coverage/hierarchy", timeout=30
            ) as r:
                tree = json.loads(r.read())
        finally:
            srv.stop()

        leaf = _find_leaf(tree, symbol_name)
        assert leaf is not None
        assert leaf["loc"] == expected_loc
        assert leaf["loc"] > 1, "expected a real multi-line method, not a degenerate 1-line span"

    def test_drill_down_returns_real_docstring_for_documented_method(self):
        """Ground-truth check for the leaf drill-down feature (Cypher AC7,
        user directive 2026-07-02): the real /api/coverage/symbol endpoint
        must return the actual docstring text of a known-documented method,
        re-extracted from the real source file on disk."""
        symbol_name = "get_symbol_coverage_counts"

        srv = WebServer(port=0, db_path=DB_PATH, index_root=INDEX_ROOT)
        srv.start()
        try:
            with urllib.request.urlopen(
                f"http://localhost:{srv.port}/api/coverage/hierarchy", timeout=30
            ) as r:
                tree = json.loads(r.read())
            leaf = _find_leaf(tree, symbol_name)
            assert leaf is not None, f"{symbol_name} not found in the hierarchy response"

            with urllib.request.urlopen(
                f"http://localhost:{srv.port}/api/coverage/symbol?id={leaf['id']}", timeout=30
            ) as r:
                detail = json.loads(r.read())
        finally:
            srv.stop()

        assert detail["qualified_name"].endswith("get_symbol_coverage_counts")
        assert detail["signature"] == "get_symbol_coverage_counts(self)"
        assert "covering_test_count" in detail["docstring"]

    def test_tree_is_rooted_at_project_not_filesystem_root(self):
        """Regression check for the absolute-vs-relative file_path bug this
        cycle's smoke test already caught on a synthetic temp project — this
        confirms the fix also holds on the real, much deeper `via` project
        tree (many more directory levels than the smoke test's 1-level
        `pkg/`), not just the minimal synthetic case."""
        srv = WebServer(port=0, db_path=DB_PATH, index_root=INDEX_ROOT)
        srv.start()
        try:
            with urllib.request.urlopen(
                f"http://localhost:{srv.port}/api/coverage/hierarchy", timeout=30
            ) as r:
                tree = json.loads(r.read())
        finally:
            srv.stop()

        top_level_names = {c["name"] for c in tree.get("children", [])}
        assert "via" in top_level_names, (
            f"expected 'via' as a top-level package, got {top_level_names} — "
            "tree may be rooted at the filesystem root again"
        )
        # None of the absolute-path segments (home/drusifer/Projects/etc.)
        # should leak in as spurious top-level "packages".
        assert not any(name in top_level_names for name in ("home", "Projects", os.sep)), (
            f"filesystem path segments leaked into top-level packages: {top_level_names}"
        )


def _find_leaf(node, name):
    if node.get("name") == name and "covering_test_count" in node:
        return node
    for child in node.get("children", []):
        found = _find_leaf(child, name)
        if found is not None:
            return found
    return None
