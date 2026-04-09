"""
Sprint 6 UAT suite validating watch-mode behaviour via subprocess-level acceptance tests.

TLDR:
    Subprocess-level UAT suite for `via index -w` covering eight acceptance criteria
    (UAT-6.1 through UAT-6.8). Key test classes: TestUAT61_Startup (3 tests: blocking,
    watching message, initial index), TestUAT62_FileModification (4 tests: .py/.md
    re-index, symbol count feedback, DB symbol update), TestUAT63_FileCreation (2 tests),
    TestUAT64_FileDeletion (2 tests: removed message, DB cleanup),
    TestUAT65_GracefulShutdown (2 tests: exit-0 on SIGINT, stopped message),
    TestUAT66_NonParseableFilesIgnored (2 tests: .json/.txt ignored),
    TestUAT67_ExclusionPatterns (1 test: --exclude respected),
    TestUAT68_ErrorResilience (1 test: syntax errors don't crash watcher).
    Helpers: _start_watch, _stop_and_collect, _open_db.
    Depends on: via.db.store, via.core.types, subprocess, signal.

Author: Trin (QA)
Sprint: 6
"""

import os
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

from via.core.types import MatchOp, SymbolType
from via.db.store import DatabaseStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STARTUP_WAIT = 1.5   # seconds to wait for initial index + "Watching" message
CHANGE_WAIT = 1.3    # seconds after a filesystem change (debounce 500ms + buffer)


def _start_watch(tmp_path, extra_args=None):
    """Launch `via index -w` as a subprocess. Returns (proc, db_path)."""
    via_dir = tmp_path / ".via"
    via_dir.mkdir(exist_ok=True)
    db_path = str(via_dir / "index.db")

    cmd = [
        sys.executable, "-m", "via", "index", "-w",
        "--db", db_path,
        str(tmp_path),
    ]
    if extra_args:
        cmd.extend(extra_args)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(Path(__file__).parent.parent.parent),
    )
    return proc, db_path


def _stop_and_collect(proc, timeout=8):
    """Send SIGINT, collect all output, return (stdout, stderr, returncode)."""
    try:
        proc.send_signal(signal.SIGINT)
    except ProcessLookupError:
        pass  # already exited
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
    return stdout, stderr, proc.returncode


@contextmanager
def _open_db(db_path, root_dir):
    """Open the index DB for post-run verification."""
    store = DatabaseStore(db_path, str(root_dir))
    store.connect()
    try:
        yield store
    finally:
        store.close()


# ---------------------------------------------------------------------------
# UAT-6.1: Startup — blocks, performs initial index
# ---------------------------------------------------------------------------

class TestUAT61_Startup:
    """AC: via index -w starts, performs initial index, prints watching message."""

    def test_startup_does_not_exit_immediately(self, tmp_path):
        """Process must stay alive (blocking) after launch."""
        (tmp_path / "app.py").write_text("def main(): pass\n")
        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)
        assert proc.poll() is None, "Watch process exited prematurely"
        _stop_and_collect(proc)

    def test_startup_prints_watching_message(self, tmp_path):
        """AC: prints 'Watching <dir> for changes... (Ctrl-C to stop)'"""
        (tmp_path / "app.py").write_text("def main(): pass\n")
        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)
        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "Watching" in combined
        assert "Ctrl-C" in combined

    def test_startup_performs_initial_index(self, tmp_path):
        """AC: on startup, performs a full incremental index."""
        (tmp_path / "models.py").write_text(
            "class User:\n    def save(self): pass\n"
        )
        proc, db_path = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)
        _stop_and_collect(proc)

        # Verify symbols are in the DB
        with _open_db(db_path, tmp_path) as store:
            results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "User"))
        assert len(results) >= 1, "Initial index should have indexed User class"


# ---------------------------------------------------------------------------
# UAT-6.2: File Modification — re-indexes and prints feedback
# ---------------------------------------------------------------------------

class TestUAT62_FileModification:
    """AC: When a supported file is modified, only that file is re-indexed."""

    def test_modify_py_triggers_reindex(self, tmp_path):
        """AC: modified .py file → 'Re-indexed: <path> (<N> symbols)'"""
        py_file = tmp_path / "service.py"
        py_file.write_text("def original(): pass\n")

        proc, db_path = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        # Modify the file
        py_file.write_text("def original(): pass\ndef added(): pass\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "Re-indexed:" in combined
        assert "service.py" in combined

    def test_modify_md_triggers_reindex(self, tmp_path):
        """AC: modified .md file → re-indexed."""
        md_file = tmp_path / "README.md"
        md_file.write_text("# Hello\n")

        proc, db_path = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        md_file.write_text("# Hello\n\n## Section Two\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "Re-indexed:" in combined
        assert "README.md" in combined

    def test_reindex_output_includes_symbol_count(self, tmp_path):
        """AC: feedback includes symbol count."""
        py_file = tmp_path / "module.py"
        py_file.write_text("x = 1\n")

        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        py_file.write_text("class Foo:\n    def bar(self): pass\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "symbol" in combined.lower()

    def test_modify_updates_db_symbols(self, tmp_path):
        """AC: after re-index, new symbols are queryable."""
        py_file = tmp_path / "thing.py"
        py_file.write_text("class OldClass: pass\n")

        proc, db_path = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        py_file.write_text("class NewClass: pass\n")
        time.sleep(CHANGE_WAIT)
        _stop_and_collect(proc)

        with _open_db(db_path, tmp_path) as store:
            new_results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "NewClass"))
            old_results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "OldClass"))

        assert len(new_results) >= 1, "NewClass should be in DB after re-index"
        assert len(old_results) == 0, "OldClass should be gone after re-index"


# ---------------------------------------------------------------------------
# UAT-6.3: File Creation — indexes new files
# ---------------------------------------------------------------------------

class TestUAT63_FileCreation:
    """AC: When a new supported file is created, it is indexed automatically."""

    def test_new_py_file_indexed(self, tmp_path):
        """AC: new .py file → printed and in DB."""
        (tmp_path / "existing.py").write_text("x = 1\n")
        proc, db_path = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        # Create new file
        new_file = tmp_path / "brand_new.py"
        new_file.write_text("class BrandNew:\n    pass\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "brand_new.py" in combined

        with _open_db(db_path, tmp_path) as store:
            results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "BrandNew"))
        assert len(results) >= 1, "BrandNew should be indexed"

    def test_new_md_file_indexed(self, tmp_path):
        """AC: new .md file → indexed."""
        (tmp_path / "seed.py").write_text("pass\n")
        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        new_md = tmp_path / "GUIDE.md"
        new_md.write_text("# Guide\n## Setup\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "GUIDE.md" in combined


# ---------------------------------------------------------------------------
# UAT-6.4: File Deletion — removes symbols from DB
# ---------------------------------------------------------------------------

class TestUAT64_FileDeletion:
    """AC: When a supported file is deleted, its symbols are removed from DB."""

    def test_deleted_file_prints_removed(self, tmp_path):
        """AC: deleted file → 'Removed: <filepath>'"""
        py_file = tmp_path / "doomed.py"
        py_file.write_text("class Doomed: pass\n")

        proc, db_path = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        py_file.unlink()
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "Removed:" in combined
        assert "doomed.py" in combined

    def test_deleted_file_symbols_removed_from_db(self, tmp_path):
        """AC: symbols of deleted file are gone from DB."""
        py_file = tmp_path / "temp_module.py"
        py_file.write_text("class TempClass: pass\n")

        proc, db_path = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        py_file.unlink()
        time.sleep(CHANGE_WAIT)
        _stop_and_collect(proc)

        with _open_db(db_path, tmp_path) as store:
            results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "TempClass"))
        assert len(results) == 0, "TempClass symbols should be removed after file deletion"


# ---------------------------------------------------------------------------
# UAT-6.5: SIGINT — graceful shutdown
# ---------------------------------------------------------------------------

class TestUAT65_GracefulShutdown:
    """AC: Ctrl-C (SIGINT) gracefully stops the watcher and exits cleanly."""

    def test_sigint_exits_zero(self, tmp_path):
        """AC: exits with code 0 on SIGINT."""
        (tmp_path / "app.py").write_text("x = 1\n")
        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)
        _, _, returncode = _stop_and_collect(proc)
        assert returncode == 0

    def test_sigint_prints_stopped_message(self, tmp_path):
        """AC: On Ctrl-C, prints 'Watch mode stopped.'"""
        (tmp_path / "app.py").write_text("x = 1\n")
        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)
        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "stopped" in combined.lower()


# ---------------------------------------------------------------------------
# UAT-6.6: Non-parseable files are ignored
# ---------------------------------------------------------------------------

class TestUAT66_NonParseableFilesIgnored:
    """AC: Non-parseable files (.txt, .json) are not re-indexed on change."""

    def test_json_file_change_not_reported(self, tmp_path):
        """AC: .json file changes produce no 'Re-indexed' output."""
        (tmp_path / "seed.py").write_text("pass\n")
        json_file = tmp_path / "config.json"
        json_file.write_text('{"key": "value"}\n')

        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        json_file.write_text('{"key": "updated"}\n')
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        # config.json should not appear in re-index output
        assert "config.json" not in combined

    def test_txt_file_change_not_reported(self, tmp_path):
        """AC: .txt file changes produce no 'Re-indexed' output."""
        (tmp_path / "seed.py").write_text("pass\n")
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("some notes\n")

        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        txt_file.write_text("updated notes\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        assert "notes.txt" not in combined


# ---------------------------------------------------------------------------
# UAT-6.7: Exclusion patterns — --exclude respected
# ---------------------------------------------------------------------------

class TestUAT67_ExclusionPatterns:
    """AC: Watch mode ignores changes matching --exclude patterns."""

    def test_exclude_pattern_suppresses_reindex(self, tmp_path):
        """AC: files matching --exclude PATTERN are not re-indexed."""
        gen_dir = tmp_path / "generated"
        gen_dir.mkdir()
        gen_file = gen_dir / "schema.py"
        gen_file.write_text("# generated\nx = 1\n")
        (tmp_path / "seed.py").write_text("pass\n")

        proc, _ = _start_watch(tmp_path, extra_args=["--exclude", "generated/"])
        time.sleep(STARTUP_WAIT)

        gen_file.write_text("# generated\nx = 2\ny = 3\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr
        # schema.py in generated/ should be excluded
        assert "schema.py" not in combined


# ---------------------------------------------------------------------------
# UAT-6.8: Error resilience — syntax errors don't crash the watcher
# ---------------------------------------------------------------------------

class TestUAT68_ErrorResilience:
    """AC: Syntax errors are logged and watching continues."""

    def test_syntax_error_does_not_crash_watcher(self, tmp_path):
        """AC: file with syntax error is handled without crashing."""
        (tmp_path / "good.py").write_text("def ok(): pass\n")
        bad_file = tmp_path / "broken.py"
        bad_file.write_text("def fine(): pass\n")

        proc, _ = _start_watch(tmp_path)
        time.sleep(STARTUP_WAIT)

        # Write a syntax error
        bad_file.write_text("def (BROKEN:\n    pass\n")
        time.sleep(CHANGE_WAIT)

        # Watcher should still be alive
        assert proc.poll() is None, "Watcher crashed on syntax error"

        # Modify a good file — should still work
        (tmp_path / "good.py").write_text("def ok(): pass\ndef extra(): pass\n")
        time.sleep(CHANGE_WAIT)

        stdout, stderr, _ = _stop_and_collect(proc)
        combined = stdout + stderr

        # good.py should have been re-indexed despite the earlier error
        assert "good.py" in combined
        assert proc.returncode == 0
