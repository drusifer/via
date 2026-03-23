"""Unit tests for the via Web UI HTML template — Sprint 12, Phase 6.

TLDR:
    Tests that GET / returns 200 with text/html content-type, contains key
    DOM element IDs expected by the JS, and that HTML_TEMPLATE is a non-empty
    string. Also tests CDN error banner presence and that JS fetch targets
    the correct API paths.
    Role: lightweight smoke-test of the template; not a browser/JS test.
"""
import http.client

import pytest

from via.web.template import HTML_TEMPLATE
from via.web.server import WebServer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(port, path):
    conn = http.client.HTTPConnection("localhost", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    resp.body = resp.read().decode("utf-8")
    conn.close()
    return resp


# ---------------------------------------------------------------------------
# Template content
# ---------------------------------------------------------------------------

class TestHTMLTemplate:
    def test_template_is_non_empty_string(self):
        assert isinstance(HTML_TEMPLATE, str)
        assert len(HTML_TEMPLATE) > 1000

    def test_contains_doctype(self):
        assert "<!DOCTYPE html>" in HTML_TEMPLATE

    # Required DOM IDs used by the JS
    def test_has_run_btn(self):
        assert 'id="run-btn"' in HTML_TEMPLATE

    def test_has_reset_btn(self):
        assert 'id="reset-btn"' in HTML_TEMPLATE

    def test_has_pattern_input(self):
        assert 'id="pattern"' in HTML_TEMPLATE

    def test_has_match_type_select(self):
        assert 'id="match-type"' in HTML_TEMPLATE

    def test_has_type_chips(self):
        assert 'id="type-chips"' in HTML_TEMPLATE

    def test_has_relationship_select(self):
        assert 'id="relationship"' in HTML_TEMPLATE

    def test_has_target_card(self):
        assert 'id="target-card"' in HTML_TEMPLATE

    def test_has_output_format_group(self):
        assert 'id="output-format-group"' in HTML_TEMPLATE

    def test_has_result_list(self):
        assert 'id="result-list"' in HTML_TEMPLATE

    def test_has_result_table(self):
        assert 'id="result-table"' in HTML_TEMPLATE

    def test_has_diagram_wrap(self):
        assert 'id="diagram-wrap"' in HTML_TEMPLATE

    def test_has_cdn_error_banner(self):
        assert 'id="cdn-error"' in HTML_TEMPLATE

    def test_has_status_bar(self):
        assert 'id="status-bar"' in HTML_TEMPLATE

    def test_has_toast(self):
        assert 'id="toast"' in HTML_TEMPLATE

    def test_api_endpoints_referenced(self):
        assert "/api/query" in HTML_TEMPLATE
        assert "/api/status" in HTML_TEMPLATE

    def test_all_eight_symbol_types_in_chips(self):
        for t in ["class", "function", "method", "import", "global",
                  "filepath", "filename", "header"]:
            assert f'data-type="{t}"' in HTML_TEMPLATE

    def test_all_relationship_types_in_select(self):
        for rel in ["inherits-from", "calls", "imports", "references", "has", "declares"]:
            assert rel in HTML_TEMPLATE


# ---------------------------------------------------------------------------
# Handler serves template
# ---------------------------------------------------------------------------

class TestHandlerServesTemplate:
    def setup_method(self):
        self.srv = WebServer(port=0)
        self.srv.start()

    def teardown_method(self):
        self.srv.stop()

    def test_root_returns_200(self):
        resp = _get(self.srv.port, "/")
        assert resp.status == 200

    def test_root_content_type_is_html(self):
        resp = _get(self.srv.port, "/")
        assert "text/html" in resp.getheader("Content-Type", "")

    def test_root_body_contains_doctype(self):
        resp = _get(self.srv.port, "/")
        assert "<!DOCTYPE html>" in resp.body

    def test_index_html_alias_returns_200(self):
        resp = _get(self.srv.port, "/index.html")
        assert resp.status == 200
