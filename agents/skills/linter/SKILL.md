---
name: linter
description: Run code quality checks including linting, type checking, dead code detection, duplication, and complexity analysis.
triggers: ["*qa lint", "*qa quality", "*qa check"]
---

# Linter Skill

## Overview

This skill provides code quality analysis tools for Python projects. Use these commands to catch issues before they become problems.

## Quick Reference

| Check | Command |
|-------|---------|
| All quality checks | `make lint` (if available) |
| Style (PEP-8) | `source .venv/bin/activate && pylint via/` |
| Type checking | `source .venv/bin/activate && mypy via/` |
| Dead code | `source .venv/bin/activate && vulture via/` |
| Complexity | `source .venv/bin/activate && radon cc via/ -a` |
| Duplication | `source .venv/bin/activate && pylint --disable=all --enable=duplicate-code via/` |

## Commands

### Style & Conventions (pylint)
```bash
source .venv/bin/activate && pylint via/
```
Checks PEP-8 compliance, code smells, and common errors.

**Common flags:**
- `--disable=C0114,C0115,C0116` - Disable missing docstring warnings
- `--fail-under=8` - Fail if score below 8/10
- `-r n` - No full report, just issues

### Type Checking (mypy)
```bash
source .venv/bin/activate && mypy via/
```
Static type analysis using type hints.

**Common flags:**
- `--strict` - Enable all strict checks
- `--ignore-missing-imports` - Skip untyped dependencies

### Dead Code Detection (vulture)
```bash
source .venv/bin/activate && vulture via/
```
Finds unused code (functions, variables, imports).

**Common flags:**
- `--min-confidence 80` - Only report high-confidence dead code
- `--exclude "tests/"` - Exclude test directory

### Complexity Analysis (radon)
```bash
# Cyclomatic complexity
source .venv/bin/activate && radon cc via/ -a -s

# Maintainability index
source .venv/bin/activate && radon mi via/ -s
```

**Complexity grades:**
- A (1-5): Low - simple
- B (6-10): Low - well structured
- C (11-20): Moderate - slightly complex
- D (21-30): More than moderate - more complex
- E (31-40): High - complex, alarming
- F (41+): Very high - error-prone, unstable

### Duplication Detection
```bash
source .venv/bin/activate && pylint --disable=all --enable=duplicate-code via/
```

## Installation

If tools are missing, install them:
```bash
source .venv/bin/activate && pip install pylint mypy vulture radon
```

## Workflow

1. **Before PR**: Run full lint suite
2. **On failure**: Fix issues by priority (errors > warnings > style)
3. **Complexity**: Refactor functions with grade C or worse
4. **Dead code**: Remove or mark as `# vulture: ignore`

## Integration with Trin

Trin uses this skill for:
- `*qa lint` - Run pylint on changed files
- `*qa quality` - Full quality report
- `*qa check` - Pre-commit quality gate
