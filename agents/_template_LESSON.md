# Lesson Template

## [YYYY-MM-DD] {Short Descriptive Title}

> **Tags:** #{Category} #{Component} #{AgentName}

### Context
{Briefly describe the situation, task, or error that led to this lesson. Example: "While debugging the NTAG 424 CMAC calculation..."}

### The Issue
{What went wrong? What was the blocker? Example: "We assumed standard zero-padding, but the hardware requires ISO 9797-1 padding."}

### The Solution
{How was it resolved? Example: "Implemented a custom padding function in crypto.py."}

### The Rule (The "Lesson")
{The explicit instruction for future agents. This is the most important part. Example: "ALWAYS use ISO 9797-1 padding for all CMAC operations. Never use zero padding."}

### References
- **Commit:** {Commit Hash or "N/A"}
- **Files:** `{path/to/affected_file.py}`
