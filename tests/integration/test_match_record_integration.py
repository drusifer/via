"""
Integration tests for the MatchRecord system covering the full index-to-match pipeline.

TLDR:
    End-to-end integration suite for MatchRecord (Phase 2 Task 2.5). Spins up a
    temporary project, runs `via index`, then exercises DatabaseStore.match() to
    verify each symbol type returns the correct MatchRecord subclass.
    Key fixture: indexed_project — creates temp files, indexes them, yields paths.
    Key class: TestMatchRecordIntegration — nine test methods covering
    ClassMatchRecord, MethodMatchRecord, FunctionMatchRecord, ImportMatchRecord,
    GlobalMatchRecord, supports_render_type(), __str__ format compatibility, and
    CLI pipeline output stability.
    Depends on: via.core.match_record, via.db.store, via.core.types.

Author: Drew Gutstein / Neo
------------------------------------------------------------------------------
License: GPL-3.0
"""

import os
import subprocess
import tempfile

import pytest


@pytest.fixture
def indexed_project():
    """Create a temporary project, index it, and return paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        module_py = os.path.join(tmpdir, "module.py")
        with open(module_py, "w") as f:
            f.write('''"""Test module for integration tests."""
import json
import os

MAX_SIZE = 1024

class TestClass:
    """A test class."""

    def test_method(self):
        """A test method."""
        pass

def helper_function(x, y):
    """A helper function."""
    return x + y
''')

        utils_py = os.path.join(tmpdir, "utils.py")
        with open(utils_py, "w") as f:
            f.write('''"""Utilities module."""
from pathlib import Path

def load_config(path):
    """Load configuration."""
    return {}
''')

        # Index the project
        result = subprocess.run(
            ["python", "-m", "via", "index", tmpdir],
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        assert result.returncode == 0, f"Index failed: {result.stderr}"

        db_path = os.path.join(tmpdir, ".via", "index.db")
        yield {"tmpdir": tmpdir, "db_path": db_path}


class TestMatchRecordIntegration:
    """Integration tests for MatchRecord system."""

    def test_match_returns_correct_class_record(self, indexed_project):
        """match() returns ClassMatchRecord for indexed class."""
        from via.core.match_record import ClassMatchRecord
        from via.core.types import MatchOp, SymbolType
        from via.db.store import DatabaseStore

        with DatabaseStore(indexed_project["db_path"], indexed_project["tmpdir"]) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))
            assert len(results) == 1
            assert isinstance(results[0], ClassMatchRecord)
            assert results[0].symbol_name == 'TestClass'

    def test_match_returns_correct_method_record(self, indexed_project):
        """match() returns MethodMatchRecord for indexed method."""
        from via.core.match_record import MethodMatchRecord
        from via.core.types import MatchOp, SymbolType
        from via.db.store import DatabaseStore

        with DatabaseStore(indexed_project["db_path"], indexed_project["tmpdir"]) as db:
            results = list(db.match(SymbolType.METHOD, MatchOp.GLOB, '*'))
            assert len(results) == 1
            assert isinstance(results[0], MethodMatchRecord)
            assert results[0].symbol_name == 'test_method'
            assert results[0].parent_name == 'TestClass'

    def test_match_returns_correct_function_records(self, indexed_project):
        """match() returns FunctionMatchRecord for indexed functions."""
        from via.core.match_record import FunctionMatchRecord
        from via.core.types import MatchOp, SymbolType
        from via.db.store import DatabaseStore

        with DatabaseStore(indexed_project["db_path"], indexed_project["tmpdir"]) as db:
            results = list(db.match(SymbolType.FUNCTION, MatchOp.GLOB, '*'))
            assert len(results) == 2  # helper_function and load_config
            for record in results:
                assert isinstance(record, FunctionMatchRecord)
            names = {r.symbol_name for r in results}
            assert names == {'helper_function', 'load_config'}

    def test_match_returns_correct_import_records(self, indexed_project):
        """match() returns ImportMatchRecord for indexed imports."""
        from via.core.match_record import ImportMatchRecord
        from via.core.types import MatchOp, SymbolType
        from via.db.store import DatabaseStore

        with DatabaseStore(indexed_project["db_path"], indexed_project["tmpdir"]) as db:
            results = list(db.match(SymbolType.IMPORT, MatchOp.GLOB, '*'))
            assert len(results) >= 3  # json, os, Path
            for record in results:
                assert isinstance(record, ImportMatchRecord)

    def test_match_returns_correct_global_record(self, indexed_project):
        """match() returns GlobalMatchRecord for indexed globals."""
        from via.core.match_record import GlobalMatchRecord
        from via.core.types import MatchOp, SymbolType
        from via.db.store import DatabaseStore

        with DatabaseStore(indexed_project["db_path"], indexed_project["tmpdir"]) as db:
            results = list(db.match(SymbolType.GLOBAL, MatchOp.GLOB, '*'))
            assert len(results) == 1
            assert isinstance(results[0], GlobalMatchRecord)
            assert results[0].symbol_name == 'MAX_SIZE'

    def test_match_record_str_compatible_with_cli_output(self, indexed_project):
        """MatchRecord __str__ format is compatible with CLI output."""
        from via.core.types import MatchOp, SymbolType
        from via.db.store import DatabaseStore

        with DatabaseStore(indexed_project["db_path"], indexed_project["tmpdir"]) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))
            record = results[0]
            output = str(record)

            # Should match Sprint 2 format: type:file:line:qualified_name:@offset+length
            assert output.startswith('class:')
            assert 'module.py' in output  # file path (may be absolute or relative)
            assert 'TestClass' in output  # qualified name
            assert ':@' in output  # byte position

    def test_match_supports_render_type_method(self, indexed_project):
        """MatchRecord supports_render_type() works correctly."""
        from via.core.match_record import RenderType
        from via.core.types import MatchOp, SymbolType
        from via.db.store import DatabaseStore

        with DatabaseStore(indexed_project["db_path"], indexed_project["tmpdir"]) as db:
            class_results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))
            class_record = class_results[0]

            # ClassMatchRecord supports all render types including DIAGRAM
            assert class_record.supports_render_type(RenderType.LIST)
            assert class_record.supports_render_type(RenderType.TABLE)
            assert class_record.supports_render_type(RenderType.DIAGRAM)
            assert class_record.supports_render_type(RenderType.RAW)

            method_results = list(db.match(SymbolType.METHOD, MatchOp.GLOB, '*'))
            method_record = method_results[0]

            # MethodMatchRecord does NOT support DIAGRAM
            assert method_record.supports_render_type(RenderType.LIST)
            assert method_record.supports_render_type(RenderType.TABLE)
            assert not method_record.supports_render_type(RenderType.DIAGRAM)

    def test_cli_match_output_unchanged(self, indexed_project):
        """CLI pipeline output format unchanged by MatchRecord refactor."""
        result = subprocess.run(
            ["python", "-m", "via", "-mg", "*", "-tc"],
            capture_output=True,
            text=True,
            cwd=indexed_project["tmpdir"]
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 1

        # Check format: type:file:line:qualified_name:@offset+length
        line = lines[0]
        assert line.startswith('class:')
        assert 'TestClass' in line
        assert ':@' in line  # byte position present

    def test_pipeline_match_with_match_records(self, indexed_project):
        """Pipeline match stage works with MatchRecord."""
        result = subprocess.run(
            ["python", "-m", "via", "-mg", "*", "-tc"],
            capture_output=True,
            text=True,
            cwd=indexed_project["tmpdir"]
        )

        assert result.returncode == 0
        assert 'TestClass' in result.stdout
