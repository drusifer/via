"""In-process test runner for the via CLI.

TLDR:
    run_via(cwd, *args) executes via.__main__.main() in-process (temporarily
    chdir'ing and patching sys.argv) instead of spawning `python -m via` as a
    subprocess. Subprocess invocation made per-test coverage attribution
    impossible for ~1/3 of this suite (pytest --cov cannot see inside a
    spawned subprocess) — running in-process fixes that and is also faster.
    Returns a subprocess.CompletedProcess for drop-in compatibility with
    existing .returncode/.stdout/.stderr assertions. Exception: tests that
    manage a real background daemon or talk to a server over stdin still
    need a genuine subprocess (see tests/subprocess/) — this helper is only
    for one-shot CLI invocations.
"""

import contextlib
import io
import os
import subprocess
import sys

from via.__main__ import main as _via_main


def run_via(cwd, *args, timeout=None):
    """Run the via CLI in-process with *args, as if invoked from *cwd*.

    Drop-in replacement for:
        subprocess.run([sys.executable, "-m", "via", *args],
                        capture_output=True, text=True, timeout=..., cwd=str(cwd))
    """
    argv = ["via"] + [str(a) for a in args]
    old_cwd = os.getcwd()
    old_argv = sys.argv
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        os.chdir(str(cwd))
        sys.argv = argv
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                returncode = _via_main()
            except SystemExit as exc:
                returncode = exc.code if isinstance(exc.code, int) else (1 if exc.code else 0)
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv

    return subprocess.CompletedProcess(
        args=argv,
        returncode=returncode or 0,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )
