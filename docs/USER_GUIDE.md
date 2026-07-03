# VIA User Guide

TLDR: Comprehensive entry point for VIA documentation. The guide has been distilled into atomic, focused specifications.

## Documentation Index

### 1. [Installation & Indexing](specs/installation_and_indexing.md)
Detailed setup instructions, re-indexing commands, supported programming languages, incremental update tracking, and watch mode triggers.

### 2. [Search Pipeline Syntax](specs/search_pipeline.md)
Reference for glob, regex, and SQL LIKE pattern matching, symbol type filters, context options, and the natural language interpreter grammar.

### 3. [Output Formatting](specs/output_formats.md)
Guide to configuring CLI outputs using lists, tables, syntax-highlighted source, docstring usage, and JSON arrays.

### 4. [Relationships & Container Filters](specs/relationships_and_filters.md)
Advanced querying for tracing inheritance, call graphs, import dependencies, symbol references, file containment constraints, and using the programmatic Python API.

### 5. [Temporal Filters](specs/temporal_queries.md)
Syntax and duration formats for querying files modified within or outside of specific time windows (e.g. `--newerthan`, `--olderthan`).

### 6. [Integrations (MCP & Web UI)](specs/integrations.md)
How to configure and start the Model Context Protocol (MCP) server for Claude Code and access the interactive web dashboard.

### 7. [Real-World Query Handbook & Troubleshooting](specs/real_world_queries.md)
20 common developer questions answered with exact commands, troubleshooting common errors, quick command references, and legacy syntax maps.

### 8. [Test Coverage & Quality Visualization](specs/test_coverage.md)
Capturing per-test coverage (`via coverage import-contexts`), querying it via `-Vcovered-by`, and browsing it visually in the web UI's Coverage view (intensity heatmap, efficiency table, leaf drill-down).
