"""
Unit tests for the Session Trace Tool.
"""

import json
import sys
from pathlib import Path
import pytest

# Import the session trace functions
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'agents' / 'tools'))
from session_trace import is_via_query, parse_line, parse_transcript_file


def test_is_via_query():
    """Verify via command detection rules."""
    # Direct tool calls
    assert is_via_query("via", "") is True
    assert is_via_query("via_query", "") is True
    assert is_via_query("run_query", "") is True
    
    # Non-via tool calls
    assert is_via_query("read_file", "") is False
    assert is_via_query("list_dir", "via") is False

    # Command line invocations
    assert is_via_query("run_command", "via -mg *") is True
    assert is_via_query("run_command", "./venv/bin/via --limit 5") is True
    assert is_via_query("run_shell_command", "make via ARGS='-mg Parser'") is True
    assert is_via_query("command", "python agents/tools/chat.py") is False


def test_parse_line_flat_format():
    """Verify parsing flat JSONL lines."""
    line = '{"timestamp": "2026-06-20T00:31:00Z", "conversation_id": "conv-1", "tool": "via", "input": "-mg *", "status": "SUCCESS"}'
    parsed = parse_line(line)
    assert parsed is not None
    assert parsed["timestamp"] == "2026-06-20T00:31:00Z"
    assert parsed["conversation_id"] == "conv-1"
    assert parsed["tool"] == "via"
    assert parsed["query"] == "-mg *"
    assert parsed["status"] == "SUCCESS"


def test_parse_line_nested_format():
    """Verify parsing nested tool call entries."""
    line = json.dumps({
        "time": "2026-06-20T00:32:00Z",
        "conv_id": "conv-2",
        "tool_call": {
            "name": "run_command",
            "args": {"CommandLine": "via -mg ParserABC"}
        },
        "response": {"status": 0}
    })
    parsed = parse_line(line)
    assert parsed is not None
    assert parsed["timestamp"] == "2026-06-20T00:32:00Z"
    assert parsed["conversation_id"] == "conv-2"
    assert parsed["tool"] == "run_command"
    assert parsed["query"] == "via -mg ParserABC"
    assert parsed["status"] == "SUCCESS"


def test_parse_line_mcp_format():
    """Verify parsing MCP tool calls."""
    line = json.dumps({
        "timestamp": "2026-06-20T00:33:00Z",
        "sender": "neo",
        "method": "tools/call",
        "params": {
            "name": "via",
            "arguments": {"query": "-mg * -tc"}
        },
        "success": True
    })
    parsed = parse_line(line)
    assert parsed is not None
    assert parsed["timestamp"] == "2026-06-20T00:33:00Z"
    assert parsed["conversation_id"] == "neo"
    assert parsed["tool"] == "via"
    assert parsed["query"] == "-mg * -tc"
    assert parsed["status"] == "SUCCESS"


def test_parse_line_ignores_non_via():
    """Verify non-via tools are ignored."""
    line = '{"timestamp": "2026-06-20T00:31:00Z", "conversation_id": "conv-1", "tool": "read_file", "input": "settings.json"}'
    assert parse_line(line) is None


def test_parse_transcript_file(tmp_path):
    """Verify reading and parsing a whole JSONL/JSON array file."""
    # Test JSONL format
    jsonl_file = tmp_path / "test_transcript.jsonl"
    jsonl_content = (
        '{"timestamp": "2026-06-20T00:01:00Z", "conv_id": "c1", "tool": "via", "input": "query1"}\n'
        '{"timestamp": "2026-06-20T00:02:00Z", "conv_id": "c1", "tool": "read_file", "input": "foo.py"}\n'
        '{"timestamp": "2026-06-20T00:03:00Z", "conv_id": "c2", "tool": "via", "input": "query2"}\n'
    )
    jsonl_file.write_text(jsonl_content)
    
    # Parse all
    queries = parse_transcript_file(jsonl_file)
    assert len(queries) == 2
    assert queries[0]["query"] == "query1"
    assert queries[1]["query"] == "query2"
    
    # Parse with conv_id filter
    queries_filtered = parse_transcript_file(jsonl_file, conv_id_filter="c1")
    assert len(queries_filtered) == 1
    assert queries_filtered[0]["query"] == "query1"
    
    # Test JSON Array format
    json_file = tmp_path / "test_transcript.json"
    json_data = [
        {"timestamp": "2026-06-20T00:01:00Z", "conv_id": "c1", "tool": "via", "input": "query1"},
        {"timestamp": "2026-06-20T00:02:00Z", "conv_id": "c1", "tool": "read_file", "input": "foo.py"},
        {"timestamp": "2026-06-20T00:03:00Z", "conv_id": "c2", "tool": "via", "input": "query2"}
    ]
    json_file.write_text(json.dumps(json_data))
    
    queries_json = parse_transcript_file(json_file)
    assert len(queries_json) == 2
    assert queries_json[0]["query"] == "query1"
    assert queries_json[1]["query"] == "query2"
