---
name: test-runner
description: Run tests using the project Makefile. Use for executing test suites, running specific tests, and validating code changes.
triggers: ["*test", "*qa test"]
---

# Test Runner Skill

## Overview

This skill provides standardized test execution using the project's Makefile. All test commands should go through `make` to ensure consistent environment setup.

## Commands

### Run All Tests
```bash
make test
```
Runs the complete test suite with pytest.

### Run Specific Test File
```bash
source .venv/bin/activate && pytest tests/unit/test_store.py -v
```

### Run Tests Matching Pattern
```bash
source .venv/bin/activate && pytest -k "test_pattern" -v
```

### Run with Coverage
```bash
source .venv/bin/activate && pytest --cov=via tests/ -v
```

## Quick Reference

| Action | Command |
|--------|---------|
| All tests | `make test` |
| Unit tests only | `source .venv/bin/activate && pytest tests/unit/ -v` |
| Integration tests | `source .venv/bin/activate && pytest tests/integration/ -v` |
| Single file | `source .venv/bin/activate && pytest tests/unit/test_X.py -v` |
| By pattern | `source .venv/bin/activate && pytest -k "pattern" -v` |
| Verbose output | Add `-v` or `-vv` flag |
| Stop on first fail | Add `-x` flag |

## Workflow

1. **Before testing**: Ensure dependencies are installed (`make install`)
2. **Run tests**: Use appropriate command from above
3. **On failure**: Read error output, identify failing test, fix issue
4. **Re-run**: Run specific failing test first, then full suite

## Integration with Personas

- **Neo** (`*swe test`): Run tests after implementing changes
- **Trin** (`*qa test`): Run full test suite for verification
