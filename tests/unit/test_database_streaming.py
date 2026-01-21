"""
Unit tests for DatabaseStore streaming and metadata features.

TLDR:
    Tests metadata computation (column_widths, total_matches) before streaming,
    limit parameter behavior, and that records have metadata attached.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import pytest
import tempfile
from pathlib import Path

from via.db.store import DatabaseStore
from via.core.types import SymbolType, MatchOp
from via.core.match_record import MatchRecord, ClassMatchRecord


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


class TestMetadataComputation:
    """Tests for metadata computation before streaming."""

    def test_match_returns_records_with_metadata(self, db_with_symbols):
        """Test that match() returns records with metadata attached."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))

            # All records should have metadata
            assert len(results) == 5
            for record in results:
                assert record.column_widths is not None
                assert record.total_matches is not None

    def test_metadata_total_matches_accurate(self, db_with_symbols):
        """Test that total_matches reflects actual count."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))

            # Should have 5 classes
            assert results[0].total_matches == 5

    def test_metadata_total_matches_with_pattern(self, db_with_symbols):
        """Test that total_matches is accurate with pattern filter."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            # Match only names starting with 'L' or 'V'
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '[LV]*'))

            # Should match LongerClassName and VeryVeryLongClassName
            assert len(results) == 2
            assert results[0].total_matches == 2

    def test_column_widths_contain_required_fields(self, db_with_symbols):
        """Test that column_widths has all required fields."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))

            widths = results[0].column_widths
            assert 'symbol_name' in widths
            assert 'qualified_name' in widths
            assert 'file_path' in widths
            assert 'symbol_type' in widths

    def test_column_widths_reflect_max_lengths(self, db_with_symbols):
        """Test that column_widths reflect max length across all matches."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))

            widths = results[0].column_widths

            # Max symbol_name is 'VeryVeryLongClassName' (21 chars)
            assert widths['symbol_name'] == 21

            # Max file_path is 'very_long_filename.py' (21 chars)
            assert widths['file_path'] == 21

            # Max qualified_name is 'deep.nested.module.VeryVeryLongClassName' (40 chars)
            assert widths['qualified_name'] == 40

    def test_metadata_same_for_all_records_in_batch(self, db_with_symbols):
        """Test that all records in a batch have the same metadata."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*'))

            # All should have same metadata
            first_widths = results[0].column_widths
            first_total = results[0].total_matches

            for record in results[1:]:
                assert record.column_widths == first_widths
                assert record.total_matches == first_total

    def test_metadata_computed_for_methods(self, db_with_symbols):
        """Test metadata computation works for methods."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.METHOD, MatchOp.GLOB, '*'))

            assert len(results) == 2
            assert results[0].total_matches == 2
            # Max method name is 'much_longer_method_name' (23 chars)
            assert results[0].column_widths['symbol_name'] == 23


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

    def test_metadata_total_matches_not_affected_by_limit(self, db_with_symbols):
        """Test that total_matches shows total count, not limited count."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*', limit=2))

            # Even though we only get 2 results, total_matches should be 5
            assert len(results) == 2
            assert results[0].total_matches == 5

    def test_column_widths_computed_from_all_matches_not_limited(self, db_with_symbols):
        """Test that column_widths are computed from ALL matches, not just limited ones."""
        db_path, root = db_with_symbols

        with DatabaseStore(str(db_path), str(root)) as db:
            # Get only 1 result, but widths should reflect all 5 classes
            results = list(db.match(SymbolType.CLASS, MatchOp.GLOB, '*', limit=1))

            # Even with limit=1, widths should include 'VeryVeryLongClassName'
            assert results[0].column_widths['symbol_name'] == 21

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

    def test_case_insensitive_metadata(self, db_with_symbols):
        """Test metadata computation with case insensitive matching."""
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
            assert results[0].total_matches == 1
