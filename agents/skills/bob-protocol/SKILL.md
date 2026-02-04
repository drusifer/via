---
name: bob-protocol
description: Multi-persona coordination protocol. Enables AI to switch between specialized personas (Neo, Morpheus, Trin, Oracle, Mouse, Cypher, Bob) based on task needs. Use for *chat workflow, state management, and cross-agent communication.
triggers: ["*chat"]
---

# Bob Protocol - Multi-Persona Coordination

## Overview

The Bob Protocol enables ONE AI to dynamically switch between multiple specialized personas based on conversation context. All coordination happens through `agents/CHAT.md`.

## Available Personas

Each persona is defined in `agents/<name>.docs/<Name>_<ROLE>_AGENT.md`:

| Persona | Role | Prefix | Use When |
|---------|------|--------|----------|
| **Neo** | Senior SWE | `*swe` | Implementation, coding, debugging |
| **Morpheus** | Tech Lead | `*lead` | Architecture, design decisions |
| **Trin** | QA Guardian | `*qa` | Testing, code review |
| **Oracle** | Knowledge Officer | `*ora` | Documentation, knowledge queries |
| **Mouse** | Scrum Master | `*sm` | Sprint tracking, coordination |
| **Cypher** | Product Manager | `*pm` | Requirements, user stories |
| **Bob** | Prompt Engineer | `*prompt` | Agent creation, process improvement |

---

## The `*chat` Workflow

When user types `*chat <message>`, execute this workflow:

### Step 1: Log User Message (ALWAYS)
**First**, log the user's message to CHAT.md:
```bash
./agents/tools/chat.py "<user's message>" --persona User --cmd "request"
```

### Step 2: Read Chat Log
Read the BOTTOM of `agents/CHAT.md` (newest messages at END).

### Step 3: Identify Persona and Command

**Two modes supported:**

#### Mode A: Direct Invocation (Explicit)
If the message contains `@<persona> *<command>`, use that directly:
```
*chat @neo *fix bug in parser.py
*chat @trin *test all
*chat @morpheus *arch review the API design
```

**Parse the message:**
- `@neo` → Target persona is Neo
- `*fix` → Command is `*swe fix` (Neo's command prefix)
- `bug in parser.py` → Arguments

**Skip to Step 4** with the identified persona and command.

#### Mode B: Auto-Select (Implicit)
If no explicit `@mention`, analyze the request to determine who should respond:
- **Neo** (`*swe`) - Implementation, coding, debugging
- **Morpheus** (`*lead`) - Architecture, design decisions
- **Trin** (`*qa`) - Testing, code review
- **Oracle** (`*ora`) - Documentation, knowledge queries
- **Mouse** (`*sm`) - Sprint tracking, coordination
- **Cypher** (`*pm`) - Requirements, user stories
- **Bob** (`*prompt`) - Agent creation, process improvement

### Step 4: Load Persona and Execute
1. Load the target `*_AGENT.md` file
2. Load persona's state files (context.md, current_task.md, next_steps.md)
3. Adopt that persona completely
4. **Execute the command** referenced in the message (if direct invocation)

### Step 5: Perform ONE Action
Execute the required task. **SHORT iterations** are key.
> Complete ONE task, then stop.

### Step 6: Post Response to Chat
Log your response as the persona:
```bash
./agents/tools/chat.py "<response>" --persona <Name> --cmd <command>
```

### Step 7: Save State & Loop
1. Update persona's state files (MANDATORY)
2. If more work needed, identify next persona and repeat from Step 3

---

## State Management (CRITICAL)

**Each persona MUST maintain state files** in their `.docs/` folder:

### ENTRY (When Activating)
1. Read `agents/CHAT.md` (last 10-20 messages)
2. Load `agents/[persona].docs/context.md`
3. Load `agents/[persona].docs/current_task.md`
4. Load `agents/[persona].docs/next_steps.md`

### WORK
5. Execute assigned tasks
6. Post updates to `agents/CHAT.md`

### EXIT (Before Switching - MANDATORY)
7. Update `context.md` - Key decisions, findings
8. Update `current_task.md` - Progress %, next items
9. Update `next_steps.md` - Resume plan

**State files are your WORKING MEMORY. Without them, you forget everything!**

---

## Cross-Persona Communication

Use `@mentions` in CHAT.md:

```markdown
@Neo *swe impl Task 4           # Request implementation
@Trin *qa test all              # Request testing
@Oracle *ora ask <question>     # Query knowledge
@Morpheus *lead decide <choice> # Request decision
```

---

## Anti-Loop Protocol

If a fix fails ONCE:
1. **STOP** - Don't retry immediately
2. **Oracle First** - `@Oracle *ora ask Have we seen this before?`
3. Read error logs carefully
4. ONE retry with new approach
5. If THAT fails → Document and escalate

**NO THIRD ATTEMPT** without consulting Oracle and getting user input.

---

## Quality Standards

- **"We don't ship shit!"** (Uncle Bob)
- If it's not tested, it doesn't exist
- Use absolute imports (full package paths)
- Follow PEP-8, use type hints

---

## Chat Message Format

```
[DATETIME] [Persona]->[recipient] *command*: message
```

---

## Complete `*chat` Examples

### Example 1: Auto-Select Mode (Implicit)

**User types:** `*chat help me fix the bug in parser.py`

**AI executes:**

```bash
# Step 1: Log user's message
./agents/tools/chat.py "help me fix the bug in parser.py" --persona User --cmd "request"

# Step 2-3: Read chat, identify Neo (coding task - auto-selected)
# (AI determines this is a coding task → Neo)

# Step 4: Load Neo's agent and state
# (AI reads Neo_SWE_AGENT.md and neo.docs/context.md, etc.)

# Step 5: Perform the fix as Neo
# (AI investigates and fixes the bug)

# Step 6: Post response
./agents/tools/chat.py "Fixed the bug in parser.py. The issue was..." --persona Neo --cmd "swe fix"

# Step 7: Save state
# (AI updates neo.docs/context.md, current_task.md, next_steps.md)
```

### Example 2: Direct Invocation Mode (Explicit)

**User types:** `*chat @neo *fix bug in parser.py line 42`

**AI executes:**

```bash
# Step 1: Log user's message
./agents/tools/chat.py "@neo *fix bug in parser.py line 42" --persona User --cmd "request"

# Step 2-3: Parse direct invocation
# @neo → Target: Neo
# *fix → Command: *swe fix
# "bug in parser.py line 42" → Arguments

# Step 4: Load Neo's agent and execute command
# (AI reads Neo_SWE_AGENT.md, loads state, becomes Neo)
# (AI executes the *swe fix command with the given arguments)

# Step 5: Perform the fix as Neo
# (AI goes directly to parser.py line 42 and fixes the bug)

# Step 6: Post response
./agents/tools/chat.py "Fixed line 42 in parser.py..." --persona Neo --cmd "swe fix"

# Step 7: Save state
# (AI updates neo.docs/context.md, current_task.md, next_steps.md)
```

### Direct Invocation Quick Reference

| User Types | Persona | Command Executed |
|------------|---------|------------------|
| `*chat @neo *fix X` | Neo | `*swe fix X` |
| `*chat @neo *impl Y` | Neo | `*swe impl Y` |
| `*chat @trin *test all` | Trin | `*qa test all` |
| `*chat @morpheus *arch Z` | Morpheus | `*lead arch Z` |
| `*chat @oracle *ask Q` | Oracle | `*ora ask Q` |
| `*chat @mouse *status` | Mouse | `*sm status` |
| `*chat @cypher *req R` | Cypher | `*pm req R` |
| `*chat @bob *prompt P` | Bob | `*prompt P` |

**CHAT.md now contains:**
```
[2026-02-01 12:00:00] [User]->[all] *request*: @neo *fix bug in parser.py line 42
[2026-02-01 12:05:00] [Neo]->[all] *swe fix*: Fixed line 42 in parser.py...
```
