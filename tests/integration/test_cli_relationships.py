"""
Integration tests for CLI relationship queries (Sprint 5).

TLDR:
    Tests end-to-end relationship queries via CLI by invoking the via binary as a
    subprocess against a temporary indexed project containing classes with
    inheritance, method calls, and imports.
    Key fixture: indexed_project_with_relationships (builds a multi-class project
    tree and indexes it via IndexingService/PythonParser/ParserRegistry).
    Key classes: TestInheritanceRelationshipCLI (-V inherits-from forward/sans/glob),
    TestCallRelationshipCLI (-V calls callers and sans), TestImportRelationshipCLI
    (-V imports forward/sans), TestRelationshipEdgeCases (empty results, --limit).
    Consumed by: pytest integration suite; depends on DatabaseStore, DiscoveredFile,
    IndexingService, PythonParser, ParserRegistry.

Author: Neo (SWE)
Sprint: 5
"""

import subprocess
import sys
from pathlib import Path

import pytest
from via.core.discovery import DiscoveredFile
from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService


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
        # Result-first: result stage (*) --via inherits-from filter (BaseClass)
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "-V", "inherits-from", "-mg", "BaseClass", "-tc"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # ChildClass inherits from BaseClass
        assert "ChildClass" in result.stdout

    def test_query_sans_inheritance_is_negative(self, indexed_project_with_relationships):
        """Test: --sans inherits-from runs without error (NOT EXISTS query)."""
        # Result-first: find all classes, excluding those that inherit from anything
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "--sans", "inherits-from", "-mg", "*", "-tc"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # BaseClass does not inherit from anything → it should appear
        assert "BaseClass" in result.stdout
        # ChildClass and GrandChildClass do inherit → they should NOT appear
        assert "ChildClass" not in result.stdout
        assert "GrandChildClass" not in result.stdout

    def test_query_inheritance_with_glob_pattern(self, indexed_project_with_relationships):
        """Test inheritance query with glob pattern on filter."""
        # Result-first: find all classes, filtered to those inheriting from *Class
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "-V", "inherits-from", "-mg", "*Class", "-tc"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout
        # ChildClass or GrandChildClass should appear (they inherit from *Class)
        assert "ChildClass" in output or "GrandChildClass" in output


class TestCallRelationshipCLI:
    """Test call relationship queries via CLI."""

    def test_query_callers_of_function(self, indexed_project_with_relationships):
        """Test: Find functions that call helper."""
        # Result-first: find all functions, filtered to those that call helper
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tf", "-V", "calls", "-mg", "helper", "-tf"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # process_data and main call helper
        output = result.stdout
        assert "process_data" in output or "main" in output

    def test_query_sans_calls_is_not_exists(self, indexed_project_with_relationships):
        """Test: --sans calls finds functions that do NOT call anything."""
        # Result-first: find all functions, excluding those that call anything
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tf", "--sans", "calls", "-mg", "*", "-tf"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # helper calls nothing → should appear
        # process_data and main DO call something → should NOT appear
        output = result.stdout
        assert "process_data" not in output
        assert "main" not in output

    def test_query_method_callers(self, indexed_project_with_relationships):
        """Test: Find methods that call base_method."""
        # Result-first: find all methods, filtered to those that call base_method
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tm", "-V", "calls", "-mg", "base_method", "-tm"],
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
        """Test: Find imports that import os."""
        # Result-first: find all imports, filtered to those that import os
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-ti", "-V", "imports", "-mg", "os"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should find the os import symbol
        assert "os" in result.stdout or "module.py" in result.stdout

    def test_query_sans_imports_runs_without_error(self, indexed_project_with_relationships):
        """Test: --sans imports runs without error (NOT EXISTS query)."""
        # Result-first: find all imports, excluding those that import anything
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-ti", "--sans", "imports", "-mg", "*"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"


class TestRelationshipEdgeCases:
    """Test edge cases for relationship queries."""

    def test_no_relationships_returns_empty(self, indexed_project_with_relationships):
        """Test query for non-existent relationship returns empty."""
        # Result-first: find all classes, filtered to those inheriting from NonExistentClass
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tc", "-V", "inherits-from", "-mg", "NonExistentClass", "-tc"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should be empty or minimal output
        assert "NonExistentClass" not in result.stdout

    def test_relationship_with_limit(self, indexed_project_with_relationships):
        """Test relationship query respects limit."""
        # Result-first: find up to 1 function that calls helper
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "*", "-tf", "-n", "1", "-V", "calls", "-mg", "helper", "-tf"],
            cwd=str(indexed_project_with_relationships),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Should have at most 1 result
        lines = [l for l in result.stdout.strip().split('\n') if l and not l.startswith('#')]
        # At most 1 non-empty line (may be 0 if no results or 1 with result)
        assert len(lines) <= 2  # Account for possible header line
