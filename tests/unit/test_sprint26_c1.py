"""
Unit tests for Sprint 26 Cycle 1 — Natural Query Parser.

Theme: Test-Driven Development (TDD) of LarkNaturalQueryParser, translating
English codebase queries deterministicly to standard VIA CLI pipeline args.
"""
from __future__ import annotations

import pytest
from via.pipeline.natural_query import NaturalQueryParserBase, LarkNaturalQueryParser
from via.pipeline.errors import PipelineParseError


def test_classes_exist():
    """Verify parser polymorphic interface and class structure."""
    assert issubclass(LarkNaturalQueryParser, NaturalQueryParserBase)


def test_basic_natural_queries():
    """Test basic target/matcher compilation without relationship filters."""
    parser = LarkNaturalQueryParser()

    # Simple target nouns
    assert parser.parse("find classes") == ["-mg", "*", "-tc", "-fm"]
    assert parser.parse("show me functions") == ["-mg", "*", "-tf", "-fm"]
    
    # Limit modifier 'all'
    assert parser.parse("show me all functions") == ["-mg", "*", "-tf", "-fm", "-n", "0"]
    assert parser.parse("list all files") == ["-mg", "*", "-tF", "-fm", "-n", "0"]

    # Optional articles noise word stripping
    assert parser.parse("find the classes") == ["-mg", "*", "-tc", "-fm"]
    assert parser.parse("locate a method") == ["-mg", "*", "-tm", "-fm"]
    assert parser.parse("get an import") == ["-mg", "*", "-ti", "-fm"]

    # Matchers (glob and regex)
    assert parser.parse("list files matching '*.py'") == ["-mg", "*.py", "-tF", "-fm"]
    assert parser.parse("list files matching \"*.py\"") == ["-mg", "*.py", "-tF", "-fm"]
    assert parser.parse("classes named 'UserController'") == ["-mg", "UserController", "-tc", "-fm"]
    assert parser.parse("methods whose name contains 'save'") == ["-mg", "*save*", "-tm", "-fm"]
    assert parser.parse("functions matching regex '^test_'") == ["-mr", "^test_", "-tf", "-fm"]


def test_bounds_windowing_slices():
    """Verify result window bounds map human 1-based indexing to 0-based result slices."""
    parser = LarkNaturalQueryParser()

    # first/top N
    assert parser.parse("get first 5 classes") == ["-mg", "*", "-tc", "-fm", "-n", "5"]
    assert parser.parse("show me top 20 functions") == ["-mg", "*", "-tf", "-fm", "-n", "20"]

    # last N
    assert parser.parse("search for functions last 10 matches") == ["-mg", "*", "-tf", "-fm", "--slice", "-10:"]
    assert parser.parse("methods last 40 rows") == ["-mg", "*", "-tm", "-fm", "--slice", "-40:"]

    # between X and Y
    assert parser.parse("locate methods between rows 5 and 10") == ["-mg", "*", "-tm", "-fm", "--slice", "4:10"]
    assert parser.parse("locate methods between results 1 and 20") == ["-mg", "*", "-tm", "-fm", "--slice", "0:20"]

    # range X to Y
    assert parser.parse("methods rows 5 to 8") == ["-mg", "*", "-tm", "-fm", "--slice", "4:8"]
    
    # offset from X
    assert parser.parse("classes from row 5") == ["-mg", "*", "-tc", "-fm", "--slice", "4:"]
    assert parser.parse("functions from match 1") == ["-mg", "*", "-tf", "-fm", "--slice", "0:"]


def test_unknown_target_validation():
    """Verify explicit validation errors are thrown on unknown symbol target types."""
    parser = LarkNaturalQueryParser()

    with pytest.raises(PipelineParseError) as exc_info:
        parser.parse("find widgets")
    assert "Unknown symbol target 'widgets'" in str(exc_info.value)
    assert "Valid options are:" in str(exc_info.value)
    assert "classes, functions, methods, files, globals, variables, constants, imports, headers, sections" in str(exc_info.value)

    with pytest.raises(PipelineParseError) as exc_info:
        parser.parse("list controllers matching '*Widget*'")
    assert "Unknown symbol target 'controllers'" in str(exc_info.value)


def test_relationship_chaining_and_negation():
    """Verify multi-stage relationship chaining and negated filters."""
    parser = LarkNaturalQueryParser()

    # calls / calling
    assert parser.parse("find functions calling classes matching '*Widget*'") == [
        "-mg", "*", "-tf", "--via", "calls", "-mg", "*Widget*", "-tc", "-fm"
    ]

    # nested / multiple chaining
    # A extending B not calling C
    assert parser.parse("classes extending class matching '*Controller*' not calling methods matching '*post*'") == [
        "-mg", "*", "-tc", "--via", "inherits-from", "-mg", "*Controller*", "-tc", "--sans", "calls", "-mg", "*post*", "-tm", "-fm"
    ]


def test_cli_ask_parser_integration():
    """Verify ask/q subcommand argument parsing."""
    from via.__main__ import _create_parser

    parser = _create_parser()

    # Basic ask subcommand parsing
    args = parser.parse_args(['ask', 'find classes'])
    assert args.command == 'ask'
    assert args.query == 'find classes'
    assert args.dry_run is False

    # q alias parsing
    args = parser.parse_args(['q', 'show functions'])
    assert args.command == 'q'
    assert args.query == 'show functions'

    # --dry-run / -d flag parsing
    args = parser.parse_args(['ask', 'find files', '--dry-run'])
    assert args.dry_run is True

    args = parser.parse_args(['q', 'find files', '-d'])
    assert args.dry_run is True


def test_run_ask_command_dry_run(capsys):
    """Verify _run_ask_command correctly outputs compiled parameters on dry-run."""
    import argparse
    from via.__main__ import _run_ask_command

    args = argparse.Namespace(
        query="find functions calling classes matching *Widget*",
        dry_run=True
    )
    code = _run_ask_command(args)
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == 'via -mg "*" -tf --via calls -mg "*Widget*" -tc -fm'


def test_mcp_via_ask_tool_response():
    """Verify that calling via_ask MCP logic compiles and executes correctly."""
    import logging
    from via.mcp.server import _mcp_query_response
    from via.pipeline.natural_query import LarkNaturalQueryParser

    class MockRunner:
        def __init__(self):
            self.called_args = None

        def run_cli_args(self, args):
            self.called_args = args
            return []

    runner = MockRunner()
    parser = LarkNaturalQueryParser()
    compiled_args = parser.parse("find functions calling classes matching *Widget*")

    response = _mcp_query_response(
        runner,
        compiled_args,
        logging.getLogger(__name__)
    )

    assert runner.called_args == ["-mg", "*", "-tf", "--via", "calls", "-mg", "*Widget*", "-tc", "-fm"]
    assert response == {
        "output_type": "json",
        "result": [],
        "total": 0,
        "shown": 0
    }


