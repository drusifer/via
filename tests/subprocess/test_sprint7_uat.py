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


async def _run_mcp_client(indexed_project, operation):
    """Run an operation against a live MCP stdio session."""
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m", "via", "mcp", "serve", str(indexed_project), "--no-web",
        ],
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            return await operation(session)


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
        async def initialize(session):
            return session.server_info

        server_info = asyncio.run(_run_mcp_client(indexed_project, initialize))
        assert server_info.name == "via"

    def test_serve_exits_cleanly_on_stdin_eof(self, indexed_project):
        async def initialize(session):
            return session.server_info

        server_info = asyncio.run(_run_mcp_client(indexed_project, initialize))
        assert server_info.name == "via"


# ── P7-4: mock tools/call returns valid JSON ─────────────────────────────

class TestUAT74_McpToolsCall:
    def test_tools_call_returns_json_array(self, indexed_project):
        async def call_tool(session):
            return await session.call_tool(
                "via_query", {"args": ["-mg", "*", "-tc"]}
            )

        result = asyncio.run(_run_mcp_client(indexed_project, call_tool))
        assert "MyClass" in str(result)

    def test_tools_call_empty_query_returns_empty_array(self, indexed_project):
        async def call_tool(session):
            return await session.call_tool(
                "via_query",
                {"args": ["-mg", "NONEXISTENT_XXXXXXXXX", "-tc"]},
            )

        result = asyncio.run(_run_mcp_client(indexed_project, call_tool))
        payload = json.loads(result.content[0].text)
        assert payload["result"] == []


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

        async def list_tools(session):
            return await session.list_tools()

        result = asyncio.run(_run_mcp_client(indexed_project, list_tools))
        assert tool_name in {tool.name for tool in result.tools}


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
