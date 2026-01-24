"""
Integration tests for CLI pipeline execution.

TLDR:
    Tests the new pipeline syntax end-to-end. Verifies pipeline parsing,
    stage execution, match stages, render stages, and error handling.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import subprocess
import sys
import pytest
from pathlib import Path
from via.db.store import DatabaseStore


@pytest.fixture
def indexed_project(tmp_path):
    """Create a temporary indexed project for testing."""
    # Create test Python file
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    test_module = project_dir / "module.py"
    test_module.write_text('''
import json
import os

MAX_RETRIES = 3
DEBUG_MODE = True

class TestClass:
    """A test class."""

    def test_method(self):
        """A test method."""
        pass

    def another_method(self):
        """Another method."""
        pass


class HelperClass:
    """A helper class."""
    pass


def test_function():
    """A test function."""
    pass


def helper_function():
    """A helper function."""
    pass
''')

    # Create database and populate symbols
    via_dir = project_dir / ".via"
    via_dir.mkdir()
    db_path = via_dir / "index.db"

    with DatabaseStore(str(db_path), str(project_dir)) as db:
        db.initialize_schema()

        # Insert file record
        file_id = db.insert_file(str(test_module), 'python', 500, 1234567890.0, True)

        # Insert symbols - simulating what indexer does
        db.insert_symbol('TestClass', 'class', 'module.py', 8, 'module.TestClass', 100, 200, None)
        db.insert_symbol('test_method', 'method', 'module.py', 12, 'module.TestClass.test_method', 150, 40, 'TestClass')
        db.insert_symbol('another_method', 'method', 'module.py', 17, 'module.TestClass.another_method', 200, 40, 'TestClass')
        db.insert_symbol('HelperClass', 'class', 'module.py', 23, 'module.HelperClass', 280, 50, None)
        db.insert_symbol('test_function', 'function', 'module.py', 28, 'module.test_function', 340, 50, None)
        db.insert_symbol('helper_function', 'function', 'module.py', 33, 'module.helper_function', 400, 50, None)
        db.insert_symbol('json', 'import', 'module.py', 2, 'json', 1, 11, None)
        db.insert_symbol('os', 'import', 'module.py', 3, 'os', 13, 9, None)
        db.insert_symbol('MAX_RETRIES', 'global', 'module.py', 5, 'module.MAX_RETRIES', 24, 15, None)
        db.insert_symbol('DEBUG_MODE', 'global', 'module.py', 6, 'module.DEBUG_MODE', 40, 16, None)

    return project_dir


class TestPipelineExecution:
    """Test pipeline CLI execution."""

    def test_simple_match_pipeline(self, indexed_project):
        """Test simple match pipeline: via -mg '*' -tc"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "TestClass" in result.stdout
        assert "HelperClass" in result.stdout

    def test_match_with_limit(self, indexed_project):
        """Test match with limit: via -mg '*' -tc -n 1"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "-n", "1"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Should have exactly 1 result
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) == 1

    def test_match_functions(self, indexed_project):
        """Test match functions: via -mg '*' -tf"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tf"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "test_function" in result.stdout
        assert "helper_function" in result.stdout

    def test_match_methods(self, indexed_project):
        """Test match methods: via -mg '*' -tm"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tm"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "test_method" in result.stdout
        assert "another_method" in result.stdout

    def test_match_with_pattern(self, indexed_project):
        """Test match with pattern filter: via -mg 'Test*' -tc"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "Test*", "-tc"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "TestClass" in result.stdout
        assert "HelperClass" not in result.stdout

    def test_match_case_insensitive(self, indexed_project):
        """Test case insensitive match: via -mg 'test*' -tc -I"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "test*", "-tc", "-I"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "TestClass" in result.stdout

    def test_match_imports(self, indexed_project):
        """Test match imports: via -mg '*' -ti"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-ti"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "json" in result.stdout
        assert "os" in result.stdout

    def test_match_globals(self, indexed_project):
        """Test match globals: via -mg '*' -tg"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tg"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "MAX_RETRIES" in result.stdout
        assert "DEBUG_MODE" in result.stdout


class TestPipelineWithRender:
    """Test pipeline with render output flags."""

    def test_match_and_render_list(self, indexed_project):
        """Test match with list render: via -mg '*' -tc -oL"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "-oL"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "TestClass" in result.stdout


class TestPipelineErrorHandling:
    """Test pipeline error handling."""

    def test_empty_args_shows_help(self, indexed_project):
        """Test empty args shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "via"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        # Should show help or usage
        assert result.returncode == 0 or "usage" in result.stdout.lower() or "help" in result.stdout.lower()

    def test_invalid_stage_shows_error(self, indexed_project):
        """Test invalid stage shows error."""
        result = subprocess.run(
            [sys.executable, "-m", "via", "--invalid-flag"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_database_not_found(self, tmp_path):
        """Test error when database not found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc"],
            cwd=str(empty_dir),
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "database" in result.stderr.lower() or "index" in result.stderr.lower()


class TestChainedPipeline:
    """Test chained pipeline execution."""

    def test_chained_match_with_regex(self, indexed_project):
        """Test chained match with regex: via -mg '*' -tm --via -mr '^test.*' -tm"""
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tm", "--via", "-mr", "^test.*", "-tm"],
            cwd=str(indexed_project),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "test_method" in result.stdout
        assert "another_method" not in result.stdout
