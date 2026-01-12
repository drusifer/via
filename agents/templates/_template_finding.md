# Finding Template

## [YYYY-MM-DD] {Short Descriptive Title}

> **Tags:** #{Category} #{Component} #{AgentName}

### The Discovery
{Concise statement of the fact or behavior found. Example: "The NTAG 424 DNA chip has a hardware buffer limit of 32 bytes for this specific command."}

### Context
{How was this discovered? Example: "Observed data truncation during bulk write operations in the provisioning script."}

### Evidence
{Logs, code snippets, error messages, or spec references that prove the finding.}

### Impact
{How does this affect the system? Example: "We must chunk all write operations into 30-byte segments to be safe."}

### References
- **File:** `{path/to/relevant/file}`
- **Source:** {URL, Spec Section, or "Empirical"}