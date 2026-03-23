"""Unit tests for web status API — Sprint 12, Phase 2.

TLDR:
    Tests DatabaseStore.get_counts(), DatabaseStore.get_last_indexed_iso(),
    and the get_status() function that powers GET /api/status.
    Uses a real in-memory SQLite database via DatabaseStore.
    Role: protects the status API layer; depends on DatabaseStore and WebServer.
"""
import datetime
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from via.db.store import DatabaseStore
from via.web.api.status import get_status


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path):
    """DatabaseStore backed by a temp file, schema initialised."""
    db_path = str(tmp_path / "test.db")
    root = str(tmp_path)
    store = DatabaseStore(db_path, root)
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


def _insert_file(store: DatabaseStore, path: str, indexed_at: float) -> int:
    """Insert a minimal files row and return its id."""
    cur = store.conn.execute(
        "INSERT INTO files (path, language, parsed, mtime, indexed_at) "
        "VALUES (?, 'python', 1, ?, ?)",
        (path, indexed_at, indexed_at),
    )
    return cur.lastrowid


def _insert_symbol(store: DatabaseStore, file_path: str, name: str) -> None:
    store.conn.execute(
        "INSERT INTO symbols (file_path, symbol_name, qualified_name, symbol_type, "
        "line_number, symbol_subtype) VALUES (?, ?, ?, 'function', 1, NULL)",
        (file_path, name, name),
    )


# ---------------------------------------------------------------------------
# DatabaseStore.get_counts()
# ---------------------------------------------------------------------------

class TestGetCounts:
    def test_empty_db_returns_zeros(self, tmp_db):
        counts = tmp_db.get_counts()
        assert counts == {"files": 0, "symbols": 0}

    def test_counts_files(self, tmp_db):
        _insert_file(tmp_db, "/a.py", time.time())
        _insert_file(tmp_db, "/b.py", time.time())
        counts = tmp_db.get_counts()
        assert counts["files"] == 2

    def test_counts_symbols(self, tmp_db):
        _insert_file(tmp_db, "/a.py", time.time())
        _insert_symbol(tmp_db, "/a.py", "foo")
        _insert_symbol(tmp_db, "/a.py", "bar")
        counts = tmp_db.get_counts()
        assert counts["symbols"] == 2

    def test_counts_both(self, tmp_db):
        _insert_file(tmp_db, "/a.py", time.time())
        _insert_symbol(tmp_db, "/a.py", "foo")
        _insert_file(tmp_db, "/b.py", time.time())
        _insert_symbol(tmp_db, "/b.py", "bar")
        _insert_symbol(tmp_db, "/b.py", "baz")
        counts = tmp_db.get_counts()
        assert counts == {"files": 2, "symbols": 3}


# ---------------------------------------------------------------------------
# DatabaseStore.get_last_indexed_iso()
# ---------------------------------------------------------------------------

class TestGetLastIndexedIso:
    def test_empty_db_returns_none(self, tmp_db):
        assert tmp_db.get_last_indexed_iso() is None

    def test_returns_iso8601_string(self, tmp_db):
        _insert_file(tmp_db, "/a.py", time.time())
        result = tmp_db.get_last_indexed_iso()
        assert result is not None
        # Should parse as a valid datetime
        dt = datetime.datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert dt.year >= 2020

    def test_returns_most_recent(self, tmp_db):
        t1 = 1700000000.0
        t2 = 1800000000.0
        _insert_file(tmp_db, "/a.py", t1)
        _insert_file(tmp_db, "/b.py", t2)
        result = tmp_db.get_last_indexed_iso()
        # t2 is more recent; parse and check it's later than t1
        dt = datetime.datetime.fromisoformat(result.replace("Z", "+00:00"))
        t1_dt = datetime.datetime.fromtimestamp(t1, tz=datetime.timezone.utc)
        assert dt > t1_dt


# ---------------------------------------------------------------------------
# get_status()
# ---------------------------------------------------------------------------

class TestGetStatus:
    def _make_web_server(self, count=0, last_count=0, last_time=None):
        ws = MagicMock()
        ws.reindex_state = {
            "count": count,
            "last_count": last_count,
            "last_time": last_time,
        }
        return ws

    def test_returns_all_required_keys(self, tmp_db):
        ws = self._make_web_server()
        status = get_status(db_store=tmp_db, web_server=ws)
        assert "directory" in status
        assert "file_count" in status
        assert "symbol_count" in status
        assert "last_indexed" in status
        assert "watching" in status
        assert "last_reindex_count" in status
        assert "last_reindex_files" in status
        assert "last_reindex_time" in status

    def test_file_and_symbol_counts(self, tmp_db):
        _insert_file(tmp_db, "/a.py", time.time())
        _insert_symbol(tmp_db, "/a.py", "foo")
        ws = self._make_web_server()
        status = get_status(db_store=tmp_db, web_server=ws)
        assert status["file_count"] == 1
        assert status["symbol_count"] == 1

    def test_watching_is_true(self, tmp_db):
        ws = self._make_web_server()
        status = get_status(db_store=tmp_db, web_server=ws)
        assert status["watching"] is True

    def test_last_reindex_count_from_web_server(self, tmp_db):
        ws = self._make_web_server(count=3, last_count=5)
        status = get_status(db_store=tmp_db, web_server=ws)
        assert status["last_reindex_count"] == 3
        assert status["last_reindex_files"] == 5

    def test_directory_is_string(self, tmp_db):
        ws = self._make_web_server()
        status = get_status(db_store=tmp_db, web_server=ws)
        assert isinstance(status["directory"], str)
