# BobProtocol Documentation Index

**Last Updated:** 2025-11-28

## Quick Access

Type `*help` for complete command reference with examples.

---

## Primary Documentation

### Getting Started
- **[START_HERE.md](../START_HERE.md)** - Minimal onboarding, quick start guide
- **[HELP.md](bob.docs/HELP.md)** - Complete command reference (use `*help`)
- **[BOB_SYSTEM_PROTOCOL.md](bob.docs/BOB_SYSTEM_PROTOCOL.md)** - Full protocol specification

### MCP Tools
- **[MCP_INTEGRATION_SUMMARY.md](MCP_INTEGRATION_SUMMARY.md)** - MCP overview and mappings
- **[tools/](tools/)** - Centralized tool documentation
  - [README.md](tools/README.md) - Tools overview
  - [mcp_protocol.md](tools/mcp_protocol.md) - Integration protocol
  - Individual tool docs: `*_mcp.md`

---

## Persona Documentation

### Active Personas (7)

| Persona | Role | File | Prefix |
|---------|------|------|--------|
| Bob | Prompt Engineering Expert | [Bob_PE_AGENT.md](bob.docs/Bob_PE_AGENT.md) | `*prompt` / `*reprompt` / `*learn` |
| Cypher | Product Manager | [Cypher_PM_AGENT.md](cypher.docs/Cypher_PM_AGENT.md) | `*pm` |
| Morpheus | Tech Lead / Architect | [Morpheus_SE_AGENT.md](morpheus.docs/Morpheus_SE_AGENT.md) | `*lead` |
| Neo | Senior Software Engineer | [Neo_SWE_AGENT.md](neo.docs/Neo_SWE_AGENT.md) | `*swe` |
| Oracle | Knowledge Officer | [Oracle_INFO_AGENT.md](oracle.docs/Oracle_INFO_AGENT.md) | `*ora` |
| Trin | QA / Guardian | [Trin_QA_AGENT.md](trin.docs/Trin_QA_AGENT.md) | `*qa` |
| Mouse | Scrum Master | [Mouse_SM_AGENT.md](mouse.docs/Mouse_SM_AGENT.md) | `*sm` |

---

## Team Communication

- **[CHAT.md](CHAT.md)** - Team communication log (append-only)
- Each persona maintains state in their `.docs/` folder:
  - `context.md` - Working memory
  - `current_task.md` - Active work
  - `next_steps.md` - Resume plan

---

## Template Files

Located in `agents/` root:

- **Persona Templates:**
  - `_template_PE_AGENT.md` - Prompt Engineering
  - `_template_PM_AGENT.md` - Product Manager
  - `_template_SE_AGENT.md` - Software Engineer / Tech Lead
  - `_template_SWE_AGENT.md` - Senior Software Engineer
  - `_template_INFO_AGENT.md` - Information / Knowledge
  - `_template_QA_AGENT.md` - Quality Assurance
  - `_template_SM_AGENT.md` - Scrum Master

- **State Templates:**
  - `_template_context.md`
  - `_template_current_task.md`
  - `_template_next_steps.md`

---

## MCP Tools Directory

**Location:** `agents/tools/`

### Core
- `mcp_protocol.md` - Integration protocol
- `README.md` - Tools overview

### Tools (11)
- `filesystem_mcp.md` - File operations
- `git_mcp.md` - Version control
- `testing_mcp.md` - Test execution
- `code_analysis_mcp.md` - Code quality
- `search_mcp.md` - Semantic search
- `debug_mcp.md` - Debugging
- `task_management_mcp.md` - Sprint tracking
- `editor_mcp.md` - Bulk editing
- `project_management_mcp.md` - Roadmap
- `markdown_mcp.md` - Doc processing
- `metrics_mcp.md` - Team analytics

---

## Archived Documentation

Files prefixed with `.archive_` are historical and no longer active:
- `.archive_COMMANDS.md` - (Consolidated into HELP.md)
- `.archive_state_management_fix.md` - (Implemented in protocol)

---

## Documentation Standards

### File Naming
- Persona definitions: `[PersonaName]_[ROLE]_AGENT.md`
- State files: `context.md`, `current_task.md`, `next_steps.md`
- MCP tools: `[toolname]_mcp.md`
- Templates: `_template_*.md`
- Archived: `.archive_*.md`

### Structure
- All persona docs in `agents/[persona].docs/`
- All MCP tool docs in `agents/tools/`
- Team communication in `agents/CHAT.md`
- Primary references in `agents/bob.docs/`

### Maintenance
- Update `*help` when adding commands
- Update tool docs when changing MCPs
- Archive outdated docs with `.archive_` prefix
- Keep HELP.md, BOB_SYSTEM_PROTOCOL.md, and START_HERE.md in sync

---

## Quick Command Reference

```bash
*help                          # Show complete help
*chat                          # Activate Bob System
*prompt <desc>                 # Create agent (Bob)
*swe impl <task>              # Implement (Neo)
*qa test <scope>              # Test (Trin)
*ora ask <question>           # Query knowledge (Oracle)
*lead plan <epic>             # Plan (Morpheus)
*pm doc <type>                # Create PRD (Cypher)
*sm status                    # Sprint status (Mouse)
```

---

**For Help:** Type `*help` or read `agents/bob.docs/HELP.md`
