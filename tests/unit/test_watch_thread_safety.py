"""Diagnose: does WatchService._execute fail due to check_same_thread?"""
import os
import tempfile
import threading
import time
from io import StringIO
from pathlib import Path

import pytest

from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService
from via.services.watch import WatchService


@pytest.fixture
def env(tmp_path):
    db_path = str(tmp_path / ".via" / "index.db")
    os.makedirs(str(tmp_path / ".via"))
    store = DatabaseStore(db_path, str(tmp_path))
    store.connect()
    store.initialize_schema()
    registry = ParserRegistry()
    registry.register(PythonParser())
    svc = IndexingService(store, registry)
    yield tmp_path, store, svc
    store.close()


def test_reindex_from_timer_thread_succeeds(env):
    """_reindex_file must work when called from a threading.Timer thread."""
    tmp_path, store, indexing_service = env
    output = StringIO()

    py_file = tmp_path / "mod.py"
    py_file.write_text("class Before: pass\n")

    watch = WatchService(
        indexing_service=indexing_service,
        db_store=store,
        root_dir=str(tmp_path),
        debounce_seconds=0.05,
        output=output,
    )

    # Initial index via normal path (main thread, has transaction)
    indexing_service.index(str(tmp_path))

    # Simulate a timer-thread call — exactly what WatchService._execute does
    py_file.write_text("class After: pass\n")
    errors = []

    def run_in_thread():
        try:
            watch._reindex_file(str(py_file))
        except Exception as e:
            errors.append(e)

    t = threading.Timer(0.01, run_in_thread)
    t.start()
    t.join(timeout=5)

    assert not errors, f"_reindex_file raised in timer thread: {errors}"

    from via.core.types import MatchOp, SymbolType
    after = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "After"))
    before = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "Before"))

    assert len(after) >= 1, "After should be in DB — threading bug if 0"
    assert len(before) == 0, "Before should be replaced"
