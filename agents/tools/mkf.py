#!/usr/bin/env python3
"""
mkf — make filter and build output router.

TLDR:
    Wraps `make <target>` invocations, capturing all stdout/stderr to
    build/build.out while selectively echoing output to the terminal based on a
    verbosity level (-v/-vv/-vvv). On completion it prints the last 10 lines of
    the build log and posts a pass/fail status message to agents/CHAT.md via chat.py.
    Key functions: main() orchestrates the run; should_echo() controls terminal
    output filtering; build_chat_message() composes the status summary; post_chat()
    delegates to chat.py; parse_args() handles -v/-vv/-vvv verbosity flags;
    drain() flushes remaining stream output after process exit; tail() reads the
    last N lines of a file efficiently.
    Role in the system: invoked by developers and agents instead of bare `make`;
    depends on chat.py for status reporting and writes to build/build.out for
    later inspection.
    Usage: mkf [-v|-vv|-vvv] <target> [make-args...]

"""

import os
import re
import sys
import datetime
import subprocess
from select import select
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

FAILURE_PATTERNS = re.compile(r'×|FAIL|Error:|AssertionError|failed \(|npm ERR')
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')
TAIL_LINES = 10
CHAT_MAX = 256

SCRIPT_DIR = Path(__file__).resolve().parent   # agents/tools/
PROJECT_ROOT = SCRIPT_DIR.parent.parent        # project root
BUILD_DIR = PROJECT_ROOT / 'build'
CHAT_TOOL = PROJECT_ROOT / 'agents' / 'tools' / 'chat.py'

# ── Helpers ──────────────────────────────────────────────────────────────────

def strip_ansi(text):
    return ANSI_ESCAPE.sub('', text)


def should_echo(line, is_stderr, verbosity):
    if verbosity == 0:
        return False
    if is_stderr:
        return verbosity >= 1
    # stdout
    if verbosity >= 3:
        return True
    if verbosity == 2:
        return bool(FAILURE_PATTERNS.search(strip_ansi(line)))
    return False


def drain(stream, out_file, verbosity, is_stderr):
    """Read any remaining bytes after process exits."""
    while True:
        line = stream.readline()
        if not line:
            break
        decoded = line.decode(errors='replace')
        out_file.write(decoded)
        if should_echo(decoded, is_stderr, verbosity):
            dest = sys.stderr if is_stderr else sys.stdout
            dest.write(decoded)
            dest.flush()


def tail(path, n):
    with open(path, 'rb') as f:
        # Efficient tail: seek from end
        try:
            f.seek(0, 2)
            size = f.tell()
            block = min(size, 8192)
            f.seek(-block, 2)
            lines = f.read().decode(errors='replace').splitlines()
        except OSError:
            lines = []
    return lines[-n:]


def build_chat_message(target, exit_code, build_path, tail_lines):
    status = 'PASSED' if exit_code == 0 else f'FAILED exit={exit_code}'
    header = f'Build {status} | make {target} | {build_path}'
    # Append as many tail lines as fit within CHAT_MAX
    tail_text = ''
    for line in reversed([strip_ansi(l) for l in tail_lines]):
        candidate = f'\n{line.strip()}{tail_text}'
        if len(header) + len(candidate) <= CHAT_MAX:
            tail_text = candidate
        else:
            break
    return (header + tail_text)[:CHAT_MAX]


def post_chat(message):
    if not CHAT_TOOL.exists():
        print(f'[mkf] chat tool not found at {CHAT_TOOL}', file=sys.stderr)
        return
    subprocess.run(
        [sys.executable, str(CHAT_TOOL), message, '--persona', 'make', '--cmd', 'build'],
        cwd=PROJECT_ROOT,
    )


# ── Argument parsing ─────────────────────────────────────────────────────────

def parse_args(argv):
    args = list(argv)
    verbosity = 0

    # Accept -v, -vv, -vvv as the first argument
    if args and re.fullmatch(r'-v{1,3}', args[0]):
        verbosity = len(args.pop(0)) - 1  # strip leading '-'

    if not args:
        print(__doc__)
        print('Error: no make target specified.', file=sys.stderr)
        sys.exit(1)

    return verbosity, args[0], args[1:]


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    verbosity, target, extra_args = parse_args(sys.argv[1:])

    BUILD_DIR.mkdir(exist_ok=True)
    build_path = BUILD_DIR / 'build.out'

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header = f'=== make {target} @ {timestamp} ===\n'

    cmd = ['make', target] + extra_args

    with open(build_path, 'w') as out_file:
        out_file.write(header)
        out_file.flush()

        env = os.environ.copy()
        env['MKF_ACTIVE'] = '1'

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT,
            env=env,
        )

        streams = {proc.stdout: False, proc.stderr: True}  # stream → is_stderr

        while True:
            readable, _, _ = select(list(streams.keys()), [], [], 0.1)

            for stream in readable:
                line = stream.readline()
                if not line:
                    continue
                is_stderr = streams[stream]
                decoded = line.decode(errors='replace')
                out_file.write(decoded)
                out_file.flush()
                if should_echo(decoded, is_stderr, verbosity):
                    dest = sys.stderr if is_stderr else sys.stdout
                    dest.write(decoded)
                    dest.flush()

            if proc.poll() is not None:
                drain(proc.stdout, out_file, verbosity, is_stderr=False)
                drain(proc.stderr, out_file, verbosity, is_stderr=True)
                break

        exit_code = proc.returncode

    # ── Post-run ─────────────────────────────────────────────────────────────

    tail_lines = tail(build_path, TAIL_LINES)

    print(f'\n=== last {TAIL_LINES} lines: {build_path} ===')
    print('\n'.join(tail_lines))
    print(f'=== exit {exit_code} ===\n')

    msg = build_chat_message(target, exit_code, build_path, tail_lines)
    post_chat(msg)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
