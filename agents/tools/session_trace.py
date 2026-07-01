#!/usr/bin/env python3
"""
Session Trace Tool

Filters and extracts all executed 'via' queries from the Antigravity session
transcripts, outputting a clean formatted summary.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def locate_transcripts():
    """Locate transcript files in the default Antigravity app data folder."""
    home_dir = os.path.expanduser("~")
    base_dir = Path(home_dir) / ".gemini" / "antigravity-cli"
    
    if not base_dir.exists():
        return []
        
    # Search for files with 'transcript' in their name
    transcript_files = []
    for file_path in base_dir.rglob("*"):
        if file_path.is_file() and "transcript" in file_path.name.lower():
            if file_path.suffix in (".jsonl", ".json"):
                transcript_files.append(file_path)
                
    # Sort files so newest files are processed first or consistently
    transcript_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return transcript_files


def is_via_query(tool_name, query_str):
    """Determine if a tool call/command execution represents a 'via' query."""
    if not tool_name:
        return False
        
    tool_lower = tool_name.lower()
    
    # Direct via tool calls
    if tool_lower in ("via", "via_query", "run_query", "query_via"):
        return True
        
    # Shell commands running via
    if tool_lower in ("run_command", "run_shell_command", "command", "execute_command"):
        if not query_str:
            return False
        # Match commands starting with via, ./venv/bin/via, make via, etc.
        q_clean = query_str.strip().lstrip("./").lstrip("python ")
        if q_clean.startswith("via") or q_clean.startswith("make via") or "via " in q_clean:
            return True
            
    return False


def parse_line(line):
    """
    Parse a single JSONL line and extract via query details if present.
    Supports flat, nested, and MCP schemas.
    """
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    # Extract conversation id
    conv_id = (
        data.get("conversation_id")
        or data.get("conv_id")
        or data.get("sender")
        or data.get("session_id")
        or "N/A"
    )

    # Extract timestamp
    timestamp = (
        data.get("timestamp")
        or data.get("time")
        or data.get("created_at")
        or "N/A"
    )

    tool_name = None
    args_raw = None
    status = "UNKNOWN"

    # MCP tool call
    if data.get("method") == "tools/call":
        params = data.get("params", {})
        tool_name = params.get("name")
        args_raw = params.get("arguments")
    # Nested tool call
    elif "tool_call" in data and isinstance(data["tool_call"], dict):
        tc = data["tool_call"]
        tool_name = tc.get("name") or tc.get("tool")
        args_raw = tc.get("args") or tc.get("arguments") or tc.get("input")
    # Flat tool call
    elif "tool" in data:
        tool_name = data["tool"]
        args_raw = data.get("input") or data.get("args") or data.get("arguments")
    # Other potential schemas
    elif "name" in data and ("args" in data or "arguments" in data):
        tool_name = data["name"]
        args_raw = data.get("args") or data.get("arguments")
    elif "command" in data:
        tool_name = "run_command"
        args_raw = data["command"]

    if not tool_name:
        return None

    # Normalize arguments to string
    args_str = ""
    if isinstance(args_raw, dict):
        args_str = (
            args_raw.get("CommandLine")
            or args_raw.get("command")
            or args_raw.get("query")
            or args_raw.get("args")
            or json.dumps(args_raw)
        )
    elif isinstance(args_raw, (list, tuple)):
        args_str = " ".join(str(x) for x in args_raw)
    elif args_raw is not None:
        args_str = str(args_raw)

    # If it is not a via query, skip it
    if not is_via_query(tool_name, args_str):
        return None

    # Extract execution status
    status_raw = None
    if "response" in data and isinstance(data["response"], dict):
        resp = data["response"]
        for key in ("status", "success", "exit_code"):
            if key in resp:
                status_raw = resp[key]
                break
    if status_raw is None:
        for key in ("status", "success", "exit_code"):
            if key in data:
                status_raw = data[key]
                break

    if status_raw is not None:
        if isinstance(status_raw, bool):
            status = "SUCCESS" if status_raw else "FAILED"
        elif isinstance(status_raw, int):
            status = "SUCCESS" if status_raw == 0 else "FAILED"
        else:
            status = str(status_raw).upper()

    return {
        "timestamp": timestamp,
        "conversation_id": conv_id,
        "tool": tool_name,
        "query": args_str.strip(),
        "status": status,
    }


def parse_transcript_file(file_path, conv_id_filter=None):
    """Parse a single transcript file and extract via queries."""
    queries = []
    
    try:
        # Check if the file is a JSON array or JSONL
        with open(file_path, "r", encoding="utf-8") as f:
            first_char = ""
            for char in f.read(100):
                if char.strip():
                    first_char = char
                    break
            
            f.seek(0)
            if first_char == "[":
                # Try parsing as JSON array
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            # Re-serialize to parse through parse_line
                            parsed = parse_line(json.dumps(item))
                            if parsed:
                                if not conv_id_filter or parsed["conversation_id"] == conv_id_filter:
                                    queries.append(parsed)
                        return queries
                except json.JSONDecodeError:
                    f.seek(0)
            
            # Default to JSONL line-by-line parsing
            for line in f:
                if not line.strip():
                    continue
                parsed = parse_line(line)
                if parsed:
                    if not conv_id_filter or parsed["conversation_id"] == conv_id_filter:
                        queries.append(parsed)
                        
    except Exception as e:
        print(f"Error reading transcript file {file_path}: {e}", file=sys.stderr)
        
    return queries


def print_summary(queries):
    """Print the extracted via query trace in chronological format."""
    print("=" * 80)
    print("                           VIA SESSION QUERY TRACE")
    print("=" * 80)
    
    if not queries:
        print("No via queries found in the selected transcript(s).")
        print("=" * 80)
        return

    # Sort chronologically by timestamp (fall back to list order if N/A)
    sorted_queries = sorted(
        queries, 
        key=lambda q: q["timestamp"] if q["timestamp"] != "N/A" else ""
    )

    for i, q in enumerate(sorted_queries, 1):
        print(f"[{i}] Timestamp:       {q['timestamp']}")
        print(f"    Conversation ID: {q['conversation_id']}")
        print(f"    Tool / Invocation: {q['tool']}")
        print(f"    Query Command:   {q['query']}")
        print(f"    Status:          {q['status']}")
        print("-" * 80)
        
    print(f"Total via queries found: {len(sorted_queries)}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Extract and summarize 'via' queries from session transcripts."
    )
    parser.add_argument(
        "--path",
        help="Path to a specific transcript file (JSON/JSONL) to parse.",
    )
    parser.add_argument(
        "--conv-id",
        help="Filter queries by a specific Conversation ID.",
    )
    
    args = parser.parse_args()
    
    queries = []
    
    if args.path:
        target_path = Path(args.path)
        if not target_path.exists():
            print(f"Error: Specified path does not exist: {args.path}", file=sys.stderr)
            sys.exit(1)
        queries = parse_transcript_file(target_path, args.conv_id)
    else:
        # Auto-locate transcripts
        transcript_files = locate_transcripts()
        if not transcript_files:
            print("No transcript files automatically located under ~/.gemini/antigravity-cli/.", file=sys.stderr)
            print("Please run with --path to specify a transcript file directly.", file=sys.stderr)
            sys.exit(0)
            
        print(f"Found {len(transcript_files)} transcript file(s). Parsing...", file=sys.stderr)
        for filepath in transcript_files:
            queries.extend(parse_transcript_file(filepath, args.conv_id))
            
    print_summary(queries)


if __name__ == "__main__":
    main()
