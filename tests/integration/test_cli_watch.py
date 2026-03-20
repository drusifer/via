"""Integration tests for via index -w (Watch Mode, Sprint 6)."""

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _run_via(*args, input=None, timeout=10):
    result = subprocess.run(
        [sys.executable, "-m", "via"] + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
        input=input,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    return result


class TestWatchCLI:
    """CLI integration tests for watch mode."""

    def test_watch_flag_no_longer_says_not_implemented(self, tmp_path):
        """via index -w should start watch mode, not print an error."""
        db_path = str(tmp_path / ".via" / "index.db")
        os.makedirs(str(tmp_path / ".via"), exist_ok=True)
        Path(tmp_path / "sample.py").write_text("def foo(): pass\n")

        # Launch watch mode and immediately send SIGINT
        proc = subprocess.Popen(
            [sys.executable, "-m", "via", "index", "-w", "--db", db_path, str(tmp_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.5)  # Let it start up
        proc.send_signal(signal.SIGINT)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr
        assert "not implemented" not in combined.lower()

    def test_watch_prints_watching_message(self, tmp_path):
        """via index -w should print 'Watching ... for changes'."""
        db_path = str(tmp_path / ".via" / "index.db")
        os.makedirs(str(tmp_path / ".via"), exist_ok=True)
        Path(tmp_path / "sample.py").write_text("def bar(): pass\n")

        proc = subprocess.Popen(
            [sys.executable, "-m", "via", "index", "-w", "--db", db_path, str(tmp_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(1.0)  # Give it time to print the watching message
        proc.send_signal(signal.SIGINT)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr
        assert "Watching" in combined

    def test_watch_exits_cleanly_on_sigint(self, tmp_path):
        """via index -w should exit with code 0 on SIGINT."""
        db_path = str(tmp_path / ".via" / "index.db")
        os.makedirs(str(tmp_path / ".via"), exist_ok=True)
        Path(tmp_path / "sample.py").write_text("x = 1\n")

        proc = subprocess.Popen(
            [sys.executable, "-m", "via", "index", "-w", "--db", db_path, str(tmp_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.8)
        proc.send_signal(signal.SIGINT)
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

        assert proc.returncode == 0
