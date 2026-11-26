"""
Sprint 6 UAT suite validating watch-mode behaviour via subprocess-level acceptance tests.

TLDR:
    Subprocess-level UAT suite for `via index -w` covering eight acceptance criteria
    (UAT-6.1 through UAT-6.8). Keeps one shared live `via index -w` watcher process
    running across UAT-6.1/6.2/6.3/6.4/6.6/6.7/6.8 (plus one dedicated SIGINT run
    for UAT-6.5), using event-driven output waits instead of blind sleeps, keeping
    100% of test methods and assertions while cutting runtime by ~10x.

Author: Trin (QA)
Sprint: 6
"""

import signal
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

from via.core.types import MatchOp, SymbolType
from via.db.store import DatabaseStore


NEGATIVE_WAIT = 0.8  # debounce (0.5s) + buffer for asserting NO re-index occurs


class _WatchSession:
    """Manages a live `via index -w` subprocess with line-buffered ready/event waits."""

    def __init__(self, tmp_dir: Path, extra_args=None):
        via_dir = tmp_dir / ".via"
        via_dir.mkdir(exist_ok=True)
        self.tmp_dir = tmp_dir
        self.db_path = str(via_dir / "index.db")

        cmd = [
            sys.executable, "-u", "-m", "via", "index", "-w",
            "--db", self.db_path,
            str(tmp_dir),
        ]
        if extra_args:
            cmd.extend(extra_args)

        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        self._lines: list[str] = []
        self._cond = threading.Condition()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        self.wait_for("Watching", timeout=10.0)

    def _pump(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            with self._cond:
                self._lines.append(line)
                self._cond.notify_all()

    @property
    def output(self) -> str:
        with self._cond:
            return "".join(self._lines)

    def mark(self) -> int:
        """Return current output line count so callers can inspect only new lines."""
        with self._cond:
            return len(self._lines)

    def output_since(self, mark: int) -> str:
        with self._cond:
            return "".join(self._lines[mark:])

    def wait_for(self, substring: str, timeout: float = 6.0, since: int = 0) -> bool:
        deadline = time.monotonic() + timeout
        with self._cond:
            while substring not in "".join(self._lines[since:]):
                remaining = deadline - time.monotonic()
                if remaining <= 0 or self.proc.poll() is not None:
                    return substring in "".join(self._lines[since:])
                self._cond.wait(timeout=min(remaining, 0.05))
            return True

    def stop(self, timeout: float = 8.0) -> tuple[str, int]:
        try:
            self.proc.send_signal(signal.SIGINT)
        except ProcessLookupError:
            pass
        try:
            self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self._reader.join(timeout=2.0)
        return self.output, self.proc.returncode


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
# Shared live watcher fixture (reused across UAT-6.1/6.2/6.3/6.4/6.6/6.7/6.8)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live_watch(tmp_path_factory):
    """Keep one `via index -w --exclude generated/` watcher alive across all live UATs."""
    tmp_dir = tmp_path_factory.mktemp("sprint6_live")
    (tmp_dir / "models.py").write_text("class User:\n    def save(self): pass\n")
    (tmp_dir / "service.py").write_text("class OldClass: pass\n")
    (tmp_dir / "README.md").write_text("# Hello\n")
    (tmp_dir / "doomed.py").write_text("class Doomed: pass\n")
    (tmp_dir / "config.json").write_text('{"key": "value"}\n')
    (tmp_dir / "notes.txt").write_text("some notes\n")
    (tmp_dir / "good.py").write_text("def ok(): pass\n")
    (tmp_dir / "broken.py").write_text("def fine(): pass\n")
    gen_dir = tmp_dir / "generated"
    gen_dir.mkdir()
    (gen_dir / "schema.py").write_text("# generated\nx = 1\n")

    sess = _WatchSession(tmp_dir, extra_args=["--exclude", "generated/"])
    try:
        yield sess
    finally:
        sess.stop()


# ---------------------------------------------------------------------------
# UAT-6.1: Startup — blocks, performs initial index
# ---------------------------------------------------------------------------

class TestUAT61_Startup:
    """AC: via index -w starts, performs initial index, prints watching message."""

    def test_startup_does_not_exit_immediately(self, live_watch):
        """Process must stay alive (blocking) after launch."""
        assert live_watch.proc.poll() is None, "Watch process exited prematurely"

    def test_startup_prints_watching_message(self, live_watch):
        """AC: prints 'Watching <dir> for changes... (Ctrl-C to stop)'"""
        assert "Watching" in live_watch.output
        assert "Ctrl-C" in live_watch.output

    def test_startup_performs_initial_index(self, live_watch):
        """AC: on startup, performs a full incremental index."""
        with _open_db(live_watch.db_path, live_watch.tmp_dir) as store:
            results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "User"))
        assert len(results) >= 1, "Initial index should have indexed User class"


# ---------------------------------------------------------------------------
# UAT-6.2: File Modification — re-indexes and prints feedback
# ---------------------------------------------------------------------------

class TestUAT62_FileModification:
    """AC: When a supported file is modified, only that file is re-indexed."""

    @pytest.fixture(scope="class")
    @classmethod
    def modified(cls, live_watch):
        mark = live_watch.mark()
        (live_watch.tmp_dir / "service.py").write_text(
            "class NewClass:\n    def bar(self): pass\n"
        )
        (live_watch.tmp_dir / "README.md").write_text("# Hello\n\n## Section Two\n")
        assert live_watch.wait_for("service.py", timeout=6.0, since=mark)
        assert live_watch.wait_for("README.md", timeout=6.0, since=mark)
        return {"output": live_watch.output_since(mark), "db_path": live_watch.db_path, "tmp_dir": live_watch.tmp_dir}

    def test_modify_py_triggers_reindex(self, modified):
        """AC: modified .py file → 'Re-indexed: <path> (<N> symbols)'"""
        assert "Re-indexed:" in modified["output"]
        assert "service.py" in modified["output"]

    def test_modify_md_triggers_reindex(self, modified):
        """AC: modified .md file → re-indexed."""
        assert "Re-indexed:" in modified["output"]
        assert "README.md" in modified["output"]

    def test_reindex_output_includes_symbol_count(self, modified):
        """AC: feedback includes symbol count."""
        assert "symbol" in modified["output"].lower()

    def test_modify_updates_db_symbols(self, modified):
        """AC: after re-index, new symbols are queryable."""
        with _open_db(modified["db_path"], modified["tmp_dir"]) as store:
            new_results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "NewClass"))
            old_results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "OldClass"))
        assert len(new_results) >= 1, "NewClass should be in DB after re-index"
        assert len(old_results) == 0, "OldClass should be gone after re-index"


# ---------------------------------------------------------------------------
# UAT-6.3: File Creation — indexes new files
# ---------------------------------------------------------------------------

class TestUAT63_FileCreation:
    """AC: When a new supported file is created, it is indexed automatically."""

    @pytest.fixture(scope="class")
    @classmethod
    def created(cls, live_watch):
        mark = live_watch.mark()
        (live_watch.tmp_dir / "brand_new.py").write_text("class BrandNew:\n    pass\n")
        (live_watch.tmp_dir / "GUIDE.md").write_text("# Guide\n## Setup\n")
        assert live_watch.wait_for("brand_new.py", timeout=6.0, since=mark)
        assert live_watch.wait_for("GUIDE.md", timeout=6.0, since=mark)
        return {"output": live_watch.output_since(mark), "db_path": live_watch.db_path, "tmp_dir": live_watch.tmp_dir}

    def test_new_py_file_indexed(self, created):
        """AC: new .py file → printed and in DB."""
        assert "brand_new.py" in created["output"]
        with _open_db(created["db_path"], created["tmp_dir"]) as store:
            results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "BrandNew"))
        assert len(results) >= 1, "BrandNew should be indexed"

    def test_new_md_file_indexed(self, created):
        """AC: new .md file → indexed."""
        assert "GUIDE.md" in created["output"]


# ---------------------------------------------------------------------------
# UAT-6.4: File Deletion — removes symbols from DB
# ---------------------------------------------------------------------------

class TestUAT64_FileDeletion:
    """AC: When a supported file is deleted, its symbols are removed from DB."""

    @pytest.fixture(scope="class")
    @classmethod
    def deleted(cls, live_watch):
        mark = live_watch.mark()
        (live_watch.tmp_dir / "doomed.py").unlink()
        assert live_watch.wait_for("Removed:", timeout=6.0, since=mark)
        return {"output": live_watch.output_since(mark), "db_path": live_watch.db_path, "tmp_dir": live_watch.tmp_dir}

    def test_deleted_file_prints_removed(self, deleted):
        """AC: deleted file → 'Removed: <filepath>'"""
        assert "Removed:" in deleted["output"]
        assert "doomed.py" in deleted["output"]

    def test_deleted_file_symbols_removed_from_db(self, deleted):
        """AC: symbols of deleted file are gone from DB."""
        with _open_db(deleted["db_path"], deleted["tmp_dir"]) as store:
            results = list(store.match(SymbolType.CLASS, MatchOp.GLOB, "Doomed"))
        assert len(results) == 0, "Doomed symbols should be removed after file deletion"


# ---------------------------------------------------------------------------
# UAT-6.6 & UAT-6.7: Non-parseable & excluded files are ignored
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ignored_and_excluded(live_watch):
    """Touch .json, .txt, and --exclude generated/schema.py together, wait once."""
    mark = live_watch.mark()
    (live_watch.tmp_dir / "config.json").write_text('{"key": "updated"}\n')
    (live_watch.tmp_dir / "notes.txt").write_text("updated notes\n")
    (live_watch.tmp_dir / "generated" / "schema.py").write_text("# generated\nx = 2\ny = 3\n")
    time.sleep(NEGATIVE_WAIT)
    return live_watch.output_since(mark)


class TestUAT66_NonParseableFilesIgnored:
    """AC: Non-parseable files (.txt, .json) are not re-indexed on change."""

    def test_json_file_change_not_reported(self, ignored_and_excluded):
        """AC: .json file changes produce no 'Re-indexed' output."""
        assert "config.json" not in ignored_and_excluded

    def test_txt_file_change_not_reported(self, ignored_and_excluded):
        """AC: .txt file changes produce no 'Re-indexed' output."""
        assert "notes.txt" not in ignored_and_excluded


class TestUAT67_ExclusionPatterns:
    """AC: Watch mode ignores changes matching --exclude patterns."""

    def test_exclude_pattern_suppresses_reindex(self, ignored_and_excluded):
        """AC: files matching --exclude PATTERN are not re-indexed."""
        assert "schema.py" not in ignored_and_excluded


# ---------------------------------------------------------------------------
# UAT-6.8: Error resilience — syntax errors don't crash the watcher
# ---------------------------------------------------------------------------

class TestUAT68_ErrorResilience:
    """AC: Syntax errors are logged and watching continues."""

    def test_syntax_error_does_not_crash_watcher(self, live_watch):
        """AC: file with syntax error is handled without crashing."""
        mark = live_watch.mark()
        (live_watch.tmp_dir / "broken.py").write_text("def (BROKEN:\n    pass\n")
        (live_watch.tmp_dir / "good.py").write_text("def ok(): pass\ndef extra(): pass\n")
        assert live_watch.wait_for("good.py", timeout=6.0, since=mark)
        assert live_watch.proc.poll() is None, "Watcher crashed on syntax error"
        assert "good.py" in live_watch.output_since(mark)


# ---------------------------------------------------------------------------
# UAT-6.5: SIGINT — graceful shutdown (stops a live watcher cleanly)
# ---------------------------------------------------------------------------

class TestUAT65_GracefulShutdown:
    """AC: Ctrl-C (SIGINT) gracefully stops the watcher and exits cleanly."""

    @pytest.fixture(scope="class")
    @classmethod
    def shutdown_run(cls, tmp_path_factory):
        tmp_dir = tmp_path_factory.mktemp("uat65")
        (tmp_dir / "app.py").write_text("x = 1\n")
        sess = _WatchSession(tmp_dir)
        output, returncode = sess.stop()
        return {"output": output, "returncode": returncode}

    def test_sigint_exits_zero(self, shutdown_run):
        """AC: exits with code 0 on SIGINT."""
        assert shutdown_run["returncode"] == 0

    def test_sigint_prints_stopped_message(self, shutdown_run):
        """AC: On Ctrl-C, prints 'Watch mode stopped.'"""
        assert "stopped" in shutdown_run["output"].lower()
