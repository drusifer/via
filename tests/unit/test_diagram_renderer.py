"""
Tests for DiagramRenderer.

TDD: Tests written first, then implementation.
"""

import pytest
from via.core.match_record import ClassMatchRecord, MethodMatchRecord, RenderType
from via.renderers.diagram import DiagramRenderer
from via.renderers.formatters.diagram_formatters import (
    MermaidAsciiFormatter,
    MermaidHtmlFormatter,
    MermaidMarkdownFormatter,
)


class TestDiagramRendererBasics:
    """Test basic DiagramRenderer properties."""

    def test_diagram_renderer_exists(self):
        """Test DiagramRenderer can be instantiated."""
        renderer = DiagramRenderer(MermaidAsciiFormatter())
        assert renderer is not None

    def test_diagram_renderer_accepts_formatter(self):
        """Test renderer accepts different formatters."""
        ascii_renderer = DiagramRenderer(MermaidAsciiFormatter())
        md_renderer = DiagramRenderer(MermaidMarkdownFormatter())
        html_renderer = DiagramRenderer(MermaidHtmlFormatter())

        assert ascii_renderer.formatter is not None
        assert md_renderer.formatter is not None
        assert html_renderer.formatter is not None


class TestDiagramRendererOutput:
    """Test diagram rendering output."""

    def test_render_single_class(self):
        """Test rendering a single class."""
        renderer = DiagramRenderer(MermaidAsciiFormatter())

        records = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='MyClass',
                qualified_name='module.MyClass',
                file_path='test.py',
                line_number=10,
            )
        ]

        output = renderer.render(iter(records))

        assert 'classDiagram' in output
        assert 'class MyClass' in output

    def test_render_multiple_classes(self):
        """Test rendering multiple classes."""
        renderer = DiagramRenderer(MermaidAsciiFormatter())

        records = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='ClassA',
                qualified_name='module.ClassA',
                file_path='test.py',
                line_number=10,
            ),
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='ClassB',
                qualified_name='module.ClassB',
                file_path='test.py',
                line_number=20,
            ),
        ]

        output = renderer.render(iter(records))

        assert 'classDiagram' in output
        assert 'class ClassA' in output
        assert 'class ClassB' in output

    def test_render_class_with_inheritance(self):
        """Test rendering class with inheritance relationship."""
        renderer = DiagramRenderer(MermaidAsciiFormatter())

        records = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='Parent',
                qualified_name='module.Parent',
                file_path='test.py',
                line_number=10,
            ),
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='Child',
                qualified_name='module.Child',
                file_path='test.py',
                line_number=20,
                base_classes=['Parent'],
            ),
        ]

        output = renderer.render(iter(records))

        assert 'classDiagram' in output
        assert 'class Parent' in output
        assert 'class Child' in output
        # Check inheritance relationship
        assert 'Parent <|-- Child' in output

    def test_render_empty_records(self):
        """Test rendering with no records."""
        renderer = DiagramRenderer(MermaidAsciiFormatter())

        output = renderer.render(iter([]))

        assert 'No classes to diagram' in output

    def test_filters_non_class_records(self):
        """Test that non-class records are filtered out."""
        renderer = DiagramRenderer(MermaidAsciiFormatter())

        records = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='MyClass',
                qualified_name='module.MyClass',
                file_path='test.py',
                line_number=10,
            ),
            MethodMatchRecord(
                symbol_type='method',
                symbol_name='my_method',
                qualified_name='module.MyClass.my_method',
                file_path='test.py',
                line_number=15,
            ),
        ]

        output = renderer.render(iter(records))

        assert 'class MyClass' in output
        # Methods should not appear as separate classes
        assert 'class my_method' not in output


class TestMermaidFormatters:
    """Test Mermaid formatters."""

    def test_ascii_formatter(self):
        """Test ASCII formatter returns plain mermaid."""
        formatter = MermaidAsciiFormatter()
        mermaid = "classDiagram\n    class Foo"

        result = formatter.format_diagram(mermaid)

        assert result == mermaid

    def test_markdown_formatter(self):
        """Test Markdown formatter wraps in code fence."""
        formatter = MermaidMarkdownFormatter()
        mermaid = "classDiagram\n    class Foo"

        result = formatter.format_diagram(mermaid)

        assert result.startswith("```mermaid")
        assert result.endswith("```")
        assert mermaid in result

    def test_html_formatter(self):
        """Test HTML formatter includes mermaid.js."""
        formatter = MermaidHtmlFormatter()
        mermaid = "classDiagram\n    class Foo"

        result = formatter.format_diagram(mermaid)

        assert '<!DOCTYPE html>' in result
        assert 'mermaid' in result
        assert '<div class="mermaid">' in result
        assert mermaid in result


class TestDiagramRendererWithFormatters:
    """Test DiagramRenderer with different formatters."""

    def test_render_with_markdown_formatter(self):
        """Test rendering with Markdown formatter."""
        renderer = DiagramRenderer(MermaidMarkdownFormatter())

        records = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='MyClass',
                qualified_name='module.MyClass',
                file_path='test.py',
                line_number=10,
            )
        ]

        output = renderer.render(iter(records))

        assert output.startswith("```mermaid")
        assert 'classDiagram' in output
        assert output.endswith("```")

    def test_render_with_html_formatter(self):
        """Test rendering with HTML formatter."""
        renderer = DiagramRenderer(MermaidHtmlFormatter())

        records = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='MyClass',
                qualified_name='module.MyClass',
                file_path='test.py',
                line_number=10,
            )
        ]

        output = renderer.render(iter(records))

        assert '<!DOCTYPE html>' in output
        assert 'mermaid.js' in output or 'mermaid' in output
        assert 'classDiagram' in output
