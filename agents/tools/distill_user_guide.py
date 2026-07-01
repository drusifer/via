import os

workspace_dir = "/home/drusifer/Projects/via"
user_guide_path = os.path.join(workspace_dir, "docs", "USER_GUIDE.md")
specs_dir = os.path.join(workspace_dir, "docs", "specs")

os.makedirs(specs_dir, exist_ok=True)

with open(user_guide_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def get_chunk(start_idx, end_idx):
    # line numbers in view_file are 1-indexed.
    # start_idx is 1-indexed inclusive, end_idx is 1-indexed inclusive.
    return "".join(lines[start_idx-1:end_idx])

# Define the specs to generate
specs = [
    {
        "filename": "installation_and_indexing.md",
        "title": "VIA Installation and Indexing Specification",
        "tldr": "Instructions for installing VIA, running basic index operations, tracking incremental changes, and using watch mode.",
        "toc": [
            "- [Installation](#installation)",
            "- [Quick Start](#quick-start)",
            "- [Indexing](#indexing)",
            "- [Watch Mode](#watch-mode)"
        ],
        "content": get_chunk(26, 131) + "\n---\n\n" + get_chunk(595, 605)
    },
    {
        "filename": "search_pipeline.md",
        "title": "VIA Search Pipeline Specification",
        "tldr": "Complete guide to matching patterns and searching symbols using the pipeline syntax, context options, and natural language query translation.",
        "toc": [
            "- [Searching with Pipeline Syntax](#searching-with-pipeline-syntax)",
            "- [Context Lines](#context-lines)",
            "- [Natural Language Queries](#natural-language-queries-via-ask--via-q)"
        ],
        "content": get_chunk(133, 201) + "\n---\n\n" + get_chunk(306, 337) + "\n---\n\n" + get_chunk(1176, 1215)
    },
    {
        "filename": "output_formats.md",
        "title": "VIA Output Formats Specification",
        "tldr": "Reference for formatting search results using list, table, raw source, highlighted code, usage docstrings, and JSON formats.",
        "toc": [
            "- [Output Formats](#output-formats)",
            "- [List Output](#list-output-default)",
            "- [Table Output](#table-output)",
            "- [Raw Source Output](#raw-source-output)",
            "- [Formatted Output](#formatted-output-syntax-highlighting)",
            "- [Usage Output](#usage-output-docstrings)"
        ],
        "content": get_chunk(203, 305)
    },
    {
        "filename": "relationships_and_filters.md",
        "title": "VIA Relationship Queries and Container Filters",
        "tldr": "Guide to building advanced queries that trace inheritance, calls, imports, references, and container declarations, plus programmatic Python API usage.",
        "toc": [
            "- [Relationship Queries](#relationship-queries)",
            "- [Container Filters](#container-filters-via-declares)",
            "- [Python API](#python-api)"
        ],
        "content": get_chunk(339, 472) + "\n---\n\n" + get_chunk(515, 550) + "\n---\n\n" + get_chunk(474, 513)
    },
    {
        "filename": "temporal_queries.md",
        "title": "VIA Temporal Queries Specification",
        "tldr": "Reference guide for filtering symbols based on file modification durations using newerthan and olderthan filters.",
        "toc": [
            "- [Temporal Queries](#temporal-queries)",
            "- [Duration Format](#duration-format)",
            "- [Examples](#examples)"
        ],
        "content": get_chunk(552, 593)
    },
    {
        "filename": "integrations.md",
        "title": "VIA Integrations: MCP Server and Web UI",
        "tldr": "How to register and run VIA as a Model Context Protocol (MCP) server for AI agents, and using the interactive browser interface.",
        "toc": [
            "- [MCP Mode (AI Agent Integration)](#mcp-mode-ai-agent-integration)",
            "- [Web Interface](#web-interface)"
        ],
        "content": get_chunk(607, 710)
    },
    {
        "filename": "real_world_queries.md",
        "title": "VIA Real-World Queries, Troubleshooting, and Quick Reference",
        "tldr": "Practical query handbook, legacy subcommand mapping, troubleshooting guide, and cheat sheet for daily developer workflows.",
        "toc": [
            "- [Legacy Subcommand Syntax](#legacy-subcommand-syntax)",
            "- [Practical Examples](#practical-examples)",
            "- [20 Real-World Queries](#20-real-world-queries)",
            "- [Troubleshooting](#troubleshooting)",
            "- [Quick Reference](#quick-reference)"
        ],
        "content": get_chunk(713, 1174)
    }
]

# Generate each distilled specification document
for spec in specs:
    dest_path = os.path.join(specs_dir, spec["filename"])
    
    file_content = [
        f"# {spec['title']}\n",
        f"TL;DR: {spec['tldr']}\n",
        "## Table of Contents\n"
    ]
    file_content.extend(spec["toc"])
    file_content.append("\n---\n")
    file_content.append(spec["content"])
    
    with open(dest_path, 'w', encoding='utf-8') as out_f:
        out_f.write("\n".join(file_content))
    print(f"Created distilled spec: docs/specs/{spec['filename']}")

# Generate the new high-level USER_GUIDE.md index file
user_guide_content = """# VIA User Guide

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
"""

with open(user_guide_path, 'w', encoding='utf-8') as f:
    f.write(user_guide_content)
print("Updated USER_GUIDE.md to act as the index.")
