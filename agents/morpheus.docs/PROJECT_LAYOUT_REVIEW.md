# VIA Project Layout Review

**Reviewer:** Morpheus (Tech Lead)
**Date:** 2026-01-10
**Sprint:** 1 (In Progress)
**Overall Grade:** B+ (Good foundation with minor improvements needed)

---

## Current Structure

```
via/
├── cli/              # CLI interface (empty - pending)
├── core/             # Core business logic
│   └── discovery.py  # File discovery with .gitignore
├── db/               # Database layer
│   ├── schema.py     # SQL schema definitions
│   └── store.py      # DatabaseStore CRUD operations
├── parsers/          # Language parsers
│   ├── base.py       # ParserABC + entity dataclasses
│   ├── registry.py   # Parser registry
│   └── python_parser.py  # Python AST parser
└── services/         # High-level services (empty - pending)

tests/
├── unit/             # Unit tests (65 tests, 88% coverage)
│   ├── test_database.py
│   ├── test_discovery.py
│   ├── test_parser_registry.py
│   └── test_python_parser.py
└── integration/      # Integration tests (empty - pending)
```

---

## ✅ Strengths

### 1. **Clear Separation of Concerns**
- Database layer isolated in `db/`
- Parsers cleanly separated in `parsers/`
- Core business logic in `core/`
- Good adherence to SRP (Single Responsibility Principle)

### 2. **Layered Architecture**
- Data access layer (`db/`)
- Domain logic layer (`core/`, `parsers/`)
- Application layer (`services/` - pending)
- Presentation layer (`cli/` - pending)

### 3. **Strong Test Coverage**
- 65 unit tests across all core components
- 88% code coverage
- Tests organized by component
- Good use of fixtures and parametrization

### 4. **Extensibility**
- `ParserABC` allows adding new language parsers
- `ParserRegistry` provides plugin architecture
- Database schema supports multiple languages

### 5. **Proper Python Package Structure**
- All packages have `__init__.py`
- Proper use of relative imports
- Clear module boundaries

---

## ⚠️ Issues Found

### **CRITICAL Issues (Must Fix)**

None identified. Foundation is solid.

### **MAJOR Issues (Should Fix Soon)**

#### 1. **Missing `__init__.py` Exports**
**Location:** All `__init__.py` files
**Issue:** Empty `__init__.py` files - no public API exposed

**Current:**
```python
# via/__init__.py
"""VIA - Python codebase indexing and querying CLI tool."""
__version__ = "0.1.0"
```

**Recommended:**
```python
"""VIA - Python codebase indexing and querying CLI tool."""

__version__ = "0.1.0"

# Public API exports
from .db.store import DatabaseStore
from .parsers.registry import ParserRegistry, get_global_registry
from .parsers.python_parser import PythonParser
from .core.discovery import FileDiscovery

__all__ = [
    "DatabaseStore",
    "ParserRegistry",
    "get_global_registry",
    "PythonParser",
    "FileDiscovery",
    "__version__",
]
```

**Why:** Makes imports cleaner (`from via import DatabaseStore` vs `from via.db.store import DatabaseStore`)

---

#### 2. **Missing Entry Point**
**Location:** `via/__main__.py`
**Issue:** Entry point defined in pyproject.toml but file doesn't exist

**Current:** `pyproject.toml` has `via = "via.__main__:main"` but no `__main__.py`

**Recommended:** Create `via/__main__.py`:
```python
"""Entry point for VIA CLI."""

def main():
    """Main entry point."""
    print("VIA v0.1.0 - Implementation in progress")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

**Why:** Allows `python -m via` and `via` commands to work

---

#### 3. **Parser Base Module Organization**
**Location:** `via/parsers/base.py`
**Issue:** Mixing entity dataclasses with abstract parser interface

**Current:** One file with 7 dataclasses + 1 ABC (150 lines)

**Recommended:** Split into:
```
parsers/
├── __init__.py
├── base.py           # ParserABC only
├── entities.py       # All entity dataclasses
├── registry.py
└── python_parser.py
```

**Why:** Better SRP, easier to find entities vs parser interface

---

### **MINOR Issues (Nice to Have)**

#### 4. **Missing Type Hints in Some Places**
**Location:** `via/db/store.py:_to_relative_path()`, `_to_absolute_path()`
**Issue:** Some internal methods missing return type hints

**Recommendation:** Add full type hints everywhere for better IDE support

---

#### 5. **No Logging Configuration**
**Location:** Missing `via/core/logging.py`
**Issue:** No centralized logging setup (will need for -v/-vv/-vvv flags)

**Recommended:** Add logging module early:
```python
# via/core/logging.py
import logging

def setup_logging(verbosity: int = 0):
    """Setup logging based on verbosity level."""
    levels = [logging.WARNING, logging.INFO, logging.DEBUG, logging.DEBUG]
    level = levels[min(verbosity, len(levels) - 1)]

    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
```

**Why:** Core requirement from spec, better to add early

---

#### 6. **Database Store Transaction Context Manager**
**Location:** `via/db/store.py`
**Issue:** Manual transaction management (begin/commit/rollback)

**Current:**
```python
store.begin_transaction()
try:
    # do work
    store.commit_transaction()
except:
    store.rollback_transaction()
```

**Recommended:** Add transaction context manager:
```python
@contextmanager
def transaction(self):
    """Context manager for transactions."""
    self.begin_transaction()
    try:
        yield self
        self.commit_transaction()
    except Exception:
        self.rollback_transaction()
        raise

# Usage:
with store.transaction():
    # do work - auto commit/rollback
```

**Why:** Cleaner API, prevents forgetting to commit/rollback

---

#### 7. **Missing Constants Module**
**Location:** Missing `via/core/constants.py`
**Issue:** Magic numbers scattered (10MB size limit, etc.)

**Recommended:** Centralize constants:
```python
# via/core/constants.py

# File size limits
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Default paths
DEFAULT_INDEX_DIR = ".via"
DEFAULT_DB_NAME = "index.db"

# Database
SCHEMA_VERSION = 1
```

**Why:** Easier to maintain, single source of truth

---

## 📋 Best Practices Compliance

| Practice | Status | Notes |
|----------|--------|-------|
| Package structure | ✅ GOOD | Proper `__init__.py`, clear hierarchy |
| Test organization | ✅ GOOD | Unit/integration split, good coverage |
| Dependency injection | ✅ GOOD | Store/parsers accept dependencies |
| Interface segregation | ✅ GOOD | Small, focused interfaces (ParserABC) |
| DRY principle | ✅ GOOD | Good code reuse |
| SOLID principles | ✅ GOOD | Well-applied throughout |
| Type hints | ⚠️ MOSTLY | Some missing in internal methods |
| Docstrings | ✅ GOOD | All public APIs documented |
| Logging | ❌ MISSING | Need to add before CLI work |
| Configuration | ⚠️ PENDING | Will need for CLI flags |

---

## 🎯 Recommended Action Items

### Before Continuing with Indexing Service:

1. **[HIGH]** Add `via/__main__.py` entry point
2. **[HIGH]** Export public API in `via/__init__.py`
3. **[MEDIUM]** Add `via/core/logging.py` module
4. **[MEDIUM]** Add `via/core/constants.py` module
5. **[LOW]** Split `parsers/base.py` into `base.py` + `entities.py`
6. **[LOW]** Add transaction context manager to DatabaseStore

### Can Defer Until Later:

- Missing type hints in internal methods
- Additional helper utilities
- Performance optimizations

---

## 💡 Architecture Patterns Observed

### ✅ **Good Patterns Being Used:**

1. **Repository Pattern** - DatabaseStore acts as repository
2. **Strategy Pattern** - ParserABC with multiple implementations
3. **Registry Pattern** - ParserRegistry for parser lookup
4. **Data Transfer Objects** - Entity dataclasses for parsed data
5. **Context Manager** - DatabaseStore connection management

### 🔮 **Patterns to Consider Adding:**

1. **Factory Pattern** - For creating parsers dynamically
2. **Observer Pattern** - For file watching in `-w` mode
3. **Command Pattern** - For CLI subcommands
4. **Builder Pattern** - For complex query building (Phase 2)

---

## 🏆 Overall Assessment

**Grade: B+**

The project structure is well-organized with clear separation of concerns and good test coverage. The foundation is solid for building the indexing service and CLI.

**Key Strengths:**
- Clean architecture
- Strong test coverage
- Extensible design
- Good use of Python idioms

**Areas for Improvement:**
- Missing entry point and public API exports (critical for next phase)
- No logging setup (needed for CLI verbosity)
- Could benefit from constants module
- Minor refinements to transaction API

**Recommendation:** Address HIGH priority items (entry point + public API) before continuing with indexing service. MEDIUM priority items (logging, constants) should be added when implementing CLI.

---

## 📝 Next Steps

After addressing HIGH priority items, Neo should continue with:
1. Indexing Service (S5) - orchestrates discovery + parsing + storage
2. CLI Command (S7) - implements `via index` subcommand
3. Progress Feedback (S8) - adds verbosity levels
4. Incremental Indexing (S9) - mtime-based updates

The current foundation is strong enough to support these components.

**Reviewed by:** @Morpheus
**Posted to:** agents/morpheus.docs/PROJECT_LAYOUT_REVIEW.md
