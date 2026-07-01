# VIA Temporal Queries Specification

TL;DR: Reference guide for filtering symbols based on file modification durations using newerthan and olderthan filters.

## Table of Contents

- [Temporal Queries](#temporal-queries)
- [Duration Format](#duration-format)
- [Examples](#examples)

---

## Temporal Queries

Filter symbols by when their source file was last modified. Useful for finding recently changed code or stale symbols.

### Syntax

```
via -m<X> PATTERN -t<Y> --newerthan DURATION
via -m<X> PATTERN -t<Y> --olderthan DURATION
```

### Duration Format

Human-friendly durations: `30s`, `5m`, `2h`, `1d`, `1w`

| Unit | Example | Meaning |
|------|---------|---------|
| `s` | `30s` | 30 seconds |
| `m` | `5m` | 5 minutes |
| `h` | `2h` | 2 hours |
| `d` | `1d` | 1 day |
| `w` | `1w` | 1 week |

### Examples

```bash
# Classes in files modified in the last hour
via -mg '*' -tc --newerthan 1h

# All symbols changed today
via -mg '*' --newerthan 1d -n 0

# Functions in files not touched in over a week (stale code)
via -mg '*' -tf --olderthan 1w

# Recently changed test functions
via -mg 'test_*' -tf --newerthan 2d
```

> **Note**: Timestamps are per-symbol. Watch mode updates symbol mtimes as files change — only modified symbols get new timestamps, not all symbols in the file.

---
