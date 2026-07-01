#!/usr/bin/env python3
"""
chat_merge.py — Sort agents/CHAT.md chronologically, inferring times for
date-only timestamps by interpolating between their dated neighbours.

Usage:
    python agents/tools/chat_merge.py [--file PATH] [--dry-run]

Default: agents/CHAT.md (in-place rewrite with backup at .bak).

Algorithm for date-only timestamps (e.g. <small>2026-06-24</small>):
  1. Find the previous block with a full datetime → t_before
  2. Find the next block with a full datetime   → t_after
  3. Assign the midpoint (or distribute evenly if several consecutive date-only blocks)
  4. Sort all blocks by assigned datetime
  5. Rewrite timestamps of inferred blocks to show the assigned time
"""

import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

CHAT_DEFAULT = Path('agents/CHAT.md')
TS_FULL_RE = re.compile(r'^(\[<small>)([\d]{4}-[\d]{2}-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2})(</small>\])')
TS_DATE_RE = re.compile(r'^(\[<small>)([\d]{4}-[\d]{2}-[\d]{2})(</small>\])')
BLOCK_SEP = '\n---\n'


def parse_blocks(text: str) -> tuple[str, list[str]]:
    """Return (header, [block, ...]) where each block starts with its timestamp line."""
    # Header = everything up to the first timestamp line
    first = re.search(r'(?:^|\n)---\n(?=\[<small>)', text)
    if first:
        header = text[:first.start()]
        body = text[first.start():]
    else:
        header = ''
        body = text

    raw = re.split(r'\n---\n(?=\[<small>)', body.lstrip('\n').lstrip('-').lstrip('\n'))
    return header, [b for b in raw if b.strip()]


def block_ts(block: str) -> tuple[datetime | None, bool]:
    """
    Return (datetime, is_inferred).
    is_inferred=True when only a date (no time) was present.
    """
    first = block.split('\n')[0]
    m = TS_FULL_RE.match(first)
    if m:
        return datetime.fromisoformat(m.group(2)), False
    m = TS_DATE_RE.match(first)
    if m:
        # Midnight as placeholder; will be replaced by interpolation
        return datetime.fromisoformat(m.group(2) + ' 00:00:00'), True
    return None, False


def interpolate(blocks: list[str]) -> list[tuple[datetime, str]]:
    """
    Assign a definitive datetime to every block.
    Date-only blocks get a time interpolated between their full-datetime neighbours.
    """
    parsed: list[tuple[datetime, bool, str]] = []
    for b in blocks:
        dt, inferred = block_ts(b)
        if dt is None:
            # Malformed — treat as epoch so it sorts to the top
            dt = datetime(2000, 1, 1)
            inferred = True
        parsed.append((dt, inferred, b))

    # Interpolate runs of inferred timestamps
    n = len(parsed)
    result: list[tuple[datetime, str]] = []
    i = 0
    while i < n:
        dt, inferred, b = parsed[i]
        if not inferred:
            result.append((dt, b))
            i += 1
        else:
            # Collect the run of inferred blocks
            run_start = i
            while i < n and parsed[i][1]:
                i += 1
            run_end = i  # exclusive

            # Anchor times
            t_before = parsed[run_start - 1][0] if run_start > 0 else None
            t_after  = parsed[run_end][0]     if run_end < n   else None

            run_len = run_end - run_start

            if t_before is None and t_after is None:
                # No anchors — keep midnight placeholder
                for j in range(run_start, run_end):
                    result.append((parsed[j][0], parsed[j][2]))
            elif t_before is None:
                # Only right anchor — back-fill with 1-minute steps before t_after
                for j in range(run_start, run_end):
                    offset = run_len - (j - run_start)
                    result.append((t_after - timedelta(minutes=offset), parsed[j][2]))
            elif t_after is None:
                # Only left anchor — forward-fill with 1-minute steps after t_before
                for j in range(run_start, run_end):
                    result.append((t_before + timedelta(minutes=(j - run_start + 1)), parsed[j][2]))
            else:
                # Both anchors — distribute evenly in the interval
                span = (t_after - t_before).total_seconds()
                step = span / (run_len + 1)
                for j in range(run_start, run_end):
                    assigned = t_before + timedelta(seconds=step * (j - run_start + 1))
                    result.append((assigned, parsed[j][2]))

    return result


def rewrite_ts(block: str, assigned: datetime) -> str:
    """Replace date-only timestamp with full datetime in block text."""
    first, *rest = block.split('\n', 1)
    m = TS_DATE_RE.match(first)
    if m:
        new_ts = assigned.strftime('%Y-%m-%d %H:%M:%S')
        new_first = m.group(1) + new_ts + m.group(3) + first[m.end():]
        return new_first + ('\n' + rest[0] if rest else '')
    return block


def merge(path: Path, dry_run: bool = False) -> None:
    text = path.read_text()
    header, blocks = parse_blocks(text)

    if not blocks:
        print('No message blocks found.')
        return

    assigned = interpolate(blocks)

    # Sort by assigned datetime (stable)
    assigned.sort(key=lambda x: x[0])

    # Rewrite date-only blocks with inferred times
    rewritten = []
    for dt, block in assigned:
        _, inferred = block_ts(block)
        rewritten.append((dt, rewrite_ts(block, dt) if inferred else block))

    # Reconstruct file
    body = BLOCK_SEP.join(b for _, b in rewritten)
    output = header.rstrip('\n') + '\n\n---\n' + body + '\n'

    if dry_run:
        # Track which original blocks had date-only timestamps (before rewriting)
        orig_inferred = {id(b): block_ts(b)[1] for b in blocks}
        orig_positions = {id(b): i for i, b in enumerate(blocks)}
        changes = 0
        inferred_count = 0
        for new_i, (dt, b) in enumerate(rewritten):
            was_inferred = orig_inferred.get(id(b), False)
            orig_i = orig_positions.get(id(b))
            if was_inferred:
                inferred_count += 1
                print(f'  [inferred → {dt:%H:%M:%S}] {b.split(chr(10))[0][:70]}')
            elif orig_i is not None and orig_i != new_i:
                changes += 1
                print(f'  [reordered {orig_i}→{new_i}] {b.split(chr(10))[0][:70]}')
        print(f'{len(blocks)} blocks · {inferred_count} timestamps inferred · {changes} reordered')
    else:
        bak = path.with_suffix('.md.bak')
        shutil.copy2(path, bak)
        path.write_text(output)
        inferred_count = sum(1 for _, b in assigned if block_ts(b)[1])
        print(f'Merged {len(rewritten)} blocks ({inferred_count} timestamps inferred).')
        print(f'Backup: {bak}')
        print(f'Output: {path}')


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--file', default=str(CHAT_DEFAULT), help='Path to CHAT.md')
    p.add_argument('--dry-run', action='store_true', help='Show what would change without writing')
    args = p.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f'ERROR: {path} not found', file=sys.stderr)
        sys.exit(1)

    merge(path, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
