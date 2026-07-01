"""Sprint 22 Cycle 3 tests for docs, schema, and help wording."""
from __future__ import annotations

from pathlib import Path

from via.__main__ import _build_pipeline_help
from via.mcp.schema import build_tool_schema


ROOT = Path(__file__).resolve().parents[2]


def test_help_teaches_result_stage_first_model():
    help_text = _build_pipeline_help()

    assert "via <match stage> [--via|--sans REL <relationship stage>]" in help_text
    assert "Use one match flag (-mg, -mr, or -ms) per stage" in help_text
    assert "Prefer canned shortcuts for callers/subclasses" in help_text
    assert "via -mg 'Base' -tc --via inherits-from -mg '*' -tc" in help_text
    assert "All symbols declared in a file" not in help_text


def test_mcp_schema_teaches_stage_filters_and_regex():
    schema = build_tool_schema()
    description = schema["description"]
    examples = schema["examples"]

    assert "via <match stage> [--via|--sans REL <relationship stage>]" in description
    assert "Common tasks:" in description
    assert "Use only one match flag (-mg, -mr, or -ms) per stage" in description
    assert '["-mr", "^get_", "-tm"]' in description
    assert "does not provide" in description
    assert "known anchor before --via" in description

    subclass_example = next(
        ex for ex in examples
        if ex["description"].startswith("Find all subclasses")
    )
    assert subclass_example["args"] == [
        "-mg", "BaseClass", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"
    ]


def test_project_quick_reference_removed_inverse_declares_claim():
    project = (ROOT / "agents" / "PROJECT.md").read_text()

    assert "Find files declaring X" in project
    assert "Find all symbols in a file" not in project
    assert "Relationship stages filter the initial result stage" in project
    assert "not a relationship shortcut" in project


def test_user_guide_relationship_section_uses_result_stage_language():
    guide = (ROOT / "docs" / "specs" / "relationships_and_filters.md").read_text()

    assert "via <result-stage> --via <rel> <filter-stage>" in guide
    assert "result stage" in guide
    assert "filter stage" in guide
    assert "Use only one match flag" in guide
    assert "Container Filters (`--via declares`)" in guide
    assert "does not invert the query" in guide
    assert "Container Queries" not in guide
    assert "via <anchor>" not in guide
    assert "anchor LEFT" not in guide
