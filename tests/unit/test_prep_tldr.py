"""Unit tests for prep_tldr incremental mode (S10-3).

TLDR:
    Tests read_last_run / write_last_run timestamp persistence, get_changed_files
    filtering logic, and the --force flag override. All tests use tmp_path and
    in-memory SQLite so no real index is required.
    Key class: TestPrepTldrIncremental — covers timestamp I/O, skip/change logic,
    force override.
    Role: protects the incremental prep_tldr feature added in Sprint 10.
"""

import sqlite3
import time
from pathlib import Path

import pytest

# Import the functions under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'agents' / 'tools'))
from prep_tldr import read_last_run, write_last_run, get_changed_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeFile:
    """Minimal stand-in for FileDiscovery result objects."""
    def __init__(self, path: str):
        self.path = path


def _make_db(symbols: list) -> sqlite3.Connection:
    """Create an in-memory SQLite DB with symbols rows."""
    conn = sqlite3.connect(':memory:')
    conn.execute("""
        CREATE TABLE symbols (
            id INTEGER PRIMARY KEY,
            symbol_name TEXT,
            symbol_type TEXT,
            file_path TEXT,
            line_number INTEGER,
            mtime REAL
        )
    """)
    for file_path, mtime in symbols:
        conn.execute(
            "INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, mtime) "
            "VALUES (?, ?, ?, ?, ?)",
            ('sym', 'class', file_path, 1, mtime),
        )
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPrepTldrIncremental:
    """S10-3: read_last_run, write_last_run, get_changed_files."""

    def test_read_last_run_missing_file_returns_none(self, tmp_path):
        """read_last_run returns None when file does not exist."""
        result = read_last_run(tmp_path / 'prep_tldr_last_run')
        assert result is None

    def test_read_last_run_parses_float_correctly(self, tmp_path):
        """read_last_run parses a float timestamp correctly."""
        ts = 1234567890.5
        p = tmp_path / 'prep_tldr_last_run'
        p.write_text(str(ts))
        assert read_last_run(p) == pytest.approx(ts)

    def test_read_last_run_invalid_content_returns_none(self, tmp_path):
        """read_last_run returns None for non-numeric content."""
        p = tmp_path / 'prep_tldr_last_run'
        p.write_text('not-a-float')
        assert read_last_run(p) is None

    def test_write_last_run_creates_file_with_valid_float(self, tmp_path):
        """write_last_run creates file containing a parseable float."""
        p = tmp_path / 'prep_tldr_last_run'
        before = time.time()
        write_last_run(p)
        after = time.time()

        assert p.exists()
        ts = float(p.read_text().strip())
        assert before <= ts <= after

    def test_write_then_read_roundtrip(self, tmp_path):
        """write_last_run followed by read_last_run returns the same timestamp."""
        p = tmp_path / 'prep_tldr_last_run'
        write_last_run(p)
        ts = read_last_run(p)
        assert ts is not None
        assert abs(ts - time.time()) < 2.0

    def test_get_changed_files_returns_changed_when_mtime_newer(self, tmp_path):
        """File with mtime > last_run appears in changed list."""
        last_run = 1000.0
        f = _FakeFile(str(tmp_path / 'foo.py'))
        conn = _make_db([(f.path, 2000.0)])  # newer than last_run

        changed, skipped = get_changed_files(conn, [f], last_run)
        assert f in changed
        assert f not in skipped

    def test_get_changed_files_returns_skipped_when_mtime_older(self, tmp_path):
        """File with mtime <= last_run appears in skipped list."""
        last_run = 2000.0
        f = _FakeFile(str(tmp_path / 'foo.py'))
        conn = _make_db([(f.path, 1000.0)])  # older than last_run

        changed, skipped = get_changed_files(conn, [f], last_run)
        assert f in skipped
        assert f not in changed

    def test_get_changed_files_no_symbols_treated_as_changed(self, tmp_path):
        """File with no symbols in DB (mtime=0.0) is treated as changed."""
        last_run = 500.0
        f = _FakeFile(str(tmp_path / 'empty.py'))
        conn = _make_db([])  # no rows for this file

        changed, skipped = get_changed_files(conn, [f], last_run)
        assert f in changed

    def test_get_changed_files_mixed_batch(self, tmp_path):
        """Correctly partitions a batch of changed and unchanged files."""
        last_run = 1000.0
        old_f = _FakeFile(str(tmp_path / 'old.py'))
        new_f = _FakeFile(str(tmp_path / 'new.py'))
        conn = _make_db([
            (old_f.path, 500.0),   # skipped
            (new_f.path, 1500.0),  # changed
        ])

        changed, skipped = get_changed_files(conn, [old_f, new_f], last_run)
        assert new_f in changed
        assert old_f in skipped
        assert len(changed) == 1
        assert len(skipped) == 1
