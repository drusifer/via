"""
Unit tests for Sprint 8 — Line Number Index (P1 + P2).

Covers:
  P1: line_offsets schema, migration, upsert, get_line_byte_range, FK cascade,
      IndexingService._index_line_offsets integration.
  P2: parse_line_slice, _apply_line_slice (added when P2 is implemented).
"""

import os
import sqlite3
import tempfile

import pytest

from via.db.schema import SCHEMA_VERSION
from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    """Return a connected DatabaseStore backed by a temp file."""
    db_path = str(tmp_path / "test.db")
    store = DatabaseStore(db_path, str(tmp_path))
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return path for a temp DB (not yet initialised)."""
    return str(tmp_path / "test.db"), str(tmp_path)


# ── P1-7a: Schema — line_offsets table exists after initialize_schema ─────────

def test_line_offsets_table_exists(tmp_db):
    cursor = tmp_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='line_offsets'"
    )
    assert cursor.fetchone() is not None, "line_offsets table should exist"


def test_line_offsets_index_exists(tmp_db):
    cursor = tmp_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_line_offsets_file'"
    )
    assert cursor.fetchone() is not None, "idx_line_offsets_file index should exist"


def test_schema_version_is_4(tmp_db):
    assert SCHEMA_VERSION == 6
    version = tmp_db.get_metadata("schema_version")
    assert version == "6"


# ── P1-7b: Migration — existing DB at version 3 migrates to 4 cleanly ────────

def test_migration_v3_to_v4(tmp_db_path):
    db_path, root = tmp_db_path

    # Build a version-3 database (no line_offsets table)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at REAL NOT NULL, description TEXT)")
    conn.execute("CREATE TABLE files (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT UNIQUE NOT NULL, language TEXT, size_bytes INTEGER, mtime REAL, indexed_at REAL, parsed BOOLEAN DEFAULT 0, oversized BOOLEAN DEFAULT 0)")
    conn.execute("INSERT INTO metadata VALUES ('schema_version', '3')")
    conn.commit()
    conn.close()

    # Now open with DatabaseStore and initialize_schema (should migrate to v4)
    store = DatabaseStore(db_path, root)
    store.connect()
    store.initialize_schema()

    # Table should now exist
    cursor = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='line_offsets'"
    )
    assert cursor.fetchone() is not None, "line_offsets table should be created during migration"

    version = store.get_metadata("schema_version")
    assert version == "6"
    store.close()


# ── P1-7c: upsert_line_offsets idempotent ─────────────────────────────────────

def test_upsert_line_offsets_idempotent(tmp_db):
    file_id = tmp_db.insert_file(
        path=os.path.join(tmp_db.index_root, "f.py"),
        parsed=True,
    )
    offsets = [(file_id, 1, 0, 5), (file_id, 2, 5, 10)]

    tmp_db.upsert_line_offsets(file_id, offsets)
    tmp_db.upsert_line_offsets(file_id, offsets)  # second call — must not duplicate

    cursor = tmp_db.conn.execute(
        "SELECT COUNT(*) FROM line_offsets WHERE file_id = ?", (file_id,)
    )
    assert cursor.fetchone()[0] == 2, "should have exactly 2 rows after idempotent upsert"


# ── P1-7d: get_line_byte_range returns correct bytes ─────────────────────────

SAMPLE_CONTENT = b"line one\nline two\nline three\n"
# Byte offsets:
#  line 1 "line one\n"   offset=0  length=9
#  line 2 "line two\n"   offset=9  length=9
#  line 3 "line three\n" offset=18 length=11


def _insert_sample_file(store, content=SAMPLE_CONTENT):
    path = os.path.join(store.index_root, "sample.py")
    file_id = store.insert_file(path=path, parsed=True)
    offsets = []
    pos = 0
    for num, line in enumerate(content.splitlines(keepends=True), start=1):
        offsets.append((file_id, num, pos, len(line)))
        pos += len(line)
    store.upsert_line_offsets(file_id, offsets)
    return path, file_id


def test_get_line_byte_range_single_line(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    off, length = tmp_db.get_line_byte_range(path, 2, 2)
    assert off == 9
    assert length == 9
    assert SAMPLE_CONTENT[off:off + length] == b"line two\n"


def test_get_line_byte_range_multi_line(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    off, length = tmp_db.get_line_byte_range(path, 1, 2)
    assert off == 0
    assert length == 18
    assert SAMPLE_CONTENT[off:off + length] == b"line one\nline two\n"


def test_get_line_byte_range_all_lines(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    off, length = tmp_db.get_line_byte_range(path, 1, 3)
    assert off == 0
    assert length == len(SAMPLE_CONTENT)


def test_get_line_byte_range_unknown_file_returns_zero(tmp_db):
    result = tmp_db.get_line_byte_range("/nonexistent/path.py", 1, 5)
    assert result == (0, 0)


def test_get_line_byte_range_out_of_range_returns_zero(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    result = tmp_db.get_line_byte_range(path, 100, 200)
    assert result == (0, 0)


# ── P1-7e: content read at returned byte offset matches expected lines ────────

def test_byte_range_matches_actual_content(tmp_db, tmp_path):
    content = b"alpha\nbeta\ngamma\ndelta\n"
    fpath = str(tmp_path / "test.py")
    with open(fpath, "wb") as fh:
        fh.write(content)

    file_id = tmp_db.insert_file(path=fpath, parsed=True)
    offsets = []
    pos = 0
    for num, line in enumerate(content.splitlines(keepends=True), start=1):
        offsets.append((file_id, num, pos, len(line)))
        pos += len(line)
    tmp_db.upsert_line_offsets(file_id, offsets)

    off, length = tmp_db.get_line_byte_range(fpath, 2, 3)
    assert content[off:off + length] == b"beta\ngamma\n"


# ── P1-8: FK cascade — deleting file cascades to line_offsets ────────────────

def test_fk_cascade_delete_removes_line_offsets(tmp_db):
    path, file_id = _insert_sample_file(tmp_db)

    # Verify offsets exist
    count_before = tmp_db.conn.execute(
        "SELECT COUNT(*) FROM line_offsets WHERE file_id = ?", (file_id,)
    ).fetchone()[0]
    assert count_before > 0

    # Delete the file record
    tmp_db.conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    tmp_db.conn.commit()

    # line_offsets should be gone via FK cascade
    count_after = tmp_db.conn.execute(
        "SELECT COUNT(*) FROM line_offsets WHERE file_id = ?", (file_id,)
    ).fetchone()[0]
    assert count_after == 0, "line_offsets should cascade-delete with file"


# ── P1: get_line_count ────────────────────────────────────────────────────────

def test_get_line_count(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    assert tmp_db.get_line_count(path) == 3


def test_get_line_count_unknown_file(tmp_db):
    assert tmp_db.get_line_count("/no/such/file.py") == 0


# ── P1: IndexingService integration — line offsets populated after index ──────

def test_indexing_service_populates_line_offsets(tmp_path):
    """After indexing a real .py file, line_offsets rows should exist."""
    from via.parsers.registry import ParserRegistry
    from via.services.indexing import IndexingService

    content = b"class Foo:\n    pass\n"
    src = tmp_path / "foo.py"
    src.write_bytes(content)

    db_path = str(tmp_path / "index.db")
    store = DatabaseStore(db_path, str(tmp_path))
    store.connect()
    store.initialize_schema()

    registry = ParserRegistry()
    registry.register(PythonParser())
    service = IndexingService(store, registry)
    service.index(str(tmp_path))

    # There should be line_offsets rows for foo.py
    cursor = store.conn.execute(
        "SELECT COUNT(*) FROM line_offsets lo JOIN files f ON lo.file_id = f.id WHERE f.path LIKE '%foo.py'"
    )
    count = cursor.fetchone()[0]
    assert count == 2, f"Expected 2 line offset rows, got {count}"

    store.close()


# ── P2: parse_line_slice ──────────────────────────────────────────────────────

from via.core.utils import parse_line_slice


def test_parse_line_slice_range():
    assert parse_line_slice("5:10") == (5, 10)


def test_parse_line_slice_open_end():
    assert parse_line_slice("1:") == (1, None)


def test_parse_line_slice_open_start():
    assert parse_line_slice(":5") == (None, 5)


def test_parse_line_slice_single():
    assert parse_line_slice("7") == (7, 7)


def test_parse_line_slice_negative():
    start, end = parse_line_slice("-10:")
    assert start == -10
    assert end is None


def test_parse_line_slice_invalid():
    import pytest
    with pytest.raises((ValueError, TypeError)):
        parse_line_slice("foo")


# ── P2: _apply_line_slice via PipelineExecutor ────────────────────────────────

def _make_executor_with_store(store):
    from via.pipeline.executor import PipelineExecutor
    return PipelineExecutor(store)


def _make_namespace(**kwargs):
    import argparse
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _make_match_record(file_path, line_number, byte_offset=0, byte_length=10):
    from via.core.match_record import FunctionMatchRecord
    return FunctionMatchRecord(
        symbol_name="test",
        symbol_type="function",
        file_path=file_path,
        line_number=line_number,
        byte_offset=byte_offset,
        byte_length=byte_length,
        qualified_name="test.test",
        parent_name=None,
    )


def test_apply_line_slice_updates_byte_range(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    executor = _make_executor_with_store(tmp_db)
    record = _make_match_record(path, line_number=1)
    args = _make_namespace(line_slice="2:2")

    results = list(executor._apply_line_slice(iter([record]), args))
    assert len(results) == 1
    assert results[0].byte_offset == 9    # "line two\n" starts at 9
    assert results[0].byte_length == 9
    assert results[0].line_number == 2


def test_apply_line_slice_open_end(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    executor = _make_executor_with_store(tmp_db)
    record = _make_match_record(path, line_number=1)
    args = _make_namespace(line_slice="1:")

    results = list(executor._apply_line_slice(iter([record]), args))
    assert len(results) == 1
    assert results[0].byte_offset == 0
    assert results[0].byte_length == len(SAMPLE_CONTENT)


def test_apply_line_slice_out_of_range_skips(tmp_db):
    path, _ = _insert_sample_file(tmp_db)
    executor = _make_executor_with_store(tmp_db)
    record = _make_match_record(path, line_number=1)
    args = _make_namespace(line_slice="100:200")

    results = list(executor._apply_line_slice(iter([record]), args))
    assert len(results) == 0
