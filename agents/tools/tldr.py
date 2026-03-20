#!/usr/bin/env python3
"""
Print TLDR: block contents from all *.py and *.md files.

TLDR:
    Scans the project for files containing a TLDR: marker and prints
    each file's one-liner summary and block so agents can orient without
    opening files. Uses via.core.discovery for file discovery (respects
    .gitignore and project layout). Used by `make tldr`.
"""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Ensure via is importable when run directly
sys.path.insert(0, str(PROJECT_ROOT))

from via.core.discovery import FileDiscovery  # noqa: E402

TARGET_EXTENSIONS = {'.py', '.md'}


def find_tldr(path: str) -> tuple[str, list[str]] | None:
    """Return (one_liner, block_lines) for the TLDR block, or None if absent."""
    result = find_tldr_with_coords(path)
    if result is None:
        return None
    return (result['one_liner'], result['block_lines'])


def find_tldr_with_coords(path: str) -> dict | None:
    """Return TLDR block with coordinates, or None if absent.

    Returns dict with: one_liner, block_lines, block_text,
    start_line (1-based), end_line (1-based, inclusive),
    start_byte, end_byte.
    """
    try:
        raw = Path(path).read_bytes()
        lines = raw.decode('utf-8', errors='ignore').splitlines(keepends=True)
    except OSError:
        return None

    for i, line in enumerate(lines):
        if line.strip() != 'TLDR:':
            continue

        one_liner = ''
        if i >= 2 and lines[i - 1].strip() == '':
            one_liner = lines[i - 2].strip()

        block = []
        j = i + 1
        while j < len(lines):
            l = lines[j]
            if not l.strip():
                break
            if l[0] not in (' ', '\t'):
                break
            block.append(l.rstrip())
            j += 1

        if not block:
            return None

        # start_line = one-liner line (or TLDR: line if no one-liner)
        start_idx = (i - 2) if one_liner else i
        end_idx = j - 1  # last line of block (0-based)

        byte_offsets = [0]
        for l in lines:
            byte_offsets.append(byte_offsets[-1] + len(l.encode('utf-8')))

        return {
            'one_liner':   one_liner,
            'block_lines': block,
            'block_text':  '\n'.join(block),
            'start_line':  start_idx + 1,
            'end_line':    end_idx + 1,
            'start_byte':  byte_offsets[start_idx],
            'end_byte':    byte_offsets[end_idx + 1],
        }

    return None


def main():
    discovery = FileDiscovery(
        root_dir=str(PROJECT_ROOT),
        parseable_extensions=TARGET_EXTENSIONS,
    )

    results: list[tuple[str, tuple[str, list[str]]]] = []
    for discovered in discovery.discover():
        ext = Path(discovered.path).suffix
        if ext not in TARGET_EXTENSIONS:
            continue
        result = find_tldr(discovered.path)
        if result:
            rel = os.path.relpath(discovered.path, PROJECT_ROOT)
            results.append((rel, result))

    for rel, (one_liner, block) in sorted(results):
        print(f'{rel}:')
        if one_liner:
            print(one_liner)
        print('TLDR:')
        for line in block:
            print(line)
        print()


if __name__ == '__main__':
    main()
