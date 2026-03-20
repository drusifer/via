"""
Parser package for via — exposes language-specific source file parsers.

TLDR:
    Namespace package that groups all language-specific parsers used by the
    via indexing pipeline. It contains no logic of its own; its role is to
    make the parsers sub-tree importable as `via.parsers`.
    Key modules: python_parser (Python AST analysis), markdown_parser
    (Markdown heading/link extraction), registry (parser lookup by file type).
    Consumed by the indexing service via the parser registry; depends on nothing
    inside via at package-init time.
"""
