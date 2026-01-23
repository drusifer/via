"""
Tests for UsageRenderer.

TDD: Tests written first, then implementation.
"""

import pytest
from unittest.mock import patch, MagicMock
from via.renderers.usage import UsageRenderer, MAX_USAGES_PER_SYMBOL
from via.renderers.formatters.usage_formatters import (
    UsageLocation,
    AsciiUsageFormatter,
    MarkdownUsageFormatter,
    HtmlUsageFormatter,
)
from via.core.match_record import FunctionMatchRecord, ClassMatchRecord, MethodMatchRecord


class TestUsageRendererBasics:
    def test_usage_renderer_exists(self):
        """UsageRenderer class should exist."""
        renderer = UsageRenderer()
        assert renderer is not None

    def test_usage_renderer_has_render_method(self):
        """UsageRenderer should have a render method."""
        renderer = UsageRenderer()
        assert hasattr(renderer, 'render')

    def test_usage_renderer_default_formatter(self):
        """UsageRenderer should use AsciiUsageFormatter by default."""
        renderer = UsageRenderer()
        assert isinstance(renderer.formatter, AsciiUsageFormatter)

    def test_usage_renderer_custom_formatter(self):
        """UsageRenderer should accept custom formatter."""
        formatter = MarkdownUsageFormatter()
        renderer = UsageRenderer(formatter=formatter)
        assert isinstance(renderer.formatter, MarkdownUsageFormatter)


class TestUsageRendererOutput:
    def test_render_empty_records(self):
        """Rendering with no records should return an empty string."""
        renderer = UsageRenderer()
        output = renderer.render(iter([]))
        assert output == ''

    @patch.object(UsageRenderer, '_find_usages')
    def test_render_single_record_with_usages(self, mock_find_usages):
        """Rendering a single record with usages should show them."""
        mock_find_usages.return_value = [
            UsageLocation(file_path='other.py', line_number=10, context='my_function()'),
            UsageLocation(file_path='test.py', line_number=20, context='result = my_function()')
        ]

        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='my_function',
            qualified_name='module.my_function',
            file_path='src/foo.py',
            line_number=42,
            byte_offset=100,
            byte_length=50
        )

        renderer = UsageRenderer()
        output = renderer.render(iter([record]))

        assert 'my_function' in output
        assert 'src/foo.py:42' in output
        assert 'other.py:10' in output
        assert 'test.py:20' in output

    @patch.object(UsageRenderer, '_find_usages')
    def test_render_record_no_usages(self, mock_find_usages):
        """Rendering a record with no usages should show appropriate message."""
        mock_find_usages.return_value = []

        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='unused_function',
            qualified_name='module.unused_function',
            file_path='src/foo.py',
            line_number=42,
            byte_offset=100,
            byte_length=50
        )

        renderer = UsageRenderer()
        output = renderer.render(iter([record]))

        assert 'unused_function' in output
        assert 'No usages found' in output

    @patch.object(UsageRenderer, '_find_usages')
    def test_render_multiple_records(self, mock_find_usages):
        """Rendering multiple records should show usages for each."""
        mock_find_usages.side_effect = [
            [UsageLocation(file_path='a.py', line_number=1, context='foo()')],
            [UsageLocation(file_path='b.py', line_number=2, context='bar()')]
        ]

        records = [
            FunctionMatchRecord(
                symbol_type='function',
                symbol_name='foo',
                qualified_name='mod.foo',
                file_path='foo.py',
                line_number=10,
                byte_offset=0,
                byte_length=20
            ),
            FunctionMatchRecord(
                symbol_type='function',
                symbol_name='bar',
                qualified_name='mod.bar',
                file_path='bar.py',
                line_number=20,
                byte_offset=0,
                byte_length=20
            )
        ]

        renderer = UsageRenderer()
        output = renderer.render(iter(records))

        assert 'foo' in output
        assert 'bar' in output
        assert 'a.py:1' in output
        assert 'b.py:2' in output

    @patch.object(UsageRenderer, '_find_usages')
    def test_render_limits_usages(self, mock_find_usages):
        """Rendering should limit usages to MAX_USAGES_PER_SYMBOL."""
        # Create more usages than the limit
        usages = [
            UsageLocation(file_path=f'file{i}.py', line_number=i, context=f'usage {i}')
            for i in range(MAX_USAGES_PER_SYMBOL + 10)
        ]
        mock_find_usages.return_value = usages

        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='popular_func',
            qualified_name='mod.popular_func',
            file_path='src.py',
            line_number=1,
            byte_offset=0,
            byte_length=20
        )

        renderer = UsageRenderer()
        output = renderer.render(iter([record]))

        # Should show the "more" indicator
        assert 'more usages' in output.lower()


class TestUsageRendererGrep:
    def test_find_usages_skips_definition(self):
        """find_usages should skip the definition line."""
        renderer = UsageRenderer()

        # Mock grep output that includes definition line
        mock_output = (
            "src/foo.py:42:def my_function():\n"  # Definition - should skip
            "other.py:10:my_function()\n"           # Usage - should include
        )

        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='my_function',
            qualified_name='module.my_function',
            file_path='src/foo.py',
            line_number=42,
            byte_offset=100,
            byte_length=50
        )

        usages = renderer._parse_grep_output(mock_output, 'src/foo.py', 42)

        assert len(usages) == 1
        assert usages[0].file_path == 'other.py'
        assert usages[0].line_number == 10

    def test_parse_grep_output_handles_empty(self):
        """parse_grep_output should handle empty output."""
        renderer = UsageRenderer()
        usages = renderer._parse_grep_output('', 'foo.py', 1)
        assert usages == []

    def test_parse_grep_output_handles_malformed_lines(self):
        """parse_grep_output should skip malformed lines."""
        renderer = UsageRenderer()

        mock_output = (
            "good.py:10:valid line\n"
            "bad_line_no_colon\n"
            "another.py:abc:not a number\n"
            "valid.py:20:another valid\n"
        )

        usages = renderer._parse_grep_output(mock_output, 'def.py', 1)

        assert len(usages) == 2
        assert usages[0].file_path == 'good.py'
        assert usages[1].file_path == 'valid.py'


class TestUsageFormatters:
    def test_ascii_formatter_header(self):
        """ASCII formatter should format header correctly."""
        formatter = AsciiUsageFormatter()
        header = formatter.format_header('my_func', 'src/foo.py', 42)
        assert 'my_func' in header
        assert 'src/foo.py:42' in header

    def test_ascii_formatter_usage(self):
        """ASCII formatter should format usage correctly."""
        formatter = AsciiUsageFormatter()
        usage = UsageLocation(file_path='test.py', line_number=10, context='  my_func()  ')
        output = formatter.format_usage(usage)
        assert 'test.py:10' in output
        assert 'my_func()' in output

    def test_ascii_formatter_no_usages(self):
        """ASCII formatter should format no usages message."""
        formatter = AsciiUsageFormatter()
        output = formatter.format_no_usages('unused')
        assert 'unused' in output
        assert 'No usages found' in output

    def test_markdown_formatter_header(self):
        """Markdown formatter should include clickable link."""
        formatter = MarkdownUsageFormatter()
        header = formatter.format_header('my_func', 'src/foo.py', 42)
        assert '[src/foo.py:42]' in header
        assert '#L42' in header

    def test_markdown_formatter_usage(self):
        """Markdown formatter should use markdown links."""
        formatter = MarkdownUsageFormatter()
        usage = UsageLocation(file_path='test.py', line_number=10, context='my_func()')
        output = formatter.format_usage(usage)
        assert '[test.py:10]' in output
        assert '#L10' in output
        assert '`my_func()`' in output

    def test_html_formatter_header(self):
        """HTML formatter should include HTML elements."""
        formatter = HtmlUsageFormatter()
        header = formatter.format_header('my_func', 'src/foo.py', 42)
        assert '<h3>' in header
        assert '<code>my_func</code>' in header
        assert '<a href=' in header

    def test_html_formatter_usage(self):
        """HTML formatter should use HTML links and code elements."""
        formatter = HtmlUsageFormatter()
        usage = UsageLocation(file_path='test.py', line_number=10, context='my_func()')
        output = formatter.format_usage(usage)
        assert '<li>' in output
        assert '<a href=' in output
        assert '<code>' in output


class TestUsageRendererIntegration:
    @patch('shutil.which')
    def test_no_search_tool_available(self, mock_which):
        """Renderer should show error when no search tool is available."""
        mock_which.return_value = None

        renderer = UsageRenderer()

        record = FunctionMatchRecord(
            symbol_type='function',
            symbol_name='my_function',
            qualified_name='module.my_function',
            file_path='src/foo.py',
            line_number=42,
            byte_offset=100,
            byte_length=50
        )

        output = renderer.render(iter([record]))
        assert 'ripgrep' in output.lower() or 'grep' in output.lower()
        assert 'error' in output.lower()
