# The chat archive

This folder exists to keep the long term memory for this project.

# Agent Instructions:

When the chat log is longer than 500 lines or so perform these steps:
1. scan the first 35% to 50% of the CHAT.md file starting with the oldest (top) messages.
2. Move that content to a new file in this chat_archive folder.  The file should be called CHAT-archive-[YYYY-mm-ddTHH:MM].md 
3. Insert a **TL;DR** summary at the top using the `agents/templates/_template_tldr.md` template
4. Delete the archived content from top of `agents/CHAT.md` and replace it with a `See chat_archive/CHAT-archive-[YYYY-mm-ddTHH:MM].md` reference. 

> [!IMPORTANT]
> Preserve older references at the top of CHAT.md
