"""Unit tests for WatchService (Sprint 6 - Watch Mode)."""

import os
import sys
import tempfile
import threading
import time
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService
from via.services.watch import WatchService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        # Minimal Python file so initial index has something
        Path(d, "hello.py").write_text("def hello(): pass\n")
        yield d


@pytest.fixture
def db_store(temp_dir):
    db_path = os.path.join(temp_dir, ".via", "index.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    store = DatabaseStore(db_path, temp_dir)
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


@pytest.fixture
def indexing_service(db_store):
    registry = ParserRegistry()
    registry.register(PythonParser())
    return IndexingService(db_store, registry)


@pytest.fixture
def output():
    return StringIO()


@pytest.fixture
def watch_service(indexing_service, db_store, temp_dir, output):
    return WatchService(
        indexing_service=indexing_service,
        db_store=db_store,
        root_dir=temp_dir,
        debounce_seconds=0.05,  # Short debounce for tests
        output=output,
    )


# ---------------------------------------------------------------------------
# Story 1: Basic Watch Mode
# ---------------------------------------------------------------------------

class TestWatchServiceInit:
    def test_init_stores_root_dir_as_absolute(self, watch_service, temp_dir):
        assert watch_service.root_dir == str(Path(temp_dir).resolve())

    def test_init_default_debounce(self, indexing_service, db_store, temp_dir):
        svc = WatchService(indexing_service, db_store, temp_dir)
        assert svc.debounce_seconds == 0.5


class TestWatchedFileFilter:
    """Test _is_watched_file extension and exclusion logic."""

    def test_python_file_is_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, "foo.py")
        assert watch_service._is_watched_file(path) is True

    def test_pyx_file_is_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, "ext.pyx")
        assert watch_service._is_watched_file(path) is True

    def test_pyi_file_is_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, "stubs.pyi")
        assert watch_service._is_watched_file(path) is True

    def test_markdown_file_is_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, "README.md")
        assert watch_service._is_watched_file(path) is True

    def test_json_file_not_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, "config.json")
        assert watch_service._is_watched_file(path) is False

    def test_txt_file_not_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, "notes.txt")
        assert watch_service._is_watched_file(path) is False

    def test_pyc_file_not_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, "__pycache__", "foo.pyc")
        assert watch_service._is_watched_file(path) is False

    def test_gitdir_file_not_watched(self, watch_service, temp_dir):
        path = os.path.join(temp_dir, ".git", "config")
        assert watch_service._is_watched_file(path) is False


# ---------------------------------------------------------------------------
# Story 2: Terminal feedback
# ---------------------------------------------------------------------------

class TestReindexFile:
    """Test _reindex_file produces correct output."""

    def test_reindex_modified_file_prints_message(self, watch_service, temp_dir, output):
        path = os.path.join(temp_dir, "hello.py")
        watch_service._reindex_file(path)
        msg = output.getvalue()
        assert "Re-indexed:" in msg
        assert "hello.py" in msg

    def test_reindex_new_file_prints_indexed(self, watch_service, temp_dir, output):
        new_file = os.path.join(temp_dir, "new_mod.py")
        Path(new_file).write_text("class NewClass: pass\n")
        watch_service._reindex_file(new_file)
        msg = output.getvalue()
        assert "Re-indexed:" in msg
        assert "new_mod.py" in msg

    def test_reindex_shows_symbol_count(self, watch_service, temp_dir, output):
        path = os.path.join(temp_dir, "hello.py")
        watch_service._reindex_file(path)
        msg = output.getvalue()
        # Should contain "(N symbols)"
        assert "symbol" in msg

    def test_reindex_parse_error_does_not_raise(self, watch_service, temp_dir, output):
        bad_file = os.path.join(temp_dir, "broken.py")
        Path(bad_file).write_text("def (:\n    pass\n")  # Syntax error
        # Should not raise
        watch_service._reindex_file(bad_file)

    def test_reindex_missing_file_does_not_raise(self, watch_service, temp_dir, output):
        ghost = os.path.join(temp_dir, "ghost.py")
        # File doesn't exist — should remove instead, not crash
        watch_service._reindex_file(ghost)


class TestRemoveFile:
    """Test _remove_file produces correct output."""

    def test_remove_file_prints_message(self, watch_service, temp_dir, output, db_store):
        # First index a file so there's something to delete
        path = os.path.join(temp_dir, "hello.py")
        watch_service._reindex_file(path)
        output.truncate(0)
        output.seek(0)

        watch_service._remove_file(path)
        msg = output.getvalue()
        assert "Removed:" in msg
        assert "hello.py" in msg

    def test_remove_file_deletes_from_db(self, watch_service, temp_dir, db_store):
        path = os.path.join(temp_dir, "hello.py")
        watch_service._reindex_file(path)
        watch_service._remove_file(path)
        assert db_store.get_file_by_path(path) is None

    def test_remove_nonexistent_file_does_not_raise(self, watch_service, temp_dir):
        ghost = os.path.join(temp_dir, "ghost.py")
        watch_service._remove_file(ghost)  # Should not raise


# ---------------------------------------------------------------------------
# Story 2: Debounce
# ---------------------------------------------------------------------------

class TestDebounce:
    """Test that rapid events are collapsed into one action."""

    def test_debounce_collapses_rapid_events(self, watch_service, temp_dir, output):
        path = os.path.join(temp_dir, "hello.py")
        reindex_calls = []

        original = watch_service._reindex_file
        def counting_reindex(p):
            reindex_calls.append(p)
            original(p)

        watch_service._reindex_file = counting_reindex

        # Fire 5 events rapidly
        for _ in range(5):
            watch_service._schedule(path, 'modified')

        # Wait for debounce to fire
        time.sleep(watch_service.debounce_seconds * 3)

        # Should have only indexed once despite 5 events
        assert len(reindex_calls) == 1

    def test_debounce_ignored_for_unwatched_extension(self, watch_service, temp_dir):
        json_path = os.path.join(temp_dir, "config.json")
        # Should silently do nothing
        watch_service._schedule(json_path, 'modified')
        time.sleep(watch_service.debounce_seconds * 3)
        # No assertion needed — just must not raise


# ---------------------------------------------------------------------------
# Story 3: Exclusions
# ---------------------------------------------------------------------------

class TestExclusionPatterns:
    """Test that exclude patterns are respected."""

    def test_venv_files_not_watched(self, indexing_service, db_store, temp_dir):
        output = StringIO()
        svc = WatchService(
            indexing_service, db_store, temp_dir,
            exclude_patterns=['.venv/'],
            debounce_seconds=0.05,
            output=output,
        )
        path = os.path.join(temp_dir, ".venv", "lib", "site.py")
        assert svc._is_watched_file(path) is False

    def test_custom_exclude_pattern(self, indexing_service, db_store, temp_dir):
        output = StringIO()
        svc = WatchService(
            indexing_service, db_store, temp_dir,
            exclude_patterns=['generated/'],
            debounce_seconds=0.05,
            output=output,
        )
        path = os.path.join(temp_dir, "generated", "schema.py")
        assert svc._is_watched_file(path) is False


# ---------------------------------------------------------------------------
# Story 4: Error resilience
# ---------------------------------------------------------------------------

class TestErrorResilience:
    """WatchService must survive errors without crashing."""

    def test_db_error_during_reindex_does_not_crash(self, watch_service, temp_dir, output):
        path = os.path.join(temp_dir, "hello.py")
        # Break indexing_service temporarily
        original = watch_service.indexing_service._index_file
        watch_service.indexing_service._index_file = MagicMock(
            side_effect=RuntimeError("DB locked")
        )
        # Must not raise
        watch_service._reindex_file(path)
        watch_service.indexing_service._index_file = original

    def test_stop_is_idempotent(self, watch_service):
        """Calling stop() before start() must not raise."""
        watch_service.stop()
        watch_service.stop()


# ---------------------------------------------------------------------------
# Story 5: start() prints startup and stop messages
# ---------------------------------------------------------------------------

class TestStartupShutdown:
    """Test that start() prints expected messages (via mock Observer)."""

    def test_start_prints_watching_message(self, watch_service, output):
        with patch('via.services.watch.Observer') as MockObserver:
            mock_obs = MagicMock()
            MockObserver.return_value = mock_obs

            # Simulate immediate stop
            stop_event = watch_service._stop_event
            threading.Timer(0.05, stop_event.set).start()

            watch_service.start()

        out = output.getvalue()
        assert "Watching" in out
        assert "Ctrl-C" in out

    def test_start_prints_stop_message(self, watch_service, output):
        with patch('via.services.watch.Observer') as MockObserver:
            mock_obs = MagicMock()
            MockObserver.return_value = mock_obs

            stop_event = watch_service._stop_event
            threading.Timer(0.05, stop_event.set).start()

            watch_service.start()

        out = output.getvalue()
        assert "stopped" in out.lower()

    def test_start_runs_initial_index(self, watch_service, output):
        with patch('via.services.watch.Observer') as MockObserver:
            mock_obs = MagicMock()
            MockObserver.return_value = mock_obs

            stop_event = watch_service._stop_event
            threading.Timer(0.05, stop_event.set).start()

            with patch.object(watch_service.indexing_service, 'index', wraps=watch_service.indexing_service.index) as mock_index:
                watch_service.start()
                assert mock_index.called
