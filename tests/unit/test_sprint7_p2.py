"""
Unit tests for Sprint 7 P2 — DB Correctness (WAL, delete_file_completely, reindex_file).

TLDR:
    Tests WAL journal mode is enabled in DatabaseStore.connect(), delete_file_completely()
    removes symbols+relationships+file atomically, and IndexingService.reindex_file()
    is public, transactional, and idempotent.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import os
import tempfile

import pytest

from via.db.store import DatabaseStore
from via.services.indexing import IndexingService
from via.parsers.registry import ParserRegistry
from via.parsers.python_parser import PythonParser
from via.core.discovery import DiscoveredFile


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def db_store(temp_dir):
    db_path = os.path.join(temp_dir, "test.db")
    store = DatabaseStore(db_path, temp_dir)
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


@pytest.fixture
def populated_store(db_store, temp_dir):
    """Store with one file, two symbols, and a relationship."""
    rel_path = "sample.py"
    abs_path = os.path.join(temp_dir, rel_path)

    db_store.insert_file(abs_path, mtime=1000.0, size_bytes=100)
    # Symbols table stores absolute paths (matches _store_class_symbols behaviour)
    sym1 = db_store.insert_symbol('MyClass', 'class', abs_path, 1, 'sample.MyClass')
    sym2 = db_store.insert_symbol('my_func', 'function', abs_path, 10, 'sample.my_func')
    db_store.insert_relationship(sym2, sym1, 'calls')
    return db_store, rel_path, abs_path


# ── P2-1: WAL mode ─────────────────────────────────────────────────────────

class TestWALMode:
    def test_wal_mode_enabled_after_connect(self, temp_dir):
        db_path = os.path.join(temp_dir, "wal_test.db")
        store = DatabaseStore(db_path, temp_dir)
        store.connect()
        try:
            cursor = store.conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            mode = cursor.fetchone()[0]
            assert mode == 'wal', f"Expected WAL mode, got {mode!r}"
        finally:
            store.close()


# ── P2-2: delete_file_completely ─────────────────────────────────────────

class TestDeleteFileCompletely:
    def test_removes_file_record(self, populated_store):
        store, rel_path, abs_path = populated_store
        store.delete_file_completely(abs_path)
        files = store.get_all_files()
        paths = [f['path'] for f in files]
        assert rel_path not in paths

    def test_removes_symbols(self, populated_store):
        store, rel_path, abs_path = populated_store
        store.delete_file_completely(abs_path)
        cursor = store.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM symbols WHERE file_path = ?", (abs_path,))
        count = cursor.fetchone()[0]
        assert count == 0

    def test_removes_relationships(self, populated_store):
        store, rel_path, abs_path = populated_store
        # Verify relationship exists before deletion
        cursor = store.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM symbol_references")
        assert cursor.fetchone()[0] == 1

        store.delete_file_completely(abs_path)

        # After complete deletion, relationship should be gone
        cursor.execute("SELECT COUNT(*) FROM symbol_references")
        assert cursor.fetchone()[0] == 0

    def test_all_three_removed_atomically(self, populated_store):
        store, rel_path, abs_path = populated_store
        cursor = store.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM symbols WHERE file_path = ?", (abs_path,))
        assert cursor.fetchone()[0] == 2

        store.delete_file_completely(abs_path)

        cursor.execute("SELECT COUNT(*) FROM symbols WHERE file_path = ?", (abs_path,))
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM files WHERE path = ?", (rel_path,))
        assert cursor.fetchone()[0] == 0

    def test_delete_nonexistent_path_is_safe(self, db_store, temp_dir):
        abs_path = os.path.join(temp_dir, "nonexistent.py")
        db_store.delete_file_completely(abs_path)  # must not raise


# ── P2-3: IndexingService.reindex_file ────────────────────────────────────

@pytest.fixture
def py_file(temp_dir):
    path = os.path.join(temp_dir, "indexme.py")
    with open(path, 'w') as f:
        f.write("class Foo:\n    pass\n\ndef bar():\n    pass\n")
    return path


@pytest.fixture
def indexing_svc(db_store, temp_dir):
    registry = ParserRegistry()
    registry.register(PythonParser())
    svc = IndexingService(db_store, registry)
    return svc


class TestReindexFile:
    def test_reindex_file_is_public_method(self, indexing_svc):
        assert hasattr(indexing_svc, 'reindex_file')
        assert callable(indexing_svc.reindex_file)

    def test_reindex_file_indexes_new_file(self, indexing_svc, py_file, db_store):
        discovered = DiscoveredFile(
            path=py_file,
            size_bytes=os.path.getsize(py_file),
            mtime=os.path.getmtime(py_file),
            is_parseable=True,
            is_oversized=False,
        )
        indexing_svc.reindex_file(discovered)
        cursor = db_store.conn.cursor()
        cursor.execute("SELECT symbol_name FROM symbols WHERE symbol_name IN ('Foo', 'bar')")
        names = {row[0] for row in cursor.fetchall()}
        assert 'Foo' in names
        assert 'bar' in names

    def test_reindex_file_is_idempotent(self, indexing_svc, py_file, db_store):
        discovered = DiscoveredFile(
            path=py_file,
            size_bytes=os.path.getsize(py_file),
            mtime=os.path.getmtime(py_file),
            is_parseable=True,
            is_oversized=False,
        )
        indexing_svc.reindex_file(discovered)
        indexing_svc.reindex_file(discovered)
        cursor = db_store.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM symbols WHERE symbol_name = 'Foo'"
        )
        count = cursor.fetchone()[0]
        assert count == 1, f"Expected 1 Foo after double-index, got {count}"
