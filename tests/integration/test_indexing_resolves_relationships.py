"""Regression test: IndexingService.index() must resolve pending relationships.

TLDR:
    Guards against the bug where resolve_pending_relationships() was not called
    inside IndexingService.index(), leaving all relationships as pending and
    making all relationship queries return empty results in production.

    The failure mode is subtle: unit tests call resolve_pending_relationships()
    directly on DatabaseStore, so they pass even when index() omits the call.
    This test exercises the full public index() API and asserts relationships
    are queryable without any manual resolution step.
"""

import os
import tempfile
from pathlib import Path

import pytest

from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService


@pytest.fixture
def project_with_relationships(tmp_path):
    """Project with Python files that have known relationships."""
    (tmp_path / "base.py").write_text(
        "class Base:\n    def do_thing(self):\n        pass\n"
    )
    (tmp_path / "child.py").write_text(
        "from base import Base\n\nclass Child(Base):\n    pass\n"
    )
    (tmp_path / "caller.py").write_text(
        "from child import Child\n\ndef run():\n    c = Child()\n    c.do_thing()\n"
    )
    return tmp_path


@pytest.fixture
def db_store(project_with_relationships):
    db_path = project_with_relationships / ".via" / "index.db"
    db_path.parent.mkdir()
    store = DatabaseStore(str(db_path), str(project_with_relationships))
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


@pytest.fixture
def indexed(project_with_relationships, db_store):
    """Run the full public IndexingService.index() — no manual resolve call."""
    registry = ParserRegistry()
    registry.register(PythonParser())
    service = IndexingService(db_store, registry)
    service.index(str(project_with_relationships))
    return db_store


class TestIndexingResolvesRelationships:
    """Regression: index() must call resolve_pending_relationships() internally."""

    def test_inheritance_queryable_after_index(self, indexed):
        """Child inherits from Base — queryable without manual resolve."""
        results = list(indexed.query_relationships(
            relationship_type="inherits-from",
            object_pattern="Base",
        ))
        names = [r.symbol_name for r in results]
        assert "Child" in names, (
            "Inheritance relationship not resolved. "
            "IndexingService.index() probably missing resolve_pending_relationships() call."
        )

    def test_import_queryable_after_index(self, indexed):
        """caller.py imports from 'child' module — queryable without manual resolve."""
        # Import relationships target the module name, not the class name
        results = list(indexed.query_relationships(
            relationship_type="imports",
            object_pattern="child",
        ))
        assert len(results) > 0, (
            "Import relationship not resolved after index(). "
            "resolve_pending_relationships() not called in IndexingService.index()."
        )

    def test_no_pending_relationships_after_index(self, indexed):
        """After index(), pending_relationships table must be empty."""
        cursor = indexed.conn.execute("SELECT COUNT(*) FROM pending_relationships")
        count = cursor.fetchone()[0]
        assert count == 0, (
            f"{count} pending relationships remain after index() — "
            "resolve_pending_relationships() was not called."
        )
