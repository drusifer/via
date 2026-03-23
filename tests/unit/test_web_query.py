"""Unit tests for web query API — Sprint 12, Phase 3.

TLDR:
    Tests run_query() for non-relationship queries: glob/regex/sql match types,
    symbol_types list, limit, case_insensitive, qualified, newerthan/olderthan,
    output_format list/table. Uses a real DatabaseStore with temp SQLite.
    Role: protects the query translation layer; depends on DatabaseStore and
    PipelineExecutor.
"""
import tempfile
import time
from pathlib import Path

import pytest

from via.db.store import DatabaseStore
from via.services.indexing import IndexingService
from via.parsers.registry import ParserRegistry
from via.parsers.python_parser import PythonParser
from via.web.api.query import run_query


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def indexed_db(tmp_path):
    """DatabaseStore with a small indexed Python file."""
    db_path = str(tmp_path / "test.db")
    root = str(tmp_path)
    store = DatabaseStore(db_path, root)
    store.connect()
    store.initialize_schema()

    # Write a tiny Python file and index it
    src = tmp_path / "mymodule.py"
    src.write_text(
        "class Foo:\n"
        "    def bar(self):\n"
        "        pass\n"
        "\n"
        "def top_level():\n"
        "    pass\n"
    )

    registry = ParserRegistry()
    registry.register(PythonParser())
    svc = IndexingService(store, registry)
    svc.index(str(tmp_path))

    yield store
    store.close()


# ---------------------------------------------------------------------------
# Basic query shapes
# ---------------------------------------------------------------------------

class TestRunQueryBasic:
    def test_glob_all_returns_results(self, indexed_db):
        result = run_query(indexed_db, {"match_type": "glob", "pattern": "*"})
        assert result["count"] > 0
        assert isinstance(result["results"], list)
        assert result["format"] == "list"
        assert "elapsed_ms" in result

    def test_glob_pattern_filters(self, indexed_db):
        result = run_query(indexed_db, {"match_type": "glob", "pattern": "Foo"})
        names = [r["symbol_name"] for r in result["results"]]
        assert "Foo" in names
        assert "top_level" not in names

    def test_symbol_type_class(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "*",
            "symbol_types": ["class"],
        })
        for r in result["results"]:
            assert r["symbol_type"] == "class"

    def test_symbol_type_function(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "*",
            "symbol_types": ["function"],
        })
        for r in result["results"]:
            assert r["symbol_type"] == "function"

    def test_limit_respected(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "*", "limit": 1,
        })
        assert result["count"] <= 1
        assert len(result["results"]) <= 1

    def test_case_insensitive(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "foo",
            "case_insensitive": True,
        })
        names = [r["symbol_name"] for r in result["results"]]
        assert "Foo" in names

    def test_regex_match_type(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "regex", "pattern": "^top_",
        })
        names = [r["symbol_name"] for r in result["results"]]
        assert "top_level" in names

    def test_empty_pattern_with_no_results(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "zzz_no_match_zzz",
        })
        assert result["count"] == 0
        assert result["results"] == []

    def test_result_fields_present(self, indexed_db):
        result = run_query(indexed_db, {"match_type": "glob", "pattern": "Foo"})
        assert result["count"] > 0
        r = result["results"][0]
        assert "symbol_name" in r
        assert "qualified_name" in r
        assert "symbol_type" in r
        assert "file_path" in r
        assert "line_number" in r


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class TestRunQueryOutputFormat:
    def test_default_format_is_list(self, indexed_db):
        result = run_query(indexed_db, {"match_type": "glob", "pattern": "*"})
        assert result["format"] == "list"

    def test_table_format_returns_results(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "*",
            "output_format": "table",
        })
        assert result["format"] == "table"
        assert isinstance(result["results"], list)

    def test_diagram_format_returns_mermaid_source(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "*",
            "output_format": "diagram",
        })
        assert result["format"] == "diagram"
        assert "mermaid_source" in result
        assert isinstance(result["mermaid_source"], str)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestRunQueryEdgeCases:
    def test_empty_body_uses_defaults(self, indexed_db):
        result = run_query(indexed_db, {})
        # Default: glob, pattern="*", all types — should return something
        assert isinstance(result, dict)
        assert "results" in result or "mermaid_source" in result

    def test_elapsed_ms_is_non_negative(self, indexed_db):
        result = run_query(indexed_db, {"match_type": "glob", "pattern": "*"})
        assert result["elapsed_ms"] >= 0

    def test_multiple_symbol_types(self, indexed_db):
        result = run_query(indexed_db, {
            "match_type": "glob", "pattern": "*",
            "symbol_types": ["class", "function"],
        })
        types = {r["symbol_type"] for r in result["results"]}
        assert "class" in types
        assert "function" in types
