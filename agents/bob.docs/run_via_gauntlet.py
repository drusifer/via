import subprocess
import os

queries = [
    ["via", "-mg", "*", "-tc", "-n", "5"],
    ["via", "-mg", "__main__*", "-tN"],
    ["via", "-mg", "via.web.api.*", "-Q", "-n", "5"],
    ["via", "-mg", "*", "-tc", "--via", "inherits-from", "-mg", "ParserABC", "-tc", "-n", "5"],
    ["via", "-mg", "*", "-tf", "--via", "calls", "-mg", "parse", "-tf", "-n", "5"],
    ["via", "-mg", "*", "--via", "imports", "-mg", "sqlite3", "-n", "5"],
    ["via", "--not", "-mg", "*/tests/*", "-tF", "--via", "declared-in", "-mg", "main", "-tf"],
    ["via", "-mr", "^(list|type|id|dict|set|str|int|float|len|open|print|next|iter|map|filter|zip)$", "-tm", "-n", "5"],
    ["via", "-mg", "test_*", "-tf", "--via", "inherits-from", "-mg", "*", "-tc", "--stale"],
    ["via", "-mg", "PipelineParser", "-tc", "-oF", "-n", "1"]
]

log_path = "/home/drusifer/Projects/via/agents/bob.docs/via_gauntlet_trace.log"

with open(log_path, "w") as log_file:
    log_file.write("=== VIA GAUNTLET TRACE ===\n\n")
    for idx, cmd in enumerate(queries, 1):
        cmd_str = " ".join(cmd)
        log_file.write(f"--- Query {idx}: {cmd_str} ---\n")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            log_file.write("SUCCESS\n")
            log_file.write("STDOUT:\n")
            log_file.write(res.stdout)
            if res.stderr:
                log_file.write("STDERR:\n")
                log_file.write(res.stderr)
        except subprocess.CalledProcessError as e:
            log_file.write("FAILED\n")
            log_file.write(f"Exit code: {e.returncode}\n")
            log_file.write("STDOUT:\n")
            log_file.write(e.stdout)
            log_file.write("STDERR:\n")
            log_file.write(e.stderr)
        log_file.write("\n" + "="*40 + "\n\n")

print(f"Gauntlet complete. Trace written to {log_path}")
