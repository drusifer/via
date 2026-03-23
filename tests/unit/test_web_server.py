"""Unit tests for WebServer — Sprint 12, Phase 1.

TLDR:
    Tests the WebServer scaffold: start/stop lifecycle, port auto-selection,
    GET /api/health endpoint, CORS headers, and notify_reindex state tracking.
    Uses a real ThreadingHTTPServer on an ephemeral port (0) to avoid flakiness.
    Role: protects the web layer entry point; depends on WebServer and handler only.
"""
import http.client
import json
import socket
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from via.web.server import WebServer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(port: int, path: str) -> http.client.HTTPResponse:
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    resp.body = resp.read()
    conn.close()
    return resp


def _free_port() -> int:
    """Return an OS-assigned free port (not yet bound)."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

class TestWebServerLifecycle:
    def test_start_and_stop(self):
        srv = WebServer(port=0)  # port=0 → OS assigns ephemeral port
        srv.start()
        assert srv.port > 0
        resp = _get(srv.port, "/api/health")
        assert resp.status == 200
        srv.stop()

    def test_stop_before_start_is_safe(self):
        srv = WebServer(port=0)
        srv.stop()  # must not raise

    def test_double_stop_is_safe(self):
        srv = WebServer(port=0)
        srv.start()
        srv.stop()
        srv.stop()  # must not raise

    def test_port_property_before_start_returns_configured_value(self):
        srv = WebServer(port=7891)
        assert srv.port == 7891

    def test_port_property_after_start_returns_actual_port(self):
        srv = WebServer(port=0)
        srv.start()
        assert srv.port > 0
        srv.stop()


# ---------------------------------------------------------------------------
# Port auto-selection
# ---------------------------------------------------------------------------

class TestWebServerPortSelection:
    def test_uses_specified_port(self):
        p = _free_port()
        srv = WebServer(port=p)
        srv.start()
        assert srv.port == p
        srv.stop()

    def test_auto_selects_next_free_port_when_first_busy(self):
        # Bind port p ourselves so WebServer must fall through to p+1
        p = _free_port()
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        blocker.bind(("", p))
        blocker.listen(1)
        try:
            srv = WebServer(port=p, port_range=2)
            srv.start()
            assert srv.port == p + 1
            srv.stop()
        finally:
            blocker.close()

    def test_raises_when_all_ports_busy(self):
        p = _free_port()
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        blocker.bind(("", p))
        blocker.listen(1)
        try:
            srv = WebServer(port=p, port_range=1)  # only tries p, which is busy
            with pytest.raises(RuntimeError, match="No free port"):
                srv.start()
        finally:
            blocker.close()


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def setup_method(self):
        self.srv = WebServer(port=0)
        self.srv.start()

    def teardown_method(self):
        self.srv.stop()

    def test_returns_200(self):
        resp = _get(self.srv.port, "/api/health")
        assert resp.status == 200

    def test_returns_json_ok(self):
        resp = _get(self.srv.port, "/api/health")
        data = json.loads(resp.body)
        assert data == {"ok": True}

    def test_content_type_is_json(self):
        resp = _get(self.srv.port, "/api/health")
        assert "application/json" in resp.getheader("Content-Type", "")

    def test_unknown_path_returns_404(self):
        resp = _get(self.srv.port, "/not-a-thing")
        assert resp.status == 404


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------

class TestCORSHeaders:
    def setup_method(self):
        self.srv = WebServer(port=0)
        self.srv.start()

    def teardown_method(self):
        self.srv.stop()

    def test_cors_header_present_on_health(self):
        resp = _get(self.srv.port, "/api/health")
        assert resp.getheader("Access-Control-Allow-Origin") is not None

    def test_cors_allows_any_origin(self):
        resp = _get(self.srv.port, "/api/health")
        assert resp.getheader("Access-Control-Allow-Origin") == "*"


# ---------------------------------------------------------------------------
# Reindex state
# ---------------------------------------------------------------------------

class TestReindexState:
    def test_initial_reindex_count_is_zero(self):
        srv = WebServer(port=0)
        assert srv.reindex_state["count"] == 0
        assert srv.reindex_state["last_count"] == 0
        assert srv.reindex_state["last_time"] is None

    def test_notify_reindex_increments_count(self):
        srv = WebServer(port=0)
        srv.notify_reindex(3)
        assert srv.reindex_state["count"] == 1
        assert srv.reindex_state["last_count"] == 3

    def test_notify_reindex_multiple_times(self):
        srv = WebServer(port=0)
        srv.notify_reindex(5)
        srv.notify_reindex(2)
        assert srv.reindex_state["count"] == 2
        assert srv.reindex_state["last_count"] == 2

    def test_notify_reindex_sets_last_time(self):
        srv = WebServer(port=0)
        srv.notify_reindex(1)
        assert srv.reindex_state["last_time"] is not None
