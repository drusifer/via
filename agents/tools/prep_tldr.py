#!/usr/bin/env python3
"""
prep_tldr — Gather via symbol data for TLDR sweep sub-agents.

TLDR:
    Uses via as a library to re-index the project then gather symbol data for
    every .py and .md file, writing per-file data files to build/tldr_prep/.
    For .py files: runs UsageRenderer to extract docstrings for all classes,
    functions, and methods. For .md files: lists headers with line numbers.
    Also writes py_files.txt and md_files.txt. Prints every created path.
    Skips symlinks and files under agents/. Supports incremental mode: skips
    files unchanged since last run (tracked in .via/prep_tldr_last_run).
    Usage: python agents/tools/prep_tldr.py [root] [--force]
    Role in the system: pre-step for *ora tldr — run once before launching
    TLDR sub-agents; handles indexing internally.
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from via.core.discovery import FileDiscovery, find_index_db
from via.core.match_record import MatchRecordFactory
from via.db.store import DatabaseStore
from via.parsers.registry import get_global_registry
from via.renderers.usage import UsageRenderer
from via.services.indexing import IndexingService

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
from tldr import find_tldr_with_coords

PREP_DIR = PROJECT_ROOT / 'build' / 'tldr_prep'
FACTORY = MatchRecordFactory()
RENDERER = UsageRenderer()


def symbols_for_file(conn: sqlite3.Connection, abs_path: str) -> list:
    """Query all symbols for a file by absolute path."""
    cur = conn.execute(
        "SELECT symbol_type, symbol_name, qualified_name, file_path, "
        "line_number, byte_offset, byte_length, parent_name "
        "FROM symbols WHERE file_path = ? ORDER BY line_number",
        (abs_path,)
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def py_data(abs_path: str, rows: list) -> str:
    """Use UsageRenderer (grouped by file) to emit terse docstring data."""
    docstring_rows = [r for r in rows if r['symbol_type'] in ('class', 'function', 'method')]
    if not docstring_rows:
        return "(no classes, functions, or methods)\n"
    records = [FACTORY.create_from_row(r) for r in docstring_rows]
    return RENDERER.render(iter(records))


def md_data(abs_path: str, rows: list) -> str:
    """List headers with line numbers."""
    headers = [r for r in rows if r['symbol_type'] == 'header']
    if not headers:
        return "(no headers)\n"
    return "\n".join(f"  header {r['symbol_name']} (line {r['line_number']})" for r in headers) + "\n"


def _assemble(symbol_section: str, tldr: dict | None) -> str:
    """Combine symbol data with existing TLDR coordinates."""
    parts = [symbol_section.rstrip()]
    if tldr:
        parts.append(
            f"\nEXISTING TLDR (lines {tldr['start_line']}-{tldr['end_line']}, "
            f"bytes {tldr['start_byte']}-{tldr['end_byte']}):\n"
            f"{tldr['one_liner']}\n\n"
            f"TLDR:\n{tldr['block_text']}"
        )
    else:
        parts.append("\nEXISTING TLDR: (none)")
    return '\n'.join(parts) + '\n'


def safe_name(rel_path: str) -> str:
    return rel_path.replace('/', '_').replace('\\', '_')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Prepare per-file TLDR data for Oracle sub-agents.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('root', nargs='?', default=None,
                        help='Project root directory (default: auto-detect from script location)')
    parser.add_argument('--force', '-f', action='store_true', default=False,
                        help='Regenerate all files, ignoring last-run timestamp')
    return parser.parse_args()


def read_last_run(last_run_path: Path) -> Optional[float]:
    """Read last-run timestamp. Returns None if file absent or invalid."""
    try:
        return float(last_run_path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def write_last_run(last_run_path: Path) -> None:
    """Write current time as last-run timestamp."""
    last_run_path.write_text(str(time.time()))


def get_changed_files(conn: sqlite3.Connection, all_files: list, last_run: float) -> Tuple[list, list]:
    """Return (changed_files, skipped_files) based on symbols.mtime in DB."""
    changed, skipped = [], []
    for f in all_files:
        cur = conn.execute(
            "SELECT MAX(mtime) FROM symbols WHERE file_path = ?", (f.path,)
        )
        row = cur.fetchone()
        file_mtime = row[0] if row and row[0] is not None else None
        # None mtime means file has no indexed symbols — reprocess to pick up new content
        if file_mtime is None or file_mtime > last_run:
            changed.append(f)
        else:
            skipped.append(f)
    return changed, skipped


def main():
    args = parse_args()
    root = Path(args.root).resolve() if args.root else PROJECT_ROOT

    # Re-index before gathering data
    db_dir = root / '.via'
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / 'index.db'
    db_store = DatabaseStore(str(db_path), str(root))
    db_store.connect()
    db_store.initialize_schema()
    service = IndexingService(db_store, get_global_registry())
    service.index(str(root))
    db_store.close()

    conn = sqlite3.connect(str(db_path))

    # Determine incremental mode
    last_run_path = db_dir / 'prep_tldr_last_run'
    last_run = None if args.force else read_last_run(last_run_path)

    discovery = FileDiscovery(str(root))
    all_files = discovery.discover()

    def keep(f) -> bool:
        p = Path(f.path)
        if p.is_symlink():
            return False
        try:
            p.relative_to(root / 'agents')
            return False
        except ValueError:
            return True

    py_files = [f for f in all_files if keep(f) and Path(f.path).suffix in ('.py', '.pyx', '.pyi')]
    md_files = [f for f in all_files if keep(f) and Path(f.path).suffix in ('.md', '.markdown')]
    source_files = py_files + md_files

    def data_file(f) -> Path:
        rel = str(Path(f.path).relative_to(root))
        return PREP_DIR / f'{safe_name(rel)}_data.txt'

    if last_run is not None:
        # Incremental: compute changed vs skipped
        py_changed, py_skipped = get_changed_files(conn, py_files, last_run)
        md_changed, md_skipped = get_changed_files(conn, md_files, last_run)
        total_changed = len(py_changed) + len(md_changed)
        total_skipped = len(py_skipped) + len(md_skipped)
        last_run_dt = datetime.fromtimestamp(last_run).isoformat(timespec='seconds')
        print(f"Incremental mode: last run {last_run_dt}. Processing {total_changed} changed files ({total_skipped} skipped).")

        # Remove data files for sources that no longer exist
        existing_paths = {f.path for f in source_files}
        if PREP_DIR.exists():
            for data in PREP_DIR.iterdir():
                if data.name in ('py_files.txt', 'md_files.txt'):
                    continue
                if not any(data == data_file(f) for f in source_files if f.path in existing_paths):
                    data.unlink()

        PREP_DIR.mkdir(exist_ok=True)
        created = []

        # Always rewrite the file lists (they reflect current state)
        py_list = PREP_DIR / 'py_files.txt'
        py_list.write_text('\n'.join(f'{f.path}\t{data_file(f)}' for f in py_files) + '\n')
        created.append(py_list)

        md_list = PREP_DIR / 'md_files.txt'
        md_list.write_text('\n'.join(f'{f.path}\t{data_file(f)}' for f in md_files) + '\n')
        created.append(md_list)

        # Process only changed files
        for f in py_changed:
            rows = symbols_for_file(conn, f.path)
            tldr = find_tldr_with_coords(f.path)
            content = _assemble(py_data(f.path, rows), tldr)
            out = data_file(f)
            out.write_text(content)
            created.append(out)

        for f in md_changed:
            rows = symbols_for_file(conn, f.path)
            tldr = find_tldr_with_coords(f.path)
            content = _assemble(md_data(f.path, rows), tldr)
            out = data_file(f)
            out.write_text(content)
            created.append(out)

    else:
        # Full mode: process everything
        print(f"Full mode: processing {len(source_files)} files.")

        # Clean up stale data files from previous runs
        if PREP_DIR.exists():
            for stale in PREP_DIR.iterdir():
                stale.unlink()

        PREP_DIR.mkdir(exist_ok=True)
        created = []

        py_list = PREP_DIR / 'py_files.txt'
        py_list.write_text('\n'.join(f'{f.path}\t{data_file(f)}' for f in py_files) + '\n')
        created.append(py_list)

        md_list = PREP_DIR / 'md_files.txt'
        md_list.write_text('\n'.join(f'{f.path}\t{data_file(f)}' for f in md_files) + '\n')
        created.append(md_list)

        for f in py_files:
            rows = symbols_for_file(conn, f.path)
            tldr = find_tldr_with_coords(f.path)
            content = _assemble(py_data(f.path, rows), tldr)
            out = data_file(f)
            out.write_text(content)
            created.append(out)

        for f in md_files:
            rows = symbols_for_file(conn, f.path)
            tldr = find_tldr_with_coords(f.path)
            content = _assemble(md_data(f.path, rows), tldr)
            out = data_file(f)
            out.write_text(content)
            created.append(out)

    conn.close()

    # Write last-run timestamp after successful completion
    write_last_run(last_run_path)

    for path in created:
        print(path)


if __name__ == '__main__':
    main()
