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
| Find subclasses of X | `["-mg", "*", "-tc", "--via", "inherits-from", "-mg", "X", "-tc"]` |
| Find callers of X | `["-mg", "*", "-tf", "--via", "calls", "-mg", "X", "-tf"]` |
| Find files declaring X | `["-mg", "*", "-tF", "--via", "declares", "-mg", "X"]` |

Relationship stages filter the initial result stage. A query for “symbols declared in file” is not a relationship shortcut here; use result-stage-first queries, or a future task-language helper when available.
