"""
Unit tests for indexer symbol population.

TLDR:
    Tests that the IndexingService correctly populates the symbols table
    during indexing. Verifies symbol creation for all entity types,
    qualified name calculation, and symbol deletion on re-index.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import pytest
from pathlib import Path
from via.db.store import DatabaseStore
from via.parsers.registry import ParserRegistry
from via.parsers.python_parser import PythonParser
from via.services.indexing import IndexingService, _calculate_qualified_name
from via.core.types import SymbolType, MatchOp


@pytest.fixture
def test_project(tmp_path):
    """Create a test project with Python files."""
    # Create project structure
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    src_dir = project_dir / "src"
    src_dir.mkdir()

    # Create test module
    module_path = src_dir / "module.py"
    module_path.write_text('''
import json
import os

MAX_SIZE = 1024
DEBUG = True

class User:
    """A user class."""

    def save(self):
        """Save user."""
        pass

    def load(self):
        """Load user."""
        pass


def calculate():
    """A function."""
    pass
''')

    return project_dir, module_path


@pytest.fixture
def indexed_db(test_project):
    """Create an indexed database from test project."""
    project_dir, module_path = test_project

    # Set up database
    via_dir = project_dir / ".via"
    via_dir.mkdir()
    db_path = via_dir / "index.db"

    with DatabaseStore(str(db_path), str(project_dir)) as db:
        db.initialize_schema()

        # Set up parser
        registry = ParserRegistry()
        registry.register(PythonParser())

        # Index
        service = IndexingService(db, registry)
        service.index(str(project_dir))

        yield db, project_dir


class TestSymbolInsertion:
    """Tests for symbol insertion during indexing."""

    def test_indexer_creates_function_symbols(self, indexed_db):
        """Test that indexer creates symbol entries for functions."""
        db, _ = indexed_db
        results = list(db.match(SymbolType.FUNCTION, MatchOp.GLOB, '*', True))
        assert len(results) >= 1
        names = [r.symbol_name for r in results]
        assert 'calculate' in names

    def test_indexer_creates_class_symbols(self, indexed_db):
        """Test that indexer creates symbol entries for classes."""
        db, _ = indexed_db
        results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*', True))
        assert len(results) >= 1
        names = [r.symbol_name for r in results]
        assert 'User' in names

    def test_indexer_creates_method_symbols(self, indexed_db):
        """Test that indexer creates symbol entries for methods."""
        db, _ = indexed_db
        results = list(db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True))
        assert len(results) >= 2
        names = [r.symbol_name for r in results]
        assert 'save' in names
        assert 'load' in names

    def test_method_symbols_have_parent_name(self, indexed_db):
        """Test that method symbols have correct parent_name."""
        db, _ = indexed_db
        results = list(db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
        assert len(results) >= 1
        assert results[0].parent_name == 'User'

    def test_indexer_creates_import_symbols(self, indexed_db):
        """Test that indexer creates symbol entries for imports."""
        db, _ = indexed_db
        results = list(db.match(SymbolType.IMPORT, MatchOp.GLOB, '*', True))
        assert len(results) >= 2
        names = [r.symbol_name for r in results]
        assert 'json' in names
        assert 'os' in names

    def test_indexer_creates_global_symbols(self, indexed_db):
        """Test that indexer creates symbol entries for globals."""
        db, _ = indexed_db
        results = list(db.match(SymbolType.GLOBAL, MatchOp.GLOB, '*', True))
        assert len(results) >= 2
        names = [r.symbol_name for r in results]
        assert 'MAX_SIZE' in names
        assert 'DEBUG' in names

    def test_indexer_creates_file_symbols(self, indexed_db):
        """Test that indexer creates filename and filepath symbols."""
        db, _ = indexed_db

        # Check filename
        filename_results = list(db.match(SymbolType.FILENAME, MatchOp.GLOB, '*', True))
        assert len(filename_results) >= 1
        names = [r.symbol_name for r in filename_results]
        assert 'module.py' in names

        # Check filepath
        filepath_results = list(db.match(SymbolType.FILEPATH, MatchOp.GLOB, '*', True))
        assert len(filepath_results) >= 1


class TestQualifiedNameCalculation:
    """Tests for qualified name calculation."""

    def test_qualified_name_for_function(self):
        """Test qualified name calculation for functions."""
        qname = _calculate_qualified_name('src/utils.py', 'calculate', None)
        assert qname == 'utils.calculate'

    def test_qualified_name_for_method(self):
        """Test qualified name calculation for methods."""
        qname = _calculate_qualified_name('src/models/user.py', 'save', 'User')
        assert qname == 'models.user.User.save'

    def test_qualified_name_removes_src_prefix(self):
        """Test that src/ prefix is removed from module path."""
        qname = _calculate_qualified_name('src/models/user.py', 'User', None)
        assert qname == 'models.user.User'
        assert 'src' not in qname

    def test_qualified_name_for_class(self):
        """Test qualified name for class."""
        qname = _calculate_qualified_name('models/user.py', 'User', None)
        assert qname == 'models.user.User'


class TestSymbolDeletion:
    """Tests for symbol deletion on re-index."""

    def test_reindex_deletes_old_symbols(self, test_project, tmp_path):
        """Test that re-indexing a file deletes old symbols."""
        project_dir, module_path = test_project

        # Set up database
        via_dir = project_dir / ".via"
        via_dir.mkdir()
        db_path = via_dir / "index.db"

        with DatabaseStore(str(db_path), str(project_dir)) as db:
            db.initialize_schema()

            # Set up parser
            registry = ParserRegistry()
            registry.register(PythonParser())
            service = IndexingService(db, registry)

            # First index
            service.index(str(project_dir))

            # Verify old symbols exist
            results = list(db.match(SymbolType.FUNCTION, MatchOp.GLOB, 'calculate', True))
            assert len(results) == 1

            # Modify file - remove calculate function, add new one
            module_path.write_text('''
import json

class User:
    def save(self):
        pass

def new_function():
    pass
''')

            # Re-index with force
            service.index(str(project_dir), force=True)

            # Verify old symbols deleted
            old_results = list(db.match(SymbolType.FUNCTION, MatchOp.GLOB, 'calculate', True))
            assert len(old_results) == 0

            # Verify new symbols created
            new_results = list(db.match(SymbolType.FUNCTION, MatchOp.GLOB, 'new_function', True))
            assert len(new_results) == 1
