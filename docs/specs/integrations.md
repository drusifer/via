# VIA Integrations: MCP Server and Web UI

TL;DR: How to register and run VIA as a Model Context Protocol (MCP) server for AI agents, and using the interactive browser interface.

## Table of Contents

- [MCP Mode (AI Agent Integration)](#mcp-mode-ai-agent-integration)
- [Web Interface](#web-interface)

---

## MCP Mode (AI Agent Integration)

VIA can run as an MCP (Model Context Protocol) server, exposing a `via_query` tool to Claude Code and other MCP clients over JSON-RPC 2.0 via stdio. The MCP process performs the initial index, starts watch mode, and serves the web UI, so one `via mcp serve` instance keeps everything current.

### Setup

```bash
# Register via as an MCP server in the current project
via install mcp

# Check registration status
via status mcp

# Remove registration
via uninstall mcp
```

`via install mcp` writes `.mcp.json` in the project root (next to `.via/`). Claude Code reads this at session startup and calls `tools/list` to discover the `via_query` tool.

### Starting the Server

```bash
via mcp serve              # Serve from current directory
via mcp serve /path/to/project   # Serve a specific project
```

The server starts WatchService in a background thread, serves the web UI on `http://localhost:7891` by default, and listens for JSON-RPC 2.0 on stdin/stdout. Exit by closing stdin (Claude Code does this automatically on session end).

### Calling via_query

Claude Code can call the tool with the same CLI args you would use on the command line:

```json
{"args": ["-mg", "*Parser*", "-tc"]}         // All Parser classes
{"args": ["-mg", "*", "-tf", "-n", "20"]}   // First 20 functions
{"args": ["stats"]}                           // Database statistics
```

Results are returned as a JSON array of symbol objects with fields: `symbol_name`, `symbol_type`, `file_path`, `line_number`, `byte_offset`, `byte_length`, `qualified_name`, `parent_name`.

### Inspecting the Schema

```bash
via mcp schema             # Print the via_query tool schema as JSON
```

This shows exactly what Claude Code sees when it calls `tools/list`.

---

## Web Interface

VIA includes a browser-based UI for interactive symbol search. It mirrors all CLI capabilities with point-and-click controls.

### Starting the Web UI

```bash
via web                # Start on default port (8080)
via web --port 9000    # Custom port
```

Open `http://localhost:8080` in your browser. The server auto-starts watch mode — the index stays current as you edit files.

### Layout

The UI is split into two panels:

**Left — Controls**: Build your query interactively:
- **Match**: Pattern input, match type (Glob/Regex/SQL LIKE), Case-insensitive (`-I`), Qualified names (`-Q`)
- **Symbol Types**: Chips for `Class`, `Function`, `Method`, `Import`, `Global`, `File Path`, `File Name`, `MD Header`
- **Filters**: Limit, Newer than (`--newerthan`), Older than (`--olderthan`)
- **Relationship**: Type dropdown (`--via <rel>`), Negative relationship toggle (`--sans`), Stale only toggle (`--stale`)
- **Output Format**: List / Table / Diagram toggle buttons
- **Run Query** / **Reset** (sticky at bottom of panel — always reachable)

**Right — Results**: Live query output in the selected format:
- **List**: Default card view — symbol name, colored type badge, `file:line` location
- **Table**: Sortable columns (Name, Type, File, Line) with colored type badges
- **Diagram**: Mermaid UML class diagram (inheritance trees, rendered live)

**Top — Status Bar**: Indexed directory, file count, symbol count, time since last index, and a live watch indicator (green dot = watching).

### Screenshots

**Initial load** — controls panel ready, results panel waiting for input:

![Initial load](../tests/e2e/screenshots/ux-01-initial-load.png)

**List results** — default view after querying for `Calculator`:

![List results](../tests/e2e/screenshots/ux-02-list-results.png)

**Table format** — all 9 symbols as a sortable table; Relationship section showing `--sans` and `--stale` toggles:

![Table format](../tests/e2e/screenshots/ux-03-table-format.png)

**Diagram format** — Mermaid UML inheritance diagram rendered in the results panel:

![Diagram format](../tests/e2e/screenshots/ux-04-diagram-format.png)

**Error state** — shown when the database is unavailable (run `via index .` first):

![Error state](../tests/e2e/screenshots/ux-05-error-state.png)

