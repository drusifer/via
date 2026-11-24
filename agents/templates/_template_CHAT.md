# Chat Log Format

`agents/CHAT.md` is generated and maintained by `bobp chat`; do not copy this file as a message
or hand-edit log entries. The CLI owns timestamps, persona, recipient, command, and message layout.

Post a message with the supported command:

```sh
bobp chat "<message>" --persona <Persona> --cmd <command> [--to <Persona>]
```

Keep messages concise (under 256 characters). Put longer reports in a Markdown file and post its
path. Successful posts regenerate `agents/CHAT.diagram.md`; use `bobp chat-diagram` after manual
archive or log maintenance. See `.agents/skills/chat/SKILL.md` for message and handoff conventions.

<!-- RUBRIC-START -->
## Check — CHAT

- [ ] **PASS** — Entries are created through `bobp chat` and contain its timestamp, sender, recipient, command, and message fields.
- [ ] **PASS** — Any manually maintained log change is followed by `bobp chat-diagram`.
- [ ] **FAIL** — A hand-authored entry uses a different schema, or the derived diagram is stale; repair through the CLI and regenerate the diagram.
<!-- RUBRIC-END -->
