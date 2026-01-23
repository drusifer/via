"""
Mermaid diagram formatters.

TLDR:
    Formatters for Mermaid classDiagram output. ASCII returns plain text,
    Markdown wraps in code fence, HTML includes mermaid.js for rendering.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""


class MermaidAsciiFormatter:
    """Plain text mermaid syntax formatter."""

    def format_diagram(self, mermaid: str) -> str:
        """Return mermaid syntax as-is.

        Args:
            mermaid: Mermaid diagram code

        Returns:
            Plain mermaid text
        """
        return mermaid


class MermaidMarkdownFormatter:
    """Mermaid in markdown code block formatter."""

    def format_diagram(self, mermaid: str) -> str:
        """Wrap mermaid in markdown code fence.

        Args:
            mermaid: Mermaid diagram code

        Returns:
            Markdown with mermaid code block
        """
        return f"```mermaid\n{mermaid}\n```"


class MermaidHtmlFormatter:
    """Mermaid with HTML + mermaid.js for rendering."""

    def format_diagram(self, mermaid: str) -> str:
        """Generate HTML page with mermaid.js rendering.

        Args:
            mermaid: Mermaid diagram code

        Returns:
            Complete HTML page with mermaid diagram
        """
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Class Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="mermaid">
{mermaid}
    </div>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
</body>
</html>'''
