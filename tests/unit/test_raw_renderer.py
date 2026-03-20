"""
Unit tests for the RawRenderer source-extraction renderer.

TLDR:
    Tests RawRenderer, which reads raw source from files using byte offsets
    stored in MatchRecord objects. Key test classes: TestRawRendererBasic
    (render type and factory), TestRawRendererClassSource /
    TestRawRendererMethodSource / TestRawRendererFunctionSource /
    TestRawRendererFileSource / TestRawRendererImportSource (per-type
    source extraction), TestRawRendererContextLines (before/after context
    via -A/-B/-C), TestRawRendererStreaming (O(1) iterator output),
    TestRawRendererEmptyInput (empty iterator handling),
    TestRawRendererFactory (factory registration).
    Role: protects via.renderers.raw and via.renderers.utils.source_extraction,
    consumed by the pipeline render stage.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
import tempfile
from typing import Iterator

import pytest
from via.core.match_record import (
    ClassMatchRecord,
    FileMatchRecord,
    FunctionMatchRecord,
    ImportMatchRecord,
    MethodMatchRecord,
    RenderType,
)

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
    # Find byte position of "class MyClass:"
    source = SAMPLE_SOURCE.encode('utf-8')
    start = source.find(b'class MyClass:')
    # Find end of class (next def at module level or end)
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
    # Find end (next def or class end)
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


class TestRawRendererBasic:
    """Basic tests for RawRenderer."""

    def test_raw_renderer_exists(self):
        """Test RawRenderer can be imported."""
        from via.renderers.raw import RawRenderer
        renderer = RawRenderer()
        assert renderer is not None

    def test_raw_renderer_is_renderer(self):
        """Test RawRenderer inherits from Renderer."""
        from via.renderers.base import Renderer
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        assert isinstance(renderer, Renderer)


class TestRawRendererClassSource:
    """Tests for extracting class source."""

    def test_raw_renderer_class_source(self, temp_source_file):
        """Test RawRenderer extracts class source code."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = make_class_record(temp_source_file)
        output = renderer.render(iter([record]))

        assert 'class MyClass:' in output
        assert 'def __init__' in output
        assert 'def get_value' in output

    def test_raw_renderer_no_formatting(self, temp_source_file):
        """Test RawRenderer output has no formatting (no ANSI codes)."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = make_class_record(temp_source_file)
        output = renderer.render(iter([record]))

        # No ANSI escape codes
        assert '\x1b[' not in output
        # No line numbers at start of lines
        lines = output.strip().split('\n')
        for line in lines:
            # Line shouldn't start with a number followed by colon/pipe
            assert not (line and line[0].isdigit() and (len(line) > 1 and line[1] in ':|'))


class TestRawRendererMethodSource:
    """Tests for extracting method source."""

    def test_raw_renderer_method_source(self, temp_source_file):
        """Test RawRenderer extracts method source code."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = make_method_record(temp_source_file)
        output = renderer.render(iter([record]))

        assert 'def get_value(self):' in output
        assert 'return self.value' in output


class TestRawRendererFunctionSource:
    """Tests for extracting function source."""

    def test_raw_renderer_function_source(self, temp_source_file):
        """Test RawRenderer extracts function source code."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = make_function_record(temp_source_file)
        output = renderer.render(iter([record]))

        assert 'def my_function(x, y):' in output
        assert 'return x + y' in output


class TestRawRendererFileSource:
    """Tests for extracting entire file content."""

    def test_raw_renderer_file_source(self, temp_source_file):
        """Test RawRenderer reads entire file for FileMatchRecord."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = make_file_record(temp_source_file)
        output = renderer.render(iter([record]))

        # Should contain entire file
        assert '"""Module docstring."""' in output
        assert 'import os' in output
        assert 'class MyClass:' in output
        assert 'def my_function' in output
        assert 'MY_GLOBAL = 42' in output


class TestRawRendererImportSource:
    """Tests for extracting import statements."""

    def test_raw_renderer_import_source(self, temp_source_file):
        """Test RawRenderer extracts import statement."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = make_import_record(temp_source_file)
        output = renderer.render(iter([record]))

        assert 'import os' in output


class TestRawRendererContextLines:
    """Tests for context line extraction."""

    def test_raw_renderer_context_after(self, temp_source_file):
        """Test RawRenderer -A (after context) option."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = make_import_record(temp_source_file)
        # Get import os with 1 line after (import sys)
        output = renderer.render(iter([record]), after_context=1)

        assert 'import os' in output
        assert 'import sys' in output

    def test_raw_renderer_context_before(self, temp_source_file):
        """Test RawRenderer -B (before context) option."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        # Create record for import sys (line 4)
        source = SAMPLE_SOURCE.encode('utf-8')
        start = source.find(b'import sys')
        end = source.find(b'\n\nclass')
        record = ImportMatchRecord(
            symbol_type='import',
            symbol_name='sys',
            qualified_name='sys',
            file_path=temp_source_file,
            line_number=4,
            byte_offset=start,
            byte_length=end - start,
            total_matches=1,
        )
        # Get import sys with 1 line before (import os)
        output = renderer.render(iter([record]), before_context=1)

        assert 'import os' in output
        assert 'import sys' in output

    def test_raw_renderer_context_both(self, temp_source_file):
        """Test RawRenderer -C (context both) option."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        # Create record for import sys
        source = SAMPLE_SOURCE.encode('utf-8')
        start = source.find(b'import sys')
        end = source.find(b'\n\nclass')
        record = ImportMatchRecord(
            symbol_type='import',
            symbol_name='sys',
            qualified_name='sys',
            file_path=temp_source_file,
            line_number=4,
            byte_offset=start,
            byte_length=end - start,
            total_matches=1,
        )
        # Get import sys with 1 line before and after
        output = renderer.render(iter([record]), context=1)

        assert 'import os' in output
        assert 'import sys' in output


class TestRawRendererStreaming:
    """Tests for streaming behavior."""

    def test_raw_renderer_streams(self, temp_source_file):
        """Test RawRenderer processes records one at a time (streaming)."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()

        # Create generator that tracks consumption
        consumed = []
        def record_generator():
            record = make_function_record(temp_source_file)
            consumed.append('yielded')
            yield record

        # Render should consume the iterator
        output = renderer.render(record_generator())

        assert len(consumed) == 1
        assert 'def my_function' in output

    def test_raw_renderer_multiple_records(self, temp_source_file):
        """Test RawRenderer handles multiple records."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        records = [
            make_function_record(temp_source_file),
            make_import_record(temp_source_file),
        ]
        output = renderer.render(iter(records))

        # Both should be in output
        assert 'def my_function' in output
        assert 'import os' in output


class TestRawRendererEmptyInput:
    """Tests for edge cases."""

    def test_raw_renderer_empty_input(self):
        """Test RawRenderer handles empty input."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        output = renderer.render(iter([]))

        assert output == ''

    def test_raw_renderer_missing_file(self):
        """Test RawRenderer handles missing file gracefully."""
        from via.renderers.raw import RawRenderer

        renderer = RawRenderer()
        record = ClassMatchRecord(
            symbol_type='class',
            symbol_name='Test',
            qualified_name='test.Test',
            file_path='/nonexistent/file.py',
            line_number=1,
            byte_offset=0,
            byte_length=10,
            total_matches=1,
        )
        # Should not raise, should handle gracefully
        output = renderer.render(iter([record]))
        # Output should be empty or contain error indicator
        assert output == '' or 'error' in output.lower() or 'not found' in output.lower()


class TestRawRendererFactory:
    """Tests for RawRenderer factory integration."""

    def test_factory_creates_raw_renderer(self):
        """Test RendererFactory creates RawRenderer for RAW type."""
        from via.renderers.factory import RendererFactory
        from via.renderers.raw import RawRenderer

        renderer = RendererFactory.create(RenderType.RAW)
        assert isinstance(renderer, RawRenderer)
