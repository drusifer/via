"""Sprint 23 Cycle 2 tests for task-oriented help and MCP schema."""
from __future__ import annotations

import subprocess
import sys

from via.__main__ import _build_pipeline_help
from via.mcp.schema import build_tool_schema


def test_help_contains_compact_common_tasks_and_show_expanded():
    help_text = _build_pipeline_help()

    assert "--show-expanded" in help_text
    assert "Common Tasks:" in help_text
    assert "via --canned callers --args symbol=parse_args" in help_text
    assert "via --canned symbol-body --args symbol=parse_args" in help_text
    assert "via --canned docs-headers --args pattern='*Install*'" in help_text
    assert "use uppercase -tH" in help_text
    assert "via -mr '^get_' -tm" in help_text
    assert "via -mg 'parse*' -tf -tm" in help_text
    assert "via --canned paged-scan --args pattern='*',slice=0:20 -tc" in help_text


def test_help_relationship_examples_are_runtime_oriented_without_fake_shortcuts():
    help_text = _build_pipeline_help()

    assert "Prefer canned shortcuts for callers/subclasses" in help_text
    assert "known anchor before --via" in help_text
    assert "via -mg 'parse_args' -tf --via calls -mg '*' -tf" in help_text
    assert "via -mg 'Base' -tc --via inherits-from -mg '*' -tc" in help_text
    assert "--callers" not in help_text
    assert "--callees" not in help_text
    assert "--declared-in-file" not in help_text


def test_mcp_schema_has_task_examples_without_unsupported_shortcuts():
    schema = build_tool_schema()
    description = schema["description"]
    examples = schema["examples"]

    assert "Common tasks:" in description
    assert "Use uppercase -tH" in description
    assert '["--canned", "callers", "--args", "symbol=parse_args"]' in description
    assert '["-mg", "parse*", "-tf", "-tm"]' in description
    assert "known anchor before --via" in description
    assert "callees" not in description
    assert "declared-in-file" not in description

    example_args = [ex["args"] for ex in examples]
    assert ["--canned", "symbol-body", "--args", "symbol=parse_args"] in example_args
    assert ["--canned", "callers", "--args", "symbol=connect"] in example_args
    assert ["--canned", "docs-headers", "--args", "pattern=*API*"] in example_args
    assert ["-mg", "parse*", "-tf", "-tm"] in example_args
    assert ["--canned", "paged-scan", "--args", "pattern=*,slice=0:20", "-tc"] in example_args


def test_help_growth_stays_within_sprint23_budget(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "via", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(tmp_path),
    )

    help_text = result.stdout + result.stderr
    assert len(help_text.splitlines()) <= 137
