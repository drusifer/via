"""
Integration tests for via index -w (Watch Mode, Sprint 6).

TLDR:
    Launches the via CLI as a subprocess with the -w flag, waits until the
    "Watching" ready message appears (event-driven instead of blind sleeps),
    and sends SIGINT to verify watch mode starts cleanly, prints the expected
    message, and exits with return code 0.
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest


def _run_watch_once(tmp_dir: Path):
    """Start `via index -w`, wait for the 'Watching' line, stop via SIGINT."""
    db_path = str(tmp_dir / ".via" / "index.db")
    os.makedirs(str(tmp_dir / ".via"), exist_ok=True)
    (tmp_dir / "sample.py").write_text("def foo(): pass\n")

    proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "via", "index", "-w", "--db", db_path, str(tmp_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: list[str] = []
    ready = threading.Event()

    def _reader():
        assert proc.stdout is not None
        for line in proc.stdout:
            lines.append(line)
            if "Watching" in line:
                ready.set()

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    ready.wait(timeout=8.0)

    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    t.join(timeout=2)
    return "".join(lines), proc.returncode


class TestWatchCLI:
    """CLI integration tests for watch mode sharing one event-driven subprocess run."""

    @pytest.fixture(scope="class")
    @classmethod
    def watch_run(cls, tmp_path_factory):
        return _run_watch_once(tmp_path_factory.mktemp("cli_watch"))

    def test_watch_flag_no_longer_says_not_implemented(self, watch_run):
        """via index -w should start watch mode, not print an error."""
        combined, _ = watch_run
        assert "not implemented" not in combined.lower()

    def test_watch_prints_watching_message(self, watch_run):
        """via index -w should print 'Watching ... for changes'."""
        combined, _ = watch_run
        assert "Watching" in combined

    def test_watch_exits_cleanly_on_sigint(self, watch_run):
        """via index -w should exit with code 0 on SIGINT."""
        _, returncode = watch_run
        assert returncode == 0
