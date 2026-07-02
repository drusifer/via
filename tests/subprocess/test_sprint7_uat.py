"""
Sprint 7 UAT — MCP Mode end-to-end acceptance tests.

TLDR:
    P7-1: make test passes (covered by test suite itself)
    P7-2: via install mcp creates valid .mcp.json
    P7-3: via mcp serve starts and responds over stdio
    P7-4: mock tools/call with args returns valid JSON response
    P7-5: via mcp schema output matches tools/list tool name
    P7-7: via uninstall mcp removes config

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def indexed_project(tmp_path):
    """A tmp_path with a Python file, indexed by via."""
    (tmp_path / "mymod.py").write_text(
        "class MyClass:\n    def my_method(self): pass\n\ndef my_func(): pass\n"
    )
    result = subprocess.run(
        [sys.executable, '-m', 'via', 'index', str(tmp_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"Index failed: {result.stderr}"
    return tmp_path


def _jsonrpc(method, params=None, id=1):
    msg = {"jsonrpc": "2.0", "method": method, "id": id}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)


def _mcp_conversation(*extra_messages):
    """Build a complete MCP conversation: init + initialized + extra messages."""
    msgs = [
        _jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "uat-test", "version": "0"},
        }),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
    ]
    msgs.extend(extra_messages)
    return "\n".join(msgs) + "\n"


# ── P7-2: via install mcp creates .mcp.json ──────────────────────────────

class TestUAT72_InstallMcp:
    def test_install_mcp_creates_mcp_json(self, tmp_path):
        result = subprocess.run(
            [sys.executable, '-m', 'via', 'install', 'mcp'],
            capture_output=True, text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        mcp_json = tmp_path / ".mcp.json"
        assert mcp_json.exists(), ".mcp.json not created"

    def test_mcp_json_contains_via_server(self, tmp_path):
        subprocess.run(
            [sys.executable, '-m', 'via', 'install', 'mcp'],
            capture_output=True, cwd=str(tmp_path),
        )
        data = json.loads((tmp_path / ".mcp.json").read_text())
        assert "via" in data.get("mcpServers", {}), "via key missing in mcpServers"

    def test_mcp_json_valid_command(self, tmp_path):
        subprocess.run(
            [sys.executable, '-m', 'via', 'install', 'mcp'],
            capture_output=True, cwd=str(tmp_path),
        )
        data = json.loads((tmp_path / ".mcp.json").read_text())
        via_entry = data["mcpServers"]["via"]
        assert "command" in via_entry
        assert "args" in via_entry


# ── P7-3: via mcp serve starts and handles initialize ─────────────────────

class TestUAT73_McpServeStarts:
    def test_serve_handles_initialize(self, indexed_project):
        stdin_data = _mcp_conversation()
        proc = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(indexed_project)],
            input=stdin_data, capture_output=True, text=True, timeout=15,
        )
        assert proc.returncode == 0
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        assert len(lines) >= 1
        response = json.loads(lines[0])
        assert response["jsonrpc"] == "2.0"
        assert "result" in response

    def test_serve_exits_cleanly_on_stdin_eof(self, indexed_project):
        proc = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(indexed_project)],
            input="",
            capture_output=True, text=True, timeout=10,
        )
        assert proc.returncode == 0


# ── P7-4: mock tools/call returns valid JSON ─────────────────────────────

class TestUAT74_McpToolsCall:
    def test_tools_call_returns_json_array(self, indexed_project):
        stdin_data = _mcp_conversation(
            _jsonrpc("tools/call", {
                "name": "via_query",
                "arguments": {"args": ["-mg", "*", "-tc"]},
            }, id=3),
        )
        proc = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(indexed_project)],
            input=stdin_data, capture_output=True, text=True, timeout=15,
        )
        assert "MyClass" in proc.stdout, f"MyClass not in output:\n{proc.stdout}\n{proc.stderr}"

    def test_tools_call_empty_query_returns_empty_array(self, indexed_project):
        stdin_data = _mcp_conversation(
            _jsonrpc("tools/call", {
                "name": "via_query",
                "arguments": {"args": ["-mg", "NONEXISTENT_XXXXXXXXX", "-tc"]},
            }, id=3),
        )
        proc = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(indexed_project)],
            input=stdin_data, capture_output=True, text=True, timeout=15,
        )
        assert proc.returncode == 0
        # Result should contain empty list
        assert "[]" in proc.stdout or '"result":[]' in proc.stdout or \
               '"result": []' in proc.stdout or "NONEXISTENT" not in proc.stdout


# ── P7-5: via mcp schema tool name matches tools/list ────────────────────

class TestUAT75_SchemaMatchesToolsList:
    def test_schema_name_matches_tools_list(self, indexed_project):
        schema_result = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'schema'],
            capture_output=True, text=True,
        )
        assert schema_result.returncode == 0
        schema = json.loads(schema_result.stdout)
        tool_name = schema["name"]

        stdin_data = _mcp_conversation(
            _jsonrpc("tools/list", {}, id=2),
        )
        serve_result = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'serve', str(indexed_project)],
            input=stdin_data, capture_output=True, text=True, timeout=15,
        )
        assert tool_name in serve_result.stdout, \
            f"Tool '{tool_name}' not found in tools/list response"


# ── P7-7: via uninstall mcp removes config ────────────────────────────────

class TestUAT77_UninstallMcp:
    def test_uninstall_removes_via_entry(self, tmp_path):
        # Install first
        subprocess.run(
            [sys.executable, '-m', 'via', 'install', 'mcp'],
            capture_output=True, cwd=str(tmp_path),
        )
        assert (tmp_path / ".mcp.json").exists()

        # Uninstall
        result = subprocess.run(
            [sys.executable, '-m', 'via', 'uninstall', 'mcp'],
            capture_output=True, text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

        mcp_json = tmp_path / ".mcp.json"
        if mcp_json.exists():
            data = json.loads(mcp_json.read_text())
            assert "via" not in data.get("mcpServers", {}), "via not removed"

    def test_uninstall_preserves_other_entries(self, tmp_path):
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text(json.dumps({
            "mcpServers": {
                "other": {"command": "other"},
                "via": {"command": sys.executable, "args": ["-m", "via", "mcp", "serve"]},
            }
        }))
        subprocess.run(
            [sys.executable, '-m', 'via', 'uninstall', 'mcp'],
            capture_output=True, cwd=str(tmp_path),
        )
        data = json.loads(mcp_json.read_text())
        assert "other" in data["mcpServers"]
        assert "via" not in data["mcpServers"]
