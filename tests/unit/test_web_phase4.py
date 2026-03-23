"""Unit tests for Sprint 12 Phase 4 — CLI wire-up and WatchService hook.

TLDR:
    Tests WatchService.add_reindex_listener() fires after _execute(),
    listener exceptions do not crash the watcher, IndexCommand exposes
    --port and --no-web, and mcp serve subparser exposes the same flags.
    Role: protects the CLI integration and observer hook layers.
"""
import argparse
import threading
import time
from unittest.mock import MagicMock, patch, call

import pytest

from via.services.watch import WatchService
from via.commands.index import IndexCommand


# ---------------------------------------------------------------------------
# WatchService.add_reindex_listener()
# ---------------------------------------------------------------------------

class TestWatchServiceReindexListener:
    def _make_watch_service(self):
        svc = WatchService.__new__(WatchService)
        svc._reindex_listeners = []
        svc._lock = threading.Lock()
        svc._pending = {}
        svc.indexing_service = MagicMock()
        svc.indexing_service.reindex_file.return_value = {"function": 2}
        svc.indexing_service.size_limit = 10 * 1024 * 1024  # 10MB
        svc.db_store = MagicMock()
        svc.root_dir = "/tmp/test"
        svc.debounce_seconds = 0.5
        return svc

    def test_add_listener_appends(self):
        svc = self._make_watch_service()
        cb = MagicMock()
        svc.add_reindex_listener(cb)
        assert cb in svc._reindex_listeners

    def test_multiple_listeners_all_registered(self):
        svc = self._make_watch_service()
        cb1, cb2 = MagicMock(), MagicMock()
        svc.add_reindex_listener(cb1)
        svc.add_reindex_listener(cb2)
        assert len(svc._reindex_listeners) == 2

    def test_listener_called_after_reindex(self, tmp_path):
        """Listener is called when _execute fires a reindex."""
        svc = self._make_watch_service()
        svc.root_dir = str(tmp_path)

        fired = []
        svc.add_reindex_listener(lambda count: fired.append(count))

        # Write a real file so _reindex_file can stat it
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")

        with patch.object(svc.indexing_service, 'reindex_file', return_value={"function": 2}):
            svc._execute(str(f), 'modified')

        assert len(fired) == 1
        assert fired[0] == 1  # 1 file changed

    def test_listener_not_called_for_delete(self, tmp_path):
        """Deleted-file _execute should not call reindex listeners."""
        svc = self._make_watch_service()
        svc.root_dir = str(tmp_path)

        fired = []
        svc.add_reindex_listener(lambda count: fired.append(count))

        with patch.object(svc.db_store, 'delete_file_completely'):
            svc._execute("/gone.py", 'deleted')

        assert fired == []

    def test_listener_exception_does_not_crash(self, tmp_path):
        """A failing listener must not propagate and crash WatchService."""
        svc = self._make_watch_service()
        svc.root_dir = str(tmp_path)

        def bad_listener(count):
            raise RuntimeError("listener exploded")

        good_called = []
        svc.add_reindex_listener(bad_listener)
        svc.add_reindex_listener(lambda c: good_called.append(c))

        f = tmp_path / "test.py"
        f.write_text("x = 1\n")

        with patch.object(svc.indexing_service, 'reindex_file', return_value={"function": 1}):
            # Must not raise despite bad_listener raising
            svc._execute(str(f), 'modified')

        # Good listener still fired
        assert len(good_called) == 1


# ---------------------------------------------------------------------------
# IndexCommand --port and --no-web
# ---------------------------------------------------------------------------

class TestIndexCommandNewArgs:
    def _parse(self, *args):
        parser = argparse.ArgumentParser()
        IndexCommand.add_arguments(parser)
        return parser.parse_args(list(args))

    def test_port_default(self):
        ns = self._parse()
        assert ns.port == 7891

    def test_port_custom(self):
        ns = self._parse("--port", "8080")
        assert ns.port == 8080

    def test_no_web_default_false(self):
        ns = self._parse()
        assert ns.no_web is False

    def test_no_web_flag(self):
        ns = self._parse("--no-web")
        assert ns.no_web is True

    def test_watch_and_port_together(self):
        ns = self._parse("-w", "--port", "9000")
        assert ns.watch is True
        assert ns.port == 9000


# ---------------------------------------------------------------------------
# MCP serve subparser --port and --no-web
# ---------------------------------------------------------------------------

class TestMcpServeNewArgs:
    def _parse_mcp_serve(self, *args):
        from via.__main__ import _create_parser
        parser = _create_parser()
        return parser.parse_args(["mcp", "serve"] + list(args))

    def test_mcp_serve_port_default(self):
        ns = self._parse_mcp_serve()
        assert ns.port == 7891

    def test_mcp_serve_port_custom(self):
        ns = self._parse_mcp_serve("--port", "8888")
        assert ns.port == 8888

    def test_mcp_serve_no_web_default_false(self):
        ns = self._parse_mcp_serve()
        assert ns.no_web is False

    def test_mcp_serve_no_web_flag(self):
        ns = self._parse_mcp_serve("--no-web")
        assert ns.no_web is True
