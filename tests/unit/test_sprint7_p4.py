"""
Unit tests for Sprint 7 P4 — MCP Schema (via mcp schema command).

TLDR:
    Tests build_tool_schema() returns valid JSON with all flag groups,
    RelationshipType enum values, and at least 8 annotated examples.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import json
import subprocess
import sys

import pytest


class TestBuildToolSchema:
    def test_module_exists(self):
        from via.mcp.schema import build_tool_schema
        assert callable(build_tool_schema)

    def test_returns_dict(self):
        from via.mcp.schema import build_tool_schema
        result = build_tool_schema()
        assert isinstance(result, dict)

    def test_schema_is_valid_json_serializable(self):
        from via.mcp.schema import build_tool_schema
        result = build_tool_schema()
        # Must serialize without error
        dumped = json.dumps(result)
        assert len(dumped) > 0

    def test_schema_has_name(self):
        from via.mcp.schema import build_tool_schema
        result = build_tool_schema()
        assert result.get('name') == 'via_query'

    def test_schema_has_description(self):
        from via.mcp.schema import build_tool_schema
        result = build_tool_schema()
        assert 'description' in result
        assert len(result['description']) > 10

    def test_schema_has_input_schema(self):
        from via.mcp.schema import build_tool_schema
        result = build_tool_schema()
        assert 'inputSchema' in result
        input_schema = result['inputSchema']
        assert input_schema.get('type') == 'object'

    def test_schema_includes_match_flags(self):
        from via.mcp.schema import build_tool_schema
        from via.core.flag_groups import MATCH_FLAGS
        result = build_tool_schema()
        dumped = json.dumps(result)
        # At least one match flag short form should appear in schema
        assert any(f.short in dumped or f.long in dumped for f in MATCH_FLAGS)

    def test_schema_includes_type_flags(self):
        from via.mcp.schema import build_tool_schema
        from via.core.flag_groups import TYPE_FLAGS
        result = build_tool_schema()
        dumped = json.dumps(result)
        assert any(f.short in dumped or f.long in dumped for f in TYPE_FLAGS)

    def test_schema_includes_output_flags(self):
        from via.mcp.schema import build_tool_schema
        from via.core.flag_groups import OUTPUT_FLAGS
        result = build_tool_schema()
        dumped = json.dumps(result)
        assert any(f.short in dumped or f.long in dumped for f in OUTPUT_FLAGS)

    def test_schema_includes_relationship_flags(self):
        from via.mcp.schema import build_tool_schema
        from via.core.flag_groups import RELATIONSHIP_FLAGS
        result = build_tool_schema()
        dumped = json.dumps(result)
        assert any(f.short in dumped or f.long in dumped for f in RELATIONSHIP_FLAGS)

    def test_schema_has_at_least_8_examples(self):
        from via.mcp.schema import build_tool_schema
        result = build_tool_schema()
        # Examples can be at top level or in inputSchema
        examples = result.get('examples', [])
        if not examples:
            examples = result.get('inputSchema', {}).get('examples', [])
        assert len(examples) >= 8, f"Expected >=8 examples, got {len(examples)}"


class TestMcpSchemaInit:
    def test_mcp_package_init_exists(self):
        import via.mcp
        assert via.mcp is not None


class TestViaMcpSchemaCLI:
    def test_via_mcp_schema_subcommand_exists(self):
        """via mcp schema should run without error."""
        result = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'schema'],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"via mcp schema failed: {result.stderr}"

    def test_via_mcp_schema_output_is_valid_json(self):
        result = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'schema'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)

    def test_via_mcp_schema_has_name(self):
        result = subprocess.run(
            [sys.executable, '-m', 'via', 'mcp', 'schema'],
            capture_output=True, text=True
        )
        parsed = json.loads(result.stdout)
        assert parsed.get('name') == 'via_query'

    def test_schema_description_mentions_Q_flag_for_full_path(self):
        from via.mcp.schema import build_tool_schema
        result = build_tool_schema()
        desc = result['description']
        assert '-Q' in desc, "Schema description must mention -Q for full-path matching"
        assert 'full-path' in desc.lower() or 'full path' in desc.lower()
