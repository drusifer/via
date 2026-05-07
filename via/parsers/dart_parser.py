"""Dart language parser using tree-sitter."""

from pathlib import Path
from typing import Optional, Set

from .base import (
    CallEntity,
    ClassEntity,
    FunctionEntity,
    GlobalEntity,
    ImportEntity,
    ParserABC,
    ParseResult,
)

_DART_EXTENSIONS: Set[str] = {'.dart'}
_MAX_SIZE = 10 * 1024 * 1024


class DartParser(ParserABC):
    """Parser for Dart source files using tree-sitter-language-pack."""

    _parser = None
    _language = None

    @property
    def language_name(self) -> str:
        """Return the parser language name."""
        return 'dart'

    def can_parse(self, file_path: str) -> bool:
        """Return True iff the file extension is `.dart`."""
        return Path(file_path).suffix.lower() in _DART_EXTENSIONS

    def get_supported_extensions(self) -> Set[str]:
        """Return supported Dart source extensions."""
        return set(_DART_EXTENSIONS)

    def _get_parser(self):
        """Return a lazily initialized tree-sitter Dart parser."""
        if DartParser._parser is None:
            try:
                import tree_sitter_language_pack as tslp
                from tree_sitter import Parser
            except ImportError as exc:
                raise ImportError(
                    "tree-sitter packages required for Dart parsing. "
                    "Install with: pip install tree-sitter tree-sitter-language-pack"
                ) from exc
            DartParser._language = tslp.get_language('dart')
            DartParser._parser = Parser(DartParser._language)
        return DartParser._parser

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Parse Dart content and extract structural code entities."""
        result = ParseResult(file_path=file_path, language='dart')

        if len(content) > _MAX_SIZE:
            result.parse_error = f"File exceeds {_MAX_SIZE // (1024*1024)}MB parse limit"
            return result

        try:
            parser = self._get_parser()
        except Exception as exc:  # noqa: BLE001
            result.parse_error = str(exc)
            return result

        try:
            tree = parser.parse(content)
        except Exception as exc:  # noqa: BLE001
            result.parse_error = f"tree-sitter parse failed: {exc}"
            return result

        if tree.root_node.has_error:
            result.parse_error = "Syntax errors detected; partial parse returned"

        _extract_top_level_symbols(tree.root_node, content, result)
        return result


def _node_text(node, content: bytes) -> str:
    """Return UTF-8 text for a tree-sitter node."""
    return content[node.start_byte:node.end_byte].decode('utf-8', errors='replace')


def _node_line_start(node) -> int:
    """Return 1-indexed start line."""
    return node.start_point[0] + 1


def _node_line_end(node) -> int:
    """Return 1-indexed end line."""
    return node.end_point[0] + 1


def _first_descendant(node, node_type: str):
    """Return the first descendant node of the given type."""
    if node.type == node_type:
        return node
    for child in node.children:
        found = _first_descendant(child, node_type)
        if found is not None:
            return found
    return None


def _descendants(node, node_type: str):
    """Yield descendant nodes of the given type."""
    if node.type == node_type:
        yield node
    for child in node.children:
        yield from _descendants(child, node_type)


def _first_identifier_before_params(signature_node):
    """Return the first identifier before a Dart parameter list."""
    for child in signature_node.children:
        if child.type == 'formal_parameter_list':
            return None
        if child.type == 'identifier':
            return child
        found = _first_identifier_before_params(child)
        if found is not None:
            return found
    return None


def _strip_dart_string(value: str) -> str:
    """Strip simple Dart string delimiters from an import/export/part URI."""
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
        return value[1:-1]
    return value


def _extract_top_level_symbols(root_node, content: bytes, result: ParseResult) -> None:
    """Extract all supported top-level Dart symbols."""
    children = list(root_node.children)
    for idx, node in enumerate(children):
        if node.type == 'import_or_export':
            _extract_directive(node, content, result)
        elif node.type == 'part_directive':
            _extract_directive(node, content, result)
        elif node.type == 'class_definition':
            result.classes.append(_extract_type_declaration(node, content, result=result))
        elif node.type == 'mixin_declaration':
            result.classes.append(_extract_type_declaration(node, content, 'mixin', result=result))
        elif node.type == 'enum_declaration':
            result.classes.append(_extract_type_declaration(node, content, 'enum', result=result))
        elif node.type == 'extension_declaration':
            result.classes.append(_extract_type_declaration(node, content, 'extension', result=result))
        elif node.type == 'function_signature':
            body = _next_body(children, idx)
            function = _extract_function(node, content, body)
            result.functions.append(function)
            _extract_calls(body, content, result, function.name, 'function')
        elif node.type == 'static_final_declaration_list':
            _extract_globals(node, content, result)


def _next_body(siblings: list, idx: int):
    """Return a following Dart function_body sibling if present."""
    if idx + 1 < len(siblings) and siblings[idx + 1].type == 'function_body':
        return siblings[idx + 1]
    return None


def _extract_directive(node, content: bytes, result: ParseResult) -> None:
    """Extract import/export/part directives as ImportEntity records."""
    string_node = (
        _first_descendant(node, 'string_literal')
        or _first_descendant(node, 'configurable_uri')
        or _first_descendant(node, 'uri')
    )
    if string_node is None:
        return
    result.imports.append(ImportEntity(
        module=_strip_dart_string(_node_text(string_node, content)),
        line_number=_node_line_start(node),
        byte_offset=node.start_byte,
        byte_length=node.end_byte - node.start_byte,
    ))


def _extract_type_declaration(
    node,
    content: bytes,
    subtype: Optional[str] = None,
    result: Optional[ParseResult] = None,
) -> ClassEntity:
    """Extract a class-like Dart declaration."""
    name_node = _first_descendant(node, 'identifier')
    name = _node_text(name_node, content) if name_node is not None else '<anonymous>'
    class_entity = ClassEntity(
        name=name,
        line_start=_node_line_start(node),
        line_end=_node_line_end(node),
        byte_offset=node.start_byte,
        byte_length=node.end_byte - node.start_byte,
        bases=_extract_base_names(node, content),
        symbol_subtype=subtype,
    )
    body = _first_child(node, ('class_body', 'extension_body'))
    if body is not None:
        _extract_methods(body, content, class_entity, result)
    return class_entity


def _first_child(node, node_types: tuple[str, ...]):
    """Return first direct child matching any type."""
    for child in node.children:
        if child.type in node_types:
            return child
    return None


def _extract_base_names(node, content: bytes) -> Optional[str]:
    """Extract extends/with/implements target names from a Dart class."""
    base_nodes = []
    for child in node.children:
        if child.type in ('superclass', 'interfaces'):
            base_nodes.extend(_type_identifiers_excluding_type_args(child))
    names = [_node_text(base, content) for base in base_nodes]
    return ', '.join(names) if names else None


def _type_identifiers_excluding_type_args(node):
    """Yield type identifiers while ignoring generic type argument internals."""
    if node.type == 'type_arguments':
        return
    if node.type == 'type_identifier':
        yield node
    for child in node.children:
        yield from _type_identifiers_excluding_type_args(child)


def _extract_methods(
    body_node,
    content: bytes,
    class_entity: ClassEntity,
    result: Optional[ParseResult],
) -> None:
    """Extract methods and constructors from a Dart class-like body."""
    children = list(body_node.children)
    for idx, child in enumerate(children):
        if child.type == 'method_signature':
            signature = _first_descendant(child, 'function_signature')
            if signature is not None:
                body = _next_body(children, idx)
                method = _extract_function(signature, content, body)
                class_entity.methods.append(method)
                if result is not None:
                    _extract_calls(body, content, result, method.name, 'method', class_entity.name)
        elif child.type == 'declaration':
            constructor = _first_descendant(child, 'constructor_signature')
            constant_constructor = _first_descendant(child, 'constant_constructor_signature')
            constructor_node = constant_constructor or constructor
            if constructor_node is not None:
                class_entity.methods.append(_extract_constructor(constructor_node, content, child))


def _extract_function(signature_node, content: bytes, body_node=None) -> FunctionEntity:
    """Extract a Dart function or method from a function_signature node."""
    name_node = _first_identifier_before_params(signature_node)
    end_node = body_node or signature_node
    return FunctionEntity(
        name=_node_text(name_node, content) if name_node is not None else '<anonymous>',
        line_start=_node_line_start(signature_node),
        line_end=_node_line_end(end_node),
        byte_offset=signature_node.start_byte,
        byte_length=end_node.end_byte - signature_node.start_byte,
    )


def _extract_constructor(constructor_node, content: bytes, declaration_node) -> FunctionEntity:
    """Extract a constructor as a method with constructor subtype."""
    name_parts = []
    for child in constructor_node.children:
        if child.type == 'formal_parameter_list':
            break
        if child.type == 'identifier':
            name_parts.append(_node_text(child, content))
    name = '.'.join(name_parts) if name_parts else '<constructor>'
    return FunctionEntity(
        name=name,
        line_start=_node_line_start(declaration_node),
        line_end=_node_line_end(declaration_node),
        byte_offset=declaration_node.start_byte,
        byte_length=declaration_node.end_byte - declaration_node.start_byte,
        symbol_subtype='constructor',
    )


def _extract_calls(
    body_node,
    content: bytes,
    result: ParseResult,
    caller_name: str,
    caller_type: str,
    caller_parent: Optional[str] = None,
) -> None:
    """Extract simple Dart calls from function and method bodies."""
    if body_node is None:
        return
    for call_node, callee_node in _call_sites(body_node):
        result.calls.append(CallEntity(
            caller_name=caller_name,
            callee_name=_node_text(callee_node, content),
            line_number=_node_line_start(call_node),
            byte_offset=call_node.start_byte,
            byte_length=call_node.end_byte - call_node.start_byte,
            caller_type=caller_type,
            caller_parent=caller_parent,
        ))


def _call_sites(node):
    """Yield simple identifier/selector call sites from a Dart body."""
    children = list(node.children)
    for idx, child in enumerate(children[:-1]):
        if child.type == 'identifier' and children[idx + 1].type == 'selector':
            yield node, child
    for child in children:
        yield from _call_sites(child)


def _extract_globals(node, content: bytes, result: ParseResult) -> None:
    """Extract top-level static/final/const declarations as globals."""
    for decl in _descendants(node, 'static_final_declaration'):
        name_node = _first_descendant(decl, 'identifier')
        if name_node is None:
            continue
        result.globals.append(GlobalEntity(
            name=_node_text(name_node, content),
            line_number=_node_line_start(decl),
            byte_offset=decl.start_byte,
            byte_length=decl.end_byte - decl.start_byte,
        ))
