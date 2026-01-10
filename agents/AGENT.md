# All Agent's General Instructions:

The following applies to all BOB Protocol Agents regardles of persona.

> [!IMPORTANT]
> Agends must adear to State Management Protocol

## State Management Protocol (CRITICAL)

**ENTRY:**
When Initializing as a persona: 
1. Read `agents/CHAT.md` - Understand team context (last 10-20 messages)
2. Load `agents/cypher.docs/context.md` - Your accumulated knowledge
3. Load `agents/cypher.docs/current_task.md` - What you were working on
4. Load `agents/cypher.docs/next_steps.md` - Integrate requested action in the context of current_task.md and next_steps.md

**WORK:**
5. Execute assigned tasks and complete steps
6. Sumarize work in `agents/cypher.docs/<TASKNAME>_Summary_<YYYY-mm-ddTHH:MM>.md`
6. Post updates to `agents/CHAT.md` using `agents/templates/_CHAT.md`

**EXIT (Before Switching - MANDATORY):**
7. Update `context.md` - Product decisions, findings. replace / merge content as needed
8. Update `current_task.md` - Progress %, completed items, next items
9. Update `next_steps.md` - For follow up tasks.

**State files are your WORKING MEMORY. Keep them clean. Without them, you don't exist!**

## Global Agent Standards
- **Working Memory**: Use `agents/cypher.docs/` for detailed reports
- **Oracle Protocol**: Consult Oracle before major product decisions
- **Command Syntax**: Use `*pm` prefix for all commands
- **Use Templates**: See `agents/templates/*.md`




## Operational Guidelines

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

