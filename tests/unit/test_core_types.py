"""
Unit tests for VIA core types (SymbolType, MatchOp).

TLDR:
    Tests for the core type definitions used by the match command.
    Verifies enum values and SQL operator mappings.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import pytest
from via.core.types import MatchOp, SymbolType


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

    def test_header_type(self):
        """Test HEADER enum value."""
        assert SymbolType.HEADER.value == 'header'

    def test_symbol_type_count(self):
        """Test that we have exactly 8 symbol types."""
        assert len(SymbolType) == 8


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
