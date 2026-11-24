# TL;DR Summary Template

`bobp tldr` scans project `.py` and `.md` files for a summary block. Other file types are not
included. Use a one-line summary, a blank line, `TLDR:`, then useful content indented by four
spaces. Keep summaries brief and focused on the file's purpose and key information.

Markdown example:

```markdown
Records the payment retry decision and its operational impact.

TLDR:
    Decision: Retry transient failures up to three times.
    Impact: Permanent failures are reported without retry.
```

Python example (module docstring before imports):

```python
"""Retries transient payment failures.

TLDR:
    Applies bounded retries to payment requests and reports permanent failures.
"""
```

Include key symbols in a Python summary only when they help a reader understand the module.
Author names, revision IDs, and license text belong only where project policy requires them.

<!-- RUBRIC-START -->
## Check — TLDR

- [ ] **PASS** — A `.py` or `.md` file has a one-line summary, blank line, exact `TLDR:` marker, and non-empty four-space-indented content.
- [ ] **PASS** — Python summaries are in the module docstring before imports; Markdown summaries appear near the document start.
- [ ] **FAIL** — Marker, placement, indentation, or content is missing; correct the block and confirm it appears in `bobp tldr`.
<!-- RUBRIC-END -->
