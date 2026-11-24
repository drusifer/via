# Complexity Refactoring Plan

**Author**: Morpheus (Architect)
**Date**: 2026-01-21
**Status**: Proposed

## Overview

Simple fixes for 4 C901 complexity violations remaining after Sprint 3 refactoring.

---

## 1. `factory.py:create` (13 → 10) - EASIEST

**Problem**: Nested if/elif for render_type and format_type combinations.

**Fix**: Use lookup tables instead of conditionals.

```python
# Before: 13 branches of if/elif
if render_type == RenderType.TABLE:
    if format_type == FormatType.ASCII:
        return TableRenderer(AsciiTableFormatter())
    elif format_type == FormatType.MD:
        ...

# After: 2 dict lookups
TABLE_FORMATTERS = {
    FormatType.ASCII: AsciiTableFormatter,
    FormatType.MD: MarkdownTableFormatter,
    FormatType.HTML: HtmlTableFormatter,
}
CODE_FORMATTERS = {
    FormatType.ASCII: AsciiCodeFormatter,
    FormatType.MD: MarkdownCodeFormatter,
    FormatType.HTML: HtmlCodeFormatter,
}

def create(render_type, format_type=None):
    if render_type == RenderType.LIST:
        return ListRenderer()
    if render_type == RenderType.RAW:
        return RawRenderer()
    if render_type == RenderType.TABLE:
        fmt = TABLE_FORMATTERS.get(format_type or FormatType.ASCII, AsciiTableFormatter)
        return TableRenderer(fmt())
    if render_type == RenderType.FORMATTED:
        fmt = CODE_FORMATTERS.get(format_type or FormatType.ASCII, AsciiCodeFormatter)
        return FormattedRenderer(fmt())
    raise ValueError(f"Unsupported: {render_type}")
```

**Effort**: ~15 min | **Risk**: Low

---

## 2. `__main__.py:_run_match_command` (11 → 10) - EASY

**Problem**: Sequential validation checks add complexity.

**Fix**: Extract `_determine_match_op()` helper.

```python
# Before: inline if/elif in main function
if args.regex:
    match_op = MatchOp.REGEXP
elif args.sql:
    match_op = MatchOp.LIKE
else:
    match_op = MatchOp.GLOB

# After: extract to helper
def _determine_match_op(args) -> MatchOp:
    if args.regex:
        return MatchOp.REGEXP
    if args.sql:
        return MatchOp.LIKE
    return MatchOp.GLOB
```

**Effort**: ~10 min | **Risk**: Low

---

## 3. `indexing.py:_store_parsed_file` (12 → 10) - MEDIUM

**Problem**: Long method doing file update/insert + entity storage.

**Fix**: Extract `_store_entities()` helper for entity insertion loop.

```python
# Before: all in one method
def _store_parsed_file(self, file_info, parse_result):
    # 30+ lines of file handling
    # 40+ lines of entity insertion

# After: split responsibilities
def _store_parsed_file(self, file_info, parse_result):
    file_id = self._upsert_file(file_info, parse_result)
    return self._store_entities(file_id, parse_result)

def _upsert_file(self, file_info, parse_result) -> int:
    # Handle insert vs update logic

def _store_entities(self, file_id, parse_result) -> dict:
    # Store classes, methods, functions, imports, globals
```

**Effort**: ~30 min | **Risk**: Medium

---

## 4. `python_parser.py:_extract_entities` (15 → 10) - HARDER

**Problem**: Multiple `isinstance` checks with nested conditions in a loop.

**Fix**: Use handler dispatch pattern.

```python
# Before: big if/elif chain in loop
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        if self._is_top_level_function(tree, node):
            ...
    elif isinstance(node, ast.ClassDef):
        ...

# After: handler dispatch
HANDLERS = {
    ast.FunctionDef: '_handle_function',
    ast.AsyncFunctionDef: '_handle_function',
    ast.ClassDef: '_handle_class',
    ast.Import: '_handle_import',
    ast.ImportFrom: '_handle_import',
    ast.Assign: '_handle_assign',
    ast.AnnAssign: '_handle_ann_assign',
}

def _extract_entities(self, tree, text, result):
    for node in ast.walk(tree):
        handler_name = HANDLERS.get(type(node))
        if handler_name:
            getattr(self, handler_name)(tree, node, text, result)
```

**Effort**: ~45 min | **Risk**: Medium (more changes)

---

## Recommended Order

1. `factory.py` - Quickest win, lowest risk
2. `__main__.py` - Simple extraction
3. `indexing.py` - Moderate refactor
4. `python_parser.py` - Most complex, defer if time-constrained

## Alternative: Raise Threshold

If refactoring is low priority, consider raising `max-complexity` to 15 in `pyproject.toml`:

```toml
[tool.ruff.lint.mccabe]
max-complexity = 15  # Was 10
```

This is a pragmatic choice if the functions are well-tested and readable despite complexity.

---

## Summary

| Function | Complexity | Fix | Effort | Risk |
|----------|------------|-----|--------|------|
| factory.py:create | 13 | Lookup tables | 15 min | Low |
| __main__.py:_run_match_command | 11 | Extract helper | 10 min | Low |
| indexing.py:_store_parsed_file | 12 | Split method | 30 min | Medium |
| python_parser.py:_extract_entities | 15 | Handler dispatch | 45 min | Medium |

**Total Effort**: ~100 min for all 4, or ~25 min for quick wins (1 & 2)
