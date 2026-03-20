# Template for TL;DR summaries

## Standard TLDR Marker

**All files — markdown, Python, and any other text file — use the same marker:**

```
One-line summary of this file.

TLDR:
    [Summary content, can be multiple lines]
    [Indented with exactly 4 spaces]
    [Blank line or dedent ends the block]
```

### Rules
- The label is always `TLDR:` (all caps, colon, no semicolon) on its own line
- Content starts on the **next line**, indented with **exactly 4 spaces**
- A blank line or dedent ends the block
- The line above `TLDR:` must be blank, and above that must be the one-line summary
- **Do not use `TL;DR:`, `tldr:`, or any other variant**

### `make tldr` — how it works

`make tldr` runs `agents/tools/tldr.py`, which uses `via` to discover all `*.py` and `*.md`
files in the project, then reads each for a `TLDR:` block and prints a sorted summary.

To appear in `make tldr` output a file must have:
1. A one-liner summary line
2. A blank line
3. `TLDR:` on its own line
4. Content indented with exactly 4 spaces

---

## Content Forms

Choose the form that fits the content. The `TLDR:` marker is always the same — only what goes inside it changes.

### 1. The "Action-Oriented" Form
**Best for**: Project updates, sprint reviews, or anything where the reader needs to know if they must do something.
```
One-line summary of the update.

TLDR:
    Goal: [Why this matters]
    Status: [Where we are now]
    Action: [What the reader needs to do + Deadline]
```

### 2. The "Context-First" Form
**Best for**: Lengthy articles, research papers, incident reports, or deep-dive notes.
```
One-line summary of the topic.

TLDR:
    [2-3 sentence summary covering Who, What, and Why.]
    Key Insight: [The most important discovery or takeaway.]
    Bottom Line: [The ultimate conclusion or "so what".]
```

### 3. The "BLUF" Form (Bottom Line Up Front)
**Best for**: Decision records, architecture choices, high-stakes memos.
```
One-line statement of the decision or result.

TLDR:
    Impact: [How this affects the project/team.]
    Next Steps: [2-3 immediate milestones.]
```

### 4. The "Technical/Feature" Form
**Best for**: Release notes, sprint docs, feature proposals, bug post-mortems.
```
One-line summary of the change or feature.

TLDR:
    Problem: [What was broken or missing.]
    Solution: [What was implemented.]
    Breaking Changes: [Yes/No + brief detail.]
```

### 5. The "Code Module" Form
**Best for**: Python module docstrings — describes what a file contains and its role in the system.
Place as the module-level docstring at the top of every `.py` file, before imports.

```python
"""
One-line summary of what this module provides.

TLDR:
    [What this module does and why it exists — 2-4 sentences.]
    [Key classes/functions: name each one and what it does.]
    [Role in the system: what consumes this / what it depends on.]
    [Design notes: non-obvious patterns, gotchas — omit if none.]

Author: [Name]
------------------------------------------------------------------------------
$Id: [hash] $

License: GPL-3.0
"""
```

**Field guidance (Code Module):**
- **First line**: single sentence — shows up in `help()` and IDE hovers
- **TLDR body**: name every public class and function
- **Role**: "consumed by PipelineExecutor", "called by IndexingService", etc.
- **Design notes**: only if non-obvious (thread safety, lazy init, denormalization, etc.)
- **$Id / License**: preserve existing values exactly; omit `$Id` if absent

---

## `make tldr` Discoverability

`make tldr` scans all `*.md` and `*.py` files for `TLDR:` and reports which files have summaries.

To ensure a file shows up in `make tldr`, it must contain the exact marker `TLDR:` (uppercase, colon).
