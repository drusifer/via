"""
JS/TS function-body AST analyzers.

TLDR:
    Private module providing _BodyAnalyzer ABC and three concrete subclasses
    (_CallBodyAnalyzer, _HttpCallBodyAnalyzer, _StringConstantBodyAnalyzer) that
    recursively walk a tree-sitter AST function body and collect code entities
    without crossing nested function boundaries (_FUNCTION_BOUNDARIES).
    Extracted from javascript_parser.py to keep that module focused on top-level
    dispatch. Only javascript_parser.py should import from this module.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""

from abc import ABC, abstractmethod
from typing import Optional

from .base import CallEntity, StringConstantEntity


# ---------------------------------------------------------------------------
# Shared constants and helpers
# ---------------------------------------------------------------------------

# Node types that define a new function scope — we stop recursing into these
# when collecting entities for an outer function to prevent mis-attribution.
_FUNCTION_BOUNDARIES = frozenset({
    'function_declaration',
    'function',
    'arrow_function',
    'method_definition',
})


def _node_text(node, content: bytes) -> str:
    """Extract UTF-8 text for a tree-sitter node from raw content bytes."""
    return content[node.start_byte:node.end_byte].decode('utf-8', errors='replace')


def _node_line_start(node) -> int:
    """Return the 1-indexed start line for a tree-sitter node."""
    return node.start_point[0] + 1


def _normalize_js_string(text: str) -> str:
    """Strip common JS string delimiters for matching/display."""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"', '`'):
        return text[1:-1]
    return text


def _get_callee_name(call_node, content: bytes) -> Optional[str]:
    """Return the callee name from a call_expression node, or None to skip."""
    func_node = call_node.child_by_field_name('function')
    if func_node is None:
        return None
    if func_node.type == 'identifier':
        return _node_text(func_node, content)
    if func_node.type == 'member_expression':
        return _node_text(func_node, content)
    return None


def _get_http_target(call_node, content: bytes) -> Optional[str]:
    """Return a static HTTP target URL/path for supported JS HTTP patterns."""
    func_node = call_node.child_by_field_name('function')
    args_node = call_node.child_by_field_name('arguments')
    if func_node is None or args_node is None:
        return None

    func_text = _node_text(func_node, content)
    named_args = [child for child in args_node.named_children]

    if func_text in ('fetch', 'axios', 'axios.get', 'axios.post', 'axios.put', 'axios.delete'):
        if not named_args:
            return None
        first = named_args[0]
        if first.type in ('string', 'template_string'):
            return _normalize_js_string(_node_text(first, content)) or None
    return None


# ---------------------------------------------------------------------------
# Body analyzer ABC and concrete subclasses
# ---------------------------------------------------------------------------

class _BodyAnalyzer(ABC):
    """Walk a JS/TS AST function body, collecting entities without crossing
    nested function boundaries.

    Subclasses implement _walk() with their specific node-matching logic.
    The shared entry point is collect().
    """

    def collect(
        self,
        root_node,
        content: bytes,
        *,
        caller_name: str,
        caller_type: str,
        caller_parent: Optional[str],
    ) -> list:
        """Walk *root_node* and return all collected entities."""
        out: list = []
        self._walk(root_node, content, caller_name, caller_type, caller_parent, out)
        return out

    @abstractmethod
    def _walk(
        self,
        node,
        content: bytes,
        caller_name: str,
        caller_type: str,
        caller_parent: Optional[str],
        out: list,
    ) -> None:
        """Subclass implements the specific node-matching and recursion logic."""


class _CallBodyAnalyzer(_BodyAnalyzer):
    """Collect all JS/TS function and method call expressions."""

    def _walk(self, node, content, caller_name, caller_type, caller_parent, out):
        if node.type == 'call_expression':
            callee = _get_callee_name(node, content)
            if callee:
                out.append(CallEntity(
                    caller_name=caller_name,
                    callee_name=callee,
                    line_number=_node_line_start(node),
                    byte_offset=node.start_byte,
                    byte_length=node.end_byte - node.start_byte,
                    caller_type=caller_type,
                    caller_parent=caller_parent,
                ))
            # Recurse into arguments for chained calls and callbacks
            args = node.child_by_field_name('arguments')
            if args:
                self._walk(args, content, caller_name, caller_type, caller_parent, out)
            return

        for child in node.children:
            if child.type == 'call_expression':
                callee = _get_callee_name(child, content)
                if callee:
                    out.append(CallEntity(
                        caller_name=caller_name,
                        callee_name=callee,
                        line_number=_node_line_start(child),
                        byte_offset=child.start_byte,
                        byte_length=child.end_byte - child.start_byte,
                        caller_type=caller_type,
                        caller_parent=caller_parent,
                    ))
                args = child.child_by_field_name('arguments')
                if args:
                    self._walk(args, content, caller_name, caller_type, caller_parent, out)
            elif child.type not in _FUNCTION_BOUNDARIES:
                self._walk(child, content, caller_name, caller_type, caller_parent, out)


class _HttpCallBodyAnalyzer(_BodyAnalyzer):
    """Collect HTTP call expressions (fetch, axios, XMLHttpRequest)."""

    def _walk(self, node, content, caller_name, caller_type, caller_parent, out):
        if node.type == 'call_expression':
            target = _get_http_target(node, content)
            if target:
                out.append(CallEntity(
                    caller_name=caller_name,
                    callee_name=target,
                    line_number=_node_line_start(node),
                    byte_offset=node.start_byte,
                    byte_length=node.end_byte - node.start_byte,
                    caller_type=caller_type,
                    caller_parent=caller_parent,
                ))
            args = node.child_by_field_name('arguments')
            if args:
                self._walk(args, content, caller_name, caller_type, caller_parent, out)
            return

        for child in node.children:
            self._visit_child(child, content, caller_name, caller_type, caller_parent, out)

    def _visit_child(self, child, content, caller_name, caller_type, caller_parent, out):
        if child.type == 'call_expression':
            target = _get_http_target(child, content)
            if target:
                out.append(CallEntity(
                    caller_name=caller_name,
                    callee_name=target,
                    line_number=_node_line_start(child),
                    byte_offset=child.start_byte,
                    byte_length=child.end_byte - child.start_byte,
                    caller_type=caller_type,
                    caller_parent=caller_parent,
                ))
            args = child.child_by_field_name('arguments')
            if args:
                self._walk(args, content, caller_name, caller_type, caller_parent, out)
        elif child.type == 'new_expression':
            ctor = child.child_by_field_name('constructor')
            if ctor and _node_text(ctor, content) == 'XMLHttpRequest':
                self._walk(child, content, caller_name, caller_type, caller_parent, out)
        elif child.type not in _FUNCTION_BOUNDARIES:
            self._walk(child, content, caller_name, caller_type, caller_parent, out)


class _StringConstantBodyAnalyzer(_BodyAnalyzer):
    """Collect string literal constants within a function or method body."""

    def _walk(self, node, content, caller_name, caller_type, caller_parent, out):
        if node.type in ('string', 'template_string'):
            value = _normalize_js_string(_node_text(node, content))
            if value:
                out.append(StringConstantEntity(
                    value=value,
                    line_number=_node_line_start(node),
                    byte_offset=node.start_byte,
                    byte_length=node.end_byte - node.start_byte,
                    owner_name=caller_name,
                    owner_type=caller_type,
                    owner_parent=caller_parent,
                ))
            return

        for child in node.children:
            if child.type in ('string', 'template_string'):
                value = _normalize_js_string(_node_text(child, content))
                if value:
                    out.append(StringConstantEntity(
                        value=value,
                        line_number=_node_line_start(child),
                        byte_offset=child.start_byte,
                        byte_length=child.end_byte - child.start_byte,
                        owner_name=caller_name,
                        owner_type=caller_type,
                        owner_parent=caller_parent,
                    ))
            elif child.type not in _FUNCTION_BOUNDARIES:
                self._walk(child, content, caller_name, caller_type, caller_parent, out)
