"""Unit tests for the renderer system (base, list, table, factory, formatters).

TLDR:
    Tests the full renderer hierarchy and factory. Key helper: make_test_records
    (generates MatchRecord iterators with optional total for "N more" logic). Key
    test classes: TestRendererBase (abstract interface, streaming contract),
    TestRendererFactory (format string to renderer mapping), TestListRenderer
    (plain/raw/code/markdown/html output, "... N more" truncation indicator),
    TestTableRenderer (column layout, per-type rows), TestTableFormatters
    (individual formatter units), TestRendererIntegration (end-to-end output
    correctness across format combinations).
    Role: protects the renderer layer consumed by PipelineExecutor; depends on
    MatchRecord, ClassMatchRecord, FunctionMatchRecord, MethodMatchRecord.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Iterator

import pytest
from via.core.match_record import (
    ClassMatchRecord,
    FormatType,
    FunctionMatchRecord,
    MatchRecord,
    MethodMatchRecord,
    RenderType,
)


def make_test_records(count: int = 3, total: int = None) -> Iterator[MatchRecord]:
    """Create test MatchRecord instances with metadata."""
    if total is None:
        total = count

    metadata_widths = {
        'symbol_name': 15,
        'qualified_name': 30,
        'file_path': 20,
        'symbol_type': 8,
        'parent_name': 10,
    }

    for i in range(count):
        yield ClassMatchRecord(
            symbol_type='class',
            symbol_name=f'TestClass{i}',
            qualified_name=f'module.TestClass{i}',
            file_path='module.py',
            line_number=10 + i * 10,
            byte_offset=100 + i * 100,
            byte_length=50,
            column_widths=metadata_widths,
            total_matches=total,
        )


class TestRendererBase:
    """Tests for Renderer base class."""

    def test_renderer_is_abstract(self):
        """Test Renderer cannot be instantiated directly."""
        from via.renderers.base import Renderer
        with pytest.raises(TypeError):
            Renderer()

    def test_renderer_has_render_method(self):
        """Test Renderer has abstract render method."""
        from via.renderers.base import Renderer
        assert hasattr(Renderer, 'render')


class TestRendererFactory:
    """Tests for RendererFactory."""

    def test_factory_creates_list_renderer(self):
        """Test factory creates ListRenderer for LIST type."""
        from via.renderers.factory import RendererFactory
        from via.renderers.list import ListRenderer

        renderer = RendererFactory.create(RenderType.LIST)
        assert isinstance(renderer, ListRenderer)

    def test_factory_creates_table_renderer_ascii(self):
        """Test factory creates TableRenderer with ASCII format."""
        from via.renderers.factory import RendererFactory
        from via.renderers.table import TableRenderer

        renderer = RendererFactory.create(RenderType.TABLE, FormatType.ASCII)
        assert isinstance(renderer, TableRenderer)

    def test_factory_creates_table_renderer_markdown(self):
        """Test factory creates TableRenderer with Markdown format."""
        from via.renderers.factory import RendererFactory
        from via.renderers.table import TableRenderer

        renderer = RendererFactory.create(RenderType.TABLE, FormatType.MD)
        assert isinstance(renderer, TableRenderer)

    def test_factory_creates_table_renderer_html(self):
        """Test factory creates TableRenderer with HTML format."""
        from via.renderers.factory import RendererFactory
        from via.renderers.table import TableRenderer

        renderer = RendererFactory.create(RenderType.TABLE, FormatType.HTML)
        assert isinstance(renderer, TableRenderer)

    def test_factory_default_format_is_ascii(self):
        """Test factory uses ASCII as default format."""
        from via.renderers.factory import RendererFactory
        from via.renderers.table import TableRenderer

        renderer = RendererFactory.create(RenderType.TABLE)
        assert isinstance(renderer, TableRenderer)


class TestListRenderer:
    """Tests for ListRenderer."""

    def test_list_renderer_basic_output(self):
        """Test ListRenderer outputs one line per record."""
        from via.renderers.list import ListRenderer

        renderer = ListRenderer()
        records = list(make_test_records(3))
        output = renderer.render(iter(records))

        lines = output.strip().split('\n')
        assert len(lines) == 3
        assert 'class:module.py:10:module.TestClass0' in lines[0]
        assert 'class:module.py:20:module.TestClass1' in lines[1]
        assert 'class:module.py:30:module.TestClass2' in lines[2]

    def test_list_renderer_includes_byte_position(self):
        """Test ListRenderer includes byte position in output."""
        from via.renderers.list import ListRenderer

        renderer = ListRenderer()
        records = list(make_test_records(1))
        output = renderer.render(iter(records))

        assert '@100+50' in output

    def test_list_renderer_more_indicator(self):
        """Test ListRenderer shows '... N more' when results limited."""
        from via.renderers.list import ListRenderer

        renderer = ListRenderer()
        # 2 records shown, but total_matches=5
        records = list(make_test_records(2, total=5))
        output = renderer.render(iter(records))

        assert '... (3 more)' in output

    def test_list_renderer_no_more_indicator_when_all_shown(self):
        """Test ListRenderer doesn't show indicator when all results shown."""
        from via.renderers.list import ListRenderer

        renderer = ListRenderer()
        records = list(make_test_records(3, total=3))
        output = renderer.render(iter(records))

        assert '... (' not in output

    def test_list_renderer_empty_input(self):
        """Test ListRenderer handles empty input."""
        from via.renderers.list import ListRenderer

        renderer = ListRenderer()
        output = renderer.render(iter([]))

        assert output == ''


class TestTableRenderer:
    """Tests for TableRenderer."""

    def test_table_renderer_ascii_format(self):
        """Test TableRenderer outputs ASCII table."""
        from via.renderers.formatters.table_formatters import AsciiTableFormatter
        from via.renderers.table import TableRenderer

        renderer = TableRenderer(AsciiTableFormatter())
        records = list(make_test_records(2))
        output = renderer.render(iter(records))

        # Should have header, separator, and data rows
        lines = output.strip().split('\n')
        assert len(lines) >= 3
        # Check for pipe separators
        assert '|' in lines[0]

    def test_table_renderer_markdown_format(self):
        """Test TableRenderer outputs Markdown table."""
        from via.renderers.formatters.table_formatters import MarkdownTableFormatter
        from via.renderers.table import TableRenderer

        renderer = TableRenderer(MarkdownTableFormatter())
        records = list(make_test_records(2))
        output = renderer.render(iter(records))

        # Check for markdown separator row
        assert '|---' in output or '| ---' in output

    def test_table_renderer_html_format(self):
        """Test TableRenderer outputs HTML table."""
        from via.renderers.formatters.table_formatters import HtmlTableFormatter
        from via.renderers.table import TableRenderer

        renderer = TableRenderer(HtmlTableFormatter())
        records = list(make_test_records(2))
        output = renderer.render(iter(records))

        assert '<table' in output
        assert '<thead>' in output
        assert '<tbody>' in output
        assert '</table>' in output

    def test_table_renderer_uses_metadata_widths(self):
        """Test TableRenderer uses column widths from metadata."""
        from via.renderers.formatters.table_formatters import AsciiTableFormatter
        from via.renderers.table import TableRenderer

        renderer = TableRenderer(AsciiTableFormatter())
        records = list(make_test_records(2))
        output = renderer.render(iter(records))

        # Columns should be padded consistently
        lines = output.strip().split('\n')
        # All data rows should have same length (proper padding)
        data_lines = [l for l in lines if 'TestClass' in l]
        if len(data_lines) > 1:
            assert len(data_lines[0]) == len(data_lines[1])

    def test_table_renderer_more_indicator(self):
        """Test TableRenderer shows '... N more' in footer."""
        from via.renderers.formatters.table_formatters import AsciiTableFormatter
        from via.renderers.table import TableRenderer

        renderer = TableRenderer(AsciiTableFormatter())
        records = list(make_test_records(2, total=10))
        output = renderer.render(iter(records))

        assert '8 more' in output or '... (8 more)' in output

    def test_table_renderer_empty_input(self):
        """Test TableRenderer handles empty input."""
        from via.renderers.formatters.table_formatters import AsciiTableFormatter
        from via.renderers.table import TableRenderer

        renderer = TableRenderer(AsciiTableFormatter())
        output = renderer.render(iter([]))

        # Should output empty or minimal output
        assert output == '' or 'No results' in output


class TestTableFormatters:
    """Tests for table formatters."""

    def test_ascii_formatter_header(self):
        """Test ASCII formatter creates proper header."""
        from via.renderers.formatters.table_formatters import AsciiTableFormatter

        formatter = AsciiTableFormatter()
        widths = {'symbol_name': 10, 'file_path': 15, 'line_number': 5}
        header = formatter.format_header(widths)

        assert 'Name' in header or 'name' in header.lower()
        assert '|' in header

    def test_ascii_formatter_row(self):
        """Test ASCII formatter creates proper row."""
        from via.renderers.formatters.table_formatters import AsciiTableFormatter

        formatter = AsciiTableFormatter()
        widths = {'symbol_name': 15, 'file_path': 20, 'line_number': 5}
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='TestClass',
            qualified_name='module.TestClass',
            file_path='module.py',
            line_number=10,
        )
        row = formatter.format_row(record, widths)

        assert 'TestClass' in row
        assert 'module.py' in row
        assert '|' in row

    def test_markdown_formatter_separator(self):
        """Test Markdown formatter includes separator row."""
        from via.renderers.formatters.table_formatters import MarkdownTableFormatter

        formatter = MarkdownTableFormatter()
        widths = {'symbol_name': 10, 'file_path': 15}
        header = formatter.format_header(widths)

        # Markdown tables need |---|---| separator
        assert '---' in header

    def test_html_formatter_structure(self):
        """Test HTML formatter creates proper structure."""
        from via.renderers.formatters.table_formatters import HtmlTableFormatter

        formatter = HtmlTableFormatter()
        widths = {'symbol_name': 10, 'file_path': 15}
        header = formatter.format_header(widths)

        assert '<th>' in header or '<th ' in header


class TestRendererIntegration:
    """Integration tests for renderer system."""

    def test_list_renderer_with_methods(self):
        """Test ListRenderer works with MethodMatchRecord."""
        from via.renderers.list import ListRenderer

        renderer = ListRenderer()
        records = [
            MethodMatchRecord(
                symbol_type='method',
                symbol_name='test_method',
                qualified_name='module.Class.test_method',
                file_path='module.py',
                line_number=15,
                parent_name='Class',
                total_matches=1,
            )
        ]
        output = renderer.render(iter(records))

        assert 'method:module.py:15' in output
        assert 'test_method' in output

    def test_table_renderer_with_mixed_types(self):
        """Test TableRenderer works with mixed record types."""
        from via.renderers.formatters.table_formatters import AsciiTableFormatter
        from via.renderers.table import TableRenderer

        renderer = TableRenderer(AsciiTableFormatter())
        records = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='MyClass',
                qualified_name='module.MyClass',
                file_path='module.py',
                line_number=10,
                column_widths={'symbol_name': 15, 'file_path': 15, 'symbol_type': 8},
                total_matches=2,
            ),
            FunctionMatchRecord(
                symbol_type='function',
                symbol_name='my_func',
                qualified_name='module.my_func',
                file_path='module.py',
                line_number=30,
                column_widths={'symbol_name': 15, 'file_path': 15, 'symbol_type': 8},
                total_matches=2,
            ),
        ]
        output = renderer.render(iter(records))

        assert 'MyClass' in output
        assert 'my_func' in output
