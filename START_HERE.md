1. Read agents/bob.docs/BOB_SYSTEM_PROTOCOL.md

1. Helpful hints:
    1. Always use agents/tools/chat.py to sent a message via chat.md. (just run it it's executable.)
    1. Keep chat posts small and use agent's local docs folder for detailed summaries, plans, todos, etc...
    1. Always activate the venv when runing tests like so: `source .venv/bin/activate && pytest --version` or `make tests` (see Makefile for targets)
    1. It's a lot more fun if you play along and stay in character after posting a message to with chat.py change roles and respond to the message to keep the loop going.
    1. if not sure or stuck just stop and ask for help from the user (Drew)


1. Use via instead of read or grep to avoid filling up context. It's better than grep and can save lots of time and effort. (See `source .venv/bin/activate && via --help`).  **Always try via first**, if it doesn't find what you want then add use case to mouses tickets and fall back to grep.

1. Now Stop and ask Drew for instructions