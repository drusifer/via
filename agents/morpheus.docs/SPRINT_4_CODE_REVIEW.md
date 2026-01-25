# Sprint 4 Code Review - Tech Debt Assessment

**Reviewer**: Morpheus (SE Lead)
**Date**: 2026-01-24
**Scope**: Full codebase review for code quality (DRY, KISS, Code Smells)
**Target**: @Neo for implementation

---

## Executive Summary

**Verdict**: NEEDS REFACTORING - Multiple code quality issues identified

| Severity | Count | Action Required |
|----------|-------|-----------------|
| HIGH | 6 | Must fix in Sprint 4 |
| MEDIUM | 5 | Should fix in Sprint 4 |
| LOW | 4 | Nice to have |

---

## HIGH Priority Issues

### H1: Duplicated `_safe_print` Function
**Location**:
- [__main__.py:22-43](via/__main__.py#L22-L43)
- [executor.py:13-26](via/pipeline/executor.py#L13-L26)

**Problem**: Identical implementation copied verbatim in two files.

**Fix**: Extract to `via/core/utils.py`:
```python
# via/core/utils.py
def safe_print(text: str, file=None) -> None:
    """Print text safely, handling Unicode encoding errors."""
    ...
```

**Files to modify**: 2

---

### H2: Duplicated `_format_header` Method
**Location**:
- [raw.py:84-100](via/renderers/raw.py#L84-L100)
- [formatted.py:161-177](via/renderers/formatted.py#L161-L177)

**Problem**: Nearly identical header formatting logic in both renderers.

**Fix**: Extract to base class or shared utility:
```python
# via/renderers/base.py
def format_delimiter_header(record: MatchRecord, end_line: int, divider_char='#', width=60) -> str:
    ...
```

**Files to modify**: 3

---

### H3: Duplicated Context Option Extraction
**Location**:
- [raw.py:48-57](via/renderers/raw.py#L48-L57)
- [formatted.py:64-74](via/renderers/formatted.py#L64-L74)

**Problem**: Same pattern for handling -A, -B, -C options duplicated.

**Fix**: Create a dataclass for context options:
```python
@dataclass
class ContextOptions:
    before: int = 0
    after: int = 0

    @classmethod
    def from_options(cls, **options) -> 'ContextOptions':
        context = options.get('context', 0)
        before = context or options.get('before_context', 0)
        after = context or options.get('after_context', 0)
        return cls(before=before, after=after)
```

**Files to modify**: 3

---

### H4: Repeated Database Connection Check
**Location**: [store.py](via/db/store.py) (~30 occurrences)

**Problem**: Every method starts with:
```python
if not self.conn:
    raise RuntimeError("Database not connected")
```

**Fix**: Use a decorator:
```python
def require_connection(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.conn:
            raise RuntimeError("Database not connected")
        return func(self, *args, **kwargs)
    return wrapper

# Usage
@require_connection
def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
    ...
```

**Files to modify**: 1, but many methods

---

### H5: Duplicated Match Syntax Logic
**Location**:
- [executor.py:135-142](via/pipeline/executor.py#L135-L142)
- [executor.py:217-225](via/pipeline/executor.py#L217-L225)

**Problem**: Same if/elif block for converting match_syntax to MatchOp appears twice.

**Fix**: Extract to helper function:
```python
def get_match_op(match_syntax: str) -> MatchOp:
    """Convert match syntax suffix to MatchOp enum."""
    return {
        'r': MatchOp.REGEXP,
        's': MatchOp.LIKE,
    }.get(match_syntax, MatchOp.GLOB)
```

**Files to modify**: 1

---

### H6: Render Support Defined in Two Places
**Location**:
- [executor.py:30-41](via/pipeline/executor.py#L30-L41) (SYMBOL_RENDER_SUPPORT dict)
- [match_record.py](via/core/match_record.py) (each subclass's `supports_render_type`)

**Problem**: Symbol render support is defined polymorphically in MatchRecord AND as a dict in executor. These can drift out of sync.

**Fix**: Remove `SYMBOL_RENDER_SUPPORT` dict from executor. The polymorphic `supports_render_type()` is the single source of truth.

**Files to modify**: 1

---

## MEDIUM Priority Issues

### M1: Long Method - `_run_index_command`
**Location**: [__main__.py:220-326](via/__main__.py#L220-L326)

**Problem**: 106 lines - violates Single Responsibility. Does validation, initialization, execution, and output.

**Fix**: Extract into smaller functions:
- `_validate_index_args(args) -> Path`
- `_initialize_indexer(db_path, target_dir) -> IndexingService`
- `_print_index_summary(stats)`

---

### M2: Primitive Obsession - String Symbol Types
**Location**: Multiple files

**Problem**: `symbol_type: str` used in MatchRecord when we have `SymbolType` enum.

**Current**:
```python
@dataclass
class MatchRecord(ABC):
    symbol_type: str  # 'class', 'method', etc.
```

**Better**:
```python
@dataclass
class MatchRecord(ABC):
    symbol_type: SymbolType  # Use the enum
```

**Files to modify**: 3-4

---

### M3: Dead Code - `MatchResult` Class
**Location**: [types.py:58-91](via/core/types.py#L58-L91)

**Problem**: `MatchResult` dataclass appears to be superseded by `MatchRecord`. It's defined but likely unused (MatchRecord is the current implementation).

**Fix**: Verify no usages, then delete.

---

### M4: Complex Pipeline Detection
**Location**: [__main__.py:507-554](via/__main__.py#L507-L554)

**Problem**: `_is_pipeline_syntax()` has complex logic with many conditions.

**Fix**: Simplify by checking for known subcommands first:
```python
def _is_pipeline_syntax(argv: list) -> bool:
    if not argv:
        return False
    subcommands = {'index', 'i', 'match', 'm', 'stats', 's', '--help', '-h', '--version'}
    if argv[0] in subcommands:
        return False
    # Everything else is pipeline syntax
    return True
```

---

### M5: Redundant symbol_type Handling in Parser
**Location**: [parser.py:149-159](via/pipeline/parser.py#L149-L159)

**Problem**: Complex logic handling both `symbol_types` list and `symbol_type` single value.

**Fix**: Always use the list. Set default to empty list, no special single-type handling needed.

---

## LOW Priority Issues

### L1: Magic Numbers
**Location**:
- [raw.py:94](via/renderers/raw.py#L94): `'#' * 60`
- [formatted.py:171](via/renderers/formatted.py#L171): `'#' * 60`
- [parser.py:251](via/pipeline/parser.py#L251): `default=10`

**Fix**: Extract to constants:
```python
# via/core/constants.py
HEADER_DIVIDER_WIDTH = 60
DEFAULT_RESULT_LIMIT = 10
```

---

### L2: Data Clump - Context Options
**Location**: Renderers

**Problem**: `after_context`, `before_context`, `context` always travel together.

**Fix**: Already addressed in H3 with `ContextOptions` dataclass.

---

### L3: Inconsistent Error Handling
**Location**: Various

**Problem**: Some methods return None, some raise exceptions, some print to stderr.

**Recommendation**: Establish pattern:
- Validation errors: raise `ValueError`
- Runtime errors: raise `RuntimeError`
- User-facing errors: print to stderr AND return error code

---

### L4: Feature Envy in Executor
**Location**: [executor.py:269-293](via/pipeline/executor.py#L269-L293)

**Problem**: `_execute_render_stage` accesses many attributes of `stage.args`.

**Fix**: Consider extracting a `RenderOptions` dataclass that `stage.args` can provide.

---

## Refactoring Priority Order

For Sprint 4, I recommend tackling in this order:

1. **H1** (safe_print) - Quick win, 2 files
2. **H5** (match_syntax) - Quick win, 1 file
3. **H6** (render support) - Delete redundant code
4. **H2 + H3** (renderer duplication) - Related, do together
5. **H4** (connection decorator) - Many changes but mechanical
6. **M3** (dead code) - Verify and delete

Estimated effort: 3-4 hours for HIGH priority items.

---

## Files Modified Count

| File | Changes |
|------|---------|
| via/__main__.py | 3 changes |
| via/pipeline/executor.py | 3 changes |
| via/db/store.py | 1 large refactor |
| via/renderers/raw.py | 2 changes |
| via/renderers/formatted.py | 2 changes |
| via/renderers/base.py | 1 new method |
| via/core/utils.py | NEW FILE |
| via/core/types.py | 1 deletion |
| via/pipeline/parser.py | 1 change |

---

## Sign-off

**Reviewed by**: Morpheus
**Status**: Ready for @Neo implementation
**Next Action**: @Neo *swe refactor H1-H6 per review

---
*Code review complete. DRY violations are the primary concern.*
