"""
Diagram renderer for class diagrams.

TLDR:
    Generates Mermaid classDiagram syntax from ClassMatchRecord objects.
    This is the ONLY renderer that MUST materialize all records because
    building inheritance relationships requires seeing all classes first.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Iterator, List

from .base import Renderer
from ..core.match_record import MatchRecord, ClassMatchRecord


class DiagramRenderer(Renderer):
    """UML class diagram renderer using Mermaid syntax.

    This renderer materializes all records to build complete class
    inheritance relationships. It filters for ClassMatchRecord only.
    """

    HELP = "-oD, --diagram: Mermaid class diagram (classes only)"
    FLAG = "-oD"

    def __init__(self, formatter):
        """Initialize with a formatter.

        Args:
            formatter: A formatter with format_diagram(mermaid) method
        """
        self.formatter = formatter

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render class diagram.

        Materializes records to build complete inheritance tree.

        Args:
            records: Iterator of MatchRecord objects
            **options: Additional options (unused)

        Returns:
            Formatted Mermaid diagram string
        """
        # Materialize - required for diagram generation
        all_records = list(records)

        # Filter for classes only
        classes = [r for r in all_records if isinstance(r, ClassMatchRecord)]

        if not classes:
            return "No classes to diagram"

        # Generate mermaid syntax
        mermaid = self._generate_mermaid(classes)

        # Apply formatter
        return self.formatter.format_diagram(mermaid)

    def _generate_mermaid(self, classes: List[ClassMatchRecord]) -> str:
        """Generate mermaid classDiagram syntax.

        Args:
            classes: List of ClassMatchRecord objects

        Returns:
            Mermaid classDiagram syntax string
        """
        lines = ['classDiagram']

        # Build class name set for relationship filtering
        class_names = {cls.symbol_name for cls in classes}

        for cls in classes:
            # Class definition
            lines.append(f'    class {cls.symbol_name} {{')

            # Add methods if available
            if cls.methods:
                for method in cls.methods:
                    # Determine visibility prefix
                    if method.startswith('_'):
                        prefix = '-'  # private
                    else:
                        prefix = '+'  # public
                    lines.append(f'        {prefix}{method}()')

            lines.append('    }')

            # Inheritance relationships (only if parent in result set)
            if cls.base_classes:
                for base in cls.base_classes:
                    if base in class_names:
                        lines.append(f'    {base} <|-- {cls.symbol_name}')

        return '\n'.join(lines)
