"""
Unit tests for MatchRecord polymorphic system.

TLDR:
    Tests the MatchRecord base class, derived classes, enums, and factory.
    Verifies render type support, str formatting, and metadata handling.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import pytest
from abc import ABC


class TestRenderTypeEnum:
    """Tests for RenderType enum."""

    def test_render_type_list(self):
        """Test LIST render type exists."""
        from via.core.match_record import RenderType
        assert RenderType.LIST.value == 'list'

    def test_render_type_table(self):
        """Test TABLE render type exists."""
        from via.core.match_record import RenderType
        assert RenderType.TABLE.value == 'table'

    def test_render_type_diagram(self):
        """Test DIAGRAM render type exists."""
        from via.core.match_record import RenderType
        assert RenderType.DIAGRAM.value == 'diagram'

    def test_render_type_usage(self):
        """Test USAGE render type exists."""
        from via.core.match_record import RenderType
        assert RenderType.USAGE.value == 'usage'

    def test_render_type_raw(self):
        """Test RAW render type exists."""
        from via.core.match_record import RenderType
        assert RenderType.RAW.value == 'raw'

    def test_render_type_formatted(self):
        """Test FORMATTED render type exists."""
        from via.core.match_record import RenderType
        assert RenderType.FORMATTED.value == 'formatted'

    def test_render_type_count(self):
        """Test correct number of render types."""
        from via.core.match_record import RenderType
        assert len(RenderType) == 6


class TestFormatTypeEnum:
    """Tests for FormatType enum."""

    def test_format_type_ascii(self):
        """Test ASCII format type exists."""
        from via.core.match_record import FormatType
        assert FormatType.ASCII.value == 'ascii'

    def test_format_type_md(self):
        """Test MD format type exists."""
        from via.core.match_record import FormatType
        assert FormatType.MD.value == 'md'

    def test_format_type_html(self):
        """Test HTML format type exists."""
        from via.core.match_record import FormatType
        assert FormatType.HTML.value == 'html'

    def test_format_type_png(self):
        """Test PNG format type exists."""
        from via.core.match_record import FormatType
        assert FormatType.PNG.value == 'png'

    def test_format_type_count(self):
        """Test correct number of format types."""
        from via.core.match_record import FormatType
        assert len(FormatType) == 4


class TestMatchRecordBase:
    """Tests for MatchRecord base class."""

    def test_matchrecord_is_abstract(self):
        """Test MatchRecord cannot be instantiated directly."""
        from via.core.match_record import MatchRecord
        with pytest.raises(TypeError):
            MatchRecord(
                symbol_type='class',
                symbol_name='Foo',
                qualified_name='module.Foo',
                file_path='module.py',
                line_number=10,
            )

    def test_matchrecord_has_supports_render_type(self):
        """Test MatchRecord has abstract supports_render_type method."""
        from via.core.match_record import MatchRecord
        assert hasattr(MatchRecord, 'supports_render_type')


class TestClassMatchRecord:
    """Tests for ClassMatchRecord."""

    def test_class_record_creation(self):
        """Test ClassMatchRecord can be created."""
        from via.core.match_record import ClassMatchRecord
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
            byte_offset=100,
            byte_length=200,
        )
        assert record.symbol_name == 'TestClass'
        assert record.symbol_type == 'class'

    def test_class_record_str_format(self):
        """Test ClassMatchRecord __str__ format."""
        from via.core.match_record import ClassMatchRecord
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
            byte_offset=100,
            byte_length=200,
        )
        expected = 'class:module.py:10:module.TestClass:@100+200'
        assert str(record) == expected

    def test_class_record_str_without_byte_offset(self):
        """Test ClassMatchRecord __str__ without byte offset."""
        from via.core.match_record import ClassMatchRecord
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
        )
        expected = 'class:module.py:10:module.TestClass'
        assert str(record) == expected

    def test_class_record_supports_list(self):
        """Test ClassMatchRecord supports LIST render type."""
        from via.core.match_record import ClassMatchRecord, RenderType
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
        )
        assert record.supports_render_type(RenderType.LIST) is True

    def test_class_record_supports_table(self):
        """Test ClassMatchRecord supports TABLE render type."""
        from via.core.match_record import ClassMatchRecord, RenderType
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
        )
        assert record.supports_render_type(RenderType.TABLE) is True

    def test_class_record_supports_diagram(self):
        """Test ClassMatchRecord supports DIAGRAM render type."""
        from via.core.match_record import ClassMatchRecord, RenderType
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
        )
        assert record.supports_render_type(RenderType.DIAGRAM) is True

    def test_class_record_supports_raw(self):
        """Test ClassMatchRecord supports RAW render type."""
        from via.core.match_record import ClassMatchRecord, RenderType
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
        )
        assert record.supports_render_type(RenderType.RAW) is True

    def test_class_record_supports_formatted(self):
        """Test ClassMatchRecord supports FORMATTED render type."""
        from via.core.match_record import ClassMatchRecord, RenderType
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
        )
        assert record.supports_render_type(RenderType.FORMATTED) is True

    def test_class_record_with_metadata(self):
        """Test ClassMatchRecord with metadata fields."""
        from via.core.match_record import ClassMatchRecord
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
            column_widths={'symbol_name': 20, 'file_path': 30},
            total_matches=100,
        )
        assert record.column_widths == {'symbol_name': 20, 'file_path': 30}
        assert record.total_matches == 100


class TestMethodMatchRecord:
    """Tests for MethodMatchRecord."""

    def test_method_record_creation(self):
        """Test MethodMatchRecord can be created."""
        from via.core.match_record import MethodMatchRecord
        record = MethodMatchRecord(
            symbol_type='method',
            symbol_name='test_method',
            qualified_name='module.TestClass.test_method',
            file_path='module.py',
            line_number=15,
            parent_name='TestClass',
        )
        assert record.symbol_name == 'test_method'
        assert record.parent_name == 'TestClass'

    def test_method_record_no_diagram_support(self):
        """Test MethodMatchRecord does NOT support DIAGRAM render type."""
        from via.core.match_record import MethodMatchRecord, RenderType
        record = MethodMatchRecord(
            symbol_type='method',
            symbol_name='test_method',
            qualified_name='module.TestClass.test_method',
            file_path='module.py',
            line_number=15,
        )
        assert record.supports_render_type(RenderType.DIAGRAM) is False

    def test_method_record_supports_list(self):
        """Test MethodMatchRecord supports LIST render type."""
        from via.core.match_record import MethodMatchRecord, RenderType
        record = MethodMatchRecord(
            symbol_type='method',
            symbol_name='test_method',
            qualified_name='module.TestClass.test_method',
            file_path='module.py',
            line_number=15,
        )
        assert record.supports_render_type(RenderType.LIST) is True


class TestFunctionMatchRecord:
    """Tests for FunctionMatchRecord."""

    def test_function_record_creation(self):
        """Test FunctionMatchRecord can be created."""
        from via.core.match_record import FunctionMatchRecord
        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='helper',
            qualified_name='module.helper',
            file_path='module.py',
            line_number=20,
        )
        assert record.symbol_name == 'helper'

    def test_function_record_no_diagram_support(self):
        """Test FunctionMatchRecord does NOT support DIAGRAM render type."""
        from via.core.match_record import FunctionMatchRecord, RenderType
        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='helper',
            qualified_name='module.helper',
            file_path='module.py',
            line_number=20,
        )
        assert record.supports_render_type(RenderType.DIAGRAM) is False

    def test_function_record_supports_formatted(self):
        """Test FunctionMatchRecord supports FORMATTED render type."""
        from via.core.match_record import FunctionMatchRecord, RenderType
        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='helper',
            qualified_name='module.helper',
            file_path='module.py',
            line_number=20,
        )
        assert record.supports_render_type(RenderType.FORMATTED) is True


class TestFileMatchRecord:
    """Tests for FileMatchRecord."""

    def test_file_record_creation(self):
        """Test FileMatchRecord can be created."""
        from via.core.match_record import FileMatchRecord
        record = FileMatchRecord(
            symbol_type='filepath',
            symbol_name='module.py',
            qualified_name='module.py',
            file_path='module.py',
            line_number=0,
        )
        assert record.symbol_name == 'module.py'

    def test_file_record_supports_raw(self):
        """Test FileMatchRecord supports RAW render type."""
        from via.core.match_record import FileMatchRecord, RenderType
        record = FileMatchRecord(
            symbol_type='filepath',
            symbol_name='module.py',
            qualified_name='module.py',
            file_path='module.py',
            line_number=0,
        )
        assert record.supports_render_type(RenderType.RAW) is True

    def test_file_record_no_diagram_support(self):
        """Test FileMatchRecord does NOT support DIAGRAM render type."""
        from via.core.match_record import FileMatchRecord, RenderType
        record = FileMatchRecord(
            symbol_type='filepath',
            symbol_name='module.py',
            qualified_name='module.py',
            file_path='module.py',
            line_number=0,
        )
        assert record.supports_render_type(RenderType.DIAGRAM) is False

    def test_file_record_no_formatted_support(self):
        """Test FileMatchRecord does NOT support FORMATTED render type."""
        from via.core.match_record import FileMatchRecord, RenderType
        record = FileMatchRecord(
            symbol_type='filepath',
            symbol_name='module.py',
            qualified_name='module.py',
            file_path='module.py',
            line_number=0,
        )
        assert record.supports_render_type(RenderType.FORMATTED) is False


class TestImportMatchRecord:
    """Tests for ImportMatchRecord."""

    def test_import_record_creation(self):
        """Test ImportMatchRecord can be created."""
        from via.core.match_record import ImportMatchRecord
        record = ImportMatchRecord(
            symbol_type='import',
            symbol_name='json',
            qualified_name='json',
            file_path='module.py',
            line_number=1,
        )
        assert record.symbol_name == 'json'

    def test_import_record_supports_usage(self):
        """Test ImportMatchRecord supports USAGE render type."""
        from via.core.match_record import ImportMatchRecord, RenderType
        record = ImportMatchRecord(
            symbol_type='import',
            symbol_name='json',
            qualified_name='json',
            file_path='module.py',
            line_number=1,
        )
        assert record.supports_render_type(RenderType.USAGE) is True

    def test_import_record_no_diagram_support(self):
        """Test ImportMatchRecord does NOT support DIAGRAM render type."""
        from via.core.match_record import ImportMatchRecord, RenderType
        record = ImportMatchRecord(
            symbol_type='import',
            symbol_name='json',
            qualified_name='json',
            file_path='module.py',
            line_number=1,
        )
        assert record.supports_render_type(RenderType.DIAGRAM) is False


class TestGlobalMatchRecord:
    """Tests for GlobalMatchRecord."""

    def test_global_record_creation(self):
        """Test GlobalMatchRecord can be created."""
        from via.core.match_record import GlobalMatchRecord
        record = GlobalMatchRecord(
            symbol_type='global',
            symbol_name='MAX_RETRIES',
            qualified_name='module.MAX_RETRIES',
            file_path='module.py',
            line_number=5,
        )
        assert record.symbol_name == 'MAX_RETRIES'

    def test_global_record_supports_formatted(self):
        """Test GlobalMatchRecord supports FORMATTED render type."""
        from via.core.match_record import GlobalMatchRecord, RenderType
        record = GlobalMatchRecord(
            symbol_type='global',
            symbol_name='MAX_RETRIES',
            qualified_name='module.MAX_RETRIES',
            file_path='module.py',
            line_number=5,
        )
        assert record.supports_render_type(RenderType.FORMATTED) is True

    def test_global_record_no_diagram_support(self):
        """Test GlobalMatchRecord does NOT support DIAGRAM render type."""
        from via.core.match_record import GlobalMatchRecord, RenderType
        record = GlobalMatchRecord(
            symbol_type='global',
            symbol_name='MAX_RETRIES',
            qualified_name='module.MAX_RETRIES',
            file_path='module.py',
            line_number=5,
        )
        assert record.supports_render_type(RenderType.DIAGRAM) is False


class TestMatchRecordFactory:
    """Tests for MatchRecordFactory."""

    def test_factory_creates_class_record(self):
        """Test factory creates ClassMatchRecord for class type."""
        from via.core.match_record import MatchRecordFactory, ClassMatchRecord
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'class',
            'symbol_name': 'TestClass',
            'qualified_name': 'module.TestClass',
            'file_path': 'module.py',
            'line_number': 10,
            'byte_offset': 100,
            'byte_length': 200,
            'parent_name': None,
        }
        record = factory.create_from_row(row)
        assert isinstance(record, ClassMatchRecord)
        assert record.symbol_name == 'TestClass'

    def test_factory_creates_method_record(self):
        """Test factory creates MethodMatchRecord for method type."""
        from via.core.match_record import MatchRecordFactory, MethodMatchRecord
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'method',
            'symbol_name': 'test_method',
            'qualified_name': 'module.TestClass.test_method',
            'file_path': 'module.py',
            'line_number': 15,
            'byte_offset': 150,
            'byte_length': 50,
            'parent_name': 'TestClass',
        }
        record = factory.create_from_row(row)
        assert isinstance(record, MethodMatchRecord)
        assert record.parent_name == 'TestClass'

    def test_factory_creates_function_record(self):
        """Test factory creates FunctionMatchRecord for function type."""
        from via.core.match_record import MatchRecordFactory, FunctionMatchRecord
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'function',
            'symbol_name': 'helper',
            'qualified_name': 'module.helper',
            'file_path': 'module.py',
            'line_number': 20,
            'byte_offset': 200,
            'byte_length': 100,
            'parent_name': None,
        }
        record = factory.create_from_row(row)
        assert isinstance(record, FunctionMatchRecord)

    def test_factory_creates_file_record(self):
        """Test factory creates FileMatchRecord for filepath type."""
        from via.core.match_record import MatchRecordFactory, FileMatchRecord
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'filepath',
            'symbol_name': 'module.py',
            'qualified_name': 'module.py',
            'file_path': 'module.py',
            'line_number': 0,
            'byte_offset': None,
            'byte_length': None,
            'parent_name': None,
        }
        record = factory.create_from_row(row)
        assert isinstance(record, FileMatchRecord)

    def test_factory_creates_import_record(self):
        """Test factory creates ImportMatchRecord for import type."""
        from via.core.match_record import MatchRecordFactory, ImportMatchRecord
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'import',
            'symbol_name': 'json',
            'qualified_name': 'json',
            'file_path': 'module.py',
            'line_number': 1,
            'byte_offset': 0,
            'byte_length': 11,
            'parent_name': None,
        }
        record = factory.create_from_row(row)
        assert isinstance(record, ImportMatchRecord)

    def test_factory_creates_global_record(self):
        """Test factory creates GlobalMatchRecord for global type."""
        from via.core.match_record import MatchRecordFactory, GlobalMatchRecord
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'global',
            'symbol_name': 'MAX_RETRIES',
            'qualified_name': 'module.MAX_RETRIES',
            'file_path': 'module.py',
            'line_number': 5,
            'byte_offset': 50,
            'byte_length': 15,
            'parent_name': None,
        }
        record = factory.create_from_row(row)
        assert isinstance(record, GlobalMatchRecord)

    def test_factory_with_metadata(self):
        """Test factory attaches metadata to record."""
        from via.core.match_record import MatchRecordFactory
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'class',
            'symbol_name': 'TestClass',
            'qualified_name': 'module.TestClass',
            'file_path': 'module.py',
            'line_number': 10,
            'byte_offset': 100,
            'byte_length': 200,
            'parent_name': None,
        }
        metadata = {
            'column_widths': {'symbol_name': 20},
            'total_matches': 50,
        }
        record = factory.create_from_row(row, metadata)
        assert record.column_widths == {'symbol_name': 20}
        assert record.total_matches == 50

    def test_factory_without_metadata(self):
        """Test factory works without metadata."""
        from via.core.match_record import MatchRecordFactory
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'class',
            'symbol_name': 'TestClass',
            'qualified_name': 'module.TestClass',
            'file_path': 'module.py',
            'line_number': 10,
            'byte_offset': 100,
            'byte_length': 200,
            'parent_name': None,
        }
        record = factory.create_from_row(row)
        assert record.column_widths is None
        assert record.total_matches is None

    def test_factory_unknown_type_raises_error(self):
        """Test factory raises ValueError for unknown symbol type."""
        from via.core.match_record import MatchRecordFactory
        factory = MatchRecordFactory()
        row = {
            'symbol_type': 'unknown_type',
            'symbol_name': 'foo',
            'qualified_name': 'foo',
            'file_path': 'module.py',
            'line_number': 1,
            'byte_offset': None,
            'byte_length': None,
            'parent_name': None,
        }
        with pytest.raises(ValueError) as exc_info:
            factory.create_from_row(row)
        assert 'unknown_type' in str(exc_info.value)
