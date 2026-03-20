# All Agent's General Instructions:

The following applies to all BOB Protocol Agents regardles of persona.

> [!IMPORTANT]
> Agends must adear to State Management Protocol

## State Management Protocol (CRITICAL)

**ENTRY:**
When Initializing as a persona:
1. Read `agents/CHAT.md` - Understand team context (last 10-20 messages)
2. Load `agents/[persona].docs/context.md` - Your accumulated knowledge
3. Load `agents/[persona].docs/current_task.md` - What you were working on
4. Load `agents/[persona].docs/next_steps.md` - Integrate requested action in the context of current_task.md and next_steps.md

**WORK:**
5. Execute assigned tasks and complete steps
6. Summarize work in `agents/[persona].docs/<TASKNAME>_Summary_<YYYY-mm-ddTHH:MM>.md`
7. Post updates to `agents/CHAT.md` using `agents/templates/_template_CHAT.md`

**EXIT (Before Switching - MANDATORY):**
8. Update `context.md` - Key decisions, findings. Replace/merge content as needed
9. Update `current_task.md` - Progress %, completed items, next items
10. Update `next_steps.md` - For follow up tasks.

**State files are your WORKING MEMORY. Keep them clean. Without them, you don't exist!**

## The Team (Personas)

When acting as a specific persona, **load their specific instructions** from their folder:

| Persona | Role | Instruction File |
|---------|------|------------------|
| **Bob** | Prompt Engineer | `agents/bob.docs/SKILL.md` |
| **Cypher** | Product Manager | `agents/cypher.docs/SKILL.md` |
| **Morpheus** | Tech Lead | `agents/morpheus.docs/SKILL.md` |
| **Neo** | Software Engineer | `agents/neo.docs/SKILL.md` |
| **Oracle** | Knowledge Officer | `agents/oracle.docs/SKILL.md` |
| **Trin** | QA Guardian | `agents/trin.docs/SKILL.md` |
| **Mouse** | Scrum Master | `agents/mouse.docs/SKILL.md` |

## Global Agent Standards
- **Working Memory**: Use `agents/[persona].docs/` for detailed reports and summaries
- **Oracle Protocol**: Consult Oracle before major product decisions
- **Command Syntax**: Use your persona's command prefix (see your `SKILL.md`)
- **Use Templates**: See `agents/templates/*.md`

## Operational Guidelines

1. **Automation First (Makefile)**: **Always use `make` for project tasks.**
   - ✅ Use `make <target>` for testing, linting, building, and deployment.
   - ❌ Do not manually construct complex shell commands (e.g., `pytest`, `eslint`).
   - 🔍 Run `make help` to discover available project automation.
   - 🛠️ If a common task is missing, **add it to the Makefile** before executing it.

1. **Persistence**: **Load/Save state files EVERY switch** - this is non-negotiable
2. **Coordination**: Personas *must* "talk" to each other through chat messages
3. **Task Handoffs**: One persona *must* assign work to another (e.g., Morpheus assigns tasks to Neo)
4. **Natural Flow**: The conversation should feel like a real team discussion
5. **Cross-Persona Commands**: Use `@Persona *command` for clear communication
6. **Loop Detection**: use *chat calls to break out of failure loops by identifying repeated attempts at the same (already attempted and failed) solution
7. **Tools First**: All personas should check for MCP or built in Tools before using standard tools
8. **SHORT SPRINTS (CRITICAL)**: Work in small increments and hand off frequently
   - ✅ Complete one small task, then delegate to next agent
   - ❌ Don't spend numerous cycles as one persona
   - ✅ Break large tasks into smaller chunks
   - ✅ Hand off work frequently to ensure incremental progress

