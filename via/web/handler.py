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
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

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
        elif self.path == "/api/coverage/hierarchy":
            self._handle_coverage_hierarchy()
        elif self.path == "/api/coverage/test-efficiency":
            self._handle_coverage_test_efficiency()
        elif self.path.startswith("/api/coverage/symbol"):
            self._handle_coverage_symbol()
        elif self.path in ("/", "/index.html"):
            self._handle_index()
        elif self.path.startswith("/static/"):
            self._handle_static()
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
        if web_server is None or web_server.db_path is None or web_server.index_root is None:
            self._json({"error": "server not initialised"}, status=500)
            return
        from via.db.store import DatabaseStore
        from via.web.api.status import get_status
        with DatabaseStore(web_server.db_path, web_server.index_root) as db_store:
            data = get_status(db_store=db_store, web_server=web_server)
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
        if web_server is None or web_server.db_path is None or web_server.index_root is None:
            self._json({"error": "server not initialised"}, status=500)
            return
        from via.db.store import DatabaseStore
        from via.web.api.query import run_query
        try:
            with DatabaseStore(web_server.db_path, web_server.index_root) as db_store:
                result = run_query(db_store, body)
            self._json(result)
        except Exception as exc:
            self._json({"error": str(exc)}, status=500)

    def _handle_coverage_hierarchy(self) -> None:
        web_server = getattr(self.server, "web_server", None)
        if web_server is None or web_server.db_path is None or web_server.index_root is None:
            self._json({"error": "server not initialised"}, status=500)
            return
        from via.db.store import DatabaseStore
        from via.web.api.coverage import get_coverage_hierarchy
        with DatabaseStore(web_server.db_path, web_server.index_root) as db_store:
            data = get_coverage_hierarchy(db_store)
        self._json(data)

    def _handle_coverage_test_efficiency(self) -> None:
        web_server = getattr(self.server, "web_server", None)
        if web_server is None or web_server.db_path is None or web_server.index_root is None:
            self._json({"error": "server not initialised"}, status=500)
            return
        from via.db.store import DatabaseStore
        from via.web.api.coverage import get_test_efficiency
        with DatabaseStore(web_server.db_path, web_server.index_root) as db_store:
            data = get_test_efficiency(db_store)
        self._json({"results": data})

    def _handle_coverage_symbol(self) -> None:
        query = parse_qs(urlsplit(self.path).query)
        raw_id = query.get("id", [None])[0]
        if raw_id is None or not raw_id.isdigit():
            self._json({"error": "missing or invalid id"}, status=400)
            return
        web_server = getattr(self.server, "web_server", None)
        if web_server is None or web_server.db_path is None or web_server.index_root is None:
            self._json({"error": "server not initialised"}, status=500)
            return
        from via.db.store import DatabaseStore
        from via.web.api.coverage import get_symbol_detail
        with DatabaseStore(web_server.db_path, web_server.index_root) as db_store:
            data = get_symbol_detail(db_store, int(raw_id))
        if data is None:
            self._json({"error": "symbol not found"}, status=404)
            return
        self._json(data)

    def _handle_static(self) -> None:
        filename = self.path[len("/static/"):]
        # Reject directory traversal and non-JS files
        if "/" in filename or not filename.endswith(".js"):
            self._not_found()
            return
        static_dir = Path(__file__).parent / "static"
        file_path = static_dir / filename
        if not file_path.is_file():
            self._not_found()
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(body)

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
