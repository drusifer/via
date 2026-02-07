"""
Integration tests for CLI relationship queries (Sprint 5).

TLDR:
    Tests end-to-end relationship queries via CLI: inheritance, calls, imports.
    Verifies pipeline parsing and execution for relationship-based queries.

Author: Neo (SWE)
Sprint: 5
"""

import subprocess
import sys
import pytest
from pathlib import Path
from via.db.store import DatabaseStore
from via.services.indexing import IndexingService
from via.parsers.registry import ParserRegistry
from via.parsers.python_parser import PythonParser
from via.core.discovery import DiscoveredFile


@pytest.fixture
def indexed_project_with_relationships(tmp_path):
    """Create a temporary indexed project with relationships for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create test Python file with inheritance, calls, and imports
    test_module = project_dir / "module.py"
    test_module.write_text('''
import os
import json
from pathlib import Path

class BaseClass:
    """A base class."""
    def base_method(self):
        """Base method."""
        pass


class ChildClass(BaseClass):
    """A child class that inherits from BaseClass."""
    def child_method(self):
        """Child method that calls base method."""
        self.base_method()


class GrandChildClass(ChildClass):
    """Grandchild that inherits from ChildClass."""
    pass


def helper():
    """A helper function."""
    return 42


def process_data():
    """Process data by calling helper."""
    result = helper()
    return result * 2


def main():
    """Main entry point."""
    value = process_data()
    helper()
    return value
''')

    # Create database and index the file
    via_dir = project_dir / ".via"
    via_dir.mkdir()
    db_path = via_dir / "index.db"

    registry = ParserRegistry()
    registry.register(PythonParser())

    with DatabaseStore(str(db_path), str(project_dir)) as db:
        db.initialize_schema()

        # Use actual indexing service to index the file
        indexing_service = IndexingService(db, registry)
        file_info = DiscoveredFile(
            path=str(test_module),
            size_bytes=test_module.stat().st_size,
            mtime=test_module.stat().st_mtime,
            is_parseable=True,
            is_oversized=False
        )
        indexing_service._index_file(file_info)

        # Resolve pending relationships
        db.resolve_pending_relationships()

    return project_dir


class TestInheritanceRelationshipCLI:
    """Test inheritance relationship queries via CLI."""

    def test_query_classes_inheriting_from_base(self, indexed_project_with_relationships):
        """Test: Find classes that inherit from BaseClass."""
        # Syntax: -mg RELATE_TO -tc -Vinh RESULTS_FILTER
        # "Find all classes (*) that inherit from BaseClass"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # ChildClass inherits from BaseClass
        assert "ChildClass" in result.stdout

    def test_query_what_class_inherits_from_inverted(self, indexed_project_with_relationships):
        """Test: Find what ChildClass inherits from (inverted query)."""
        # With --invert: "Find all classes (*) that ChildClass inherits from"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "ChildClass", "-tc", "-Vinh", "-mg", "*", "--invert"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # ChildClass inherits from BaseClass
        assert "BaseClass" in result.stdout

    def test_query_inheritance_with_glob_pattern(self, indexed_project_with_relationships):
        """Test inheritance query with glob pattern."""
        # "Find all classes (*) that inherit from any *Class"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*Class", "-tc", "-Vinh", "-mg", "*"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should find classes inheriting from any *Class
        output = result.stdout
        # Either ChildClass or GrandChildClass should appear
        assert "ChildClass" in output or "GrandChildClass" in output


class TestCallRelationshipCLI:
    """Test call relationship queries via CLI."""

    def test_query_callers_of_function(self, indexed_project_with_relationships):
        """Test: Find functions that call helper."""
        # "Find all functions (*) that call helper"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "helper", "-tf", "-Vca", "-mg", "*"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # process_data and main call helper
        output = result.stdout
        assert "process_data" in output or "main" in output

    def test_query_what_function_calls_inverted(self, indexed_project_with_relationships):
        """Test: Find what main() calls (inverted query)."""
        # With --invert: "Find all functions (*) that main calls"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "main", "-tf", "-Vca", "-mg", "*", "--invert"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # main calls process_data and helper
        output = result.stdout
        assert "process_data" in output or "helper" in output

    def test_query_method_callers(self, indexed_project_with_relationships):
        """Test: Find methods that call base_method."""
        # "Find all methods (*) that call base_method"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "base_method", "-tm", "-Vca", "-mg", "*"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # child_method calls base_method
        assert "child_method" in result.stdout


class TestImportRelationshipCLI:
    """Test import relationship queries via CLI."""

    def test_query_files_importing_module(self, indexed_project_with_relationships):
        """Test: Find files/symbols that import os."""
        # "Find all imports (*) that import os"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "os", "-ti", "-Vimp", "-mg", "*"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should find the os import symbol
        assert "os" in result.stdout or "module.py" in result.stdout

    def test_query_what_file_imports_inverted(self, indexed_project_with_relationships):
        """Test: Find what modules the os import relates to (inverted)."""
        # With --invert: "Find all modules (*) that os imports"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "os", "-ti", "-Vimp", "-mg", "*", "--invert"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should find the os module
        assert "os" in result.stdout


class TestRelationshipEdgeCases:
    """Test edge cases for relationship queries."""

    def test_no_relationships_returns_empty(self, indexed_project_with_relationships):
        """Test query for non-existent relationship returns empty."""
        # "Find all classes (*) that inherit from NonExistentClass"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "NonExistentClass", "-tc", "-Vinh", "-mg", "*"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should be empty or minimal output
        assert "NonExistentClass" not in result.stdout

    def test_relationship_with_limit(self, indexed_project_with_relationships):
        """Test relationship query respects limit."""
        # "Find up to 1 function that calls helper"
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "helper", "-tf", "-Vca", "-mg", "*", "-n", "1"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should have at most 1 result
        lines = [l for l in result.stdout.strip().split('\n') if l and not l.startswith('#')]
        # At most 1 non-empty line (may be 0 if no results or 1 with result)
        assert len(lines) <= 2  # Account for possible header line
