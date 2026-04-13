"""Sprint 22 Cycle 2 tests for match-stage and regex validation."""
from __future__ import annotations

import pytest

from via.pipeline.errors import PipelineParseError
from via.pipeline.parser import PipelineParser


def test_repeated_match_glob_rejected_in_result_stage():
    with pytest.raises(PipelineParseError) as excinfo:
        PipelineParser().parse(["-mg", "*mcp*", "-mg", "*schema*", "-tf"])

    exc = excinfo.value
    assert exc.code == "multiple_matchers"
    assert "Use one match flag per stage" in (exc.hint or "")


def test_mixed_matchers_rejected_in_result_stage():
    with pytest.raises(PipelineParseError) as excinfo:
        PipelineParser().parse(["-mg", "*schema*", "-mr", "^test_", "-tf"])

    exc = excinfo.value
    assert exc.code == "multiple_matchers"
    assert "result stage" in str(exc)


def test_repeated_matcher_rejected_in_filter_stage():
    with pytest.raises(PipelineParseError) as excinfo:
        PipelineParser().parse([
            "-mg", "*handler*", "-tf",
            "--via", "calls",
            "-mg", "*parse*", "-mg", "*args*", "-tf",
        ])

    exc = excinfo.value
    assert exc.code == "multiple_matchers"
    assert "filter stage" in str(exc)


def test_separate_result_and_filter_stage_matchers_are_valid():
    stages = PipelineParser().parse([
        "-mg", "*handler*", "-tf",
        "--via", "calls",
        "-mr", "^parse_", "-tf",
    ])

    assert len(stages) == 1
    assert stages[0].args.pattern == "*handler*"
    assert stages[0].args.relationship.filter_pattern == "^parse_"
    assert stages[0].args.relationship.filter_match_syntax == "r"


def test_invalid_regex_rejected_in_result_stage():
    with pytest.raises(PipelineParseError) as excinfo:
        PipelineParser().parse(["-mr", "[", "-tf"])

    exc = excinfo.value
    assert exc.code == "invalid_regex"
    assert "Fix the -mr" in (exc.hint or "")


def test_invalid_regex_rejected_in_filter_stage():
    with pytest.raises(PipelineParseError) as excinfo:
        PipelineParser().parse([
            "-mg", "*handler*", "-tf",
            "--via", "calls",
            "-mr", "[", "-tf",
        ])

    exc = excinfo.value
    assert exc.code == "invalid_regex"
    assert "filter stage" in str(exc)


def test_valid_regex_with_no_matches_still_parses():
    stages = PipelineParser().parse(["-mr", "^NoSuchSymbol$", "-tf"])

    assert len(stages) == 1
    assert stages[0].args.pattern == "^NoSuchSymbol$"
    assert stages[0].args.match_syntax == "r"


def test_multi_type_or_remains_valid():
    stages = PipelineParser().parse(["-mg", "*mcp*", "-tf", "-tm", "-tc"])

    assert len(stages) == 1
    assert stages[0].args.symbol_types == ["function", "method", "class"]
    assert stages[0].args.symbol_type is None
