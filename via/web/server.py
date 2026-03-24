"""
WebServer — lifecycle manager for via's embedded HTTP server.

TLDR:
    WebServer wraps Python's ThreadingHTTPServer to serve the via Web UI
    in a daemon thread. It auto-selects a free port in the configured range
    (default 7891–7900), exposes a notify_reindex() hook for WatchService
    callbacks, and provides reindex_state for the /api/status endpoint.
    start() is non-blocking; stop() shuts down cleanly.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
import datetime
import socket
import threading
from http.server import ThreadingHTTPServer
from typing import Optional

from .handler import ViaRequestHandler


class WebServer:
    """Embedded HTTP server for the via Web UI.

    Runs in a daemon thread alongside WatchService or the MCP server.
    Uses port auto-selection to avoid conflicts.

    Args:
        port: Starting port to try (default 7891).
        port_range: Number of ports to try before raising (default 10).
    """

    def __init__(
        self,
        port: int = 7891,
        port_range: int = 10,
        db_path: Optional[str] = None,
        index_root: Optional[str] = None,
    ) -> None:
        self._configured_port = port
        self._port_range = port_range
        self._actual_port: int = port
        self._db_path: Optional[str] = db_path
        self._index_root: Optional[str] = index_root
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._reindex_count: int = 0
        self._reindex_last_count: int = 0
        self._reindex_last_time: Optional[str] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Find a free port and start the HTTP server in a daemon thread.

        Raises:
            RuntimeError: If no free port is found in the configured range.
        """
        self._httpd = self._bind_server()
        self._actual_port = self._httpd.server_address[1]

        # Pass server reference to handler via a closure attribute
        self._httpd.web_server = self

        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            daemon=True,
            name="via-web-server",
        )
        self._thread.start()

    def stop(self) -> None:
        """Shut down the HTTP server. Safe to call before start() or twice."""
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd = None

    @property
    def port(self) -> int:
        """Actual bound port (equals configured port unless auto-selected)."""
        return self._actual_port

    def notify_reindex(self, files_changed: int) -> None:
        """Called by WatchService after each re-index batch.

        Args:
            files_changed: Number of files processed in this batch.
        """
        now = datetime.datetime.now(datetime.UTC).isoformat()
        with self._lock:
            self._reindex_count += 1
            self._reindex_last_count = files_changed
            self._reindex_last_time = now

    @property
    def db_path(self) -> Optional[str]:
        """Path to the SQLite index database, or None if not set."""
        return self._db_path

    @property
    def index_root(self) -> Optional[str]:
        """Indexed root directory, or None if not set."""
        return self._index_root

    @property
    def reindex_state(self) -> dict:
        """Snapshot of re-index state for /api/status.

        Returns:
            dict with keys: count (total batches), last_count (files in last
            batch), last_time (ISO8601 UTC string or None).
        """
        with self._lock:
            return {
                "count": self._reindex_count,
                "last_count": self._reindex_last_count,
                "last_time": self._reindex_last_time,
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _bind_server(self) -> ThreadingHTTPServer:
        """Try ports in range until one binds successfully.

        Returns:
            Bound ThreadingHTTPServer instance.

        Raises:
            RuntimeError: If all ports in range are busy.
        """
        start = self._configured_port
        end = start + self._port_range

        for port in range(start, end):
            try:
                httpd = ThreadingHTTPServer(("", port), ViaRequestHandler)
                httpd.allow_reuse_address = True
                return httpd
            except OSError:
                continue

        raise RuntimeError(
            f"No free port in range {start}–{end - 1}. "
            f"Use --port to specify a different starting port."
        )
