"""
Renderer utility modules: source extraction helpers for raw and formatted renderers.

TLDR:
    Re-exports extract_source, find_context_start, and find_context_end from
    source_extraction.py. These are the only public symbols in this package.
    Consumed by RawRenderer and FormattedRenderer for byte-offset-based source
    code extraction with optional context line support.

"""

from .source_extraction import extract_source, find_context_end, find_context_start

__all__ = ['extract_source', 'find_context_start', 'find_context_end']
