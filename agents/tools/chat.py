#!/usr/bin/env python3
"""
CLI tool for appending formatted messages to agents/CHAT.md.

TLDR:
    Provides a simple command-line interface for posting messages to the shared
    CHAT.md communication log used by AI agents in the project. Each message is
    stamped with a timestamp, persona, command prefix, and optional recipient list.
    Key function: main() — parses arguments and appends a formatted message entry
    to agents/CHAT.md, enforcing a 256-character message limit.
    Role in the system: consumed by mkf.py (which calls it to post build status)
    and invoked directly by agents or developers to coordinate via the chat log.

"""

import argparse
import datetime
import os
import sys
from pathlib import Path


def is_make_build(persona, cmd):
    """Return whether this message is mkf's build-status chat entry."""
    return persona.lower() == "make" and cmd.lstrip("*").lower() == "build"


def last_entry_is_make_build(content):
    """Detect whether the final chat entry is a make build-status entry."""
    marker = "\n---\n["
    start = content.rfind(marker)
    if start == -1:
        return False

    entry = content[start + 1 :]
    first_line = next((line for line in entry.splitlines() if line.startswith("[")), "")
    return "[**make**]" in first_line and "build" in first_line


def write_message(chat_file, formatted_line, overwrite_last_make_build):
    """Append a message, or replace the final make build entry when requested."""
    path = Path(chat_file)

    try:
        content = path.read_text()
    except FileNotFoundError:
        print(f"Error: Could not find {chat_file}")
        sys.exit(1)

    if overwrite_last_make_build and last_entry_is_make_build(content):
        marker = "\n---\n["
        start = content.rfind(marker)
        path.write_text(content[:start] + formatted_line)
        return "Replaced last make build message in"

    with path.open("a") as f:
        f.write(formatted_line)
    return "Appended to"


def main():
    parser = argparse.ArgumentParser(description="Append a message to agents/CHAT.md")
    parser.add_argument("message", help="The message content max  256 characters")
    parser.add_argument("--persona", "-p", default=os.environ.get("USER", "User"), help="Persona name (default: $USER)")
    parser.add_argument("--cmd", "-c", default="chat", help="Command prefix (default: chat)")
    parser.add_argument("--to", "-t", action="append", help="Name of intended recipient. Can be provided multiple times. (default: all)")
    
    args = parser.parse_args()
    
    # Calculate path to CHAT.md (assuming script is in agents/tools/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chat_file = os.path.abspath(os.path.join(script_dir, "..", "CHAT.md"))
    
    timestamp = datetime.datetime.now().strftime("<small>%Y-%m-%d %H:%M:%S</small>")

    if len(args.message) > 256:
        print("Error: Message exceeds 256 characters. Use a Markdown file for longer messages. Then use chat to send the location of the file and a short summary.")
        sys.exit(1)
    
    # Format: [DATETIME] [Persona] *cmd message
    # If cmd doesn't start with *, add it
    cmd = args.cmd
    if not cmd.startswith("*"):
        cmd = "*" + cmd

    # Handle list of recipients or default to "all"
    to = ','.join(args.to) if args.to else "all"
        
    formatted_line = f"\n---\n[{timestamp}] [**{args.persona}**]->[**{to}**] {cmd}*:\n {args.message}\n"
    
    action = write_message(
        chat_file,
        formatted_line,
        overwrite_last_make_build=is_make_build(args.persona, cmd),
    )
    print(f"{action} {chat_file}:")
    print(formatted_line.strip())

if __name__ == "__main__":
    main()
