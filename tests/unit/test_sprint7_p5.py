"""
Unit tests for Sprint 7 P5 — MCP Server (via mcp serve).

TLDR:
    Tests run_mcp_server exists, via mcp serve can cold-start without a
    pre-existing index, and delegates to the combined MCP/watch/web runtime.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

class TestMcpServerModule:
    def test_server_module_exists(self):
        from via.mcp.server import run_mcp_server
        assert callable(run_mcp_server)


class TestMcpServeColdStart:
    def test_serve_creates_index_dir_and_delegates_to_combined_runtime(
        self,
        tmp_path,
        monkeypatch,
    ):
        """via mcp serve should not require a separate via index process."""
        from via import __main__ as cli

        calls = {}

        def fake_run_mcp_server(root_dir, db_path, port=7891, no_web=False):
            calls["root_dir"] = root_dir
            calls["db_path"] = db_path
            calls["port"] = port
            calls["no_web"] = no_web
            return 0

        monkeypatch.setattr("via.mcp.server.run_mcp_server", fake_run_mcp_server)

        result = cli._run_mcp_serve(str(tmp_path), port=7892)

        assert result == 0
        assert (tmp_path / ".via").is_dir()
        assert calls == {
            "root_dir": str(tmp_path.resolve()),
            "db_path": str(tmp_path.resolve() / ".via" / "index.db"),
            "port": 7892,
            "no_web": False,
        }
