"""
MCP tool schema builder for via_query.

TLDR:
    build_tool_schema() constructs the MCP tool definition for via_query,
    including name, description, inputSchema (args: list[str]), and at least
    8 annotated examples. Reads MATCH_FLAGS, TYPE_FLAGS, OUTPUT_FLAGS,
    and FORMAT_FLAGS to build a comprehensive description that Claude can use
    to construct correct via CLI invocations.
    Used by `via mcp schema` (human inspection) and `tools/list` (FastMCP).

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

from via.core.flag_groups import (
    FORMAT_FLAGS,
    MATCH_FLAGS,
    OUTPUT_FLAGS,
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

    description = (
        "Query the VIA codebase index. Pass CLI args as a list of strings.\n\n"
        f"Match flags: {match_help}\n"
        f"Type filters: {type_help}\n"
        f"Output formats: {output_help}\n"
        f"Format modifiers: {format_help}\n\n"
        "Relationship query syntax:\n"
        "  --via/-V REL  Positive: return subjects WITH the relationship to the object.\n"
        "  --sans/-S REL Negative: return subjects with NO such relationship.\n"
        "  REL is one of: inherits-from, calls, imports, references, declares\n\n"
        "  KNOWN anchor goes on the LEFT (before --via/--sans). Wildcard * goes on the RIGHT.\n"
        "  --via: returns things that relate TO the anchor (callers, subclasses, importers).\n"
        "    Example: find all subclasses of Renderer\n"
        "      [\"-mg\", \"Renderer\", \"-tc\", \"--via\", \"inherits-from\", \"-mg\", \"*\", \"-tc\"]\n"
        "  --sans: returns subjects with no matching relationship.\n"
        "    Example: find functions that call nothing\n"
        "      [\"-mg\", \"*\", \"-tf\", \"--sans\", \"calls\", \"-mg\", \"*\", \"-tf\"]\n\n"
        "Match-stage filters (add to any match stage):\n"
        "  --lang LANG    Filter by language: py/python, js/javascript, ts/typescript, md/markdown\n"
        "  --subtype TYPE Filter by symbol subtype (case-sensitive; e.g. interface, enum, arrow_function).\n"
        "                 Unknown values return empty (no error).\n\n"
        "Note: -mg matches against the symbol name (not file path). For filepath symbols (-tF),\n"
        "the match is against the basename (e.g. 'utils.py'). For full-path matching, add -Q\n"
        "(e.g. via -mg 'via/core/*' -tF -Q matches by directory path, not just filename).\n\n"
        "Note: --via references tracks name usages inside function/method bodies only. Class\n"
        "inheritance declarations and module-level usages are not tracked by references.\n\n"
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
            "args": ["-mg", "BaseClass", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"],
        },
        {
            "description": "Find what a class inherits FROM (swap anchor and result sides)",
            "args": ["-mg", "MyClass", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"],
        },
        {
            "description": "Find callers of a function (anchor=func, result=callers)",
            "args": ["-mg", "connect", "-tf", "--via", "calls", "-mg", "*"],
        },
        {
            "description": "Find what a method calls (anchor on method, result=callees)",
            "args": ["-mg", "my_method", "-tm", "--via", "calls", "-mg", "*"],
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
            "args": ["-mg", "logging", "--via", "imports", "-mg", "*"],
        },
        {
            "description": "Find classes that inherit from nothing (--sans negation)",
            "args": ["-mg", "*", "-tc", "--sans", "inherits-from", "-mg", "*", "-tc"],
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
