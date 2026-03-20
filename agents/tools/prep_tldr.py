#!/usr/bin/env python3
"""
prep_tldr — Gather via symbol data for TLDR sweep sub-agents.

TLDR:
    Uses via as a library to re-index the project then gather symbol data for
    every .py and .md file, writing per-file data files to build/tldr_prep/.
    For .py files: runs UsageRenderer to extract docstrings for all classes,
    functions, and methods. For .md files: lists headers with line numbers.
    Also writes py_files.txt and md_files.txt. Prints every created path.
    Skips symlinks and files under agents/. Usage: python agents/tools/prep_tldr.py [project_root]
    Role in the system: pre-step for *ora tldr — run once before launching
    TLDR sub-agents; handles indexing internally.
"""

import sqlite3
import sys
from pathlib import Path

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


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PROJECT_ROOT

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

    # Clean up stale data files from previous runs before reindexing
    if PREP_DIR.exists():
        for stale in PREP_DIR.iterdir():
            stale.unlink()

    PREP_DIR.mkdir(exist_ok=True)
    created = []

    def data_file(f) -> Path:
        rel = str(Path(f.path).relative_to(root))
        return PREP_DIR / f'{safe_name(rel)}_data.txt'

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
        rel = str(Path(f.path).relative_to(root))
        out = PREP_DIR / f'{safe_name(rel)}_data.txt'
        out.write_text(content)
        created.append(out)

    for f in md_files:
        rows = symbols_for_file(conn, f.path)
        tldr = find_tldr_with_coords(f.path)
        content = _assemble(md_data(f.path, rows), tldr)
        rel = str(Path(f.path).relative_to(root))
        out = PREP_DIR / f'{safe_name(rel)}_data.txt'
        out.write_text(content)
        created.append(out)

    conn.close()

    for path in created:
        print(path)


if __name__ == '__main__':
    main()
