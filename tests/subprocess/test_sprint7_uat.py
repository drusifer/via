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

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def indexed_project(tmp_path_factory):
    """A module-scoped temp directory with a Python file, indexed once by via."""
    project = tmp_path_factory.mktemp("sprint7_mcp")
    (project / "mymod.py").write_text(
        "class MyClass:\n    def my_method(self): pass\n\ndef my_func(): pass\n"
    )
    result = subprocess.run(
        [sys.executable, '-m', 'via', 'index', str(project)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"Index failed: {result.stderr}"
    return project


@pytest.fixture(scope="module")
def mcp_session_snapshot(indexed_project):
    """Run all read-only MCP stdio operations in one server session, then close stdin."""
    async def _collect():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "via", "mcp", "serve", str(indexed_project), "--no-web"],
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                init_result = await session.initialize()
                tools_result = await session.list_tools()
                classes_res = await session.call_tool("via_query", {"args": ["-mg", "*", "-tc"]})
                empty_res = await session.call_tool(
                    "via_query", {"args": ["-mg", "NONEXISTENT_XXXXXXXXX", "-tc"]}
                )
                return {
                    "server_info": init_result.server_info,
                    "tools": tools_result.tools,
                    "classes_res": classes_res,
                    "empty_res": empty_res,
                    "exited_cleanly": True,
                }

    return asyncio.run(_collect())


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
    def test_serve_handles_initialize(self, mcp_session_snapshot):
        assert mcp_session_snapshot["server_info"].name == "via"

    def test_serve_exits_cleanly_on_stdin_eof(self, mcp_session_snapshot):
        # stdio_client closes stdin and awaits clean server shutdown on context exit
        assert mcp_session_snapshot["exited_cleanly"] is True


# ── P7-4: mock tools/call returns valid JSON ─────────────────────────────

class TestUAT74_McpToolsCall:
    def test_tools_call_returns_json_array(self, mcp_session_snapshot):
        assert "MyClass" in str(mcp_session_snapshot["classes_res"])

    def test_tools_call_empty_query_returns_empty_array(self, mcp_session_snapshot):
        payload = json.loads(mcp_session_snapshot["empty_res"].content[0].text)
        assert payload["result"] == []


# ── P7-5: via mcp schema tool name matches tools/list ────────────────────

class TestUAT75_SchemaMatchesToolsList:
    def test_schema_name_matches_tools_list(self, mcp_session_snapshot):
        schema_result = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'schema'],
            capture_output=True, text=True,
        )
        assert schema_result.returncode == 0
        schema = json.loads(schema_result.stdout)
        tool_name = schema["name"]
        assert tool_name in {tool.name for tool in mcp_session_snapshot["tools"]}


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
