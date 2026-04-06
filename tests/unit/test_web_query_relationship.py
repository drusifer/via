"""Unit tests for web query API — Sprint 12, Phase 5: relationship queries.

TLDR:
    Tests run_query() for relationship queries: inherits-from, calls, imports,
    has (declares). Uses a real indexed database with Python fixtures that
    have inheritance and call relationships.
    Role: protects the relationship-query translation layer.
"""
import tempfile
from pathlib import Path

import pytest

from via.db.store import DatabaseStore
from via.services.indexing import IndexingService
from via.parsers.registry import ParserRegistry
from via.parsers.python_parser import PythonParser
from via.web.api.query import run_query, _build_stages, _build_relationship_filter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rel_db(tmp_path):
    """DatabaseStore with a Python file that has inheritance."""
    db_path = str(tmp_path / "test.db")
    root = str(tmp_path)
    store = DatabaseStore(db_path, root)
    store.connect()
    store.initialize_schema()

    src = tmp_path / "animals.py"
    src.write_text(
        "class Animal:\n"
        "    def speak(self):\n"
        "        pass\n"
        "\n"
        "class Dog(Animal):\n"
        "    def speak(self):\n"
        "        pass\n"
        "\n"
        "class Cat(Animal):\n"
        "    def speak(self):\n"
        "        pass\n"
    )

    registry = ParserRegistry()
    registry.register(PythonParser())
    IndexingService(store, registry).index(str(tmp_path))
    yield store
    store.close()


# ---------------------------------------------------------------------------
# Relationship query shapes
# ---------------------------------------------------------------------------

class TestRelationshipQuery:
    def test_inherits_from_returns_results(self, rel_db):
        result = run_query(rel_db, {
            "match_type": "glob",
            "pattern": "Animal",
            "symbol_types": ["class"],
            "relationship": "inherits-from",
            "target_pattern": "*",
            "target_symbol_types": [],
        })
        assert result["count"] > 0
        names = [r["symbol_name"] for r in result["results"]]
        assert "Dog" in names or "Cat" in names

    def test_relationship_none_is_simple_query(self, rel_db):
        """When relationship=None, behaves like a plain match query."""
        result = run_query(rel_db, {
            "match_type": "glob",
            "pattern": "*",
            "relationship": None,
        })
        assert result["count"] > 0
        assert "results" in result

    def test_unknown_relationship_raises(self, rel_db):
        with pytest.raises(Exception):
            run_query(rel_db, {
                "match_type": "glob",
                "pattern": "*",
                "relationship": "not-a-real-relationship",
            })


# ---------------------------------------------------------------------------
# _build_relationship_filter unit tests
# ---------------------------------------------------------------------------

class TestBuildRelationshipFilter:
    def test_inherits_from_maps_correctly(self):
        body = {
            "relationship": "inherits-from",
            "target_pattern": "*",
            "target_symbol_types": [],
            "invert": False,
            "stale": False,
        }
        rf = _build_relationship_filter(body, "inherits-from")
        assert rf.relationship_type.value == "inherits-from"
        assert rf.object_pattern == "*"
        assert rf.is_negative is False
        assert rf.result_stale is False

    def test_has_maps_to_declares(self):
        body = {
            "relationship": "has",
            "target_pattern": "foo*",
            "target_symbol_types": ["function"],
            "invert": False,
            "stale": False,
        }
        rf = _build_relationship_filter(body, "has")
        assert rf.relationship_type.value == "declares"
        assert rf.object_pattern == "foo*"
        assert rf.object_types == ["function"]

    def test_sans_mode_flag_passed(self):
        body = {
            "relationship": "calls",
            "target_pattern": "*",
            "target_symbol_types": [],
            "mode": "sans",
            "stale": False,
        }
        rf = _build_relationship_filter(body, "calls")
        assert rf.is_negative is True

    def test_via_mode_flag_not_inverted(self):
        body = {
            "relationship": "calls",
            "target_pattern": "*",
            "target_symbol_types": [],
            "mode": "via",
            "stale": False,
        }
        rf = _build_relationship_filter(body, "calls")
        assert rf.is_negative is False

    def test_stale_flag_passed(self):
        body = {
            "relationship": "calls",
            "target_pattern": "*",
            "target_symbol_types": [],
            "invert": False,
            "stale": True,
        }
        rf = _build_relationship_filter(body, "calls")
        assert rf.result_stale is True

    def test_target_pattern_defaults_to_glob_all(self):
        body = {"relationship": "imports", "invert": False, "stale": False}
        rf = _build_relationship_filter(body, "imports")
        assert rf.object_pattern == "*"

    def test_all_relationship_types_map(self):
        from via.web.api.query import _REL_MAP
        for name, value in _REL_MAP.items():
            body = {
                "relationship": name,
                "target_pattern": "*",
                "target_symbol_types": [],
                "invert": False,
                "stale": False,
            }
            rf = _build_relationship_filter(body, name)
            assert rf.relationship_type.value == value


# ---------------------------------------------------------------------------
# _build_stages with relationship
# ---------------------------------------------------------------------------

class TestBuildStagesRelationship:
    def test_single_stage_with_relationship(self):
        from via.pipeline.types import StageType
        body = {
            "match_type": "glob",
            "pattern": "Animal",
            "symbol_types": ["class"],
            "relationship": "inherits-from",
            "target_pattern": "*",
            "target_symbol_types": [],
            "invert": False,
            "stale": False,
        }
        stages = _build_stages(body)
        assert len(stages) == 1
        assert stages[0].stage_type == StageType.MATCH
        assert stages[0].args.relationship is not None

    def test_no_relationship_gives_none(self):
        body = {"match_type": "glob", "pattern": "*"}
        stages = _build_stages(body)
        assert stages[0].args.relationship is None
