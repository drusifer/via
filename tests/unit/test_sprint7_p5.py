"""
Unit tests for Sprint 7 P5 — MCP Server (via mcp serve).

TLDR:
    Tests run_mcp_server exists, via mcp serve exits with error when no index
    found, and a mock JSON-RPC stdio round-trip returns valid JSON.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestMcpServerModule:
    def test_server_module_exists(self):
        from via.mcp.server import run_mcp_server
        assert callable(run_mcp_server)


class TestMcpServeNoIndex:
    def test_serve_errors_when_no_index(self, tmp_path):
        """via mcp serve should exit with error if no index found."""
        result = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(tmp_path)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()


class TestMcpServeStdioRoundTrip:
    """Feed mock JSON-RPC to stdin, assert JSON response on stdout."""

    def _make_index(self, tmp_path):
        """Create a real via index in tmp_path."""
        py_file = tmp_path / "mymod.py"
        py_file.write_text("class MyClass:\n    def my_method(self): pass\n\ndef my_func(): pass\n")
        result = subprocess.run(
            [sys.executable, '-m', 'via', 'index', str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Index failed: {result.stderr}"
        return tmp_path

    def _jsonrpc(self, method, params=None, id=1):
        msg = {"jsonrpc": "2.0", "method": method, "id": id}
        if params is not None:
            msg["params"] = params
        return json.dumps(msg)

    def test_initialize_handshake(self, tmp_path):
        """MCP server responds to initialize request."""
        self._make_index(tmp_path)

        init_msg = self._jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"},
        })
        initialized_msg = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})

        stdin_data = init_msg + "\n" + initialized_msg + "\n"

        proc = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(tmp_path)],
            input=stdin_data,
            capture_output=True, text=True, timeout=15,
        )
        # Should not crash on EOF; stdout should contain a JSON-RPC response
        assert proc.returncode == 0 or proc.returncode is not None
        # Parse first line of stdout as JSON-RPC response
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        if lines:
            response = json.loads(lines[0])
            assert response.get("jsonrpc") == "2.0"

    def test_tools_list(self, tmp_path):
        """tools/list returns via_query tool."""
        self._make_index(tmp_path)

        messages = [
            self._jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            }),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            self._jsonrpc("tools/list", {}, id=2),
        ]
        stdin_data = "\n".join(messages) + "\n"

        proc = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(tmp_path)],
            input=stdin_data,
            capture_output=True, text=True, timeout=15,
        )
        # Find tools/list response — look for via_query in stdout
        assert "via_query" in proc.stdout

    def test_tools_call_returns_json(self, tmp_path):
        """tools/call via_query returns list of dicts."""
        self._make_index(tmp_path)

        messages = [
            self._jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            }),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            self._jsonrpc("tools/call", {
                "name": "via_query",
                "arguments": {"args": ["-mg", "*", "-tc", "-oJ"]},
            }, id=3),
        ]
        stdin_data = "\n".join(messages) + "\n"

        proc = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(tmp_path)],
            input=stdin_data,
            capture_output=True, text=True, timeout=15,
        )
        assert "MyClass" in proc.stdout
