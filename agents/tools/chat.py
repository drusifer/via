#!/usr/bin/env python3
import argparse
import datetime
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Append a message to agents/CHAT.md")
    parser.add_argument("message", help="The message content")
    parser.add_argument("--persona", "-p", default=os.environ.get("USER", "User"), help="Persona name (default: $USER)")
    parser.add_argument("--cmd", "-c", default="chat", help="Command prefix (default: chat)")
    parser.add_argument("--to", "-t", default="all", help="Name of intended recepient. Can be provided multiple times. (default: all)", nargs='?')
    
    args = parser.parse_args()
    
    # Calculate path to CHAT.md (assuming script is in agents/tools/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chat_file = os.path.abspath(os.path.join(script_dir, "..", "CHAT.md"))
    
    timestamp = datetime.datetime.now().strftime("<small>%Y-%m-%d %H:%M:%S</small>")
    
    # Format: [DATETIME] [Persona] *cmd message
    # If cmd doesn't start with *, add it
    cmd = args.cmd
    if not cmd.startswith("*"):
        cmd = "*" + cmd

    to = args.to
    if type(to) == list:
      to = ','.join(args.to)
        
    formatted_line = f"[{timestamp}] [**{args.persona}**]->[**{to}**] *{cmd}*:\n\n {args.message}\n\n"
    
    try:
        with open(chat_file, "a") as f:
            f.write(formatted_line)
        print(f"Appended to {chat_file}:")
        print(formatted_line.strip())
    except FileNotFoundError:
        print(f"Error: Could not find {chat_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
