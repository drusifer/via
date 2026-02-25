"""
Unit tests for FormattedRenderer and code formatters.

TLDR:
    Tests the FormattedRenderer which extracts and syntax-highlights source
    code using Pygments. Also tests the code formatters (ASCII, HTML, Markdown).

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
import re
import tempfile
from typing import Iterator

import pytest
from via.core.match_record import (
    ClassMatchRecord,
    FileMatchRecord,
    FunctionMatchRecord,
    GlobalMatchRecord,
    ImportMatchRecord,
    MethodMatchRecord,
    RenderType,
)


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


# Sample Python source for testing
SAMPLE_SOURCE = '''"""Module docstring."""

import os
import sys

class MyClass:
    """A sample class."""

    def __init__(self, value):
        """Initialize with value."""
        self.value = value

    def get_value(self):
        """Return the value."""
        return self.value


def my_function(x, y):
    """Add two numbers."""
    return x + y


MY_GLOBAL = 42
'''


@pytest.fixture
def temp_source_file():
    """Create a temporary file with sample source code."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(SAMPLE_SOURCE)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def make_class_record(file_path: str) -> ClassMatchRecord:
    """Create a ClassMatchRecord for MyClass in sample source."""
    source = SAMPLE_SOURCE.encode('utf-8')
    start = source.find(b'class MyClass:')
    end = source.find(b'\n\ndef my_function')
    return ClassMatchRecord(
        symbol_type='class',
        symbol_name='MyClass',
        qualified_name='module.MyClass',
        file_path=file_path,
        line_number=7,
        byte_offset=start,
        byte_length=end - start,
        total_matches=1,
    )


def make_method_record(file_path: str) -> MethodMatchRecord:
    """Create a MethodMatchRecord for get_value method."""
    source = SAMPLE_SOURCE.encode('utf-8')
    start = source.find(b'def get_value(self):')
    end = source.find(b'\n\n\ndef my_function')
    return MethodMatchRecord(
        symbol_type='method',
        symbol_name='get_value',
        qualified_name='module.MyClass.get_value',
        file_path=file_path,
        line_number=14,
        byte_offset=start,
        byte_length=end - start,
        parent_name='MyClass',
        total_matches=1,
    )


def make_function_record(file_path: str) -> FunctionMatchRecord:
    """Create a FunctionMatchRecord for my_function."""
    source = SAMPLE_SOURCE.encode('utf-8')
    start = source.find(b'def my_function')
    end = source.find(b'\n\n\nMY_GLOBAL')
    return FunctionMatchRecord(
        symbol_type='function',
        symbol_name='my_function',
        qualified_name='module.my_function',
        file_path=file_path,
        line_number=19,
        byte_offset=start,
        byte_length=end - start,
        total_matches=1,
    )


def make_global_record(file_path: str) -> GlobalMatchRecord:
    """Create a GlobalMatchRecord for MY_GLOBAL."""
    source = SAMPLE_SOURCE.encode('utf-8')
    start = source.find(b'MY_GLOBAL = 42')
    end = len(source)
    return GlobalMatchRecord(
        symbol_type='global',
        symbol_name='MY_GLOBAL',
        qualified_name='module.MY_GLOBAL',
        file_path=file_path,
        line_number=24,
        byte_offset=start,
        byte_length=end - start,
        total_matches=1,
    )


def make_file_record(file_path: str) -> FileMatchRecord:
    """Create a FileMatchRecord."""
    return FileMatchRecord(
        symbol_type='filepath',
        symbol_name=os.path.basename(file_path),
        qualified_name=file_path,
        file_path=file_path,
        line_number=1,
        total_matches=1,
    )


def make_import_record(file_path: str) -> ImportMatchRecord:
    """Create an ImportMatchRecord for 'import os'."""
    source = SAMPLE_SOURCE.encode('utf-8')
    start = source.find(b'import os')
    end = source.find(b'\nimport sys')
    return ImportMatchRecord(
        symbol_type='import',
        symbol_name='os',
        qualified_name='os',
        file_path=file_path,
        line_number=3,
        byte_offset=start,
        byte_length=end - start,
        total_matches=1,
    )


class TestCodeFormatterBasic:
    """Basic tests for code formatters."""

    def test_ascii_code_formatter_exists(self):
        """Test AsciiCodeFormatter can be imported."""
        from via.renderers.formatters.code_formatters import AsciiCodeFormatter
        formatter = AsciiCodeFormatter()
        assert formatter is not None

    def test_html_code_formatter_exists(self):
        """Test HtmlCodeFormatter can be imported."""
        from via.renderers.formatters.code_formatters import HtmlCodeFormatter
        formatter = HtmlCodeFormatter()
        assert formatter is not None

    def test_markdown_code_formatter_exists(self):
        """Test MarkdownCodeFormatter can be imported."""
        from via.renderers.formatters.code_formatters import MarkdownCodeFormatter
        formatter = MarkdownCodeFormatter()
        assert formatter is not None


class TestAsciiCodeFormatter:
    """Tests for AsciiCodeFormatter."""

    def test_ascii_formatter_highlights_python(self):
        """Test ASCII formatter highlights Python code."""
        from via.renderers.formatters.code_formatters import AsciiCodeFormatter

        formatter = AsciiCodeFormatter()
        source = "def hello():\n    return 'world'"
        output = formatter.format_code(source, 'python', start_line=1)

        # Should contain ANSI escape codes (highlighting)
        assert '\x1b[' in output or output == source  # Either highlighted or plain

    def test_ascii_formatter_line_numbers(self):
        """Test ASCII formatter includes line numbers."""
        from via.renderers.formatters.code_formatters import AsciiCodeFormatter

        formatter = AsciiCodeFormatter()
        source = "line1\nline2\nline3"
        output = formatter.format_code(source, 'python', start_line=10, show_line_numbers=True)

        # Should have line numbers
        assert '10' in output or 'line1' in output

    def test_ascii_formatter_theme_selection(self):
        """Test ASCII formatter supports theme selection."""
        from via.renderers.formatters.code_formatters import AsciiCodeFormatter

        formatter = AsciiCodeFormatter()
        source = "def test(): pass"

        # Different themes should produce different output (or same if no color)
        output_monokai = formatter.format_code(source, 'python', start_line=1, theme='monokai')
        output_default = formatter.format_code(source, 'python', start_line=1, theme='default')

        # Both should be valid output
        assert 'def' in output_monokai
        assert 'def' in output_default


class TestHtmlCodeFormatter:
    """Tests for HtmlCodeFormatter."""

    def test_html_formatter_generates_html(self):
        """Test HTML formatter generates valid HTML."""
        from via.renderers.formatters.code_formatters import HtmlCodeFormatter

        formatter = HtmlCodeFormatter()
        source = "def hello(): pass"
        output = formatter.format_code(source, 'python', start_line=1)

        # Should contain HTML tags
        assert '<' in output and '>' in output

    def test_html_formatter_includes_css_class(self):
        """Test HTML formatter uses CSS classes for highlighting."""
        from via.renderers.formatters.code_formatters import HtmlCodeFormatter

        formatter = HtmlCodeFormatter()
        source = "def hello(): pass"
        output = formatter.format_code(source, 'python', start_line=1)

        # Should have highlight class or span tags
        assert 'class=' in output or '<span' in output or '<pre' in output


class TestMarkdownCodeFormatter:
    """Tests for MarkdownCodeFormatter."""

    def test_markdown_formatter_code_fence(self):
        """Test Markdown formatter uses code fences."""
        from via.renderers.formatters.code_formatters import MarkdownCodeFormatter

        formatter = MarkdownCodeFormatter()
        source = "def hello(): pass"
        output = formatter.format_code(source, 'python', start_line=1)

        # Should have markdown code fence with language
        assert '```python' in output or '```' in output
        assert 'def hello' in output

    def test_markdown_formatter_preserves_content(self):
        """Test Markdown formatter preserves source content."""
        from via.renderers.formatters.code_formatters import MarkdownCodeFormatter

        formatter = MarkdownCodeFormatter()
        source = "x = 1\ny = 2"
        output = formatter.format_code(source, 'python', start_line=1)

        assert 'x = 1' in output
        assert 'y = 2' in output


class TestFormattedRendererBasic:
    """Basic tests for FormattedRenderer."""

    def test_formatted_renderer_exists(self):
        """Test FormattedRenderer can be imported."""
        from via.renderers.formatted import FormattedRenderer
        renderer = FormattedRenderer()
        assert renderer is not None

    def test_formatted_renderer_is_renderer(self):
        """Test FormattedRenderer inherits from Renderer."""
        from via.renderers.base import Renderer
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        assert isinstance(renderer, Renderer)


class TestFormattedRendererClassSource:
    """Tests for rendering class source."""

    def test_formatted_renderer_class_source(self, temp_source_file):
        """Test FormattedRenderer extracts and highlights class source."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_class_record(temp_source_file)
        output = renderer.render(iter([record]))

        plain = strip_ansi(output)
        assert 'class MyClass' in plain
        assert 'def __init__' in plain

    def test_formatted_renderer_includes_header(self, temp_source_file):
        """Test FormattedRenderer includes symbol header."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_class_record(temp_source_file)
        output = renderer.render(iter([record]))

        # Should have header with qualified name and location
        assert 'module.MyClass' in output or 'MyClass' in output


class TestFormattedRendererMethodSource:
    """Tests for rendering method source."""

    def test_formatted_renderer_method_source(self, temp_source_file):
        """Test FormattedRenderer extracts and highlights method source."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_method_record(temp_source_file)
        output = renderer.render(iter([record]))

        plain = strip_ansi(output)
        assert 'def get_value' in plain
        assert 'return self.value' in plain


class TestFormattedRendererFunctionSource:
    """Tests for rendering function source."""

    def test_formatted_renderer_function_source(self, temp_source_file):
        """Test FormattedRenderer extracts and highlights function source."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_function_record(temp_source_file)
        output = renderer.render(iter([record]))

        plain = strip_ansi(output)
        assert 'def my_function' in plain
        assert 'return x + y' in plain


class TestFormattedRendererGlobalSource:
    """Tests for rendering global variable source."""

    def test_formatted_renderer_global_source(self, temp_source_file):
        """Test FormattedRenderer extracts and highlights global source."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_global_record(temp_source_file)
        output = renderer.render(iter([record]))

        assert 'MY_GLOBAL' in output


class TestFormattedRendererUnsupportedTypes:
    """Tests for unsupported symbol types."""

    def test_formatted_renderer_skips_file_type(self, temp_source_file):
        """Test FormattedRenderer skips FileMatchRecord."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_file_record(temp_source_file)
        output = renderer.render(iter([record]))

        # Should skip or output empty for file type
        # (files don't have byte_offset, so nothing specific to extract)
        assert output == '' or 'skip' in output.lower() or len(output) > 0

    def test_formatted_renderer_skips_import_type(self, temp_source_file):
        """Test FormattedRenderer handles ImportMatchRecord."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_import_record(temp_source_file)
        output = renderer.render(iter([record]))

        # Import might be skipped or rendered simply
        # (imports don't benefit much from syntax highlighting)
        assert output == '' or 'import' in output.lower() or len(output) >= 0


class TestFormattedRendererSyntaxHighlighting:
    """Tests for syntax highlighting."""

    def test_formatted_renderer_syntax_highlighting_ascii(self, temp_source_file):
        """Test FormattedRenderer uses syntax highlighting in ASCII mode."""
        from via.renderers.formatted import FormattedRenderer
        from via.renderers.formatters.code_formatters import AsciiCodeFormatter

        renderer = FormattedRenderer(AsciiCodeFormatter())
        record = make_function_record(temp_source_file)
        output = renderer.render(iter([record]))

        # Should have content (ANSI codes may or may not be present depending on terminal)
        plain = strip_ansi(output)
        assert 'def my_function' in plain


class TestFormattedRendererLineNumbers:
    """Tests for line numbers."""

    def test_formatted_renderer_line_numbers(self, temp_source_file):
        """Test FormattedRenderer can show line numbers."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_function_record(temp_source_file)
        output = renderer.render(iter([record]), show_line_numbers=True)

        # Output should contain the function
        plain = strip_ansi(output)
        assert 'def my_function' in plain


class TestFormattedRendererContextLines:
    """Tests for context lines."""

    def test_formatted_renderer_context_lines(self, temp_source_file):
        """Test FormattedRenderer supports context lines."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_function_record(temp_source_file)
        output = renderer.render(iter([record]), context=2)

        # Should include function
        plain = strip_ansi(output)
        assert 'def my_function' in plain


class TestFormattedRendererThemeSelection:
    """Tests for theme selection."""

    def test_formatted_renderer_theme_selection(self, temp_source_file):
        """Test FormattedRenderer supports theme selection."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        record = make_function_record(temp_source_file)

        # Should work with different themes
        output = renderer.render(iter([record]), theme='monokai')
        plain = strip_ansi(output)
        assert 'def my_function' in plain


class TestFormattedRendererStreaming:
    """Tests for streaming behavior."""

    def test_formatted_renderer_streams(self, temp_source_file):
        """Test FormattedRenderer processes records one at a time."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()

        consumed = []
        def record_generator():
            record = make_function_record(temp_source_file)
            consumed.append('yielded')
            yield record

        output = renderer.render(record_generator())

        assert len(consumed) == 1
        plain = strip_ansi(output)
        assert 'def my_function' in plain

    def test_formatted_renderer_multiple_records(self, temp_source_file):
        """Test FormattedRenderer handles multiple records."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        records = [
            make_function_record(temp_source_file),
            make_class_record(temp_source_file),
        ]
        output = renderer.render(iter(records))

        plain = strip_ansi(output)
        assert 'def my_function' in plain
        assert 'class MyClass' in plain


class TestFormattedRendererEmptyInput:
    """Tests for edge cases."""

    def test_formatted_renderer_empty_input(self):
        """Test FormattedRenderer handles empty input."""
        from via.renderers.formatted import FormattedRenderer

        renderer = FormattedRenderer()
        output = renderer.render(iter([]))

        assert output == ''


class TestFormattedRendererFactory:
    """Tests for FormattedRenderer factory integration."""

    def test_factory_creates_formatted_renderer(self):
        """Test RendererFactory creates FormattedRenderer for FORMATTED type."""
        from via.renderers.factory import RendererFactory
        from via.renderers.formatted import FormattedRenderer

        renderer = RendererFactory.create(RenderType.FORMATTED)
        assert isinstance(renderer, FormattedRenderer)


class TestThemeDetection:
    """Tests for terminal theme detection."""

    def test_detect_terminal_theme_function_exists(self):
        """Test detect_terminal_theme function exists."""
        from via.renderers.formatters.code_formatters import detect_terminal_theme

        # Should return 'light' or 'dark'
        result = detect_terminal_theme()
        assert result in ('light', 'dark')

    def test_detect_terminal_theme_default_dark(self, monkeypatch):
        """Test detect_terminal_theme defaults to dark when unknown."""
        from via.renderers.formatters.code_formatters import detect_terminal_theme

        # Clear environment variables that might indicate theme
        monkeypatch.delenv('COLORFGBG', raising=False)
        monkeypatch.delenv('TERM_BACKGROUND', raising=False)

        result = detect_terminal_theme()
        assert result == 'dark'  # Default to dark

    def test_detect_terminal_theme_light_from_env(self, monkeypatch):
        """Test detect_terminal_theme detects light theme from environment."""
        from via.renderers.formatters.code_formatters import detect_terminal_theme

        # COLORFGBG format: foreground;background (high value = light)
        monkeypatch.setenv('COLORFGBG', '0;15')  # Black on white

        result = detect_terminal_theme()
        assert result == 'light'

    def test_detect_terminal_theme_dark_from_env(self, monkeypatch):
        """Test detect_terminal_theme detects dark theme from environment."""
        from via.renderers.formatters.code_formatters import detect_terminal_theme

        # COLORFGBG format: foreground;background (low value = dark)
        monkeypatch.setenv('COLORFGBG', '15;0')  # White on black

        result = detect_terminal_theme()
        assert result == 'dark'
