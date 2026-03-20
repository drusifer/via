"""
Unit tests for Sprint 7 P3 — WatchService logging cleanup.

TLDR:
    Tests that WatchService no longer accepts `output` parameter, has a
    `handle_signals` param, uses logger.info/debug instead of print, and
    delegates to reindex_file() / delete_file_completely().

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import inspect
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService
from via.services.watch import WatchService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
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
def indexing_svc(db_store, temp_dir):
    registry = ParserRegistry()
    registry.register(PythonParser())
    return IndexingService(db_store, registry)


@pytest.fixture
def svc(indexing_svc, db_store, temp_dir):
    return WatchService(
        indexing_service=indexing_svc,
        db_store=db_store,
        root_dir=temp_dir,
        debounce_seconds=0.05,
    )


# ── P3-2: No `output` parameter ───────────────────────────────────────────

class TestNoOutputParam:
    def test_output_not_in_init_signature(self, indexing_svc, db_store, temp_dir):
        sig = inspect.signature(WatchService.__init__)
        assert 'output' not in sig.parameters, \
            "output param must be removed from WatchService.__init__"

    def test_init_without_output_succeeds(self, indexing_svc, db_store, temp_dir):
        # Should not raise
        svc = WatchService(indexing_svc, db_store, temp_dir)
        assert svc is not None


# ── P3-3: handle_signals parameter ────────────────────────────────────────

class TestHandleSignals:
    def test_handle_signals_param_exists(self, indexing_svc, db_store, temp_dir):
        sig = inspect.signature(WatchService.__init__)
        assert 'handle_signals' in sig.parameters

    def test_handle_signals_default_is_true(self, indexing_svc, db_store, temp_dir):
        sig = inspect.signature(WatchService.__init__)
        assert sig.parameters['handle_signals'].default is True

    def test_handle_signals_false_accepted(self, indexing_svc, db_store, temp_dir):
        svc = WatchService(indexing_svc, db_store, temp_dir, handle_signals=False)
        assert svc is not None


# ── P3-1: logger.info replaces print ──────────────────────────────────────

class TestLoggingReplacesPrint:
    def test_reindex_uses_logger_not_print(self, svc, temp_dir, caplog):
        """_reindex_file logs, does not print to stdout."""
        py_file = os.path.join(temp_dir, "test_log.py")
        Path(py_file).write_text("def foo(): pass\n")

        with caplog.at_level(logging.INFO, logger='via.services.watch'):
            with patch('builtins.print') as mock_print:
                svc._reindex_file(py_file)

        assert any("Re-indexed:" in r.message for r in caplog.records)
        mock_print.assert_not_called()

    def test_remove_uses_logger_not_print(self, svc, temp_dir, caplog):
        """_remove_file logs, does not print."""
        py_file = os.path.join(temp_dir, "ghost.py")

        with caplog.at_level(logging.INFO, logger='via.services.watch'):
            with patch('builtins.print') as mock_print:
                svc._remove_file(py_file)

        assert any("Removed:" in r.message for r in caplog.records)
        mock_print.assert_not_called()


# ── P2-4/P2-5 via P3: reindex_file and delete_file_completely delegation ──

class TestDelegation:
    def test_reindex_file_delegates_to_public_reindex(self, svc, temp_dir):
        """_reindex_file should call indexing_service.reindex_file (not _index_file)."""
        py_file = os.path.join(temp_dir, "delegate_test.py")
        Path(py_file).write_text("class Bar: pass\n")

        with patch.object(svc.indexing_service, 'reindex_file', return_value={}) as mock:
            svc._reindex_file(py_file)

        mock.assert_called_once()

    def test_remove_file_delegates_to_delete_file_completely(self, svc, temp_dir):
        """_remove_file should call db_store.delete_file_completely (not 3 separate calls)."""
        py_file = os.path.join(temp_dir, "todel.py")

        with patch.object(svc.db_store, 'delete_file_completely') as mock_complete, \
             patch.object(svc.db_store, 'delete_file_by_path') as mock_old:
            svc._remove_file(py_file)

        mock_complete.assert_called_once_with(py_file)
        mock_old.assert_not_called()
