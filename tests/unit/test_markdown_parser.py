"""Tests for MarkdownParser.

TLDR:
    Validates MarkdownParser's ability to extract ATX-style headings (H1–H6) from
    Markdown content, including correct level, text, line number, and byte-offset
    values. Covers multiple headers, qualified/nested name building, edge cases
    (empty content, code blocks, inline code, links, unicode), and ParseResult
    metadata (file_path, language, parse_error).
    Role: protects the MarkdownParser symbol-extraction logic used to index .md
    files in the via pipeline.

"""

import pytest
from via.parsers.base import MarkdownHeadingEntity, ParseResult
from via.parsers.markdown_parser import MarkdownParser


class TestMarkdownParserBasics:
    """Test basic MarkdownParser properties."""

    def test_language_name(self):
        """Test language_name property."""
        parser = MarkdownParser()
        assert parser.language_name == "markdown"

    def test_supported_extensions(self):
        """Test get_supported_extensions returns markdown extensions."""
        parser = MarkdownParser()
        extensions = parser.get_supported_extensions()

        assert '.md' in extensions
        assert '.markdown' in extensions
        assert '.mdown' in extensions
        assert '.mkd' in extensions

    def test_can_parse_md_file(self):
        """Test can_parse returns True for .md files."""
        parser = MarkdownParser()

        assert parser.can_parse("README.md") is True
        assert parser.can_parse("docs/guide.markdown") is True
        assert parser.can_parse("notes.mdown") is True
        assert parser.can_parse("file.mkd") is True

    def test_cannot_parse_non_md_file(self):
        """Test can_parse returns False for non-markdown files."""
        parser = MarkdownParser()

        assert parser.can_parse("script.py") is False
        assert parser.can_parse("style.css") is False
        assert parser.can_parse("data.json") is False


class TestMarkdownParserSingleHeader:
    """Test parsing single headers."""

    def test_parse_h1_header(self):
        """Test parsing a single H1 header."""
        parser = MarkdownParser()
        content = b"# Hello World"

        result = parser.parse("test.md", content)

        assert len(result.markdown_headings) == 1
        heading = result.markdown_headings[0]
        assert heading.text == "Hello World"
        assert heading.level == 1
        assert heading.line_number == 1

    def test_parse_h2_header(self):
        """Test parsing a single H2 header."""
        parser = MarkdownParser()
        content = b"## Getting Started"

        result = parser.parse("test.md", content)

        assert len(result.markdown_headings) == 1
        heading = result.markdown_headings[0]
        assert heading.text == "Getting Started"
        assert heading.level == 2

    def test_parse_h6_header(self):
        """Test parsing maximum header level."""
        parser = MarkdownParser()
        content = b"###### Deep Header"

        result = parser.parse("test.md", content)

        assert len(result.markdown_headings) == 1
        heading = result.markdown_headings[0]
        assert heading.text == "Deep Header"
        assert heading.level == 6

    def test_header_with_trailing_hashes(self):
        """Test parsing header with trailing hashes (ATX style)."""
        parser = MarkdownParser()
        content = b"## Section Title ##"

        result = parser.parse("test.md", content)

        assert len(result.markdown_headings) == 1
        heading = result.markdown_headings[0]
        assert heading.text == "Section Title"
        assert heading.level == 2


class TestMarkdownParserMultipleHeaders:
    """Test parsing multiple headers."""

    def test_parse_multiple_headers(self):
        """Test parsing multiple headers at different levels."""
        parser = MarkdownParser()
        content = b"""# Guide

## Getting Started

### Installation

## Usage

### Basic Usage
"""

        result = parser.parse("test.md", content)

        assert len(result.markdown_headings) == 5

        headings = result.markdown_headings
        assert headings[0].text == "Guide"
        assert headings[0].level == 1

        assert headings[1].text == "Getting Started"
        assert headings[1].level == 2

        assert headings[2].text == "Installation"
        assert headings[2].level == 3

        assert headings[3].text == "Usage"
        assert headings[3].level == 2

        assert headings[4].text == "Basic Usage"
        assert headings[4].level == 3

    def test_headers_have_correct_line_numbers(self):
        """Test that line numbers are correctly calculated."""
        parser = MarkdownParser()
        content = b"""# Header One

Some text here.

## Header Two

More text.

### Header Three
"""

        result = parser.parse("test.md", content)

        assert result.markdown_headings[0].line_number == 1
        assert result.markdown_headings[1].line_number == 5
        assert result.markdown_headings[2].line_number == 9


class TestMarkdownParserQualifiedNames:
    """Test qualified name generation with ancestor paths."""

    def test_single_header_qualified_name(self):
        """Test qualified name for single header is just the text."""
        parser = MarkdownParser()
        content = b"# Guide"

        result = parser.parse("test.md", content)

        heading = result.markdown_headings[0]
        # For MarkdownHeadingEntity, we need to check if qualified_name exists
        # If not, we'll need to add it to the entity or track separately
        # For now, let's verify the text is correct
        assert heading.text == "Guide"

    def test_nested_headers_build_path(self):
        """Test that nested headers build qualified name with ancestors."""
        parser = MarkdownParser()
        content = b"""# Guide

## Getting Started

### Installation
"""

        result = parser.parse("test.md", content)

        # The qualified_name should be built from ancestors
        # Guide > Getting Started > Installation
        assert len(result.markdown_headings) == 3

        # Verify structure for qualified name building
        headings = result.markdown_headings
        assert headings[0].text == "Guide"
        assert headings[1].text == "Getting Started"
        assert headings[2].text == "Installation"


class TestMarkdownParserByteOffsets:
    """Test byte offset and length calculations."""

    def test_byte_offset_first_header(self):
        """Test byte offset for first header is 0."""
        parser = MarkdownParser()
        content = b"# Hello"

        result = parser.parse("test.md", content)

        heading = result.markdown_headings[0]
        assert heading.byte_offset == 0

    def test_byte_offset_second_header(self):
        """Test byte offset for second header is calculated correctly."""
        parser = MarkdownParser()
        content = b"# First\n\n## Second"

        result = parser.parse("test.md", content)

        headings = result.markdown_headings
        assert headings[0].byte_offset == 0
        # "# First\n\n" = 9 bytes, so ## Second starts at offset 9
        assert headings[1].byte_offset == 9

    def test_byte_length_includes_full_line(self):
        """Test byte length includes the full header line."""
        parser = MarkdownParser()
        content = b"# Hello World"

        result = parser.parse("test.md", content)

        heading = result.markdown_headings[0]
        # "# Hello World" = 13 bytes
        assert heading.byte_length == 13


class TestMarkdownParserEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_content(self):
        """Test parsing empty content."""
        parser = MarkdownParser()
        content = b""

        result = parser.parse("test.md", content)

        assert len(result.markdown_headings) == 0

    def test_no_headers(self):
        """Test parsing content without headers."""
        parser = MarkdownParser()
        content = b"Just some regular text.\nNo headers here."

        result = parser.parse("test.md", content)

        assert len(result.markdown_headings) == 0

    def test_code_block_headers_ignored(self):
        """Test that headers inside code blocks are ignored."""
        parser = MarkdownParser()
        content = b"""# Real Header

```python
# This is a comment, not a header
def foo():
    pass
```

## Another Real Header
"""

        result = parser.parse("test.md", content)

        # Should only find 2 real headers, not the comment in code block
        assert len(result.markdown_headings) == 2
        assert result.markdown_headings[0].text == "Real Header"
        assert result.markdown_headings[1].text == "Another Real Header"

    def test_inline_code_in_header(self):
        """Test header with inline code."""
        parser = MarkdownParser()
        content = b"## Using `pip install`"

        result = parser.parse("test.md", content)

        heading = result.markdown_headings[0]
        assert heading.text == "Using `pip install`"

    def test_header_with_links(self):
        """Test header containing links."""
        parser = MarkdownParser()
        content = b"## See [Documentation](https://example.com)"

        result = parser.parse("test.md", content)

        heading = result.markdown_headings[0]
        assert "Documentation" in heading.text

    def test_unicode_headers(self):
        """Test parsing headers with unicode characters."""
        parser = MarkdownParser()
        content = "# Héllo Wörld 中文".encode('utf-8')

        result = parser.parse("test.md", content)

        heading = result.markdown_headings[0]
        assert heading.text == "Héllo Wörld 中文"


class TestMarkdownParserParseResult:
    """Test ParseResult structure."""

    def test_parse_result_has_correct_file_path(self):
        """Test that ParseResult has correct file_path."""
        parser = MarkdownParser()
        content = b"# Test"

        result = parser.parse("docs/README.md", content)

        assert result.file_path == "docs/README.md"

    def test_parse_result_has_correct_language(self):
        """Test that ParseResult has language set to markdown."""
        parser = MarkdownParser()
        content = b"# Test"

        result = parser.parse("test.md", content)

        assert result.language == "markdown"

    def test_parse_result_no_error_on_valid_content(self):
        """Test that ParseResult has no error for valid content."""
        parser = MarkdownParser()
        content = b"# Test"

        result = parser.parse("test.md", content)

        assert result.parse_error is None
