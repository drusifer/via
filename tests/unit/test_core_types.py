"""
Unit tests for VIA core types (SymbolType, MatchOp, MatchResult).

TLDR:
    Tests for the core type definitions used by the match command.
    Verifies enum values, SQL operator mappings, and MatchResult formatting.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import pytest
from via.core.types import SymbolType, MatchOp, MatchResult


class TestSymbolTypeEnum:
    """Tests for SymbolType enum."""

    def test_symbol_type_method(self):
        """Test METHOD enum value."""
        assert SymbolType.METHOD.value == 'method'

    def test_symbol_type_class(self):
        """Test CLASS enum value."""
        assert SymbolType.CLASS.value == 'class'

    def test_symbol_type_function(self):
        """Test FUNCTION enum value."""
        assert SymbolType.FUNCTION.value == 'function'

    def test_symbol_type_filepath(self):
        """Test FILEPATH enum value."""
        assert SymbolType.FILEPATH.value == 'filepath'

    def test_symbol_type_filename(self):
        """Test FILENAME enum value."""
        assert SymbolType.FILENAME.value == 'filename'

    def test_symbol_type_import(self):
        """Test IMPORT enum value."""
        assert SymbolType.IMPORT.value == 'import'

    def test_symbol_type_global(self):
        """Test GLOBAL enum value."""
        assert SymbolType.GLOBAL.value == 'global'

    def test_symbol_type_count(self):
        """Test that we have exactly 7 symbol types."""
        assert len(SymbolType) == 7


class TestMatchOpEnum:
    """Tests for MatchOp enum."""

    def test_match_op_exact(self):
        """Test EXACT match operator."""
        assert MatchOp.EXACT.op_name == 'exact'
        assert MatchOp.EXACT.sql_op == '='
        assert MatchOp.EXACT.needs_escaping is True

    def test_match_op_glob(self):
        """Test GLOB match operator."""
        assert MatchOp.GLOB.op_name == 'glob'
        assert MatchOp.GLOB.sql_op == 'GLOB'
        assert MatchOp.GLOB.needs_escaping is True

    def test_match_op_like(self):
        """Test LIKE match operator."""
        assert MatchOp.LIKE.op_name == 'like'
        assert MatchOp.LIKE.sql_op == 'LIKE'
        assert MatchOp.LIKE.needs_escaping is True

    def test_match_op_regexp(self):
        """Test REGEXP match operator."""
        assert MatchOp.REGEXP.op_name == 'regexp'
        assert MatchOp.REGEXP.sql_op == 'REGEXP'
        assert MatchOp.REGEXP.needs_escaping is True

    def test_match_op_count(self):
        """Test that we have exactly 4 match operators."""
        assert len(MatchOp) == 4


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_match_result_creation(self):
        """Test creating a MatchResult with all fields."""
        result = MatchResult(
            symbol_type='method',
            symbol_name='save',
            qualified_name='models.user.User.save',
            file_path='src/models/user.py',
            line_number=45,
            byte_offset=1234,
            byte_length=56,
            parent_name='User'
        )
        assert result.symbol_type == 'method'
        assert result.symbol_name == 'save'
        assert result.qualified_name == 'models.user.User.save'
        assert result.file_path == 'src/models/user.py'
        assert result.line_number == 45
        assert result.byte_offset == 1234
        assert result.byte_length == 56
        assert result.parent_name == 'User'

    def test_match_result_str_with_byte_position(self):
        """Test MatchResult string formatting with byte position."""
        result = MatchResult(
            symbol_type='method',
            symbol_name='save',
            qualified_name='models.user.User.save',
            file_path='src/models/user.py',
            line_number=45,
            byte_offset=1234,
            byte_length=56,
            parent_name='User'
        )
        expected = 'method:src/models/user.py:45:models.user.User.save:@1234+56'
        assert str(result) == expected

    def test_match_result_str_without_byte_position(self):
        """Test MatchResult string formatting without byte position."""
        result = MatchResult(
            symbol_type='filepath',
            symbol_name='user.py',
            qualified_name='src/models/user.py',
            file_path='src/models/user.py',
            line_number=0,
            byte_offset=None,
            byte_length=None,
            parent_name=None
        )
        expected = 'filepath:src/models/user.py:0:src/models/user.py'
        assert str(result) == expected

    def test_match_result_with_none_parent(self):
        """Test MatchResult with None parent_name (functions, classes)."""
        result = MatchResult(
            symbol_type='function',
            symbol_name='calculate',
            qualified_name='utils.calculate',
            file_path='src/utils.py',
            line_number=15,
            byte_offset=300,
            byte_length=80,
            parent_name=None
        )
        assert result.parent_name is None
        assert 'function:src/utils.py:15:utils.calculate:@300+80' == str(result)

    def test_match_result_equality(self):
        """Test MatchResult equality comparison."""
        result1 = MatchResult(
            symbol_type='method',
            symbol_name='save',
            qualified_name='User.save',
            file_path='user.py',
            line_number=10,
            byte_offset=100,
            byte_length=50,
            parent_name='User'
        )
        result2 = MatchResult(
            symbol_type='method',
            symbol_name='save',
            qualified_name='User.save',
            file_path='user.py',
            line_number=10,
            byte_offset=100,
            byte_length=50,
            parent_name='User'
        )
        assert result1 == result2
