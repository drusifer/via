"""
HTTP request handler for the via Web UI.

TLDR:
    ViaRequestHandler routes incoming requests to the appropriate API handler
    or serves the HTML SPA. All responses include CORS headers. Unknown paths
    return 404. Logging is suppressed to avoid polluting via's output.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import Any

logger = logging.getLogger(__name__)


class ViaRequestHandler(BaseHTTPRequestHandler):
    """Routes HTTP requests for the via Web UI."""

    # ------------------------------------------------------------------
    # Route table
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._json({"ok": True})
        elif self.path == "/api/status":
            self._handle_status()
        elif self.path in ("/", "/index.html"):
            self._handle_index()
        else:
            self._not_found()

    def do_POST(self) -> None:
        if self.path == "/api/query":
            self._handle_query()
        else:
            self._not_found()

    def do_OPTIONS(self) -> None:
        """CORS preflight."""
        self.send_response(204)
        self._add_cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # Handlers (stubs — filled in later phases)
    # ------------------------------------------------------------------

    def _handle_status(self) -> None:
        web_server = getattr(self.server, "web_server", None)
        if web_server is None:
            self._json({"error": "server not initialised"}, status=500)
            return
        from via.web.api.status import get_status
        data = get_status(web_server)
        self._json(data)

    def _handle_query(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(body_bytes)
        except json.JSONDecodeError:
            self._json({"error": "invalid JSON"}, status=400)
            return
        web_server = getattr(self.server, "web_server", None)
        if web_server is None:
            self._json({"error": "server not initialised"}, status=500)
            return
        from via.web.api.query import run_query
        try:
            result = run_query(web_server, body)
            self._json(result)
        except Exception as exc:
            self._json({"error": str(exc)}, status=500)

    def _handle_index(self) -> None:
        try:
            from via.web.template import HTML_TEMPLATE
            body = HTML_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._add_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        except ImportError:
            self._json({"error": "template not yet available"}, status=503)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _not_found(self) -> None:
        self._json({"error": "not found"}, status=404)

    def _add_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: N802
        """Suppress default Apache-style access log to keep CLI output clean."""
        logger.debug(fmt, *args)
