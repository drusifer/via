"""Sprint 17 Cycle 3 tests — --contains symbol-body filtering."""

import json
import subprocess
import sys

from via.pipeline.parser import PipelineParser


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def test_pipeline_parser_accepts_contains_flag():
    parser = PipelineParser()
    stage = parser._parse_stage(["-mg", "*Controller", "-tc", "--contains", "rate_limit"])
    assert stage.args.contains_pattern == "rate_limit"


def test_cli_contains_filters_symbol_bodies_and_returns_symbols(tmp_path):
    (tmp_path / "controllers.py").write_text(
        "class UserController:\n"
        "    def handle(self):\n"
        "        rate_limit = True\n"
        "        return rate_limit\n\n"
        "class AdminController:\n"
        "    def handle(self):\n"
        "        return True\n"
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    query = _run(
        tmp_path,
        "-mg", "*Controller", "-tc", "--contains", "rate_limit", "-oJ",
    )
    assert query.returncode == 0, query.stderr
    payload = json.loads(query.stdout)
    assert [row["symbol_name"] for row in payload] == ["UserController"]
    assert payload[0]["symbol_type"] == "class"
