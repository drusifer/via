"""
JavaScript and TypeScript language parser using tree-sitter.

TLDR:
    Implements JavaScriptParser (a ParserABC subclass) that parses .js/.mjs/.cjs/.jsx
    files as JavaScript and .ts/.tsx files as TypeScript using tree-sitter grammars.
    Extracts FunctionEntity (named functions and module-level arrow functions),
    ClassEntity (classes, TS interfaces, TS enums), ImportEntity (ES module imports),
    and GlobalEntity (module-level const/let/var). Partial parse is supported:
    ERROR nodes are skipped and parse_error is set, but valid symbols are returned.
    Tree-sitter Parser objects are initialized lazily once per process.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""

from pathlib import Path
from typing import Optional, Set

from .base import (
    ClassEntity,
    FunctionEntity,
    GlobalEntity,
    ImportEntity,
    ParserABC,
    ParseResult,
    StringConstantEntity,
)
from ._js_body import (
    _node_text,
    _node_line_start,
    _normalize_js_string,
    _CallBodyAnalyzer,
    _HttpCallBodyAnalyzer,
    _StringConstantBodyAnalyzer,
)

# JS/TS extensions
_JS_EXTENSIONS: Set[str] = {'.js', '.mjs', '.cjs', '.jsx'}
_TS_EXTENSIONS: Set[str] = {'.ts', '.tsx'}
_ALL_EXTENSIONS: Set[str] = _JS_EXTENSIONS | _TS_EXTENSIONS

# Maximum file size: 10MB (matches project-wide limit)
_MAX_SIZE = 10 * 1024 * 1024


class JavaScriptParser(ParserABC):
    """Parser for JavaScript and TypeScript files using tree-sitter.

    Tree-sitter Parser objects are NOT picklable and must not be shared across
    multiprocessing workers. This class uses class-level variables (reset to None
    on fork) so each worker process initializes its own parser on first use.
    """

    # Per-process lazy singletons — reset to None after fork()
    _js_parser = None
    _ts_parser = None
    _ts_lang = None
    _js_lang = None

    @property
    def language_name(self) -> str:
        """Get language name (used when file extension is ambiguous)."""
        return 'javascript'

    def _language_for_path(self, file_path: str) -> str:
        """Return 'typescript' or 'javascript' based on file extension."""
        ext = Path(file_path).suffix.lower()
        return 'typescript' if ext in _TS_EXTENSIONS else 'javascript'

    def can_parse(self, file_path: str) -> bool:
        """Return True iff the file extension is a supported JS/TS extension."""
        ext = Path(file_path).suffix.lower()
        return ext in _ALL_EXTENSIONS

    def get_supported_extensions(self) -> Set[str]:
        """Return all supported JS/TS extensions."""
        return set(_ALL_EXTENSIONS)

    def _get_parser(self, language: str):
        """Return a tree-sitter Parser for the given language.

        Initializes lazily once per process. Raises ImportError if tree-sitter
        packages are not installed; raises RuntimeError on grammar load failure.
        """
        if language == 'typescript':
            if JavaScriptParser._ts_parser is None:
                JavaScriptParser._ts_parser, JavaScriptParser._ts_lang = (
                    self._init_ts_parser()
                )
            return JavaScriptParser._ts_parser, JavaScriptParser._ts_lang
        else:
            if JavaScriptParser._js_parser is None:
                JavaScriptParser._js_parser, JavaScriptParser._js_lang = (
                    self._init_js_parser()
                )
            return JavaScriptParser._js_parser, JavaScriptParser._js_lang

    def _init_js_parser(self):
        """Initialize tree-sitter JavaScript parser."""
        try:
            import tree_sitter_javascript as tsjs
            from tree_sitter import Language, Parser
        except ImportError as exc:
            raise ImportError(
                "tree-sitter packages required for JavaScript parsing. "
                "Install with: pip install tree-sitter tree-sitter-javascript"
            ) from exc
        lang = Language(tsjs.language())
        parser = Parser(lang)
        return parser, lang

    def _init_ts_parser(self):
        """Initialize tree-sitter TypeScript parser."""
        try:
            import tree_sitter_typescript as tsts
            from tree_sitter import Language, Parser
        except ImportError as exc:
            raise ImportError(
                "tree-sitter packages required for TypeScript parsing. "
                "Install with: pip install tree-sitter tree-sitter-typescript"
            ) from exc
        lang = Language(tsts.language_typescript())
        parser = Parser(lang)
        return parser, lang

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Parse a JS/TS file and extract code entities.

        Args:
            file_path: Path to the file being parsed
            content: Raw file content as bytes

        Returns:
            ParseResult with extracted functions, classes, imports, globals.
            On syntax errors: parse_error is set but valid symbols are returned.
        """
        language = self._language_for_path(file_path)
        result = ParseResult(file_path=file_path, language=language)

        # Size guard
        if len(content) > _MAX_SIZE:
            result.parse_error = f"File exceeds {_MAX_SIZE // (1024*1024)}MB parse limit"
            return result

        try:
            ts_parser, _lang = self._get_parser(language)
        except ImportError as exc:
            result.parse_error = str(exc)
            return result

        try:
            tree = ts_parser.parse(content)
        except Exception as exc:  # noqa: BLE001
            result.parse_error = f"tree-sitter parse failed: {exc}"
            return result

        # Check for any ERROR nodes (partial parse)
        has_error = _tree_has_error(tree.root_node)
        if has_error:
            result.parse_error = "Syntax errors detected; partial parse returned"

        # Walk the top-level statements
        _extract_symbols(tree.root_node, content, result, file_path)
        result.calls = _extract_all_calls(tree.root_node, content)
        result.http_calls = _extract_all_http_calls(tree.root_node, content)
        result.string_constants = _extract_all_string_constants(tree.root_node, content)
        return result


# ---------------------------------------------------------------------------
# AST walking helpers
# ---------------------------------------------------------------------------

def _tree_has_error(node) -> bool:
    """Return True if the tree contains any ERROR or MISSING nodes."""
    if node.type in ('ERROR', 'MISSING'):
        return True
    return any(_tree_has_error(child) for child in node.children)


def _node_line_end(node) -> int:
    """Return 1-indexed end line."""
    return node.end_point[0] + 1


def _get_body_node(node):
    """Return the body/expression node for a function-like construct."""
    body = node.child_by_field_name('body')
    if body is not None:
        return body
    named = getattr(node, 'named_children', None) or []
    return named[-1] if named else None


class _TopLevelSymbolHandler:
    """Private handler for one family of top-level JS/TS declarations."""

    node_types: tuple[str, ...] = ()

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        """Extract symbols for the given node into the parse result."""
        raise NotImplementedError


class _ImportStatementHandler(_TopLevelSymbolHandler):
    node_types = ('import_statement',)

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        _extract_import(node, content, result)


class _FunctionDeclarationHandler(_TopLevelSymbolHandler):
    node_types = ('function_declaration',)

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        result.functions.append(FunctionEntity(
            name=_node_text(name_node, content),
            line_start=_node_line_start(node),
            line_end=_node_line_end(node),
            byte_offset=node.start_byte,
            byte_length=node.end_byte - node.start_byte,
        ))


class _ClassDeclarationHandler(_TopLevelSymbolHandler):
    node_types = ('class_declaration',)

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        _extract_class(node, content, result)


class _TypeClassDeclarationHandler(_TopLevelSymbolHandler):
    symbol_subtype: Optional[str] = None

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        result.classes.append(ClassEntity(
            name=_node_text(name_node, content),
            line_start=_node_line_start(node),
            line_end=_node_line_end(node),
            byte_offset=node.start_byte,
            byte_length=node.end_byte - node.start_byte,
            symbol_subtype=self.symbol_subtype,
        ))


class _InterfaceDeclarationHandler(_TypeClassDeclarationHandler):
    node_types = ('interface_declaration',)
    symbol_subtype = 'interface'


class _EnumDeclarationHandler(_TypeClassDeclarationHandler):
    node_types = ('enum_declaration',)
    symbol_subtype = 'enum'


class _VariableDeclarationHandler(_TopLevelSymbolHandler):
    node_types = ('lexical_declaration', 'variable_declaration')

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        _extract_var_declaration(node, content, result)


class _TypeAliasDeclarationHandler(_TopLevelSymbolHandler):
    node_types = ('type_alias_declaration',)

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        name_node = node.child_by_field_name('name')
        if not name_node:
            return
        result.globals.append(GlobalEntity(
            name=_node_text(name_node, content),
            line_number=_node_line_start(node),
            byte_offset=node.start_byte,
            byte_length=node.end_byte - node.start_byte,
        ))


class _ExportDeclarationHandler(_TopLevelSymbolHandler):
    node_types = ('export_statement', 'export_default_declaration')

    def extract(self, node, content: bytes, result: ParseResult, dispatcher) -> None:
        for child in node.children:
            dispatcher.extract(child, content, result)


class _TopLevelSymbolExtractor:
    """Dispatch top-level JS/TS declarations to polymorphic handlers."""

    def __init__(self) -> None:
        self._handlers = {}
        for handler in (
            _ImportStatementHandler(),
            _FunctionDeclarationHandler(),
            _ClassDeclarationHandler(),
            _InterfaceDeclarationHandler(),
            _EnumDeclarationHandler(),
            _VariableDeclarationHandler(),
            _TypeAliasDeclarationHandler(),
            _ExportDeclarationHandler(),
        ):
            for node_type in handler.node_types:
                self._handlers[node_type] = handler

    def extract(self, node, content: bytes, result: ParseResult) -> None:
        handler = self._handlers.get(node.type)
        if handler is None:
            return
        handler.extract(node, content, result, self)


_TOP_LEVEL_SYMBOL_EXTRACTOR = _TopLevelSymbolExtractor()


def _extract_symbols(root_node, content: bytes, result: ParseResult, file_path: str) -> None:
    """Walk top-level statements and extract all symbols."""

    for node in root_node.children:
        _TOP_LEVEL_SYMBOL_EXTRACTOR.extract(node, content, result)


def _collect_named_imports(module: str, named_node, stmt_node, content: bytes, imports: list) -> None:
    """Append ImportEntity for each specifier in a named_imports node."""
    for spec in named_node.children:
        if spec.type == 'import_specifier':
            spec_name = spec.child_by_field_name('name')
            if spec_name:
                imports.append(ImportEntity(
                    module=module,
                    name=_node_text(spec_name, content),
                    line_number=_node_line_start(stmt_node),
                    byte_offset=stmt_node.start_byte,
                    byte_length=stmt_node.end_byte - stmt_node.start_byte,
                ))


def _collect_clause_imports(module: str, import_clause, stmt_node, content: bytes, result: ParseResult) -> None:
    """Dispatch each child of an import_clause to the appropriate collector."""
    has_named = False
    for child in import_clause.children:
        if child.type == 'identifier':
            result.imports.append(ImportEntity(
                module=module,
                name=_node_text(child, content),
                line_number=_node_line_start(stmt_node),
                byte_offset=stmt_node.start_byte,
                byte_length=stmt_node.end_byte - stmt_node.start_byte,
            ))
        elif child.type == 'named_imports':
            has_named = True
            _collect_named_imports(module, child, stmt_node, content, result.imports)
        elif child.type == 'namespace_import' and child.named_children:
            result.imports.append(ImportEntity(
                module=module,
                alias=_node_text(child.named_children[0], content),
                line_number=_node_line_start(stmt_node),
                byte_offset=stmt_node.start_byte,
                byte_length=stmt_node.end_byte - stmt_node.start_byte,
            ))
    if not has_named and not any(c.type in ('identifier', 'namespace_import') for c in import_clause.children):
        result.imports.append(ImportEntity(
            module=module,
            line_number=_node_line_start(stmt_node),
            byte_offset=stmt_node.start_byte,
            byte_length=stmt_node.end_byte - stmt_node.start_byte,
        ))


def _extract_import(node, content: bytes, result: ParseResult) -> None:
    """Extract ImportEntity records from an import_statement node."""
    source_node = node.child_by_field_name('source')
    if not source_node:
        return
    module = _node_text(source_node, content).strip('"\'')

    import_clause = next((c for c in node.children if c.type == 'import_clause'), None)
    if not import_clause:
        # `import 'module'` — side-effect only import
        result.imports.append(ImportEntity(
            module=module,
            line_number=_node_line_start(node),
            byte_offset=node.start_byte,
            byte_length=node.end_byte - node.start_byte,
        ))
        return

    _collect_clause_imports(module, import_clause, node, content, result)


def _extract_class(node, content: bytes, result: ParseResult) -> None:
    """Extract a ClassEntity (and its methods) from a class_declaration node."""

    name_node = node.child_by_field_name('name')
    if not name_node:
        return
    name = _node_text(name_node, content)

    # Inheritance: `class Foo extends Bar`
    # class_heritage is not a named field — find by node type
    heritage = next((c for c in node.children if c.type == 'class_heritage'), None)
    bases: Optional[str] = None
    if heritage:
        # heritage text = "extends React.Component" — strip the keyword
        heritage_text = _node_text(heritage, content)
        bases = heritage_text.replace('extends', '', 1).strip()

    cls_entity = ClassEntity(
        name=name,
        line_start=_node_line_start(node),
        line_end=_node_line_end(node),
        byte_offset=node.start_byte,
        byte_length=node.end_byte - node.start_byte,
        bases=bases,
    )

    # Extract methods from class body
    body = node.child_by_field_name('body')
    if body:
        for child in body.children:
            if child.type == 'method_definition':
                method_name_node = child.child_by_field_name('name')
                if method_name_node:
                    method_name = _node_text(method_name_node, content)
                    cls_entity.methods.append(FunctionEntity(
                        name=method_name,
                        line_start=_node_line_start(child),
                        line_end=_node_line_end(child),
                        byte_offset=child.start_byte,
                        byte_length=child.end_byte - child.start_byte,
                    ))

    result.classes.append(cls_entity)


def _extract_var_declaration(node, content: bytes, result: ParseResult) -> None:
    """Extract GlobalEntity or FunctionEntity from a module-level var/const/let."""

    for declarator in node.children:
        if declarator.type != 'variable_declarator':
            continue
        name_node = declarator.child_by_field_name('name')
        value_node = declarator.child_by_field_name('value')
        if not name_node:
            continue
        name = _node_text(name_node, content)
        if not name:
            continue

        # Arrow function assigned to a const/let/var → FunctionEntity
        if value_node and value_node.type in ('arrow_function', 'function'):
            result.functions.append(FunctionEntity(
                name=name,
                line_start=_node_line_start(node),
                line_end=_node_line_end(node),
                byte_offset=node.start_byte,
                byte_length=node.end_byte - node.start_byte,
                symbol_subtype='arrow_function' if value_node.type == 'arrow_function' else None,
            ))
        else:
            result.globals.append(GlobalEntity(
                name=name,
                line_number=_node_line_start(node),
                byte_offset=node.start_byte,
                byte_length=node.end_byte - node.start_byte,
            ))


def _extract_from_export(node, content: bytes, result: ParseResult) -> None:
    """Strip export wrapper and recurse into the inner declaration."""

    for child in node.children:
        ntype = child.type
        if ntype == 'function_declaration':
            name_node = child.child_by_field_name('name')
            if name_node:
                result.functions.append(FunctionEntity(
                    name=_node_text(name_node, content),
                    line_start=_node_line_start(child),
                    line_end=_node_line_end(child),
                    byte_offset=child.start_byte,
                    byte_length=child.end_byte - child.start_byte,
                ))
        elif ntype == 'class_declaration':
            _extract_class(child, content, result)
        elif ntype in ('lexical_declaration', 'variable_declaration'):
            _extract_var_declaration(child, content, result)


# ---------------------------------------------------------------------------
# Call extraction — body analysis delegated to _js_body analyzers
# ---------------------------------------------------------------------------

_call_analyzer = _CallBodyAnalyzer()
_http_call_analyzer = _HttpCallBodyAnalyzer()
_string_constant_analyzer = _StringConstantBodyAnalyzer()


# ---------------------------------------------------------------------------
# Shared top-level body-collection helpers (used by all three extractors)
# ---------------------------------------------------------------------------

def _collect_function_bodies(fn_node, content: bytes, analyzer, out: list) -> None:
    """Run analyzer on the body of a function_declaration node."""
    name_node = fn_node.child_by_field_name('name')
    if name_node:
        body = _get_body_node(fn_node)
        if body:
            out.extend(analyzer.collect(body, content,
                caller_name=_node_text(name_node, content),
                caller_type='function', caller_parent=None))


def _collect_class_bodies(cls_node, content: bytes, analyzer, out: list) -> None:
    """Run analyzer on each method body of a class_declaration node."""
    cls_name_node = cls_node.child_by_field_name('name')
    cls_name = _node_text(cls_name_node, content) if cls_name_node else None
    body = cls_node.child_by_field_name('body')
    if body and cls_name:
        for child in body.children:
            if child.type == 'method_definition':
                m_name_node = child.child_by_field_name('name')
                if m_name_node:
                    m_body = _get_body_node(child)
                    if m_body:
                        out.extend(analyzer.collect(m_body, content,
                            caller_name=_node_text(m_name_node, content),
                            caller_type='method', caller_parent=cls_name))


def _collect_var_bodies(decl_node, content: bytes, analyzer, out: list) -> None:
    """Run analyzer on arrow/function values in a variable/lexical declaration."""
    for declarator in decl_node.children:
        if declarator.type != 'variable_declarator':
            continue
        name_node = declarator.child_by_field_name('name')
        value_node = declarator.child_by_field_name('value')
        if name_node and value_node and value_node.type in ('arrow_function', 'function'):
            body = _get_body_node(value_node)
            if body:
                out.extend(analyzer.collect(body, content,
                    caller_name=_node_text(name_node, content),
                    caller_type='function', caller_parent=None))


def _collect_export_bodies(export_node, content: bytes, analyzer, out: list) -> None:
    """Run analyzer on exported function and class declarations."""
    for child in export_node.children:
        if child.type == 'function_declaration':
            _collect_function_bodies(child, content, analyzer, out)
        elif child.type == 'class_declaration':
            _collect_class_bodies(child, content, analyzer, out)


def _collect_string_var_bodies(decl_node, content: bytes, out: list) -> None:
    """Collect string constants from a variable/lexical declaration node.

    Handles both direct string literal assignments (``const X = 'value'``) and
    arrow-/function-body analysis so callers need not branch on value type.
    """
    for declarator in decl_node.children:
        if declarator.type != 'variable_declarator':
            continue
        name_node = declarator.child_by_field_name('name')
        value_node = declarator.child_by_field_name('value')
        if not name_node or not value_node:
            continue
        owner_name = _node_text(name_node, content)
        if value_node.type in ('string', 'template_string'):
            value = _normalize_js_string(_node_text(value_node, content))
            if value:
                out.append(StringConstantEntity(
                    value=value,
                    line_number=_node_line_start(value_node),
                    byte_offset=value_node.start_byte,
                    byte_length=value_node.end_byte - value_node.start_byte,
                    owner_name=owner_name,
                    owner_type='global',
                    owner_parent=None,
                ))
        elif value_node.type in ('arrow_function', 'function'):
            body = _get_body_node(value_node)
            if body:
                out.extend(_string_constant_analyzer.collect(body, content,
                    caller_name=owner_name, caller_type='function', caller_parent=None))


def _dedup_and_merge_string_constants(constants: list, root_node, content: bytes) -> list:
    """Dedup string constants and merge in HTTP call targets as string entries."""
    deduped: list = []
    seen: set = set()
    for item in constants:
        key = (item.value, item.line_number, item.owner_name, item.owner_type, item.owner_parent)
        if key not in seen and item.value:
            seen.add(key)
            deduped.append(item)
    for http_call in _extract_all_http_calls(root_node, content):
        key = (
            http_call.callee_name,
            http_call.line_number,
            http_call.caller_name,
            http_call.caller_type,
            http_call.caller_parent,
        )
        if key in seen or not http_call.callee_name:
            continue
        seen.add(key)
        deduped.append(StringConstantEntity(
            value=http_call.callee_name,
            line_number=http_call.line_number,
            byte_offset=http_call.byte_offset,
            byte_length=http_call.byte_length,
            owner_name=http_call.caller_name,
            owner_type=http_call.caller_type,
            owner_parent=http_call.caller_parent,
        ))
    return deduped


def _extract_all_calls(root_node, content: bytes) -> list:
    """Walk top-level nodes and extract calls from every named function/method."""
    calls: list = []
    for node in root_node.children:
        ntype = node.type
        if ntype == 'function_declaration':
            _collect_function_bodies(node, content, _call_analyzer, calls)
        elif ntype == 'class_declaration':
            _collect_class_bodies(node, content, _call_analyzer, calls)
        elif ntype in ('lexical_declaration', 'variable_declaration'):
            _collect_var_bodies(node, content, _call_analyzer, calls)
        elif ntype in ('export_statement', 'export_default_declaration'):
            _collect_export_bodies(node, content, _call_analyzer, calls)
    return calls


def _extract_all_http_calls(root_node, content: bytes) -> list:
    """Walk top-level nodes and extract supported outbound JS HTTP calls."""
    calls: list = []
    for node in root_node.children:
        ntype = node.type
        if ntype == 'function_declaration':
            _collect_function_bodies(node, content, _http_call_analyzer, calls)
        elif ntype == 'class_declaration':
            _collect_class_bodies(node, content, _http_call_analyzer, calls)
        elif ntype in ('lexical_declaration', 'variable_declaration'):
            _collect_var_bodies(node, content, _http_call_analyzer, calls)
        elif ntype in ('export_statement', 'export_default_declaration'):
            _collect_export_bodies(node, content, _http_call_analyzer, calls)
    deduped = []
    seen = set()
    for item in calls:
        key = (item.caller_name, item.caller_type, item.caller_parent, item.callee_name, item.line_number)
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _extract_all_string_constants(root_node, content: bytes) -> list:
    """Extract conservative string constants from JS/TS code."""
    constants: list = []
    for node in root_node.children:
        ntype = node.type
        if ntype == 'function_declaration':
            _collect_function_bodies(node, content, _string_constant_analyzer, constants)
        elif ntype == 'class_declaration':
            _collect_class_bodies(node, content, _string_constant_analyzer, constants)
        elif ntype in ('lexical_declaration', 'variable_declaration'):
            _collect_string_var_bodies(node, content, constants)
        elif ntype in ('export_statement', 'export_default_declaration'):
            _collect_export_bodies(node, content, _string_constant_analyzer, constants)
    return _dedup_and_merge_string_constants(constants, root_node, content)
