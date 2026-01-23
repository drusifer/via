# VIA CLI Architecture Refactor - Status Summary

## Session Summary

**Date:** January 22, 2026  
**Status:** COMPLETE - 465/467 tests passing (99.6%)  
**Coverage:** 80% overall code coverage

---

## What Was Accomplished

### 1. **Polymorphic CLI Interface Pattern** ✅
- Implemented `ArgumentProvider` and `HelpProvider` abstract base classes in `via/core/interfaces.py`
- All command classes (IndexCommand, MatchCommand, StatsCommand) implement these interfaces
- All renderer and parser base classes implement these interfaces
- All MatchRecord types (Class, Method, Function, File, Import, Global, Header) inherit help strings

### 2. **Argument Registration Refactor** ✅
- **BEFORE:** 200+ lines of argument registration in `__main__.py`
- **AFTER:** All arguments registered in command classes via `add_arguments()` classmethod
- Removed verbose epilog from main parser
- MatchCommand dynamically registers `-t` type filter with all symbol types

### 3. **Consistent Command Abbreviations** ✅
- `index` → `i` (via i for short)
- `match` → `m` (via m for short)
- `stats` → `s` (via s for short)
- All commands now have single-letter aliases for faster CLI usage

### 4. **MatchRecord Polymorphic System** ✅
- Base `MatchRecord` class is abstract (cannot be instantiated)
- 7 concrete MatchRecord subclasses with their own HELP strings:
  - ClassMatchRecord
  - MethodMatchRecord
  - FunctionMatchRecord
  - FileMatchRecord
  - ImportMatchRecord
  - GlobalMatchRecord
  - HeaderMatchRecord
- All implement `supports_render_type()` method
- All have proper `__str__()` format: `type:file:line:qualified_name[@byte+length]`

### 5. **Bug Fixes** ✅
- Fixed abstract method inheritance conflicts (removed `@abstractmethod` from concrete implementations)
- Fixed MatchRecord initialization errors (removed duplicate class definitions)
- Fixed HELP string docstring placement conflicts
- Added `return_root` parameter to `find_index_db()` function
- Fixed `-t` argument destination naming (`dest="type"` not `dest="symbol_type"`)

---

## CLI Structure (Current)

```
via [OPTIONS] COMMAND [ARGS]

Commands:
  index (i)    Index a directory tree
  match (m)    Search indexed code using pattern matching  
  stats (s)    Show database statistics

Options:
  -h, --help           Show help
  --version            Show version
  -v, --verbose        Increase verbosity (up to -vvvv)
```

### Match Command Help
```
via match [-h] [-t {class,method,function,filepath,filename,import,global,header}] 
          [-g | -r | -s] [-I] [-n N] [--db PATH] [-d DIRECTORY] pattern

Supported symbol types:
  - class: Class symbol - supports all render types including DIAGRAM
  - method: Method symbol - supports all except DIAGRAM
  - function: Function symbol - supports all except DIAGRAM
  - filepath/filename: File path symbol - supports LIST, TABLE, RAW only
  - import: Import symbol - supports LIST, TABLE, USAGE, RAW
  - global: Global variable - supports LIST, TABLE, RAW, FORMATTED
  - header: Markdown header - supports LIST, TABLE, RAW, FORMATTED
```

---

## Gaps in Implementation

### 1. **Pipeline/Render Commands Not Exposed** ❌
- `_run_pipeline_command()` exists in `__main__.py` but is NOT exposed as a CLI subcommand
- Pipeline infrastructure exists but isn't integrated into the CLI
- No `via render` command available
- **Gap:** User cannot access pipeline functionality from CLI

### 2. **Render Command Not Exposed** ❌
- Renderer infrastructure fully implemented (List, Table, Diagram, Formatted, Raw, Usage)
- Renderer factory pattern exists with all render types
- But no dedicated `via render` subcommand to use them independently
- Render is only accessible through pipeline system (which itself isn't exposed)
- **Gap:** Cannot invoke renderers directly from CLI

### 3. **Missing Render Abbreviation** ❌
- If render command added, should have `r` abbreviation for consistency
- **Gap:** Incomplete pattern enforcement

### 4. **Pipeline Documentation Missing** ❌
- No `--help` for pipeline syntax
- Users cannot discover the pipeline DSL through CLI
- Pipeline parser exists but is hidden
- **Gap:** No CLI discoverability for advanced features

### 5. **Unimplemented Features** ⚠️
Marked as "NOT IMPLEMENTED YET":
- `--watch` flag in index command (for file change monitoring)

### 6. **Test Coverage Gaps** ⚠️
- 2 tests skipped (likely due to pending implementations)
- Some CLI integration paths not fully tested
- Pipeline execution tests exist but command isn't exposed

---

## Recommendations for Next Steps

### Priority 1: Expose Pipeline/Render Commands
```python
# Add to __main__.py:
# render (r)  - Render indexed results
# pipeline (p) - Execute advanced pipeline queries
```

### Priority 2: Complete Help Text
- Update help to document pipeline syntax
- Add examples for render output types
- Document all symbol type support matrices

### Priority 3: Implement Watch Mode
- Complete `--watch` implementation in IndexCommand
- Add file change detection with automatic re-indexing

### Priority 4: Test Gaps
- Investigate why 2 tests are skipped
- Add integration tests for render command
- Add CLI discovery tests

---

## Test Results

```
Platform: Linux, Python 3.11.2
Test Framework: pytest 9.0.2

✅ 465 PASSED
⏭️  2 SKIPPED
❌ 0 FAILED

Overall: 99.6% PASS RATE
Code Coverage: 80%
```

### Coverage by Module
- `via/core/match_record.py`: 97% (excellent)
- `via/renderers/`: 79-100% (good)
- `via/parsers/`: 83-94% (good)
- `via/db/store.py`: 82% (solid)
- `via/__main__.py`: 17% (low - CLI-focused, hard to test)
- `via/services/indexing.py`: 86% (good)
- `via/pipeline/`: 77-95% (good despite not being exposed)

---

## Architecture Notes

### ArgumentProvider/HelpProvider Pattern
The interface pattern allows polymorphic argument registration and help generation:

```python
# Base interface
class ArgumentProvider:
    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None: pass

# Usage in command class
class MatchCommand(ArgumentProvider, HelpProvider):
    @classmethod
    def add_arguments(cls, parser):
        # Register arguments for all symbol types
        for record_type in MatchRecordFactory._RECORD_TYPES.values():
            # Each type can contribute arguments
        # Register common match arguments
        parser.add_argument('-t', '--type', ...)
        parser.add_argument('-g', '--glob', ...)
        # etc.
```

This design makes the CLI **extensible** - new command types or record types can be added by implementing the interfaces, and they'll automatically appear in help text.

### Benefits
✅ Single source of truth for help text  
✅ Arguments stay with their command classes  
✅ Easy to extend with new commands/types  
✅ `__main__.py` remains simple  
✅ Full test coverage possible  

---

## Commands for Local Testing

```bash
# Start environment
cd /home/drusifer/Projects/via
source venv/bin/activate

# Run all tests
pytest tests/ -q

# Run specific test category
pytest tests/acceptance/test_sprint2_uat.py -v
pytest tests/unit/test_match_record.py -v

# Test CLI
python -m via --help
python -m via i --help      # index
python -m via m --help      # match
python -m via s --help      # stats

# Test abbreviations
python -m via i /path/to/project
python -m via m -t class -g '*'
python -m via s --json
```

---

**Last Updated:** January 22, 2026
