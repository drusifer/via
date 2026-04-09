"""
Python language parser using the stdlib AST module.

TLDR:
    Implements PythonParser (a ParserABC subclass) that parses .py/.pyx/.pyi
    files using Python's built-in ast module. Extracts functions, classes,
    imports, module-level globals, call relationships, and symbol references,
    all with precise byte offsets. Handles decorators, docstrings, type hints,
    async functions, and syntax errors gracefully. Filters Python builtins and
    language constants from call and reference results to keep only meaningful
    cross-symbol relationships.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import ast
import os
from typing import Set

from .base import (
    CallEntity,
    ClassEntity,
    FunctionEntity,
    GlobalEntity,
    ImportEntity,
    ParserABC,
    ParseResult,
    ReferenceEntity,
    StringConstantEntity,
)

# Python builtins that should not be indexed as call relationships
PYTHON_BUILTINS = {
    'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
    'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed', 'sum',
    'min', 'max', 'abs', 'round', 'pow', 'divmod', 'hash', 'id', 'type', 'isinstance',
    'issubclass', 'callable', 'getattr', 'setattr', 'hasattr', 'delattr', 'dir', 'vars',
    'repr', 'ascii', 'bin', 'oct', 'hex', 'ord', 'chr', 'format', 'input', 'open',
    'iter', 'next', 'slice', 'object', 'super', 'property', 'classmethod', 'staticmethod',
    'any', 'all', 'globals', 'locals', 'exec', 'eval', 'compile', 'breakpoint',
    '__import__', 'memoryview', 'bytearray', 'bytes', 'frozenset', 'complex',
}

# Python constants and keywords that shouldn't be indexed as references
PYTHON_CONSTANTS = {
    'True', 'False', 'None', 'Ellipsis', 'NotImplemented',
    '__name__', '__doc__', '__file__', '__package__', '__spec__',
}


class PythonParser(ParserABC):
    """Parser for Python files using the ast module."""

    def can_parse(self, file_path: str) -> bool:
        """Check if file is a Python file."""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.get_supported_extensions()

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """
        Parse Python file and extract entities.

        Args:
            file_path: Path to the file
            content: File content as bytes

        Returns:
            ParseResult with extracted entities
        """
        result = ParseResult(file_path=file_path, language="python")

        try:
            # Decode content
            text = content.decode('utf-8', errors='replace')

            # Parse AST
            tree = ast.parse(text, filename=file_path)

            # Extract entities
            self._extract_entities(tree, text, result)

        except SyntaxError as e:
            result.parse_error = f"Syntax error: {e}"
        except Exception as e:
            result.parse_error = f"Parse error: {type(e).__name__}: {e}"

        return result

    def get_supported_extensions(self) -> Set[str]:
        """Get supported Python file extensions."""
        return {'.py', '.pyx', '.pyi'}

    @property
    def language_name(self) -> str:
        """Get language name."""
        return "python"

    def _extract_entities(self, tree: ast.AST, text: str, result: ParseResult) -> None:
        """
        Extract entities from AST.

        Args:
            tree: AST tree
            text: Source code text
            result: ParseResult to populate
        """
        # Handler dispatch table: node_type -> (handler_method, top_level_checker)
        handlers = {
            ast.FunctionDef: (self._handle_function, self._is_top_level_function),
            ast.AsyncFunctionDef: (self._handle_function, self._is_top_level_function),
            ast.ClassDef: (self._handle_class, self._is_top_level_class),
            ast.Import: (self._handle_import, self._is_top_level_import),
            ast.ImportFrom: (self._handle_import, self._is_top_level_import),
            ast.Assign: (self._handle_assign, self._is_top_level_assign),
            ast.AnnAssign: (self._handle_ann_assign, self._is_top_level_assign),
        }

        for node in ast.walk(tree):
            handler_info = handlers.get(type(node))
            if handler_info:
                handler, is_top_level = handler_info
                if is_top_level(tree, node):
                    handler(node, text, result)

    def _handle_function(self, node, text: str, result: ParseResult) -> None:
        """Handle FunctionDef and AsyncFunctionDef nodes."""
        func = self._extract_function(node, text, class_id=None)
        result.functions.append(func)

        # Extract calls from function body
        calls = self._extract_calls(node, text, caller_name=node.name, caller_type='function')
        result.calls.extend(calls)
        result.string_constants.extend(
            self._extract_string_constants(
                node, text, owner_name=node.name, owner_type='function'
            )
        )

        # Extract references from function body
        refs = self._extract_references(node, text, referencer_name=node.name, referencer_type='function')
        result.references.extend(refs)

        # Extract decorator and type annotation references
        refs = self._extract_decorator_references(node, text, referencer_name=node.name, referencer_type='function')
        result.references.extend(refs)
        refs = self._extract_annotation_references(node, text, referencer_name=node.name, referencer_type='function')
        result.references.extend(refs)

    def _handle_class(self, node: ast.ClassDef, text: str, result: ParseResult) -> None:
        """Handle ClassDef nodes."""
        cls = self._extract_class(node, text)
        result.classes.append(cls)

        # Extract base class, decorator, and class-body annotation references
        refs = self._extract_class_structural_references(node, text)
        result.references.extend(refs)

        # Extract calls and references from methods within the class
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                calls = self._extract_calls(
                    item, text,
                    caller_name=item.name,
                    caller_type='method',
                    caller_parent=node.name
                )
                result.calls.extend(calls)

                refs = self._extract_references(
                    item, text,
                    referencer_name=item.name,
                    referencer_type='method',
                    referencer_parent=node.name
                )
                result.references.extend(refs)

                refs = self._extract_decorator_references(
                    item, text,
                    referencer_name=item.name,
                    referencer_type='method',
                    referencer_parent=node.name
                )
                result.references.extend(refs)

                refs = self._extract_annotation_references(
                    item, text,
                    referencer_name=item.name,
                    referencer_type='method',
                    referencer_parent=node.name
                )
                result.references.extend(refs)
                result.string_constants.extend(
                    self._extract_string_constants(
                        item, text,
                        owner_name=item.name,
                        owner_type='method',
                        owner_parent=node.name,
                    )
                )

    def _handle_import(self, node, text: str, result: ParseResult) -> None:
        """Handle Import and ImportFrom nodes."""
        imports = self._extract_imports(node, text)
        result.imports.extend(imports)

    def _handle_assign(self, node: ast.Assign, text: str, result: ParseResult) -> None:
        """Handle Assign nodes (globals)."""
        globals_list = self._extract_globals(node, text)
        result.globals.extend(globals_list)
        result.string_constants.extend(self._extract_global_string_constants(node, text))

    def _handle_ann_assign(self, node: ast.AnnAssign, text: str, result: ParseResult) -> None:
        """Handle AnnAssign nodes (annotated globals)."""
        global_var = self._extract_annotated_global(node, text)
        if global_var:
            result.globals.append(global_var)
            result.string_constants.extend(
                self._extract_annotated_global_string_constants(node, text)
            )

    def _is_top_level_function(self, tree: ast.AST, node: ast.FunctionDef) -> bool:
        """Check if function is at module level (not inside a class)."""
        for top_node in ast.walk(tree):
            if top_node == node:
                continue
            if isinstance(top_node, ast.ClassDef):
                # Check if node is inside this class
                for child in ast.walk(top_node):
                    if child == node:
                        return False
        return True

    def _is_top_level_class(self, _tree: ast.AST, _node: ast.ClassDef) -> bool:
        """Check if class is at module level (not nested)."""
        # For now, assume all ClassDef nodes at module level
        # More sophisticated check could verify parent nodes
        return True

    def _is_top_level_import(self, _tree: ast.AST, _node: ast.AST) -> bool:
        """Check if import is at module level."""
        return True

    def _is_top_level_assign(self, tree: ast.AST, node: ast.AST) -> bool:
        """Check if assignment is at module level."""
        # Simple heuristic: if it's in the body of the module
        if hasattr(tree, 'body'):
            return node in tree.body
        return False

    def _extract_function(
        self,
        node: ast.FunctionDef,
        text: str,
        class_id: int = None
    ) -> FunctionEntity:
        """Extract function information."""
        # Get byte offset and length
        byte_offset = self._get_byte_offset(node, text)
        byte_length = self._get_byte_length(node, text)

        # Extract arguments
        args = self._extract_args(node.args)

        # Extract decorators
        decorators = self._extract_decorators(node.decorator_list)

        # Extract docstring
        docstring = ast.get_docstring(node)

        return FunctionEntity(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            byte_offset=byte_offset,
            byte_length=byte_length,
            class_id=class_id,
            args=args,
            decorators=decorators,
            docstring=docstring,
        )

    def _extract_class(self, node: ast.ClassDef, text: str) -> ClassEntity:
        """Extract class information."""
        # Get byte offset and length
        byte_offset = self._get_byte_offset(node, text)
        byte_length = self._get_byte_length(node, text)

        # Extract base classes
        bases = self._extract_bases(node.bases)

        # Extract decorators
        decorators = self._extract_decorators(node.decorator_list)

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._extract_function(item, text, class_id=None)
                methods.append(method)

        return ClassEntity(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            byte_offset=byte_offset,
            byte_length=byte_length,
            bases=bases,
            decorators=decorators,
            docstring=docstring,
            methods=methods,
        )

    def _extract_imports(self, node: ast.AST, text: str) -> list:
        """Extract import statements."""
        imports = []
        byte_offset = self._get_byte_offset(node, text)
        byte_length = self._get_byte_length(node, text)

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(ImportEntity(
                    module=alias.name,
                    line_number=node.lineno,
                    byte_offset=byte_offset,
                    byte_length=byte_length,
                    alias=alias.asname,
                ))

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append(ImportEntity(
                    module=module,
                    name=alias.name,
                    alias=alias.asname,
                    line_number=node.lineno,
                    byte_offset=byte_offset,
                    byte_length=byte_length,
                ))

        return imports

    def _extract_globals(self, node: ast.Assign, text: str) -> list:
        """Extract global variable assignments."""
        globals_list = []
        byte_offset = self._get_byte_offset(node, text)
        byte_length = self._get_byte_length(node, text)

        for target in node.targets:
            if isinstance(target, ast.Name):
                # Simple assignment: x = value
                value = self._extract_literal_value(node.value)
                globals_list.append(GlobalEntity(
                    name=target.id,
                    line_number=node.lineno,
                    byte_offset=byte_offset,
                    byte_length=byte_length,
                    value=value,
                ))

        return globals_list

    def _extract_annotated_global(self, node: ast.AnnAssign, text: str) -> GlobalEntity:
        """Extract annotated global variable."""
        if isinstance(node.target, ast.Name):
            byte_offset = self._get_byte_offset(node, text)
            byte_length = self._get_byte_length(node, text)

            value = None
            if node.value:
                value = self._extract_literal_value(node.value)

            type_hint = ast.unparse(node.annotation) if hasattr(ast, 'unparse') else None

            return GlobalEntity(
                name=node.target.id,
                line_number=node.lineno,
                byte_offset=byte_offset,
                byte_length=byte_length,
                value=value,
                type_hint=type_hint,
            )
        return None

    def _extract_args(self, args: ast.arguments) -> str:
        """Extract function arguments as string."""
        arg_strs = []

        # Regular args
        for arg in args.args:
            arg_str = arg.arg
            if arg.annotation:
                if hasattr(ast, 'unparse'):
                    arg_str += f": {ast.unparse(arg.annotation)}"
            arg_strs.append(arg_str)

        # *args
        if args.vararg:
            arg_str = f"*{args.vararg.arg}"
            if args.vararg.annotation:
                if hasattr(ast, 'unparse'):
                    arg_str += f": {ast.unparse(args.vararg.annotation)}"
            arg_strs.append(arg_str)

        # **kwargs
        if args.kwarg:
            arg_str = f"**{args.kwarg.arg}"
            if args.kwarg.annotation:
                if hasattr(ast, 'unparse'):
                    arg_str += f": {ast.unparse(args.kwarg.annotation)}"
            arg_strs.append(arg_str)

        return ", ".join(arg_strs)

    def _extract_decorators(self, decorator_list: list) -> str:
        """Extract decorators as string."""
        if not decorator_list:
            return None

        if hasattr(ast, 'unparse'):
            return ", ".join(f"@{ast.unparse(d)}" for d in decorator_list)
        # Fallback for older Python versions
        return ", ".join(f"@{d.id if isinstance(d, ast.Name) else 'decorator'}" for d in decorator_list)

    def _extract_bases(self, bases: list) -> str:
        """Extract base classes as string."""
        if not bases:
            return None

        if hasattr(ast, 'unparse'):
            return ", ".join(ast.unparse(b) for b in bases)
        # Fallback for older Python versions
        return ", ".join(b.id if isinstance(b, ast.Name) else 'Base' for b in bases)

    def _extract_literal_value(self, node: ast.AST) -> str:
        """Extract literal value as string if possible."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        if isinstance(node, ast.Num):  # Python < 3.8
            return repr(node.n)
        if isinstance(node, ast.Str):  # Python < 3.8
            return repr(node.s)
        if hasattr(ast, 'unparse'):
            try:
                return ast.unparse(node)
            except Exception:
                return None
        return None

    def _extract_string_literal_text(self, node: ast.AST) -> str | None:
        """Extract raw text from Python string literal nodes."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Str):
            return node.s
        return None

    def _get_byte_offset(self, node: ast.AST, text: str) -> int:
        """Calculate byte offset of a node."""
        if not hasattr(node, 'lineno'):
            return 0

        lines = text.encode('utf-8').split(b'\n')
        offset = sum(len(line) + 1 for line in lines[:node.lineno - 1])  # +1 for newline

        if hasattr(node, 'col_offset'):
            # Add column offset
            line = lines[node.lineno - 1][:node.col_offset]
            offset += len(line)

        return offset

    def _get_byte_length(self, node: ast.AST, text: str) -> int:
        """Calculate byte length of a node."""
        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return 0

        start_offset = self._get_byte_offset(node, text)

        # Calculate end offset
        lines = text.encode('utf-8').split(b'\n')
        end_offset = sum(len(line) + 1 for line in lines[:node.end_lineno - 1])

        if hasattr(node, 'end_col_offset'):
            line = lines[node.end_lineno - 1][:node.end_col_offset]
            end_offset += len(line)
        else:
            # If no end_col_offset, use end of line
            end_offset += len(lines[node.end_lineno - 1])

        return max(0, end_offset - start_offset)

    def _extract_calls(
        self,
        func_node: ast.AST,
        text: str,
        caller_name: str,
        caller_type: str = 'function',
        caller_parent: str = None
    ) -> list:
        """
        Extract function/method calls from a function body.

        Args:
            func_node: Function or method AST node
            text: Source code text
            caller_name: Name of the calling function/method
            caller_type: 'function' or 'method'
            caller_parent: Parent class name if method

        Returns:
            List of CallEntity objects
        """
        calls = []

        for node in ast.walk(func_node):
            if not isinstance(node, ast.Call):
                continue

            callee_name = self._get_callee_name(node)
            if not callee_name:
                continue

            # Skip builtins
            if callee_name in PYTHON_BUILTINS:
                continue

            byte_offset = self._get_byte_offset(node, text)
            byte_length = self._get_byte_length(node, text)

            calls.append(CallEntity(
                caller_name=caller_name,
                callee_name=callee_name,
                line_number=node.lineno,
                byte_offset=byte_offset,
                byte_length=byte_length,
                caller_type=caller_type,
                caller_parent=caller_parent,
            ))

        return calls

    def _extract_string_constants(
        self,
        func_node: ast.AST,
        text: str,
        owner_name: str,
        owner_type: str,
        owner_parent: str = None
    ) -> list:
        """Extract conservative string literals from a function or method body."""
        constants = []
        seen = set()
        body_stmts = getattr(func_node, 'body', [func_node])

        for stmt in body_stmts:
            for node in ast.walk(stmt):
                value = None
                if isinstance(node, ast.Return):
                    value = self._extract_string_literal_text(node.value)
                elif isinstance(node, ast.Call):
                    for arg in getattr(node, 'args', []):
                        value = self._extract_string_literal_text(arg)
                        if value:
                            key = (value, getattr(arg, 'lineno', None), owner_name, owner_type, owner_parent)
                            if key not in seen:
                                seen.add(key)
                                constants.append(StringConstantEntity(
                                    value=value,
                                    line_number=arg.lineno,
                                    byte_offset=self._get_byte_offset(arg, text),
                                    byte_length=max(1, self._get_byte_length(arg, text)),
                                    owner_name=owner_name,
                                    owner_type=owner_type,
                                    owner_parent=owner_parent,
                                ))
                    continue
                elif isinstance(node, ast.Assign):
                    value = self._extract_string_literal_text(node.value)
                elif isinstance(node, ast.AnnAssign):
                    value = self._extract_string_literal_text(node.value)

                if value:
                    target_node = node.value if hasattr(node, 'value') and node.value is not None else node
                    key = (value, getattr(target_node, 'lineno', None), owner_name, owner_type, owner_parent)
                    if key in seen:
                        continue
                    seen.add(key)
                    constants.append(StringConstantEntity(
                        value=value,
                        line_number=target_node.lineno,
                        byte_offset=self._get_byte_offset(target_node, text),
                        byte_length=max(1, self._get_byte_length(target_node, text)),
                        owner_name=owner_name,
                        owner_type=owner_type,
                        owner_parent=owner_parent,
                    ))

        return constants

    def _extract_global_string_constants(self, node: ast.Assign, text: str) -> list:
        """Extract module-level string constants from simple assignments."""
        value = self._extract_string_literal_text(node.value)
        if value is None:
            return []

        constants = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                constants.append(StringConstantEntity(
                    value=value,
                    line_number=node.value.lineno,
                    byte_offset=self._get_byte_offset(node.value, text),
                    byte_length=max(1, self._get_byte_length(node.value, text)),
                    owner_name=target.id,
                    owner_type='global',
                    owner_parent=None,
                ))
        return constants

    def _extract_annotated_global_string_constants(self, node: ast.AnnAssign, text: str) -> list:
        """Extract module-level string constants from annotated assignments."""
        value = self._extract_string_literal_text(node.value)
        if value is None or not isinstance(node.target, ast.Name):
            return []
        return [StringConstantEntity(
            value=value,
            line_number=node.value.lineno,
            byte_offset=self._get_byte_offset(node.value, text),
            byte_length=max(1, self._get_byte_length(node.value, text)),
            owner_name=node.target.id,
            owner_type='global',
            owner_parent=None,
        )]

    def _get_callee_name(self, call_node: ast.Call) -> str:
        """
        Extract the callee name from a Call node.

        Examples:
            func() -> 'func'
            self.method() -> 'method'
            obj.method() -> 'method'
            module.func() -> 'func'

        Args:
            call_node: AST Call node

        Returns:
            Callee name or None if cannot be determined
        """
        func = call_node.func

        if isinstance(func, ast.Name):
            # Simple function call: func()
            return func.id

        elif isinstance(func, ast.Attribute):
            # Method/attribute call: obj.method() or self.method()
            return func.attr

        return None

    def _extract_class_structural_references(
        self,
        class_node: ast.ClassDef,
        text: str,
    ) -> list:
        """Extract references from a class definition's structure.

        Covers: base classes, class-level decorators, class-body annotations.
        All references are attributed to the class symbol (referencer_type='class').
        """
        references = []
        seen_names: Set[str] = set()
        class_name = class_node.name

        def _emit(name: str, lineno: int) -> None:
            if name in seen_names or name in PYTHON_BUILTINS or name in PYTHON_CONSTANTS:
                return
            if name in ('self', 'cls'):
                return
            seen_names.add(name)
            references.append(ReferenceEntity(
                referencer_name=class_name,
                referenced_name=name,
                line_number=lineno,
                byte_offset=self._get_byte_offset_for_line(lineno, text),
                byte_length=len(name),
                referencer_type='class',
                referencer_parent=None,
            ))

        # Base classes
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                _emit(base.id, base.lineno)
            elif isinstance(base, ast.Attribute):
                _emit(base.attr, base.lineno)

        # Class decorators
        for dec in class_node.decorator_list:
            if isinstance(dec, ast.Name):
                _emit(dec.id, dec.lineno)
            elif isinstance(dec, ast.Attribute):
                _emit(dec.attr, dec.lineno)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                _emit(dec.func.id, dec.func.lineno)

        # Class-body annotations (ast.AnnAssign at class level)
        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                ann = item.annotation
                if isinstance(ann, ast.Name):
                    _emit(ann.id, ann.lineno)
                elif isinstance(ann, ast.Attribute):
                    _emit(ann.attr, ann.lineno)

        return references

    def _get_byte_offset_for_line(self, lineno: int, text: str) -> int:
        """Return the byte offset of the start of a given line (1-indexed)."""
        lines = text.splitlines(keepends=True)
        offset = 0
        for i, line in enumerate(lines):
            if i + 1 == lineno:
                return offset
            offset += len(line.encode('utf-8'))
        return offset

    def _extract_decorator_references(
        self,
        func_node: ast.AST,
        text: str,
        referencer_name: str,
        referencer_type: str = 'function',
        referencer_parent: str = None,
    ) -> list:
        """Extract decorator names as REFERENCES for a function or method node."""
        references = []
        seen_names: Set[str] = set()
        decorator_list = getattr(func_node, 'decorator_list', [])

        for dec in decorator_list:
            if isinstance(dec, ast.Name):
                name = dec.id
            elif isinstance(dec, ast.Attribute):
                name = dec.attr
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                name = dec.func.id
            else:
                continue

            if name in seen_names or name in PYTHON_BUILTINS or name in PYTHON_CONSTANTS:
                continue
            if name in ('self', 'cls'):
                continue
            seen_names.add(name)
            references.append(ReferenceEntity(
                referencer_name=referencer_name,
                referenced_name=name,
                line_number=dec.lineno,
                byte_offset=self._get_byte_offset(dec, text),
                byte_length=len(name),
                referencer_type=referencer_type,
                referencer_parent=referencer_parent,
            ))

        return references

    def _extract_annotation_references(
        self,
        func_node: ast.AST,
        text: str,
        referencer_name: str,
        referencer_type: str = 'function',
        referencer_parent: str = None,
    ) -> list:
        """Extract type annotation names as REFERENCES for a function or method node.

        Covers: parameter annotations and return type annotation.
        Skips builtins (str, int, bool, etc.) and None.
        """
        references = []
        seen_names: Set[str] = set()

        def _emit_annotation(ann) -> None:
            if ann is None:
                return
            if isinstance(ann, ast.Name):
                name = ann.id
                lineno = ann.lineno
            elif isinstance(ann, ast.Attribute):
                name = ann.attr
                lineno = ann.lineno
            elif isinstance(ann, ast.Constant):
                return  # string annotations / literals — skip
            elif isinstance(ann, ast.Subscript):
                # e.g. Optional[X], List[X] — recurse into slice
                _emit_annotation(ann.value)
                _emit_annotation(ann.slice)
                return
            elif isinstance(ann, ast.Tuple):
                for elt in ann.elts:
                    _emit_annotation(elt)
                return
            else:
                return

            if name in seen_names or name in PYTHON_BUILTINS or name in PYTHON_CONSTANTS:
                return
            if name in ('self', 'cls'):
                return
            seen_names.add(name)
            references.append(ReferenceEntity(
                referencer_name=referencer_name,
                referenced_name=name,
                line_number=lineno,
                byte_offset=self._get_byte_offset(ann, text),
                byte_length=len(name),
                referencer_type=referencer_type,
                referencer_parent=referencer_parent,
            ))

        if isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Parameter annotations
            for arg in (func_node.args.args + func_node.args.posonlyargs +
                        func_node.args.kwonlyargs):
                _emit_annotation(arg.annotation)
            if func_node.args.vararg:
                _emit_annotation(func_node.args.vararg.annotation)
            if func_node.args.kwarg:
                _emit_annotation(func_node.args.kwarg.annotation)
            # Return annotation
            _emit_annotation(func_node.returns)

        return references

    def _extract_references(
        self,
        func_node: ast.AST,
        text: str,
        referencer_name: str,
        referencer_type: str = 'function',
        referencer_parent: str = None
    ) -> list:
        """
        Extract symbol references from a function body.

        Extracts references to external symbols (globals, constants) used within
        the function. Excludes parameters, local variables, builtins, and self/cls.

        Args:
            func_node: Function or method AST node
            text: Source code text
            referencer_name: Name of the function/method making references
            referencer_type: 'function' or 'method'
            referencer_parent: Parent class name if method

        Returns:
            List of ReferenceEntity objects
        """
        references = []
        params = self._collect_parameters(func_node)
        locals_vars = self._collect_locals(func_node)
        seen_names = set()

        # Walk only the function body — not decorator_list or annotations.
        # Decorators are tracked by _extract_decorator_references; annotations
        # by _extract_annotation_references. Walking the full node caused
        # decorator names to be captured twice (S9-002).
        body_stmts = getattr(func_node, 'body', [func_node])
        for node in (n for stmt in body_stmts for n in ast.walk(stmt)):
            if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
                continue

            name = node.id
            if self._should_skip_reference(name, seen_names, params, locals_vars):
                continue

            seen_names.add(name)
            references.append(ReferenceEntity(
                referencer_name=referencer_name,
                referenced_name=name,
                line_number=node.lineno,
                byte_offset=self._get_byte_offset(node, text),
                byte_length=self._get_byte_length(node, text),
                referencer_type=referencer_type,
                referencer_parent=referencer_parent,
            ))

        return references

    def _collect_parameters(self, func_node: ast.AST) -> set:
        """Collect function parameters."""
        params = set()
        if isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in func_node.args.args:
                params.add(arg.arg)
            for arg in func_node.args.posonlyargs:
                params.add(arg.arg)
            for arg in func_node.args.kwonlyargs:
                params.add(arg.arg)
            if func_node.args.vararg:
                params.add(func_node.args.vararg.arg)
            if func_node.args.kwarg:
                params.add(func_node.args.kwarg.arg)
        return params

    def _collect_locals(self, func_node: ast.AST) -> set:
        """Collect local variables (assigned within the function)."""
        locals_vars = set()
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        locals_vars.add(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    locals_vars.add(node.target.id)
            elif isinstance(node, ast.NamedExpr):  # Walrus operator :=
                if isinstance(node.target, ast.Name):
                    locals_vars.add(node.target.id)
        return locals_vars

    def _should_skip_reference(self, name: str, seen: set, params: set, locals_vars: set) -> bool:
        """Check if a name should be skipped during reference extraction."""
        if name in seen:
            return True
        if name in params:
            return True
        if name in locals_vars:
            return True
        if name in ('self', 'cls'):
            return True
        if name in PYTHON_BUILTINS:
            return True
        if name in PYTHON_CONSTANTS:
            return True
        return False
