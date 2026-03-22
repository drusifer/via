"""
MCP tool schema builder for via_query.

TLDR:
    build_tool_schema() constructs the MCP tool definition for via_query,
    including name, description, inputSchema (args: list[str]), and at least
    8 annotated examples. Reads MATCH_FLAGS, TYPE_FLAGS, OUTPUT_FLAGS,
    RELATIONSHIP_FLAGS, and FORMAT_FLAGS to build a comprehensive description
    that Claude can use to construct correct via CLI invocations.
    Used by `via mcp schema` (human inspection) and `tools/list` (FastMCP).

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

from via.core.flag_groups import (
    FORMAT_FLAGS,
    MATCH_FLAGS,
    OUTPUT_FLAGS,
    RELATIONSHIP_FLAGS,
    TYPE_FLAGS,
)


def build_tool_schema() -> dict:
    """Build the MCP tool definition for via_query.

    Returns:
        Dict conforming to MCP tool schema format.
    """
    match_help = ", ".join(f"{f.short}/{f.long} ({f.help})" for f in MATCH_FLAGS)
    type_help = ", ".join(f"{f.short}/{f.long} ({f.help})" for f in TYPE_FLAGS)
    output_help = ", ".join(f"{f.short}/{f.long} ({f.help})" for f in OUTPUT_FLAGS)
    format_help = ", ".join(f"{f.short}/{f.long} ({f.help})" for f in FORMAT_FLAGS)
    rel_help = ", ".join(f"{f.short}/{f.long} ({f.help})" for f in RELATIONSHIP_FLAGS)

    description = (
        "Query the VIA codebase index. Pass CLI args as a list of strings.\n\n"
        f"Match flags: {match_help}\n"
        f"Type filters: {type_help}\n"
        f"Output formats: {output_help}\n"
        f"Format modifiers: {format_help}\n"
        f"Relationship queries: {rel_help}\n\n"
        "Relationship query syntax: <anchor-args> -Vxxx <result-args> [-iv]\n"
        "  KNOWN anchor goes on the LEFT (before -Vxxx). Wildcard * goes on the RIGHT.\n"
        "  Without -iv: returns things that relate TO the anchor (callers, subclasses, importers).\n"
        "    Example: find all subclasses of Renderer\n"
        "      [\"-mg\", \"Renderer\", \"-tc\", \"-Vinh\", \"-mg\", \"*\", \"-tc\"]\n"
        "  With -iv: returns what the anchor relates TO (callees, base classes, imported modules).\n"
        "    Example: find what a method calls\n"
        "      [\"-mg\", \"my_method\", \"-tm\", \"-Vca\", \"-iv\", \"-mg\", \"*\"]\n\n"
        "Note: -mg matches against the symbol name (not file path). For filepath symbols (-tF),\n"
        "the match is against the basename (e.g. 'utils.py'). For full-path matching, add -Q\n"
        "(e.g. via -mg 'via/core/*' -tF -Q matches by directory path, not just filename).\n\n"
        "Note: -Vr (references) tracks name usages inside function/method bodies only. Class\n"
        "inheritance declarations and module-level usages are not tracked by -Vr.\n\n"
        "Returns a JSON array of symbol objects when -oJ is used (default for MCP)."
    )

    examples = [
        {
            "description": "Find all classes matching a glob pattern",
            "args": ["-mg", "*Service*", "-tc"],
        },
        {
            "description": "Find functions matching a name glob pattern",
            "args": ["-mg", "*parse*", "-tf"],
        },
        {
            "description": "Find methods by regex, JSON output",
            "args": ["-mr", "^get_", "-tm", "-oJ"],
        },
        {
            "description": "Show all imports in the codebase",
            "args": ["-mg", "*", "-ti"],
        },
        {
            "description": "Find files by basename pattern (-mg matches filename, not full path)",
            "args": ["-mg", "*service*", "-tF"],
        },
        {
            "description": "Find all subclasses of a base class (anchor=base, result=subclasses)",
            "args": ["-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc"],
        },
        {
            "description": "Find what a class inherits FROM (-iv returns the base classes)",
            "args": ["-mg", "MyClass", "-tc", "-Vinh", "-iv", "-mg", "*", "-tc"],
        },
        {
            "description": "Find callers of a function (anchor=func, result=callers)",
            "args": ["-mg", "connect", "-tf", "-Vca", "-mg", "*"],
        },
        {
            "description": "Find what a method calls (-iv returns the callees; anchor on method, not class)",
            "args": ["-mg", "my_method", "-tm", "-Vca", "-iv", "-mg", "*"],
        },
        {
            "description": "Find all global variables as JSON",
            "args": ["-mg", "*", "-tg", "-oJ"],
        },
        {
            "description": "Find markdown headers matching a pattern",
            "args": ["-mg", "*API*", "-tH"],
        },
        {
            "description": "Find what imports a module (anchor=module, result=importers)",
            "args": ["-mg", "logging", "-Vimp", "-mg", "*"],
        },
    ]

    return {
        "name": "via_query",
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "CLI arguments for via query. "
                        "Example: [\"-mg\", \"*Service*\", \"-tc\", \"-oJ\"]"
                    ),
                }
            },
            "required": ["args"],
        },
        "examples": examples,
    }
