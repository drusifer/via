"""Unit tests for parser registry."""

import pytest

from via.parsers.base import ParserABC, ParseResult
from via.parsers.registry import ParserRegistry


class MockPythonParser(ParserABC):
    """Mock Python parser for testing."""

    def can_parse(self, file_path: str) -> bool:
        return file_path.endswith(('.py', '.pyx', '.pyi'))

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        return ParseResult(file_path=file_path, language="python")

    def get_supported_extensions(self) -> set:
        return {'.py', '.pyx', '.pyi'}

    @property
    def language_name(self) -> str:
        return "python"


class MockJavaScriptParser(ParserABC):
    """Mock JavaScript parser for testing."""

    def can_parse(self, file_path: str) -> bool:
        return file_path.endswith(('.js', '.jsx', '.ts', '.tsx'))

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        return ParseResult(file_path=file_path, language="javascript")

    def get_supported_extensions(self) -> set:
        return {'.js', '.jsx', '.ts', '.tsx'}

    @property
    def language_name(self) -> str:
        return "javascript"


class TestParserRegistry:
    """Test ParserRegistry class."""

    def test_register_parser(self):
        """Test registering a parser."""
        registry = ParserRegistry()
        parser = MockPythonParser()

        registry.register(parser)

        assert len(registry.get_all_parsers()) == 1
        assert registry.get_all_parsers()[0] == parser

    def test_register_parser_class(self):
        """Test registering a parser class."""
        registry = ParserRegistry()

        registry.register_class(MockPythonParser)

        assert len(registry.get_all_parsers()) == 1
        assert isinstance(registry.get_all_parsers()[0], MockPythonParser)

    def test_get_parser_by_extension(self):
        """Test getting parser by file extension."""
        registry = ParserRegistry()
        python_parser = MockPythonParser()
        js_parser = MockJavaScriptParser()

        registry.register(python_parser)
        registry.register(js_parser)

        # Test Python files
        assert registry.get_parser("test.py") == python_parser
        assert registry.get_parser("test.pyx") == python_parser
        assert registry.get_parser("test.pyi") == python_parser

        # Test JavaScript files
        assert registry.get_parser("test.js") == js_parser
        assert registry.get_parser("test.jsx") == js_parser
        assert registry.get_parser("test.ts") == js_parser

    def test_get_parser_case_insensitive(self):
        """Test that extension lookup is case-insensitive."""
        registry = ParserRegistry()
        parser = MockPythonParser()
        registry.register(parser)

        assert registry.get_parser("test.PY") == parser
        assert registry.get_parser("test.Py") == parser
        assert registry.get_parser("test.py") == parser

    def test_get_parser_no_match(self):
        """Test getting parser when no match exists."""
        registry = ParserRegistry()
        parser = MockPythonParser()
        registry.register(parser)

        assert registry.get_parser("test.java") is None
        assert registry.get_parser("test.cpp") is None

    def test_get_supported_extensions(self):
        """Test getting all supported extensions."""
        registry = ParserRegistry()
        registry.register(MockPythonParser())
        registry.register(MockJavaScriptParser())

        extensions = registry.get_supported_extensions()

        assert '.py' in extensions
        assert '.pyx' in extensions
        assert '.pyi' in extensions
        assert '.js' in extensions
        assert '.jsx' in extensions
        assert '.ts' in extensions
        assert '.tsx' in extensions
        assert len(extensions) == 7

    def test_multiple_parsers_same_extension(self):
        """Test that last registered parser wins for an extension."""
        registry = ParserRegistry()

        # Create two parsers with overlapping extensions
        class Parser1(ParserABC):
            def can_parse(self, file_path: str) -> bool:
                return file_path.endswith('.py')
            def parse(self, file_path: str, content: bytes) -> ParseResult:
                return ParseResult(file_path=file_path, language="python1")
            def get_supported_extensions(self) -> set:
                return {'.py'}
            @property
            def language_name(self) -> str:
                return "python1"

        class Parser2(ParserABC):
            def can_parse(self, file_path: str) -> bool:
                return file_path.endswith('.py')
            def parse(self, file_path: str, content: bytes) -> ParseResult:
                return ParseResult(file_path=file_path, language="python2")
            def get_supported_extensions(self) -> set:
                return {'.py'}
            @property
            def language_name(self) -> str:
                return "python2"

        parser1 = Parser1()
        parser2 = Parser2()

        registry.register(parser1)
        registry.register(parser2)

        # Last registered wins
        assert registry.get_parser("test.py") == parser2

    def test_get_all_parsers_returns_copy(self):
        """Test that get_all_parsers returns a copy."""
        registry = ParserRegistry()
        parser = MockPythonParser()
        registry.register(parser)

        parsers1 = registry.get_all_parsers()
        parsers2 = registry.get_all_parsers()

        assert parsers1 is not parsers2
        assert parsers1 == parsers2
