# Flag Groups Implementation Plan

**Author**: @Neo
**Date**: 2026-01-23
**Status**: Draft
**Effort**: 4-6 hours

---

## Summary

Refactor CLI flags into consistent prefix-based groups. Clean break, no backward compat. KISS.

---

## Flag Groups

| Group | Prefix | Purpose |
|-------|--------|---------|
| Match | `-m` | Pattern matching method |
| Type | `-t` | Symbol type to search |
| Output | `-o` | How to render results |
| Format | `-f` | Output format |

---

## Match Syntax (`-m<X>`)

| Flag | Long | Description |
|------|------|-------------|
| `-mg` | `--match-glob` | Shell glob (*, ?) |
| `-mr` | `--match-regex` | Python regex |
| `-ms` | `--match-sql` | SQL LIKE (%, _) |

---

## Symbol Type (`-t<X>`)

| Flag | Long | Description |
|------|------|-------------|
| `-tc` | `--type-class` | Classes |
| `-tf` | `--type-function` | Functions |
| `-tm` | `--type-method` | Methods |
| `-ti` | `--type-import` | Imports |
| `-tg` | `--type-global` | Globals |
| `-tF` | `--type-filepath` | File paths |
| `-tN` | `--type-filename` | File names |
| `-tH` | `--type-header` | Markdown headers |

---

## Output (`-o<X>`) - Already exists

| Flag | Long | Description |
|------|------|-------------|
| `-oL` | `--output-list` | List format |
| `-oT` | `--output-table` | Table format |
| `-oD` | `--output-diagram` | Mermaid diagram |
| `-oU` | `--output-usage` | Usage refs |
| `-oR` | `--output-raw` | Raw source |
| `-oF` | `--output-formatted` | Syntax highlighted |

---

## Format (`-f<X>`)

| Flag | Long | Description |
|------|------|-------------|
| `-fa` | `--format-ascii` | Terminal colors |
| `-fm` | `--format-markdown` | Markdown |
| `-fh` | `--format-html` | HTML |
| `-fp` | `--format-png` | PNG image |

---

## Examples

```bash
# Find classes matching glob, render as diagram
via -mg '*Match*' -tc -oD

# Find functions matching regex, render as table in markdown
via -mr '^test_.*' -tf -oT -fm

# Find headers, output raw
via -mg 'API*' -tH -oR
```

---

## Implementation

### Phase 1: Flag Registry (1h)

Create `via/core/flag_groups.py`:

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class FlagGroup(Enum):
    MATCH = 'm'
    TYPE = 't'
    OUTPUT = 'o'
    FORMAT = 'f'

@dataclass
class Flag:
    group: FlagGroup
    suffix: str
    long_name: str
    dest: str
    const: Optional[str]
    help: str

    @property
    def short(self) -> str:
        return f"-{self.group.value}{self.suffix}"

    @property
    def long(self) -> str:
        return f"--{self.long_name}"

MATCH_FLAGS = [
    Flag(FlagGroup.MATCH, 'g', 'match-glob', 'pattern', None, 'Glob pattern'),
    Flag(FlagGroup.MATCH, 'r', 'match-regex', 'pattern', None, 'Regex pattern'),
    Flag(FlagGroup.MATCH, 's', 'match-sql', 'pattern', None, 'SQL LIKE pattern'),
]

TYPE_FLAGS = [
    Flag(FlagGroup.TYPE, 'c', 'type-class', 'symbol_type', 'class', 'Classes'),
    Flag(FlagGroup.TYPE, 'f', 'type-function', 'symbol_type', 'function', 'Functions'),
    Flag(FlagGroup.TYPE, 'm', 'type-method', 'symbol_type', 'method', 'Methods'),
    Flag(FlagGroup.TYPE, 'i', 'type-import', 'symbol_type', 'import', 'Imports'),
    Flag(FlagGroup.TYPE, 'g', 'type-global', 'symbol_type', 'global', 'Globals'),
    Flag(FlagGroup.TYPE, 'F', 'type-filepath', 'symbol_type', 'filepath', 'File paths'),
    Flag(FlagGroup.TYPE, 'N', 'type-filename', 'symbol_type', 'filename', 'File names'),
    Flag(FlagGroup.TYPE, 'H', 'type-header', 'symbol_type', 'header', 'Headers'),
]

FORMAT_FLAGS = [
    Flag(FlagGroup.FORMAT, 'a', 'format-ascii', 'format', 'ascii', 'Terminal'),
    Flag(FlagGroup.FORMAT, 'm', 'format-markdown', 'format', 'md', 'Markdown'),
    Flag(FlagGroup.FORMAT, 'h', 'format-html', 'format', 'html', 'HTML'),
    Flag(FlagGroup.FORMAT, 'p', 'format-png', 'format', 'png', 'PNG'),
]
```

### Phase 2: Update Parser (2h)

Update `via/pipeline/parser.py`:

1. Import flag definitions
2. Replace hardcoded flags with registry
3. Update `_is_match_stage()` detection

```python
def _create_match_parser(self) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)

    # Match syntax (mutually exclusive)
    syntax_group = parser.add_mutually_exclusive_group()
    for flag in MATCH_FLAGS:
        syntax_group.add_argument(
            flag.short, flag.long,
            dest=flag.dest,
            metavar='PATTERN',
            action=_StoreSyntax,
            syntax=flag.suffix
        )

    # Symbol types
    for flag in TYPE_FLAGS:
        parser.add_argument(
            flag.short, flag.long,
            dest=flag.dest,
            action='store_const',
            const=flag.const
        )

    # Options
    parser.add_argument('-n', '--limit', type=int, default=10)
    parser.add_argument('-I', '--case-insensitive', action='store_true')
    parser.add_argument('-Q', '--qualified', action='store_true')

    return parser
```

### Phase 3: Update Help (1h)

Update `via/__main__.py` to generate grouped help:

```python
def _build_help() -> str:
    lines = ["via - Python codebase search", ""]
    lines.append("Match: -mg GLOB | -mr REGEX | -ms SQL")
    lines.append("Type:  -tc class | -tf func | -tm method | -ti import")
    lines.append("       -tg global | -tF filepath | -tN filename | -tH header")
    lines.append("Output: -oL list | -oT table | -oD diagram | -oU usage | -oR raw")
    lines.append("Format: -fa ascii | -fm markdown | -fh html | -fp png")
    return "\n".join(lines)
```

### Phase 4: Tests (1h)

Add tests in `tests/unit/test_flag_groups.py`:

```python
def test_match_glob():
    stages = PipelineParser().parse(['-mg', '*Match*', '-tc'])
    assert stages[0].args.pattern == '*Match*'
    assert stages[0].args.symbol_type == 'class'

def test_match_regex():
    stages = PipelineParser().parse(['-mr', '^test.*', '-tf'])
    assert stages[0].args.pattern == '^test.*'
    assert stages[0].args.match_syntax == 'r'

def test_output_format():
    stages = PipelineParser().parse(['-mg', '*', '-tc', '--via', '-oT', '-fm'])
    assert stages[1].args.render_type == 'table'
    assert stages[1].args.format == 'md'
```

---

## Files Changed

| File | Change |
|------|--------|
| `via/core/flag_groups.py` | NEW |
| `via/pipeline/parser.py` | Update flags |
| `via/__main__.py` | Update help |
| `tests/unit/test_flag_groups.py` | NEW |
| `tests/unit/test_cli_parser.py` | Update |

---

## Success Criteria

- [ ] New flags work: `-mg`, `-mr`, `-tc`, `-tf`, etc.
- [ ] `--help` shows grouped flags
- [ ] All tests pass
- [ ] Old flags removed (no backward compat)

---

## Next

1. Approve plan
2. TDD: Write tests first
3. Implement flag_groups.py
4. Update parser
5. Update help
6. Run tests
