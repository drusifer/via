# Project Capabilities

via: enabled

## MCP Tool

Use `mcp__via__via_query` to query the indexed codebase instead of Grep/Glob/Read where possible.
The via index covers all Python, JavaScript, TypeScript, and Markdown files in this project.

## Quick Reference

| Task | Args |
|------|------|
| Find a class | `["-mg", "*ClassName*", "-tc"]` |
| Find a function | `["-mg", "*func_name*", "-tf"]` |
| Find a file | `["-mg", "*filename*", "-tF"]` |
| Find a markdown section | `["-mg", "*SectionName*", "-tH"]` |
| Find subclasses of X | `["-mg", "X", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"]` |
| Find callers of X | `["-mg", "X", "-tf", "--via", "calls", "-mg", "*", "-tf"]` |
| Find all symbols in a file | `["-mg", "path/to/file.py", "-tF", "-Q", "--via", "declares", "-mg", "*"]` |
