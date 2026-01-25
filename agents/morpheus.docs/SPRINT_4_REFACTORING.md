# Sprint 4 Refactoring Architecture

**Version**: 1.0
**Date**: 2026-01-24
**Architect**: @Morpheus
**Status**: Ready for Implementation
**Reference**: [SPRINT_4_CODE_REVIEW.md](SPRINT_4_CODE_REVIEW.md)

---

## Executive Summary

This document provides architectural guidance for the Sprint 4 tech debt refactoring. It establishes patterns and conventions to eliminate DRY violations and improve code quality.

**Goal**: Reduce code duplication by ~40% in core modules while maintaining backward compatibility.

---

## 1. New Core Utils Module

### 1.1 Create `via/core/utils.py`

Extract common utilities that are duplicated across modules.

```python
# via/core/utils.py
"""Common utility functions for VIA.

This module consolidates utilities that were previously duplicated
across multiple modules.
"""

import sys
from functools import wraps
from typing import Callable, TypeVar, Any

from .types import MatchOp

F = TypeVar('F', bound=Callable[..., Any])


def safe_print(text: str, file=None) -> None:
    """Print text safely, handling Unicode encoding errors.

    Some terminals use latin-1 or ASCII encoding which can't handle
    Unicode characters like emojis. This handles such cases gracefully.

    Args:
        text: The text to print
        file: Output file (default: sys.stdout)
    """
    if file is None:
        file = sys.stdout
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        encoding = getattr(file, 'encoding', 'utf-8') or 'utf-8'
        safe_text = text.encode(encoding, errors='replace').decode(encoding)
        print(safe_text, file=file)


def get_match_op(match_syntax: str) -> MatchOp:
    """Convert match syntax suffix to MatchOp enum.

    Args:
        match_syntax: Single character suffix ('g', 'r', 's')

    Returns:
        Corresponding MatchOp enum value
    """
    return {
        'r': MatchOp.REGEXP,
        's': MatchOp.LIKE,
    }.get(match_syntax, MatchOp.GLOB)
```

### 1.2 Migration

| Old Location | New Location |
|--------------|--------------|
| `via/__main__.py:_safe_print()` | `via.core.utils.safe_print()` |
| `via/pipeline/executor.py:_safe_print()` | `via.core.utils.safe_print()` |
| `via/pipeline/executor.py:135-142` | `via.core.utils.get_match_op()` |
| `via/pipeline/executor.py:217-225` | `via.core.utils.get_match_op()` |

---

## 2. Database Connection Decorator

### 2.1 Pattern: `@require_connection`

Add a decorator to eliminate repeated connection checks in `store.py`.

```python
# via/db/store.py (add at top after imports)

def require_connection(func: F) -> F:
    """Decorator that ensures database connection exists.

    Raises:
        RuntimeError: If database is not connected
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.conn:
            raise RuntimeError("Database not connected")
        return func(self, *args, **kwargs)
    return wrapper
```

### 2.2 Usage

```python
# Before (repeated ~30 times)
def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
    if not self.conn:
        raise RuntimeError("Database not connected")
    # ... actual logic

# After
@require_connection
def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
    # ... actual logic (cleaner!)
```

### 2.3 Methods to Refactor

All public methods in `DatabaseStore` except:
- `__init__`
- `connect`
- `close`
- `__enter__` / `__exit__`

---

## 3. Renderer Base Class Consolidation

### 3.1 Context Options Dataclass

Extract repeated context option handling into a dataclass.

```python
# via/renderers/base.py (add to existing file)

from dataclasses import dataclass
from typing import Optional


@dataclass
class ContextOptions:
    """Options for context lines around matches.

    Consolidates -A, -B, -C option handling that was duplicated
    in RawRenderer and FormattedRenderer.
    """
    before: int = 0
    after: int = 0

    @classmethod
    def from_options(cls, **options) -> 'ContextOptions':
        """Create from render options dict.

        Args:
            **options: Render options including:
                - after_context: Lines after match (-A)
                - before_context: Lines before match (-B)
                - context: Lines both sides (-C, overrides -A/-B)

        Returns:
            ContextOptions instance
        """
        context = options.get('context')
        if context:
            return cls(before=context, after=context)
        return cls(
            before=options.get('before_context', 0),
            after=options.get('after_context', 0)
        )
```

### 3.2 Header Formatting Method

Add shared header formatting to base `Renderer` class.

```python
# via/renderers/base.py (add to Renderer class)

# Constants
HEADER_DIVIDER_WIDTH = 60
HEADER_DIVIDER_CHAR = '#'


class Renderer(ABC):
    # ... existing code ...

    def format_delimiter_header(
        self,
        record: 'MatchRecord',
        end_line: int,
        divider_char: str = HEADER_DIVIDER_CHAR,
        width: int = HEADER_DIVIDER_WIDTH
    ) -> str:
        """Format delimiter header for a match.

        Args:
            record: The match record
            end_line: Calculated end line number
            divider_char: Character for divider line
            width: Width of divider line

        Returns:
            Formatted header string
        """
        divider = divider_char * width
        return (
            f"{divider}\n"
            f"{divider_char} {record.file_path}:{record.line_number}-{end_line}\n"
            f"{divider_char}     {record.symbol_type} *{record.symbol_name}*\n"
            f"{divider}"
        )
```

### 3.3 Renderer Updates

```python
# via/renderers/raw.py - Updated

from .base import Renderer, ContextOptions

class RawRenderer(Renderer):
    def render(self, records: Iterator[MatchRecord], **options) -> str:
        ctx = ContextOptions.from_options(**options)  # Use shared class
        nodelims = options.get('nodelims', False)

        outputs = []
        for record in records:
            source = extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                ctx.before,  # Use dataclass
                ctx.after,
                read_full_file=True
            )
            if source:
                if nodelims:
                    outputs.append(source)
                else:
                    line_count = source.count('\n') + 1
                    end_line = record.line_number + line_count - 1
                    header = self.format_delimiter_header(record, end_line)  # Use base method
                    outputs.append(header + '\n' + source)

        return '\n'.join(outputs)

    # DELETE: _format_header method (now in base class)
```

---

## 4. Remove Redundant Render Support

### 4.1 Problem

Render support is defined in TWO places:
1. `via/pipeline/executor.py:SYMBOL_RENDER_SUPPORT` dict
2. Each `MatchRecord` subclass's `supports_render_type()` method

### 4.2 Solution

Delete `SYMBOL_RENDER_SUPPORT` dict from executor.py. The polymorphic method is the single source of truth.

```python
# via/pipeline/executor.py

# DELETE these lines (30-41):
# SYMBOL_RENDER_SUPPORT: Dict[str, Set[RenderType]] = {
#     'class': {RenderType.LIST, ...},
#     ...
# }

# DELETE: _print_unsupported_warning method that uses it

# UPDATE: _execute_render_stage to use record.supports_render_type() only
```

### 4.3 Updated Warning Logic

```python
# via/pipeline/executor.py - Simplified warning

def _execute_render_stage(self, stage: PipelineStage, records: Iterator[MatchRecord]):
    # ... existing setup ...

    skipped_types: Dict[str, int] = {}

    def filter_supported(records_iter: Iterator[MatchRecord]) -> Iterator[MatchRecord]:
        for record in records_iter:
            if record.supports_render_type(render_type):
                yield record
            else:
                skipped_types[record.symbol_type] = skipped_types.get(record.symbol_type, 0) + 1

    # ... render ...

    if skipped_types:
        total = sum(skipped_types.values())
        types_str = ', '.join(f"{t}({c})" for t, c in skipped_types.items())
        print(f"Warning: {total} records skipped (unsupported render type): {types_str}",
              file=sys.stderr)
```

---

## 5. Constants Consolidation

### 5.1 Add to `via/core/constants.py`

```python
# via/core/constants.py (additions)

# Rendering
HEADER_DIVIDER_WIDTH = 60
HEADER_DIVIDER_CHAR = '#'

# Defaults
DEFAULT_RESULT_LIMIT = 10
```

---

## 6. Dead Code Removal

### 6.1 Remove `MatchResult` Class

The `MatchResult` dataclass in `via/core/types.py` is superseded by `MatchRecord`.

**Verification**: Search for usages before deletion.
```bash
via -mg 'MatchResult' -tc -tf
```

If no usages found, delete lines 58-91 in `types.py`.

---

## 7. Implementation Order

Execute in this order for minimal risk:

| Step | Task | Files | Risk |
|------|------|-------|------|
| 1 | Create `via/core/utils.py` | New file | Low |
| 2 | Import `safe_print` in __main__.py, executor.py | 2 files | Low |
| 3 | Import `get_match_op` in executor.py | 1 file | Low |
| 4 | Add `@require_connection` decorator | store.py | Medium |
| 5 | Add `ContextOptions` to base.py | 1 file | Low |
| 6 | Add `format_delimiter_header` to base.py | 1 file | Low |
| 7 | Update raw.py to use base methods | 1 file | Low |
| 8 | Update formatted.py to use base methods | 1 file | Low |
| 9 | Remove `SYMBOL_RENDER_SUPPORT` from executor.py | 1 file | Low |
| 10 | Remove `MatchResult` from types.py | 1 file | Low |
| 11 | Add constants to constants.py | 1 file | Low |

**Run tests after each step!**

---

## 8. Testing Strategy

### 8.1 Before Refactoring

```bash
source .venv/bin/activate && pytest -v
```

Record baseline: all tests should pass.

### 8.2 After Each Step

```bash
pytest -v
```

All tests must continue to pass.

### 8.3 Regression Tests

No new tests needed - existing tests cover the functionality. Refactoring should not change behavior.

---

## 9. Success Criteria

- [ ] `via/core/utils.py` exists with `safe_print` and `get_match_op`
- [ ] No duplicate `_safe_print` functions in codebase
- [ ] No duplicate match_syntax→MatchOp logic in codebase
- [ ] `@require_connection` decorator used in store.py
- [ ] `ContextOptions` used in raw.py and formatted.py
- [ ] `format_delimiter_header` in Renderer base class only
- [ ] `SYMBOL_RENDER_SUPPORT` deleted from executor.py
- [ ] `MatchResult` deleted from types.py
- [ ] All tests pass
- [ ] No functional changes (pure refactoring)

---

**Status**: Ready for @Neo implementation
**Estimated Effort**: 3-4 hours
**Next**: @Neo *swe refactor per this architecture
