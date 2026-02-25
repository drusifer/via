"""
Integration tests for CLI index command.

TLDR:
    Tests the `via index` command end-to-end. Creates temporary test projects,
    runs the CLI, and verifies database contents, output, and exit codes.
    Tests happy path scenarios including indexing, force re-indexing, and
    custom database paths.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from via.core.constants import EXIT_SUCCESS
from via.core.types import MatchOp, SymbolType
from via.db.store import DatabaseStore


class TestCLIIndexCommand:
    """Integration tests for `via index` command."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary test project with Python files."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create sample Python file
        sample_file = project_dir / "sample.py"
        sample_file.write_text("""
\"\"\"Sample module.\"\"\"

import os
from typing import List

def hello(name: str) -> str:
    \"\"\"Greet someone.\"\"\"
    return f"Hello, {name}!"

class Person:
    \"\"\"Person class.\"\"\"

    def __init__(self, name: str):
        self.name = name

GREETING = "Welcome"
""")

        return project_dir

    def test_index_current_directory(self, temp_project, monkeypatch):
        """Test `via index` in current directory."""
        monkeypatch.chdir(temp_project)

        result = subprocess.run(
            ['via', 'index'],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS
        assert "INDEXING COMPLETE" in result.stdout
        assert "Files indexed:           1" in result.stdout
        assert "Functions:             2" in result.stdout  # hello + __init__
        assert "Classes:               1" in result.stdout
        assert "Imports:               2" in result.stdout
        assert "Globals:               1" in result.stdout

        # Verify database was created
        db_path = temp_project / ".via" / "index.db"
        assert db_path.exists()

    def test_index_specific_directory(self, temp_project):
        """Test `via index <directory>`."""
        result = subprocess.run(
            ['via', 'index', str(temp_project)],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS
        assert "INDEXING COMPLETE" in result.stdout
        assert "Files indexed:           1" in result.stdout

    def test_index_with_force(self, temp_project):
        """Test `via index --force` re-indexes all files."""
        # First index
        result1 = subprocess.run(
            ['via', 'index', str(temp_project)],
            capture_output=True,
            text=True
        )
        assert result1.returncode == EXIT_SUCCESS
        assert "Files indexed:           1" in result1.stdout

        # Second index without force (should skip)
        result2 = subprocess.run(
            ['via', 'index', str(temp_project)],
            capture_output=True,
            text=True
        )
        assert result2.returncode == EXIT_SUCCESS
        assert "Files skipped:           1" in result2.stdout
        assert "Files indexed:           0" in result2.stdout

        # Third index with --force (should re-index)
        result3 = subprocess.run(
            ['via', 'index', '--force', str(temp_project)],
            capture_output=True,
            text=True
        )
        assert result3.returncode == EXIT_SUCCESS
        assert "Files indexed:           1" in result3.stdout

    def test_index_with_custom_db(self, temp_project, tmp_path):
        """Test `via index --db <path>`."""
        custom_db = tmp_path / "custom.db"

        result = subprocess.run(
            ['via', 'index', '--db', str(custom_db), str(temp_project)],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS
        assert custom_db.exists()

        # Verify data in custom database
        with DatabaseStore(str(custom_db), str(temp_project)) as db:
            files = db.get_all_files()
            assert len(files) == 1

    def test_index_with_verbosity(self, temp_project):
        """Test `via -vvv index` shows verbose output."""
        result = subprocess.run(
            ['via', '-vvv', 'index', str(temp_project)],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS
        # Should have INFO/DEBUG log messages in stderr
        assert "INFO" in result.stderr or "DEBUG" in result.stderr

    def test_index_creates_via_directory(self, temp_project):
        """Test that .via/ directory is created."""
        via_dir = temp_project / ".via"
        assert not via_dir.exists()

        result = subprocess.run(
            ['via', 'index', str(temp_project)],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS
        assert via_dir.exists()
        assert via_dir.is_dir()

    def test_index_database_contents(self, temp_project):
        """Test that database contains correct data."""
        result = subprocess.run(
            ['via', 'index', str(temp_project)],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS

        # Query database using match API
        db_path = temp_project / ".via" / "index.db"
        with DatabaseStore(str(db_path), str(temp_project)) as db:
            # Check files
            files = db.get_all_files()
            assert len(files) == 1
            assert files[0]['path'].endswith('sample.py')

            # Check functions using match
            functions = list(db.match(SymbolType.FUNCTION, MatchOp.GLOB, '*'))
            assert len(functions) == 1
            assert functions[0].symbol_name == 'hello'

            # Check methods using match
            methods = list(db.match(SymbolType.METHOD, MatchOp.GLOB, '*'))
            assert len(methods) == 1
            assert methods[0].symbol_name == '__init__'

            # Check classes using match
            classes = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))
            assert len(classes) == 1
            assert classes[0].symbol_name == 'Person'

            # Check imports using match
            imports = list(db.match(SymbolType.IMPORT, MatchOp.GLOB, '*'))
            assert len(imports) == 2

            # Check globals using match
            globals_list = list(db.match(SymbolType.GLOBAL, MatchOp.GLOB, '*'))
            assert len(globals_list) == 1
            assert globals_list[0].symbol_name == 'GREETING'

    def test_index_empty_directory(self, tmp_path):
        """Test indexing empty directory succeeds."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = subprocess.run(
            ['via', 'index', str(empty_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS
        assert "Files indexed:           0" in result.stdout

    def test_index_no_python_files(self, tmp_path):
        """Test indexing directory with no Python files."""
        no_py_dir = tmp_path / "no_python"
        no_py_dir.mkdir()

        # Create non-Python file
        (no_py_dir / "readme.txt").write_text("Not Python")

        result = subprocess.run(
            ['via', 'index', str(no_py_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_SUCCESS
        assert "Files indexed:           0" in result.stdout
