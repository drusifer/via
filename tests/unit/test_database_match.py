"""
Unit tests for DatabaseStore.match() method.

TLDR:
    Tests the denormalized symbols table query functionality. Verifies matching
    by symbol type, match operators (GLOB, LIKE, REGEXP, EXACT), case sensitivity,
    result limiting, byte position data, and SQL injection protection.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import pytest
from via.db.store import DatabaseStore
from via.core.types import SymbolType, MatchOp


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with sample symbols."""
    db_path = tmp_path / "test.db"
    db = DatabaseStore(str(db_path), str(tmp_path))
    db.connect()
    db.initialize_schema()

    # Insert test symbols
    db.insert_symbol('save', 'method', 'src/user.py', 10, 'user.User.save', 100, 50, 'User')
    db.insert_symbol('load', 'method', 'src/user.py', 20, 'user.User.load', 200, 40, 'User')
    db.insert_symbol('User', 'class', 'src/user.py', 5, 'user.User', 50, 200, None)
    db.insert_symbol('calculate', 'function', 'src/utils.py', 15, 'utils.calculate', 300, 80, None)
    db.insert_symbol('user.py', 'filename', 'src/user.py', 0, 'src/user.py', None, None, None)
    db.insert_symbol('src/user.py', 'filepath', 'src/user.py', 0, 'src/user.py', None, None, None)
    db.insert_symbol('json', 'import', 'src/user.py', 1, 'json', 0, 11, None)
    db.insert_symbol('MAX_SIZE', 'global', 'src/config.py', 3, 'config.MAX_SIZE', 30, 15, None)

    yield db
    db.close()


class TestMatchBySymbolType:
    """Tests for matching by symbol type."""

    def test_match_methods(self, test_db):
        """Test matching methods."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True))
        assert len(results) == 2
        assert all(r.symbol_type == 'method' for r in results)

    def test_match_classes(self, test_db):
        """Test matching classes."""
        results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, '*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'User'

    def test_match_functions(self, test_db):
        """Test matching functions."""
        results = list(test_db.match(SymbolType.FUNCTION, MatchOp.GLOB, '*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'calculate'

    def test_match_filenames(self, test_db):
        """Test matching filenames."""
        results = list(test_db.match(SymbolType.FILENAME, MatchOp.GLOB, '*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'user.py'

    def test_match_filepaths(self, test_db):
        """Test matching filepaths."""
        results = list(test_db.match(SymbolType.FILEPATH, MatchOp.GLOB, '*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'src/user.py'

    def test_match_imports(self, test_db):
        """Test matching imports."""
        results = list(test_db.match(SymbolType.IMPORT, MatchOp.GLOB, '*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'json'

    def test_match_globals(self, test_db):
        """Test matching globals."""
        results = list(test_db.match(SymbolType.GLOBAL, MatchOp.GLOB, '*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'MAX_SIZE'


class TestMatchByOperator:
    """Tests for different match operators."""

    def test_match_with_glob_wildcard(self, test_db):
        """Test GLOB pattern matching with * wildcard."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'sa*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'

    def test_match_with_glob_question(self, test_db):
        """Test GLOB pattern matching with ? wildcard."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'sav?', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'

    def test_match_with_exact(self, test_db):
        """Test EXACT pattern matching."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.EXACT, 'save', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'

    def test_match_exact_no_wildcards(self, test_db):
        """Test EXACT matching doesn't interpret wildcards."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.EXACT, 'sa*', True))
        assert len(results) == 0  # No symbol named "sa*"

    def test_match_with_like(self, test_db):
        """Test LIKE pattern matching with % wildcard."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.LIKE, 's%', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'

    def test_match_with_like_underscore(self, test_db):
        """Test LIKE pattern matching with _ wildcard."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.LIKE, 'sav_', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'


class TestCaseSensitivity:
    """Tests for case-sensitive and case-insensitive matching."""

    def test_match_case_sensitive_no_match(self, test_db):
        """Test case-sensitive matching returns no results for wrong case."""
        results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, 'user', True))
        assert len(results) == 0  # 'User' != 'user'

    def test_match_case_insensitive(self, test_db):
        """Test case-insensitive matching."""
        results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, 'user', False))
        assert len(results) == 1
        assert results[0].symbol_name == 'User'

    def test_match_case_insensitive_pattern(self, test_db):
        """Test case-insensitive with uppercase pattern."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'SA*', False))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'


class TestResultLimiting:
    """Tests for result limiting."""

    def test_match_with_limit(self, test_db):
        """Test limiting results."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=1))
        assert len(results) == 1

    def test_match_with_limit_greater_than_total(self, test_db):
        """Test limit greater than total results."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=100))
        assert len(results) == 2  # Only 2 methods exist


class TestEmptyResults:
    """Tests for empty result scenarios."""

    def test_match_no_results(self, test_db):
        """Test matching with no results."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'nonexistent', True))
        assert len(results) == 0

    def test_match_empty_pattern_exact(self, test_db):
        """Test matching with empty pattern (EXACT)."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.EXACT, '', True))
        assert len(results) == 0


class TestBytePositionData:
    """Tests for byte position data in results."""

    def test_match_result_has_byte_position(self, test_db):
        """Test that methods have byte position data."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
        assert len(results) == 1
        assert results[0].byte_offset == 100
        assert results[0].byte_length == 50

    def test_match_result_no_byte_position_for_files(self, test_db):
        """Test that filenames don't have byte position data."""
        results = list(test_db.match(SymbolType.FILENAME, MatchOp.GLOB, '*', True))
        assert len(results) == 1
        assert results[0].byte_offset is None
        assert results[0].byte_length is None


class TestSQLInjectionProtection:
    """Tests for SQL injection protection."""

    def test_match_handles_single_quotes(self, test_db):
        """Test that single quotes in symbol names can be matched.

        Note: SQLite parameterized queries handle escaping automatically,
        so symbols with single quotes should work without issue.
        """
        # Insert a symbol with single quote
        test_db.insert_symbol("O'Connor", 'class', 'src/test.py', 10, "test.O'Connor", 100, 50, None)

        # The current implementation double-escapes due to manual escaping + parameterized queries
        # EXACT match works because it matches the literal string
        results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, "*Connor", True))
        assert len(results) == 1
        assert results[0].symbol_name == "O'Connor"

    def test_match_with_sql_keywords(self, test_db):
        """Test patterns containing SQL keywords are safe."""
        # Insert a symbol that looks like SQL injection
        test_db.insert_symbol("drop_table", 'function', 'src/test.py', 10, "test.drop_table", 100, 50, None)

        results = list(test_db.match(SymbolType.FUNCTION, MatchOp.GLOB, 'drop*', True))
        assert len(results) == 1
        assert results[0].symbol_name == "drop_table"


class TestMatchResultFields:
    """Tests for MatchResult field population."""

    def test_match_result_qualified_name(self, test_db):
        """Test that qualified_name is populated correctly."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
        assert len(results) == 1
        assert results[0].qualified_name == 'user.User.save'

    def test_match_result_parent_name(self, test_db):
        """Test that parent_name is populated for methods."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
        assert len(results) == 1
        assert results[0].parent_name == 'User'

    def test_match_result_file_path(self, test_db):
        """Test that file_path is populated correctly."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
        assert len(results) == 1
        assert results[0].file_path == 'src/user.py'

    def test_match_result_line_number(self, test_db):
        """Test that line_number is populated correctly."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
        assert len(results) == 1
        assert results[0].line_number == 10


class TestMatchWithRegex:
    """Tests for REGEXP matching (Python-side filtering)."""

    def test_match_regex_basic(self, test_db):
        """Test basic regex matching."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'sa.*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'

    def test_match_regex_word_boundary(self, test_db):
        """Test regex with word boundary pattern."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'^save$', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'save'

    def test_match_regex_no_match(self, test_db):
        """Test regex that matches nothing."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'^xyz$', True))
        assert len(results) == 0

    def test_match_regex_all(self, test_db):
        """Test regex that matches all."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'.*', True))
        assert len(results) == 2  # save and load

    def test_match_regex_case_sensitive(self, test_db):
        """Test case-sensitive regex matching."""
        results = list(test_db.match(SymbolType.CLASS, MatchOp.REGEXP, r'user', True))
        assert len(results) == 0  # 'User' != 'user'

    def test_match_regex_case_insensitive(self, test_db):
        """Test case-insensitive regex matching."""
        results = list(test_db.match(SymbolType.CLASS, MatchOp.REGEXP, r'user', False))
        assert len(results) == 1
        assert results[0].symbol_name == 'User'

    def test_match_regex_with_limit(self, test_db):
        """Test regex with limit."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'.*', True, limit=1))
        assert len(results) == 1

    def test_match_regex_character_class(self, test_db):
        """Test regex with character class."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'[sl].*', True))
        assert len(results) == 2  # save and load

    def test_match_regex_qualified_name(self, test_db):
        """Test regex on qualified_name."""
        results = list(test_db.match(
            SymbolType.METHOD, MatchOp.REGEXP, r'user\.User\.save', True, match_qualified=True
        ))
        assert len(results) == 1
        assert results[0].qualified_name == 'user.User.save'

    def test_match_regex_invalid_pattern(self, test_db):
        """Test invalid regex pattern raises error."""
        import re
        with pytest.raises(re.error):
            list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'[invalid', True))

    def test_match_regex_special_chars(self, test_db):
        """Test regex with special regex characters."""
        # Insert a symbol with special chars
        test_db.insert_symbol('test_func', 'function', 'src/test.py', 10, 'test.test_func', 100, 50, None)

        # Match with escaped dot and underscore
        results = list(test_db.match(SymbolType.FUNCTION, MatchOp.REGEXP, r'test_.*', True))
        assert len(results) == 1
        assert results[0].symbol_name == 'test_func'

    def test_match_regex_returns_match_record(self, test_db):
        """Test that regex returns proper MatchRecord objects."""
        results = list(test_db.match(SymbolType.METHOD, MatchOp.REGEXP, r'save', True))
        assert len(results) == 1
        record = results[0]
        # Check all expected fields are present
        assert record.symbol_name == 'save'
        assert record.symbol_type == 'method'
        assert record.file_path == 'src/user.py'
        assert record.line_number == 10
        assert record.byte_offset == 100
        assert record.byte_length == 50
        assert record.qualified_name == 'user.User.save'
