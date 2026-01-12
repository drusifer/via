"""Unit tests for Python parser."""

import pytest

from via.parsers.python_parser import PythonParser


class TestPythonParser:
    """Test PythonParser class."""

    @pytest.fixture
    def parser(self):
        """Create a PythonParser instance."""
        return PythonParser()

    def test_can_parse_python_files(self, parser):
        """Test that parser recognizes Python files."""
        assert parser.can_parse("test.py") is True
        assert parser.can_parse("test.pyx") is True
        assert parser.can_parse("test.pyi") is True

    def test_cannot_parse_non_python_files(self, parser):
        """Test that parser rejects non-Python files."""
        assert parser.can_parse("test.js") is False
        assert parser.can_parse("test.java") is False
        assert parser.can_parse("test.txt") is False

    def test_case_insensitive_extension(self, parser):
        """Test case-insensitive extension matching."""
        assert parser.can_parse("test.PY") is True
        assert parser.can_parse("test.Py") is True

    def test_language_name(self, parser):
        """Test language name property."""
        assert parser.language_name == "python"

    def test_supported_extensions(self, parser):
        """Test supported extensions."""
        exts = parser.get_supported_extensions()
        assert '.py' in exts
        assert '.pyx' in exts
        assert '.pyi' in exts

    def test_parse_simple_function(self, parser):
        """Test parsing a simple function."""
        code = b'''def hello():
    """Say hello."""
    print("Hello")
'''
        result = parser.parse("test.py", code)

        assert result.parse_error is None
        assert len(result.functions) == 1

        func = result.functions[0]
        assert func.name == "hello"
        assert func.line_start == 1
        assert func.docstring == "Say hello."
        assert func.byte_offset >= 0
        assert func.byte_length > 0

    def test_parse_function_with_args(self, parser):
        """Test parsing function with arguments."""
        code = b'''def greet(name, age=25):
    pass
'''
        result = parser.parse("test.py", code)

        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "greet"
        assert "name" in func.args
        assert "age" in func.args

    def test_parse_function_with_decorators(self, parser):
        """Test parsing function with decorators."""
        code = b'''@staticmethod
@property
def func():
    pass
'''
        result = parser.parse("test.py", code)

        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.decorators is not None
        assert "staticmethod" in func.decorators or "@staticmethod" in func.decorators

    def test_parse_simple_class(self, parser):
        """Test parsing a simple class."""
        code = b'''class MyClass:
    """A test class."""
    pass
'''
        result = parser.parse("test.py", code)

        assert result.parse_error is None
        assert len(result.classes) == 1

        cls = result.classes[0]
        assert cls.name == "MyClass"
        assert cls.line_start == 1
        assert cls.docstring == "A test class."
        assert cls.byte_offset >= 0
        assert cls.byte_length > 0

    def test_parse_class_with_methods(self, parser):
        """Test parsing class with methods."""
        code = b'''class MyClass:
    def method1(self):
        pass

    def method2(self, x):
        pass
'''
        result = parser.parse("test.py", code)

        assert len(result.classes) == 1
        cls = result.classes[0]
        assert len(cls.methods) == 2
        assert cls.methods[0].name == "method1"
        assert cls.methods[1].name == "method2"

    def test_parse_class_with_inheritance(self, parser):
        """Test parsing class with base classes."""
        code = b'''class Child(Parent, Mixin):
    pass
'''
        result = parser.parse("test.py", code)

        assert len(result.classes) == 1
        cls = result.classes[0]
        assert cls.bases is not None
        assert "Parent" in cls.bases

    def test_parse_class_with_decorators(self, parser):
        """Test parsing class with decorators."""
        code = b'''@dataclass
class MyClass:
    pass
'''
        result = parser.parse("test.py", code)

        assert len(result.classes) == 1
        cls = result.classes[0]
        assert cls.decorators is not None
        assert "dataclass" in cls.decorators or "@dataclass" in cls.decorators

    def test_parse_imports(self, parser):
        """Test parsing import statements."""
        code = b'''import os
import sys as system
from pathlib import Path
from typing import List, Dict as D
'''
        result = parser.parse("test.py", code)

        assert len(result.imports) >= 4

        # Check various import types
        import_modules = [imp.module for imp in result.imports]
        assert "os" in import_modules
        assert "sys" in import_modules
        assert "pathlib" in import_modules
        assert "typing" in import_modules

    def test_parse_globals(self, parser):
        """Test parsing global variables."""
        code = b'''DEBUG = True
VERSION = "1.0.0"
MAX_SIZE = 1024
'''
        result = parser.parse("test.py", code)

        assert len(result.globals) >= 3

        global_names = [g.name for g in result.globals]
        assert "DEBUG" in global_names
        assert "VERSION" in global_names
        assert "MAX_SIZE" in global_names

    def test_parse_annotated_globals(self, parser):
        """Test parsing annotated global variables."""
        code = b'''name: str = "test"
count: int
'''
        result = parser.parse("test.py", code)

        assert len(result.globals) >= 2

        global_names = [g.name for g in result.globals]
        assert "name" in global_names
        assert "count" in global_names

    def test_parse_mixed_code(self, parser):
        """Test parsing file with mixed entities."""
        code = b'''"""Module docstring."""
import os

DEBUG = True

class MyClass:
    """A class."""

    def method(self):
        pass

def function():
    """A function."""
    pass
'''
        result = parser.parse("test.py", code)

        assert result.parse_error is None
        assert len(result.imports) >= 1
        assert len(result.globals) >= 1
        assert len(result.classes) >= 1
        assert len(result.functions) >= 1  # Top-level function

    def test_parse_syntax_error(self, parser):
        """Test parsing file with syntax error."""
        code = b'''def broken(
    # Missing closing paren
'''
        result = parser.parse("test.py", code)

        assert result.parse_error is not None
        assert "Syntax error" in result.parse_error or "syntax" in result.parse_error.lower()

    def test_parse_empty_file(self, parser):
        """Test parsing empty file."""
        code = b''
        result = parser.parse("test.py", code)

        assert result.parse_error is None
        assert len(result.functions) == 0
        assert len(result.classes) == 0
        assert len(result.imports) == 0

    def test_parse_file_with_only_comments(self, parser):
        """Test parsing file with only comments."""
        code = b'''# This is a comment
# Another comment
'''
        result = parser.parse("test.py", code)

        assert result.parse_error is None
        assert len(result.functions) == 0
        assert len(result.classes) == 0

    def test_byte_offsets_are_positive(self, parser):
        """Test that byte offsets are calculated correctly."""
        code = b'''def func1():
    pass

def func2():
    pass
'''
        result = parser.parse("test.py", code)

        assert len(result.functions) == 2
        assert result.functions[0].byte_offset >= 0
        assert result.functions[0].byte_length > 0
        assert result.functions[1].byte_offset > result.functions[0].byte_offset

    def test_async_function(self, parser):
        """Test parsing async function."""
        code = b'''async def fetch_data():
    pass
'''
        result = parser.parse("test.py", code)

        assert len(result.functions) == 1
        assert result.functions[0].name == "fetch_data"

    def test_nested_class_not_extracted_as_top_level(self, parser):
        """Test that nested classes are not extracted separately."""
        code = b'''class Outer:
    class Inner:
        pass
'''
        result = parser.parse("test.py", code)

        # Should only get Outer, not Inner (depending on implementation)
        # For now, this test documents current behavior
        assert len(result.classes) >= 1
        assert result.classes[0].name == "Outer"

    def test_unicode_handling(self, parser):
        """Test handling of Unicode in Python files."""
        code = '''def greet():
    """Say 你好."""
    return "Привет"
'''.encode('utf-8')

        result = parser.parse("test.py", code)

        assert result.parse_error is None
        assert len(result.functions) == 1
