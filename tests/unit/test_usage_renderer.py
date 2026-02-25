"""
Unit tests for UsageRenderer (docstring extraction).

TLDR:
    Tests for the UsageRenderer that extracts and displays docstrings
    from Python source files for classes, methods, and functions.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
import tempfile

import pytest
from via.core.match_record import (
    ClassMatchRecord,
    FileMatchRecord,
    FunctionMatchRecord,
    MethodMatchRecord,
)
from via.renderers.formatters.usage_formatters import (
    AsciiUsageFormatter,
    DocstringInfo,
    HtmlUsageFormatter,
    MarkdownUsageFormatter,
)
from via.renderers.usage import DOCSTRING_TYPES, UsageRenderer


class TestUsageRendererBasics:
    """Test basic UsageRenderer functionality."""

    def test_usage_renderer_exists(self):
        """UsageRenderer can be instantiated."""
        renderer = UsageRenderer()
        assert renderer is not None

    def test_usage_renderer_has_render_method(self):
        """UsageRenderer has render method."""
        renderer = UsageRenderer()
        assert hasattr(renderer, 'render')
        assert callable(renderer.render)

    def test_usage_renderer_default_formatter(self):
        """UsageRenderer defaults to AsciiUsageFormatter."""
        renderer = UsageRenderer()
        assert isinstance(renderer.formatter, AsciiUsageFormatter)

    def test_usage_renderer_custom_formatter(self):
        """UsageRenderer accepts custom formatter."""
        formatter = MarkdownUsageFormatter()
        renderer = UsageRenderer(formatter=formatter)
        assert renderer.formatter is formatter


class TestDocstringExtraction:
    """Test docstring extraction from Python files."""

    def test_extract_class_docstring(self):
        """Extract docstring from a class."""
        source = '''
class MyClass:
    """This is the class docstring."""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            f.flush()
            temp_path = f.name

        try:
            renderer = UsageRenderer()
            record = ClassMatchRecord(
                symbol_type='class',
                symbol_name='MyClass',
                qualified_name='MyClass',
                file_path=temp_path,
                line_number=2,
            )
            docstring = renderer._extract_docstring(record)
            assert docstring == "This is the class docstring."
        finally:
            os.unlink(temp_path)

    def test_extract_function_docstring(self):
        """Extract docstring from a function."""
        source = '''
def my_function():
    """This is the function docstring."""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            f.flush()
            temp_path = f.name

        try:
            renderer = UsageRenderer()
            record = FunctionMatchRecord(
                symbol_type='function',
                symbol_name='my_function',
                qualified_name='my_function',
                file_path=temp_path,
                line_number=2,
            )
            docstring = renderer._extract_docstring(record)
            assert docstring == "This is the function docstring."
        finally:
            os.unlink(temp_path)

    def test_extract_method_docstring(self):
        """Extract docstring from a method."""
        source = '''
class MyClass:
    def my_method(self):
        """This is the method docstring."""
        pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            f.flush()
            temp_path = f.name

        try:
            renderer = UsageRenderer()
            record = MethodMatchRecord(
                symbol_type='method',
                symbol_name='my_method',
                qualified_name='MyClass.my_method',
                file_path=temp_path,
                line_number=3,
            )
            docstring = renderer._extract_docstring(record)
            assert docstring == "This is the method docstring."
        finally:
            os.unlink(temp_path)

    def test_no_docstring_returns_none(self):
        """Symbol without docstring returns None."""
        source = '''
def no_docs():
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            f.flush()
            temp_path = f.name

        try:
            renderer = UsageRenderer()
            record = FunctionMatchRecord(
                symbol_type='function',
                symbol_name='no_docs',
                qualified_name='no_docs',
                file_path=temp_path,
                line_number=2,
            )
            docstring = renderer._extract_docstring(record)
            assert docstring is None
        finally:
            os.unlink(temp_path)

    def test_multiline_docstring(self):
        """Extract multiline docstring."""
        source = '''
def documented():
    """This is a multiline docstring.

    It has multiple paragraphs.

    Args:
        None

    Returns:
        Nothing
    """
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            f.flush()
            temp_path = f.name

        try:
            renderer = UsageRenderer()
            record = FunctionMatchRecord(
                symbol_type='function',
                symbol_name='documented',
                qualified_name='documented',
                file_path=temp_path,
                line_number=2,
            )
            docstring = renderer._extract_docstring(record)
            assert "multiline docstring" in docstring
            assert "Args:" in docstring
            assert "Returns:" in docstring
        finally:
            os.unlink(temp_path)


class TestUsageRendererOutput:
    """Test UsageRenderer output formatting."""

    def test_render_empty_records(self):
        """Render with empty records returns empty string."""
        renderer = UsageRenderer()
        result = renderer.render(iter([]))
        assert result == ''

    def test_render_single_record_with_docstring(self):
        """Render single record with docstring."""
        source = '''
class TestClass:
    """Test class docstring."""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            f.flush()
            temp_path = f.name

        try:
            renderer = UsageRenderer()
            records = [
                ClassMatchRecord(
                    symbol_type='class',
                    symbol_name='TestClass',
                    qualified_name='TestClass',
                    file_path=temp_path,
                    line_number=2,
                )
            ]
            result = renderer.render(iter(records))
            assert 'TestClass' in result
            assert 'Test class docstring.' in result
        finally:
            os.unlink(temp_path)

    def test_render_skips_unsupported_types(self):
        """Render skips file types that don't have docstrings."""
        renderer = UsageRenderer()
        records = [
            FileMatchRecord(
                symbol_type='filepath',
                symbol_name='test.py',
                qualified_name='test.py',
                file_path='test.py',
                line_number=1,
            )
        ]
        result = renderer.render(iter(records))
        assert result == ''

    def test_render_multiple_records(self):
        """Render multiple records."""
        source = '''
class First:
    """First docstring."""
    pass

class Second:
    """Second docstring."""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            f.flush()
            temp_path = f.name

        try:
            renderer = UsageRenderer()
            records = [
                ClassMatchRecord(
                    symbol_type='class',
                    symbol_name='First',
                    qualified_name='First',
                    file_path=temp_path,
                    line_number=2,
                ),
                ClassMatchRecord(
                    symbol_type='class',
                    symbol_name='Second',
                    qualified_name='Second',
                    file_path=temp_path,
                    line_number=6,
                ),
            ]
            result = renderer.render(iter(records))
            assert 'First docstring.' in result
            assert 'Second docstring.' in result
        finally:
            os.unlink(temp_path)


class TestUsageFormatters:
    """Test different formatter outputs."""

    def test_ascii_formatter_with_docstring(self):
        """AsciiUsageFormatter formats symbol with docstring."""
        formatter = AsciiUsageFormatter()
        info = DocstringInfo(
            symbol_name='my_func',
            symbol_type='function',
            file_path='test.py',
            line_number=10,
            docstring='This is the docstring.'
        )
        result = formatter.format_symbol(info)
        assert '# function my_func' in result
        assert 'test.py:10' in result
        assert 'This is the docstring.' in result

    def test_ascii_formatter_without_docstring(self):
        """AsciiUsageFormatter formats symbol without docstring."""
        formatter = AsciiUsageFormatter()
        info = DocstringInfo(
            symbol_name='my_func',
            symbol_type='function',
            file_path='test.py',
            line_number=10,
            docstring=None
        )
        result = formatter.format_symbol(info)
        assert '# function my_func' in result
        assert '(no docstring)' in result

    def test_markdown_formatter_with_docstring(self):
        """MarkdownUsageFormatter formats symbol with docstring."""
        formatter = MarkdownUsageFormatter()
        info = DocstringInfo(
            symbol_name='MyClass',
            symbol_type='class',
            file_path='module.py',
            line_number=5,
            docstring='Class documentation.'
        )
        result = formatter.format_symbol(info)
        assert '## `MyClass`' in result
        assert 'module.py:5' in result
        assert '```' in result
        assert 'Class documentation.' in result

    def test_html_formatter_with_docstring(self):
        """HtmlUsageFormatter formats symbol with docstring."""
        formatter = HtmlUsageFormatter()
        info = DocstringInfo(
            symbol_name='handler',
            symbol_type='method',
            file_path='views.py',
            line_number=20,
            docstring='Handles the request.'
        )
        result = formatter.format_symbol(info)
        assert '<code>handler</code>' in result
        assert 'views.py:20' in result
        assert '<pre class="docstring">' in result
        assert 'Handles the request.' in result

    def test_html_formatter_escapes_html(self):
        """HtmlUsageFormatter escapes HTML in docstrings."""
        formatter = HtmlUsageFormatter()
        info = DocstringInfo(
            symbol_name='test',
            symbol_type='function',
            file_path='test.py',
            line_number=1,
            docstring='Use <tag> and & symbols.'
        )
        result = formatter.format_symbol(info)
        assert '&lt;tag&gt;' in result
        assert '&' in result


class TestDocstringTypes:
    """Test DOCSTRING_TYPES constant."""

    def test_docstring_types_includes_class(self):
        """DOCSTRING_TYPES includes 'class'."""
        assert 'class' in DOCSTRING_TYPES

    def test_docstring_types_includes_method(self):
        """DOCSTRING_TYPES includes 'method'."""
        assert 'method' in DOCSTRING_TYPES

    def test_docstring_types_includes_function(self):
        """DOCSTRING_TYPES includes 'function'."""
        assert 'function' in DOCSTRING_TYPES

    def test_docstring_types_excludes_file(self):
        """DOCSTRING_TYPES excludes 'filepath'."""
        assert 'filepath' not in DOCSTRING_TYPES
