# VIA Search Pipeline Specification

TL;DR: Complete guide to matching patterns and searching symbols using the pipeline syntax, context options, and natural language query translation.

## Table of Contents

- [Searching with Pipeline Syntax](#searching-with-pipeline-syntax)
- [Context Lines](#context-lines)
- [Natural Language Queries](#natural-language-queries-via-ask--via-q)

---

## Searching with Pipeline Syntax

The recommended way to search uses **pipeline syntax**:

```
via -m<X> PATTERN [-t<Y>...] [-o<Z>] [-f<W>] [OPTIONS]
```

You can specify multiple type flags to search for symbols of different types. For example, `via -mg '*' -tc -tf` will search for all classes and functions.

Use `--via <rel>` to add a relationship stage — see [Relationship Queries](#relationship-queries).

### Pattern Flags

| Flag | Type | Wildcards | Example |
|------|------|-----------|---------|
| `-mg` | Glob (default) | `*` any, `?` single | `-g '*save*'` |
| `-ms` | SQL LIKE | `%` any, `_` single | `-s '%save%'` |
| `-mr` | Regex | Full regex | `-r '^test_.*'` |

### Type Flags

| Flag | Type | Description |
|------|------|-------------|
| `-tc` | class | Class definitions |
| `-tm` | method | Class methods |
| `-tf` | function | Top-level functions |
| `-ti` | import | Import statements |
| `-tg` | global | Module-level variables |
| `-tF` | filepath | Full file paths |
| `-tN` | filename | File names only |
| `-tH` | header | Markdown headers |

**Omit type flags to search all symbol types.**

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n N` | Limit results | 10 |
| `-n 0` | Unlimited results | - |
| `-I` | Case-insensitive matching (all patterns are case-sensitive by default) | Off |
| `-Q` | Match against qualified name (useful with `-tF` for full-path matching) | Off |
| `--newerthan DURATION` | Only symbols from files modified within duration (e.g. `1h`, `2d`, `1w`) | Off |
| `--olderthan DURATION` | Only symbols from files NOT modified within duration | Off |

### Examples

```bash
# All classes
via -mg '*' -tc

# Classes ending with "Manager"
via -mg '*Manager' -tc

# Test functions (first 5)
via -mg 'test_*' -tf -n 5

# Methods containing "save" (case-insensitive)
via -mg '*save*' -tm -I

# All symbols matching "main"
via -mg '*main*'

# Unlimited results
via -mg '*' -tf -n 0
```

---

---

## Context Lines

Show surrounding code with raw (`-oR`) or formatted (`-oF`) output:

| Flag | Description |
|------|-------------|
| `-B N` | N lines before match |
| `-A N` | N lines after match |
| `-C N` | N lines before AND after |

### Examples

```bash
# Show 3 lines before the match
via -mg 'main' -tf -oR -B 3

# Show 5 lines after the match
via -mg 'User' -tc -oF -A 5

# Show 2 lines on each side
via -mg 'save' -tm -oR -C 2
```

### Disable Headers

Use `--nodelims` to remove the delimiter headers between matches:

```bash
via -mg '*' -tf -oR --nodelims
```

---

---

## Natural Language Queries (`via ask` / `via q`)

VIA includes a local, fast, deterministic natural query interpreter that compiles simplified English-like queries directly into standard VIA pipeline commands.

### Usage

```bash
via ask "find functions calling classes matching *Widget*"
via q "locate all classes extending class matching *Controller*"
```

To view the compiled VIA command without executing it, append `--dry-run` or `-d`:

```bash
via ask --dry-run "find functions calling classes matching *Widget*"
# Outputs: via -mg "*" -tf --via calls -mg "*Widget*" -tc -fm
```

### Grammar Vocabulary

| English Phrase | VIA Equivalent / Stage |
|---|---|
| **Action Prefixes** *(optional)* | `find`, `show me`, `list`, `locate`, `get`, `search for` |
| **Noise Articles** *(optional)* | `the`, `a`, `an` |
| **Target Nouns** | `class`/`classes` (`-tc`), `function`/`functions` (`-tf`), `method`/`methods` (`-tm`), `file`/`files` (`-tF`), `global`/`globals`/`variable`/`variables`/`constant`/`constants` (`-tg`), `import`/`imports` (`-ti`), `header`/`headers`/`section`/`sections` (`-tH`) |
| **Matchers** | `matching '*pattern*'`, `named '*pattern*'`, `whose name contains '*pattern*'` (`-mg`), `matching regex '<pattern>'` (`-mr`) |
| **Relational Chains** | `that call`/`calling` (`--via calls`), `called by` (`--via called-by`), `that reference`/`referencing` (`--via references`), `referenced by` (`--via referenced-by`), `that inherit from`/`extending`/`extend` (`--via inherits-from`), `inherited by`/`extended by` (`--via inherited-by`), `http calls to` (`--via http-calls`), etc. |
| **Negated Filters** | `do not call`/`not calling` (`--sans calls`), `do not reference`/`not referencing` (`--sans references`), `do not inherit from`/`not extending` (`--sans inherits-from`), `do not import`/`not importing` (`--sans imports`) |
| **Limit Modifiers** | `all` (`-n 0` to disable default result limit) |
| **Result Bounds** | `first N rows`/`top N matches` (`-n N`), `last N matches` (`--slice -N:`), `between rows X and Y` (`--slice (X-1):Y`), `from row X` (`--slice (X-1):`) |

### Example Queries

- **Basic search**: `find classes matching '*Controller*'`
- **Case-insensitive search**: `locate all classes matching '*Service*' ignoring case`
- **Result paging bounds**: `get first 10 methods matching 'save*'`
- **Negative bounds**: `show last 50 files matching '*.py'`
- **Relationship chaining**: `find functions calling classes matching '*Widget*' that extend BaseWidget`
- **Negated relationship**: `classes extending class matching '*Controller*' not calling methods matching '*post*'`
