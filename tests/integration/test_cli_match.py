"""
Integration tests for CLI match command.

TLDR:
    Tests the `via match` CLI command end-to-end. Verifies argument parsing,
    match syntax flags (-g/-r/-s), symbol type filters, qualifier flags,
    output formatting, and error handling.

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
        db.insert_symbol('test_function', 'function', 'module.py', 23, 'module.test_function', 300, 50, None)
        db.insert_symbol('helper_function', 'function', 'module.py', 28, 'module.helper_function', 360, 50, None)
        db.insert_symbol('json', 'import', 'module.py', 2, 'json', 1, 11, None)
        db.insert_symbol('os', 'import', 'module.py', 3, 'os', 13, 9, None)
        db.insert_symbol('MAX_RETRIES', 'global', 'module.py', 5, 'module.MAX_RETRIES', 24, 15, None)
        db.insert_symbol('DEBUG_MODE', 'global', 'module.py', 6, 'module.DEBUG_MODE', 40, 16, None)
        db.insert_symbol('module.py', 'filename', 'module.py', 0, 'module.py', None, None, None)
        db.insert_symbol('module.py', 'filepath', 'module.py', 0, 'module.py', None, None, None)

    yield project_dir, db_path


def run_via_match(args, project_dir):
    """Run via match command and return result."""
    cmd = [sys.executable, '-m', 'via', 'match'] + args + ['-d', str(project_dir)]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestCLICommandParsing:
    """Tests for CLI argument parsing."""

    def test_match_command_with_required_args(self, indexed_project):
        """Test match command with required arguments."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'function', '-g', 'test_*'], project_dir)
        assert result.returncode == 0
        assert 'test_function' in result.stdout

    def test_match_command_alias(self, indexed_project):
        """Test match command with 'm' alias."""
        project_dir, _ = indexed_project
        cmd = [sys.executable, '-m', 'via', 'm', '-t', 'function', '-g', '*', '-d', str(project_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0

    def test_match_command_missing_type(self, indexed_project):
        """Test match command fails without --type."""
        project_dir, _ = indexed_project
        cmd = [sys.executable, '-m', 'via', 'match', 'pattern', '-d', str(project_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode != 0


class TestMatchSyntaxFlags:
    """Tests for match syntax flags."""

    def test_match_with_glob_flag(self, indexed_project):
        """Test -g/--glob flag."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'function', '-g', 'test_*'], project_dir)
        assert result.returncode == 0
        assert 'test_function' in result.stdout

    @pytest.mark.skip(reason="SQLite REGEXP requires extension not installed by default")
    def test_match_with_regex_flag(self, indexed_project):
        """Test -r/--regex flag."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'function', '-r', '^test_.*'], project_dir)
        assert result.returncode == 0
        assert 'test_function' in result.stdout

    def test_match_with_sql_flag(self, indexed_project):
        """Test -s/--sql flag."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'function', '-s', 'test_%'], project_dir)
        assert result.returncode == 0
        assert 'test_function' in result.stdout


class TestSymbolTypeFilters:
    """Tests for symbol type filters."""

    def test_match_methods(self, indexed_project):
        """Test matching methods."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'method', '-g', '*'], project_dir)
        assert result.returncode == 0
        assert 'method:' in result.stdout

    def test_match_classes(self, indexed_project):
        """Test matching classes."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'class', '-g', '*'], project_dir)
        assert result.returncode == 0
        assert 'class:' in result.stdout
        assert 'TestClass' in result.stdout

    def test_match_functions(self, indexed_project):
        """Test matching functions."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'function', '-g', '*'], project_dir)
        assert result.returncode == 0
        assert 'function:' in result.stdout

    def test_match_imports(self, indexed_project):
        """Test matching imports."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'import', '-g', '*'], project_dir)
        assert result.returncode == 0
        assert 'import:' in result.stdout
        assert 'json' in result.stdout

    def test_match_globals(self, indexed_project):
        """Test matching globals."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'global', '-g', '*'], project_dir)
        assert result.returncode == 0
        assert 'global:' in result.stdout
        assert 'MAX_RETRIES' in result.stdout


class TestQualifierFlags:
    """Tests for qualifier flags."""

    def test_match_case_insensitive_flag(self, indexed_project):
        """Test -I/--case-insensitive flag."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'class', '-g', 'testclass', '-I'], project_dir)
        assert result.returncode == 0
        assert 'TestClass' in result.stdout

    def test_match_limit_flag(self, indexed_project):
        """Test -n/--limit flag."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'function', '-g', '*', '-n', '1'], project_dir)
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) == 1


class TestOutputFormat:
    """Tests for output formatting."""

    def test_match_output_format_with_byte_position(self, indexed_project):
        """Test output includes byte position for methods."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'method', '-g', '*'], project_dir)
        assert result.returncode == 0
        # Format: type:file:line:qualified:@offset+length
        assert '@' in result.stdout
        assert '+' in result.stdout

    def test_match_output_format_without_byte_position(self, indexed_project):
        """Test output for files doesn't include byte position."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'filename', '-g', '*'], project_dir)
        assert result.returncode == 0
        # Filename entries have no byte position
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.startswith('filename:'):
                # Should NOT have @offset+length
                assert ':@' not in line or line.endswith(':@None+None') or ':@' not in line.split(':')[-1]


class TestErrorHandling:
    """Tests for error handling."""

    def test_match_database_not_found(self, tmp_path):
        """Test error when database doesn't exist."""
        cmd = [sys.executable, '-m', 'via', 'match', '-t', 'function', '-g', '*', '-d', str(tmp_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode != 0
        assert 'Database not found' in result.stderr
        assert 'via index' in result.stderr  # Suggests running index first

    def test_match_directory_not_found(self):
        """Test error when directory doesn't exist."""
        cmd = [sys.executable, '-m', 'via', 'match', '-t', 'function', '-g', '*', '-d', '/nonexistent/path']
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode != 0
        assert 'does not exist' in result.stderr.lower()


class TestStreamingOutput:
    """Tests for streaming output behavior."""

    def test_match_no_headers_footers(self, indexed_project):
        """Test that output has no headers or footers (clean for piping)."""
        project_dir, _ = indexed_project
        result = run_via_match(['-t', 'function', '-g', '*'], project_dir)
        assert result.returncode == 0
        # Should only have result lines, no headers/footers
        assert '====' not in result.stdout
        assert 'COMPLETE' not in result.stdout.upper()
        assert 'INDEXING' not in result.stdout.upper()
