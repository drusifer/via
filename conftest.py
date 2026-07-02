"""Root pytest conftest.

TLDR:
    Two independent things:
    1. Redirects test subprocess.run(['via', ...]) calls to run in-process
       (tests/via_runner.py) instead of spawning a real subprocess. This was
       previously invisible to `pytest --cov` (coverage.py can't see inside a
       subprocess), so ~1/3 of the suite falsely looked untested under
       per-test coverage. Long-running server/daemon invocations (`mcp
       serve`, `index -w`, or any call passing stdin `input=`) are left as
       real subprocesses since they need genuine process semantics.
    2. Captures per-test outcome (pass/fail/error/skip) and total duration for
       every test in the session, writing them to .via/test_runs.json at
       session end. Consumed by `via coverage import-contexts` (Sprint 27) to
       populate the test_runs table alongside per-test coverage attribution.
"""

import json
import os
import subprocess
import time
from pathlib import Path

from tests.via_runner import run_via

_real_subprocess_run = subprocess.run


def _via_invocation_args(cmd):
    """Return the via CLI args if *cmd* invokes via, else None."""
    if not cmd:
        return None
    if cmd[0] == 'via':
        return list(cmd[1:])
    if len(cmd) >= 3 and Path(str(cmd[0])).stem.startswith('python') and cmd[1] == '-m' and cmd[2] == 'via':
        return list(cmd[3:])
    return None


def _patched_subprocess_run(cmd, *args, **kwargs):
    via_args = _via_invocation_args(cmd)
    is_long_running = (
        via_args is not None
        and (via_args[:2] == ['mcp', 'serve'] or '-w' in via_args or '--watch' in via_args)
    )
    if via_args is not None and not is_long_running and 'input' not in kwargs:
        cwd = kwargs.get('cwd') or os.getcwd()
        return run_via(cwd, *via_args)
    return _real_subprocess_run(cmd, *args, **kwargs)


subprocess.run = _patched_subprocess_run

_TEST_RUNS: dict = {}

_STATUS_BY_OUTCOME = {
    'passed': 'pass',
    'failed': 'fail',
    'skipped': 'skip',
}


def pytest_runtest_logreport(report):
    entry = _TEST_RUNS.setdefault(
        report.nodeid, {'duration': 0.0, 'status': None}
    )
    entry['duration'] += report.duration

    if report.when == 'call':
        entry['status'] = _STATUS_BY_OUTCOME.get(report.outcome, report.outcome)
    elif report.when in ('setup', 'teardown') and report.outcome == 'failed':
        # A setup/teardown failure means the test body may never have run —
        # record 'error' unless a 'call' phase already reported a real result.
        if entry['status'] is None:
            entry['status'] = 'error'
    elif report.when == 'setup' and report.outcome == 'skipped':
        if entry['status'] is None:
            entry['status'] = 'skip'


def pytest_sessionfinish(session, exitstatus):
    if not _TEST_RUNS:
        return
    out_path = Path(session.config.rootdir) / '.via' / 'test_runs.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    now = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
    payload = {
        test_id: {
            'status': data['status'] or 'error',
            'duration_seconds': data['duration'],
            'last_run_at': now,
        }
        for test_id, data in _TEST_RUNS.items()
    }
    out_path.write_text(json.dumps(payload, indent=2))
