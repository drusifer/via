"""
Unit tests for relationship query pipeline execution.

TLDR:
    Tests that relationship queries (inheritance, calls, imports) return correct
    results through the PipelineParser + PipelineExecutor, regardless of file
    indexing order. Regression tests for the resolve_pending_relationships bug
    where import symbols were preferred over definition symbols.

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
from via.pipeline.executor import PipelineExecutor
from via.pipeline.parser import PipelineParser
from via.services.indexing import IndexingService


@pytest.fixture
def relationship_project(tmp_path):
    """Create and index a project with inheritance, calls, and imports."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    (project_dir / "fileA.py").write_text('''
class BaseClass:
    def base_method(self):
        return 42

class FinalClass:
    pass

def func_a():
    return 1

def helper_util():
    return "helper"
''')

    (project_dir / "fileB.py").write_text('''
from fileA import BaseClass, func_a, helper_util

class ChildClass(BaseClass):
    def child_method(self):
        return self.base_method()

class AnotherChild(BaseClass):
    pass

def func_b():
    result = func_a()
    helper_util()
    return result
''')

    via_dir = project_dir / ".via"
    via_dir.mkdir()
    db_path = via_dir / "index.db"

    registry = ParserRegistry()
    registry.register(PythonParser())

    with DatabaseStore(str(db_path), str(project_dir)) as db:
        db.initialize_schema()
        svc = IndexingService(db, registry)
        for f in sorted(project_dir.glob("*.py")):
            fi = DiscoveredFile(
                path=str(f),
                size_bytes=f.stat().st_size,
                mtime=f.stat().st_mtime,
                is_parseable=True,
                is_oversized=False,
            )
            svc._index_file(fi)
        db.resolve_pending_relationships()

    return project_dir, db_path


class TestRelationshipPipelineExecution:
    """Test PipelineParser + PipelineExecutor for relationship queries."""

    def _execute_pipeline(self, db_path, project_dir, argv):
        """Parse and execute a pipeline, return list of MatchRecords."""
        parser = PipelineParser()
        stages = parser.parse(argv)
        with DatabaseStore(str(db_path), str(project_dir)) as db:
            executor = PipelineExecutor(db)
            result = executor.execute(stages)
            if result is not None:
                return list(result)
            return []

    def test_forward_inheritance(self, relationship_project):
        """Forward inheritance query returns children."""
        project_dir, db_path = relationship_project
        records = self._execute_pipeline(
            db_path, project_dir,
            ["-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc"],
        )
        names = [r.symbol_name for r in records]
        assert "ChildClass" in names, f"Expected ChildClass in {names}"

    def test_inverted_inheritance(self, relationship_project):
        """Inverted inheritance query returns parent."""
        project_dir, db_path = relationship_project
        records = self._execute_pipeline(
            db_path, project_dir,
            ["-mg", "ChildClass", "-tc", "-Vinh", "-mg", "*", "-tc", "--invert"],
        )
        names = [r.symbol_name for r in records]
        assert "BaseClass" in names, f"Expected BaseClass in {names}"

    def test_forward_calls(self, relationship_project):
        """Forward calls query returns callers."""
        project_dir, db_path = relationship_project
        records = self._execute_pipeline(
            db_path, project_dir,
            ["-mg", "func_a", "-tf", "-Vca", "-mg", "*", "-tf"],
        )
        names = [r.symbol_name for r in records]
        assert "func_b" in names, f"Expected func_b in {names}"

    def test_inverted_calls(self, relationship_project):
        """Inverted calls query returns callees."""
        project_dir, db_path = relationship_project
        records = self._execute_pipeline(
            db_path, project_dir,
            ["-mg", "func_b", "-tf", "-Vca", "-mg", "*", "--invert"],
        )
        names = [r.symbol_name for r in records]
        assert "func_a" in names or "helper_util" in names, f"Expected callees in {names}"

    def test_pipeline_stage_parsing(self, relationship_project):
        """Verify pipeline parser correctly parses relationship args."""
        parser = PipelineParser()
        stages = parser.parse(["-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc"])
        assert len(stages) == 1
        stage = stages[0]
        args = stage.args
        assert args.pattern == "BaseClass"
        assert args.relationship is not None
        assert args.relationship.object_pattern == "*"
        assert args.relationship.invert is False


class TestRelationshipResolutionOrder:
    """Regression tests: relationship resolution must prefer definitions over imports.

    When files are indexed in non-alphabetical order, import symbols may be
    created before definition symbols. resolve_pending_relationships must
    resolve to the definition (class/function/method) rather than the import.
    """

    @pytest.fixture
    def reverse_indexed_project(self, tmp_path):
        """Create project indexed in REVERSE order (fileB before fileA)."""
        project_dir = tmp_path / "reverse"
        project_dir.mkdir()

        (project_dir / "fileA.py").write_text('''
class BaseClass:
    def base_method(self):
        return "base"
def func_a():
    return "func_a"
''')

        (project_dir / "fileB.py").write_text('''
from fileA import BaseClass, func_a
class ChildClass(BaseClass):
    def child_method(self):
        return self.base_method()
def func_b():
    return func_a()
''')

        via_dir = project_dir / ".via"
        via_dir.mkdir()
        db_path = via_dir / "index.db"

        registry = ParserRegistry()
        registry.register(PythonParser())

        with DatabaseStore(str(db_path), str(project_dir)) as db:
            db.initialize_schema()
            svc = IndexingService(db, registry)
            # Index in REVERSE order to trigger the bug
            files = sorted(project_dir.glob("*.py"), reverse=True)
            for f in files:
                fi = DiscoveredFile(
                    path=str(f),
                    size_bytes=f.stat().st_size,
                    mtime=f.stat().st_mtime,
                    is_parseable=True,
                    is_oversized=False,
                )
                svc._index_file(fi)
            db.resolve_pending_relationships()

        return project_dir, db_path

    def test_relationships_resolve_to_definitions(self, reverse_indexed_project):
        """Relationships should target definition symbols, not import symbols."""
        project_dir, db_path = reverse_indexed_project
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("""
            SELECT s.symbol_name, s.symbol_type, t.symbol_name, t.symbol_type
            FROM symbol_references r
            JOIN symbols s ON r.from_symbol_id = s.id
            JOIN symbols t ON r.to_symbol_id = t.id
            WHERE r.reference_type = 'inherits-from'
        """)
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) > 0, "Should have inheritance relationships"
        for source_name, source_type, target_name, target_type in rows:
            assert target_type == 'class', \
                f"Inheritance target {target_name} should be type 'class', got '{target_type}'"

    def test_forward_inheritance_works_with_reverse_order(self, reverse_indexed_project):
        """Forward inheritance query works regardless of indexing order."""
        project_dir, db_path = reverse_indexed_project
        parser = PipelineParser()
        stages = parser.parse(["-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc"])
        with DatabaseStore(str(db_path), str(project_dir)) as db:
            executor = PipelineExecutor(db)
            result = executor.execute(stages)
            records = list(result) if result else []
        names = [r.symbol_name for r in records]
        assert "ChildClass" in names, f"Expected ChildClass in {names}"

    def test_subprocess_works_with_reverse_order(self, reverse_indexed_project):
        """CLI subprocess works regardless of indexing order."""
        project_dir, db_path = reverse_indexed_project
        result = subprocess.run(
            [sys.executable, "-m", "via", "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "ChildClass" in result.stdout, \
            f"Expected ChildClass in stdout=[{result.stdout}] stderr=[{result.stderr}]"

    def test_object_type_filter_works_with_reverse_order(self, reverse_indexed_project):
        """DB query with object_type='class' filter works after resolution fix."""
        project_dir, db_path = reverse_indexed_project
        with DatabaseStore(str(db_path), str(project_dir)) as db:
            results = list(db.query_relationships(
                relationship_type='inherits-from',
                object_pattern='BaseClass',
                object_type='class',
                invert=False,
            ))
            names = [r.symbol_name for r in results]
            assert "ChildClass" in names, f"Expected ChildClass with object_type=class: {names}"
