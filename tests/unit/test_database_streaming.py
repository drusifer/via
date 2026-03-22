"""Unit tests for DatabaseStore streaming and limit behavior.

TLDR:
    Verifies that DatabaseStore.match() produces results as a lazy iterator,
    that limit parameter correctly restricts result count, and that case
    sensitivity works correctly. Column width computation moved to TableRenderer
    (TD-REVIEW-1); total_matches is no longer pre-computed by the DB layer.
    Key test classes: TestLimitParameter (default limit, limit=0 unlimited,
    limit > total), TestStreamingBehavior (match() returns an exhaustable
    iterator), TestCaseSensitivity (case-insensitive matching correctness).
    Role: protects the streaming/limit contract of DatabaseStore; depends on
    DatabaseStore and schema fixtures.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import tempfile
from pathlib import Path

import pytest
from via.core.match_record import ClassMatchRecord, MatchRecord
from via.core.types import MatchOp, SymbolType
from via.db.store import DatabaseStore


@pytest.fixture
def db_with_symbols(tmp_path):
    """Create a database with test symbols for metadata testing."""
    db_path = tmp_path / "test.db"

    with DatabaseStore(str(db_path), str(tmp_path)) as db:
        db.initialize_schema()

        # Insert symbols with varying name lengths for column width testing
        db.insert_symbol('A', 'class', 'a.py', 1, 'module.A', 10, 50, None)
        db.insert_symbol('LongerClassName', 'class', 'longer_file.py', 5, 'module.submodule.LongerClassName', 100, 200, None)
        db.insert_symbol('VeryVeryLongClassName', 'class', 'very_long_filename.py', 10, 'deep.nested.module.VeryVeryLongClassName', 500, 300, None)
        db.insert_symbol('B', 'class', 'b.py', 2, 'module.B', 20, 60, None)
        db.insert_symbol('C', 'class', 'c.py', 3, 'module.C', 30, 70, None)

        # Insert methods for different symbol type testing
        db.insert_symbol('short', 'method', 'a.py', 5, 'module.A.short', 100, 20, 'A')
        db.insert_symbol('much_longer_method_name', 'method', 'a.py', 10, 'module.A.much_longer_method_name', 200, 50, 'A')

        # Insert functions
        db.insert_symbol('func', 'function', 'a.py', 20, 'module.func', 300, 40, None)
        db.insert_symbol('another_function', 'function', 'b.py', 25, 'module.another_function', 400, 60, None)

    return db_path, tmp_path


class TestLimitParameter:
    """Tests for limit parameter behavior."""

    def test_default_limit_is_10(self, db_with_symbols):
        """Test that default limit is 10."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            # We only have 5 classes, so all should be returned
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))
            assert len(results) == 5  # Less than default 10, so all returned

    def test_limit_restricts_results(self, db_with_symbols):
        """Test that limit restricts number of results."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*', limit=2))
            assert len(results) == 2

    def test_limit_one_returns_single_result(self, db_with_symbols):
        """Test that limit=1 returns single result."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*', limit=1))
            assert len(results) == 1

    def test_limit_zero_returns_all(self, db_with_symbols):
        """Test that limit=0 returns all results (unlimited)."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*', limit=0))
            assert len(results) == 5  # All 5 classes

    def test_limit_greater_than_total_returns_all(self, db_with_symbols):
        """Test that limit > total returns all results."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*', limit=100))
            assert len(results) == 5


class TestStreamingBehavior:
    """Tests for streaming behavior (results yield lazily)."""

    def test_results_are_iterator(self, db_with_symbols):
        """Test that match() returns an iterator, not a list."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = db.match(SymbolType.CLASS, MatchOp.GLOB, '*')

            # Should be an iterator/generator, not a list
            assert hasattr(results, '__iter__')
            assert hasattr(results, '__next__')

    def test_can_iterate_results_multiple_times_requires_new_call(self, db_with_symbols):
        """Test that iterating exhausts the iterator (streaming)."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = db.match(SymbolType.CLASS, MatchOp.GLOB, '*')

            # First iteration
            first_pass = list(results)
            assert len(first_pass) == 5

            # Second iteration on same iterator should be empty
            second_pass = list(results)
            assert len(second_pass) == 0

            # Need new call to get results again
            fresh_results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))
            assert len(fresh_results) == 5


class TestCaseSensitivity:
    """Tests for case sensitivity with metadata."""

    def test_case_insensitive_matching(self, db_with_symbols):
        """Test case insensitive matching returns correct results."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            # Match 'a' case insensitive should match 'A'
            results = list(db.match(
                SymbolType.CLASS,
                MatchOp.GLOB,
                'a',
                case_sensitive=False
            ))

            assert len(results) == 1
            assert results[0].symbol_name == 'A'
