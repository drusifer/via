# VIA Output Formats Specification

TL;DR: Reference for formatting search results using list, table, raw source, highlighted code, usage docstrings, and JSON formats.

## Table of Contents

- [Output Formats](#output-formats)
- [List Output](#list-output-default)
- [Table Output](#table-output)
- [Raw Source Output](#raw-source-output)
- [Formatted Output](#formatted-output-syntax-highlighting)
- [Usage Output](#usage-output-docstrings)

---

## Output Formats

Output flags control how results are rendered:

| Flag | Format | Description |
|------|--------|-------------|
| `-oL` | List | One result per line (default) |
| `-oT` | Table | ASCII table format |
| `-oR` | Raw | Source code extraction |
| `-oF` | Formatted | Syntax-highlighted source |
| `-oU` | Usage | Renders the docstring of the matched symbol |
| `-oJ` | JSON | JSON array of symbol objects (AI agents / MCP) |

### Format Modifiers (-f<X>)

These secondary flags control the output encoding (for use with `-oR`, `-oF`, `-oT`, etc.):

| Flag | Format |
|------|--------|
| `-fa` | ASCII (terminal colors) |
| `-fm` | Markdown |
| `-fh` | HTML |
| `-fp` | PNG image |

### List Output (Default)

```bash
via -mg '*' -tc -n 3
```

Output:
```
class:via/core/types.py:35:MatchOp:@890+120
class:via/core/types.py:58:MatchResult:@1234+340
class:via/db/store.py:42:DatabaseStore:@1456+8900
```

### Table Output

```bash
via -mg '*Record' -tc -oT
```

Output:
```
| Type  | Name               | File                    | Line | Qualified Name       |
|-------|--------------------|-------------------------|------|----------------------|
| class | MatchRecord        | via/core/match_record.py | 41  | MatchRecord          |
| class | ClassMatchRecord   | via/core/match_record.py | 89  | ClassMatchRecord     |
| class | MethodMatchRecord  | via/core/match_record.py | 112 | MethodMatchRecord    |
```

### Raw Source Output

```bash
via -mg 'extract_source' -tf -oR
```

Output:
```
############################################################
# via/renderers/utils/source_extraction.py:21-67
#     function *extract_source*
############################################################
def extract_source(
    file_path: str,
    byte_offset: Optional[int],
    byte_length: Optional[int],
    before_context: int = 0,
    after_context: int = 0,
    read_full_file: bool = False
) -> str:
    """Extract source code from file."""
    ...
```

### Formatted Output (Syntax Highlighting)

```bash
via -mg 'Renderer' -tc -oF -n 1
```

Output shows syntax-highlighted Python code with ANSI colors.

---


### Usage Output (Docstrings)

```bash
via -mg 'MyClassName' -tc -oU
```

Output:
```
############################################################
# via/my_module.py:123
#     class *MyClassName*
############################################################
This is the docstring for MyClassName.
It can be multiple lines.
```

