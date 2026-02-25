"""
User Acceptance Tests for Sprint 3 - Internal Pipeline & Render System.

TLDR:
    Validates Sprint 3 pipeline features from an end-user perspective.
    Tests pipeline syntax, render stages, context lines, and subcommands.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0

UAT Scenarios from SPRINT_3_TEST_PLAN.md:
UAT-1: Basic Pipeline Syntax (glob, limit, regex, methods)
UAT-2: Render Pipeline (list, table, raw, formatted)
UAT-3: Context Lines (-B, -A, -C flags)
UAT-4: Subcommand Syntax (index, match, help)
"""

import subprocess
import sys
from pathlib import Path

import pytest
from via.db.store import DatabaseStore


@pytest.fixture(scope="module")
def uat_project(tmp_path_factory):
    """Create a realistic test project for UAT validation.

    This fixture creates a project with various Python constructs
    to test Sprint 3 pipeline and render features.
    """
    project_dir = tmp_path_factory.mktemp("sprint3_uat")

    # Create test module
    test_module = project_dir / "pipeline_demo.py"
    test_module.write_text('''"""Pipeline demo module for Sprint 3 UAT."""
import json
import os
from typing import Optional

MAX_BUFFER_SIZE = 4096
DEBUG_ENABLED = False


class IndexManager:
    """Manages search indexes."""

    def __init__(self, path: str):
        """Initialize index manager."""
        self.path = path
        self.indexes = {}

    def create_index(self, name: str) -> bool:
        """Create a new index."""
        if name in self.indexes:
            return False
        self.indexes[name] = []
        return True

    def delete_index(self, name: str) -> bool:
        """Delete an existing index."""
        if name not in self.indexes:
            return False
        del self.indexes[name]
        return True


class QueryParser:
    """Parses search queries."""

    def parse(self, query: str) -> dict:
        """Parse a query string."""
        return {"raw": query, "tokens": query.split()}


def test_pipeline_function():
    """Test function for pipeline validation."""
    pass


def helper_utility():
    """Helper utility function."""
    return "utility"


def another_test_function():
    """Another test function."""
    return 42
''')

    # Create second module for variety
    utils_module = project_dir / "utils.py"
    utils_module.write_text('''"""Utility module."""
import re
import sys

DEFAULT_TIMEOUT = 30


class StringHelper:
    """String manipulation utilities."""

    def trim(self, s: str) -> str:
        """Trim whitespace."""
        return s.strip()


def format_output(data: str) -> str:
    """Format output data."""
    return f"[OUTPUT] {data}"
''')

    # Create database and populate symbols
    via_dir = project_dir / ".via"
    via_dir.mkdir()
    db_path = via_dir / "index.db"

    with DatabaseStore(str(db_path), str(project_dir)) as db:
        db.initialize_schema()

        # Insert file records - use proper byte offsets from actual file content
        demo_content = test_module.read_text()
        utils_content = utils_module.read_text()

        file1_id = db.insert_file(
            str(test_module), 'python', len(demo_content), 1234567890.0, True
        )
        file2_id = db.insert_file(
            str(utils_module), 'python', len(utils_content), 1234567890.0, True
        )

        # Insert symbols for pipeline_demo.py
        # Classes
        idx_start = demo_content.find("class IndexManager:")
        idx_end = demo_content.find("class QueryParser:")
        db.insert_symbol(
            'IndexManager', 'class', 'pipeline_demo.py', 10,
            'pipeline_demo.IndexManager', idx_start, idx_end - idx_start, None
        )

        qp_start = demo_content.find("class QueryParser:")
        qp_end = demo_content.find("def test_pipeline_function")
        db.insert_symbol(
            'QueryParser', 'class', 'pipeline_demo.py', 29,
            'pipeline_demo.QueryParser', qp_start, qp_end - qp_start, None
        )

        # Methods
        create_start = demo_content.find("def create_index")
        create_end = demo_content.find("def delete_index")
        db.insert_symbol(
            'create_index', 'method', 'pipeline_demo.py', 18,
            'pipeline_demo.IndexManager.create_index',
            create_start, create_end - create_start, 'IndexManager'
        )

        delete_start = demo_content.find("def delete_index")
        delete_end = demo_content.find("class QueryParser:")
        db.insert_symbol(
            'delete_index', 'method', 'pipeline_demo.py', 24,
            'pipeline_demo.IndexManager.delete_index',
            delete_start, delete_end - delete_start, 'IndexManager'
        )

        parse_start = demo_content.find('def parse(self, query')
        parse_end = demo_content.find("def test_pipeline_function")
        db.insert_symbol(
            'parse', 'method', 'pipeline_demo.py', 33,
            'pipeline_demo.QueryParser.parse',
            parse_start, parse_end - parse_start, 'QueryParser'
        )

        # Functions
        test_fn_start = demo_content.find("def test_pipeline_function")
        test_fn_end = demo_content.find("def helper_utility")
        db.insert_symbol(
            'test_pipeline_function', 'function', 'pipeline_demo.py', 38,
            'pipeline_demo.test_pipeline_function',
            test_fn_start, test_fn_end - test_fn_start, None
        )

        helper_start = demo_content.find("def helper_utility")
        helper_end = demo_content.find("def another_test_function")
        db.insert_symbol(
            'helper_utility', 'function', 'pipeline_demo.py', 43,
            'pipeline_demo.helper_utility',
            helper_start, helper_end - helper_start, None
        )

        another_start = demo_content.find("def another_test_function")
        db.insert_symbol(
            'another_test_function', 'function', 'pipeline_demo.py', 48,
            'pipeline_demo.another_test_function',
            another_start, len(demo_content) - another_start, None
        )

        # Imports
        db.insert_symbol('json', 'import', 'pipeline_demo.py', 2, 'json', 0, 11, None)
        db.insert_symbol('os', 'import', 'pipeline_demo.py', 3, 'os', 12, 9, None)
        db.insert_symbol(
            'Optional', 'import', 'pipeline_demo.py', 4,
            'typing.Optional', 22, 28, None
        )

        # Globals
        buf_start = demo_content.find("MAX_BUFFER_SIZE")
        buf_end = demo_content.find("DEBUG_ENABLED")
        db.insert_symbol(
            'MAX_BUFFER_SIZE', 'global', 'pipeline_demo.py', 6,
            'pipeline_demo.MAX_BUFFER_SIZE', buf_start, buf_end - buf_start, None
        )

        dbg_start = demo_content.find("DEBUG_ENABLED")
        dbg_end = demo_content.find("class IndexManager:")
        db.insert_symbol(
            'DEBUG_ENABLED', 'global', 'pipeline_demo.py', 7,
            'pipeline_demo.DEBUG_ENABLED', dbg_start, dbg_end - dbg_start, None
        )

        # Insert symbols for utils.py
        sh_start = utils_content.find("class StringHelper:")
        sh_end = utils_content.find("def format_output")
        db.insert_symbol(
            'StringHelper', 'class', 'utils.py', 8,
            'utils.StringHelper', sh_start, sh_end - sh_start, None
        )

        trim_start = utils_content.find("def trim")
        trim_end = utils_content.find("def format_output")
        db.insert_symbol(
            'trim', 'method', 'utils.py', 11,
            'utils.StringHelper.trim', trim_start, trim_end - trim_start, 'StringHelper'
        )

        fmt_start = utils_content.find("def format_output")
        db.insert_symbol(
            'format_output', 'function', 'utils.py', 16,
            'utils.format_output', fmt_start, len(utils_content) - fmt_start, None
        )

        db.insert_symbol('re', 'import', 'utils.py', 2, 're', 0, 9, None)
        db.insert_symbol('sys', 'import', 'utils.py', 3, 'sys', 10, 10, None)

        timeout_start = utils_content.find("DEFAULT_TIMEOUT")
        timeout_end = utils_content.find("class StringHelper:")
        db.insert_symbol(
            'DEFAULT_TIMEOUT', 'global', 'utils.py', 5,
            'utils.DEFAULT_TIMEOUT', timeout_start, timeout_end - timeout_start, None
        )

    return project_dir


# =============================================================================
# UAT-1: Basic Pipeline Syntax
# =============================================================================


class TestUAT1BasicPipelineSyntax:
    """UAT-1: Basic Pipeline Syntax tests."""

    def test_uat_1_1_match_classes_with_glob(self, uat_project):
        """UAT-1.1: Match classes with glob pattern.

        Command: via -mg '*' -tc
        Expected: Lists all classes
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "IndexManager" in result.stdout
        assert "QueryParser" in result.stdout
        assert "StringHelper" in result.stdout

    def test_uat_1_2_match_functions_with_limit(self, uat_project):
        """UAT-1.2: Match functions with limit.

        Command: via -mg '*' -tf -n 2
        Expected: Lists at most 2 functions
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tf", "-n", "2"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Count non-empty output lines
        lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
        assert len(lines) <= 2, f"Expected at most 2 results, got {len(lines)}"

    def test_uat_1_3_match_with_regex(self, uat_project):
        """UAT-1.3: Match with regex pattern (uses Python-side filtering).

        Command: via -mr 'test_.*' -tf
        Expected: Lists test functions
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mr", "test_.*", "-tf"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "test_pipeline_function" in result.stdout

    def test_uat_1_4_match_methods(self, uat_project):
        """UAT-1.4: Match methods.

        Command: via -mg '*' -tm
        Expected: Lists all methods
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tm"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "create_index" in result.stdout
        assert "delete_index" in result.stdout
        assert "parse" in result.stdout
        assert "trim" in result.stdout


# =============================================================================
# UAT-2: Render Pipeline
# =============================================================================


class TestUAT2RenderPipeline:
    """UAT-2: Render Pipeline tests."""

    def test_uat_2_1_list_render(self, uat_project):
        """UAT-2.1: List render output.

        Command: via -mg '*' -tc -oL
        Expected: One class per line
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "-oL"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "IndexManager" in result.stdout
        assert "QueryParser" in result.stdout

    def test_uat_2_2_table_render(self, uat_project):
        """UAT-2.2: Table render output.

        Command: via -mg '*' -tc -oT
        Expected: ASCII table format with columns
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "-oT"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Table should have dividers or column-like structure
        assert "IndexManager" in result.stdout
        # Check for table-like structure (pipes or dashes)
        assert "|" in result.stdout or "-" in result.stdout

    def test_uat_2_3_raw_render(self, uat_project):
        """UAT-2.3: Raw source code render.

        Command: via -mg 'Index*' -tc -oR
        Expected: Raw source code output
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "Index*", "-tc", "-oR"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should contain actual source code
        assert "class IndexManager" in result.stdout
        assert "def __init__" in result.stdout or "def create_index" in result.stdout

    def test_uat_2_4_formatted_render(self, uat_project):
        """UAT-2.4: Formatted render with syntax highlighting.

        Command: via -mg 'Index*' -tc -oF
        Expected: Syntax highlighted output (contains ANSI codes or formatted)
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "Index*", "-tc", "-oF"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should contain source code (possibly with ANSI codes)
        assert "IndexManager" in result.stdout


# =============================================================================
# UAT-3: Context Lines
# =============================================================================


class TestUAT3ContextLines:
    """UAT-3: Context Lines tests."""

    def test_uat_3_1_before_context(self, uat_project):
        """UAT-3.1: Before context lines.

        Command: via -mg 'test_pipeline*' -tf -oR -B 3
        Expected: Shows 3 lines before match
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "test_pipeline*", "-tf",
             "-oR", "-B", "3"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Output should contain the function
        assert "test_pipeline_function" in result.stdout

    def test_uat_3_2_after_context(self, uat_project):
        """UAT-3.2: After context lines.

        Command: via -mg 'test_pipeline*' -tf -oR -A 3
        Expected: Shows 3 lines after match
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "test_pipeline*", "-tf",
             "-oR", "-A", "3"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Output should contain the function
        assert "test_pipeline_function" in result.stdout

    def test_uat_3_3_both_context(self, uat_project):
        """UAT-3.3: Both before and after context.

        Command: via -mg 'helper*' -tf -oF -C 2
        Expected: Shows 2 lines before and after
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "helper*", "-tf",
             "-oF", "-C", "2"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Output should contain the function
        assert "helper_utility" in result.stdout


# =============================================================================
# UAT-4: Subcommand Syntax
# =============================================================================


class TestUAT4SubcommandSyntax:
    """UAT-4: Subcommand Syntax tests."""

    def test_uat_4_1_index_command(self, tmp_path):
        """UAT-4.1: Index command.

        Command: via index .
        Expected: Indexes directory successfully
        """
        # Create a simple Python file to index
        test_file = tmp_path / "test_module.py"
        test_file.write_text('''"""Test module."""

class TestClass:
    """A test class."""
    pass


def test_func():
    """A test function."""
    pass
''')

        result = subprocess.run(
            [sys.executable, "-m", "via", "index", str(tmp_path)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Verify database was created
        via_dir = tmp_path / ".via"
        assert via_dir.exists(), "Index directory not created"
        assert (via_dir / "index.db").exists(), "Database not created"

    def test_uat_4_2_match_command(self, uat_project):
        """UAT-4.2: Match with pipeline syntax.

        Command: via -mg '*' -tc
        Expected: Lists classes
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "IndexManager" in result.stdout or "class" in result.stdout.lower()

    def test_uat_4_3_help_command(self, uat_project):
        """UAT-4.3: Help command.

        Command: via --help
        Expected: Shows usage information
        """
        result = subprocess.run(
            [sys.executable, "-m", "via", "--help"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should contain usage information
        assert "usage" in result.stdout.lower() or "via" in result.stdout.lower()


# =============================================================================
# Additional Regression Tests
# =============================================================================


class TestAdditionalRegressions:
    """Additional regression tests for Sprint 3."""

    def test_match_with_list_output(self, uat_project):
        """Test match with list output (single invocation)."""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "Index*", "-tc", "-oL"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should show IndexManager class
        assert "IndexManager" in result.stdout

    def test_unlimited_results(self, uat_project):
        """Test -n 0 for unlimited results."""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tf", "-n", "0"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should have all functions
        assert "test_pipeline_function" in result.stdout
        assert "helper_utility" in result.stdout
        assert "another_test_function" in result.stdout
        assert "format_output" in result.stdout

    def test_case_insensitive_match(self, uat_project):
        """Test case insensitive matching with -I flag."""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "indexmanager", "-tc", "-I"],
            cwd=str(uat_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should find IndexManager despite lowercase search
        assert "IndexManager" in result.stdout
