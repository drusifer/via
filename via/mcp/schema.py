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
        "Command structure:\n"
        "  via <match stage> [--via|--sans REL <relationship stage>] [options]\n"
        "  Use only one match flag (-mg, -mr, or -ms) per stage; type flags may be combined.\n"
        "  Use uppercase -tH for markdown headers; lowercase -th is not a valid flag.\n\n"
        "Common tasks:\n"
        "  Find symbol: [\"-mg\", \"*Service*\", \"-tc\"]\n"
        "  Read symbol body: [\"--canned\", \"symbol-body\", \"--args\", \"symbol=parse_args\"]\n"
        "  Find callers: [\"--canned\", \"callers\", \"--args\", \"symbol=parse_args\"]\n"
        "  Docs headers: [\"--canned\", \"docs-headers\", \"--args\", \"pattern=*API*\"]\n"
        "  Regex naming search: [\"-mr\", \"^get_\", \"-tm\"]\n"
        "  Multi-type search: [\"-mg\", \"parse*\", \"-tf\", \"-tm\"]\n"
        "  Paged broad scan: [\"--canned\", \"paged-scan\", \"--args\", \"pattern=*,slice=0:20\", \"-tc\"]\n\n"
        "Dart/Flutter examples:\n"
        "  Dart classes: [\"-mg\", \"*Screen\", \"-tc\", \"--lang\", \"dart\"]\n"
        "  Flutter build methods: [\"-mg\", \"build\", \"-tm\", \"--lang\", \"dart\", \"-oR\"]\n"
        "  Stateful widgets: [\"-mg\", \"*\", \"-tc\", \"--lang\", \"dart\", \"--via\", \"inherits-from\", \"-mg\", \"StatefulWidget\", \"-tc\"]\n"
        "  Dart imports/exports/parts are directive strings, not resolved package dependencies.\n"
        "  VIA does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.\n\n"
        "Advanced relationship query syntax:\n"
        "  Prefer --canned for common caller/subclass tasks.\n"
        "  Current runtime positive lookups use the known anchor before --via and wildcard result filter after it.\n"
        "  REL is one of: inherits-from, calls, imports, references, declares\n\n"
        "  Example: find all subclasses of Renderer\n"
        "      [\"-mg\", \"Renderer\", \"-tc\", \"--via\", \"inherits-from\", \"-mg\", \"*\", \"-tc\"]\n"
        "  Example: find functions that call connect\n"
        "      [\"-mg\", \"connect\", \"-tf\", \"--via\", \"calls\", \"-mg\", \"*\", \"-tf\"]\n"
        "  Example: find functions that call nothing\n"
        "      [\"-mg\", \"*\", \"-tf\", \"--sans\", \"calls\", \"-mg\", \"*\", \"-tf\"]\n\n"
        "  Note: --via declares filters containers that declare matching symbols. It does not provide\n"
        "  a supported inverse shortcut for returning all symbols declared in a file.\n\n"
        "Match-stage filters (add to any match stage):\n"
        "  --lang LANG    Filter by language: py/python, js/javascript, ts/typescript, dart, md/markdown\n"
        "  --subtype TYPE Filter by symbol subtype (case-sensitive; e.g. interface, enum, arrow_function).\n"
        "                 Unknown values return empty (no error).\n\n"
        "Note: -mg matches against the symbol name (not file path). For filepath symbols (-tF),\n"
        "the match is against the basename (e.g. 'utils.py'). For full-path matching, add -Q\n"
        "(e.g. via -mg 'via/core/*' -tF -Q matches by directory path, not just filename).\n\n"
        "Note: --via references tracks name usages inside function/method bodies only. Class\n"
        "inheritance declarations and module-level usages are not tracked by references.\n\n"
        "Result windowing: use --slice start:end to paginate (e.g. --slice 0:20 for first 20,\n"
        "--slice 20:40 for next 20). Mutually exclusive with -n/--limit.\n\n"
        "Response shape: {\"output_type\": \"...\", \"result\": ..., \"total\": N, \"shown\": M}.\n"
        "  output_type: \"json\" (default) | \"diagram\" | \"raw\" | \"table\" | \"list\" | \"formatted\" | \"usage\"\n"
        "  result: array of symbol dicts when output_type=json; plain text string otherwise.\n"
        "  total/shown: full match count and count returned (useful for --slice pagination).\n"
        "  When output_type=diagram and no relationships exist, falls back to output_type=json\n"
        "  with an empty result and a 'note' field explaining the fallback.\n\n"
        "Returns symbol objects in result array (JSON dicts with symbol_name, file_path, etc.) "
        "when no output format flag is used."
    )

    examples = [
        {
            "description": "Find a class by glob pattern",
            "args": ["-mg", "*Service*", "-tc"],
        },
        {
            "description": "Read a function, method, or class body",
            "args": ["--canned", "symbol-body", "--args", "symbol=parse_args"],
        },
        {
            "description": "Find callers of a function",
            "args": ["--canned", "callers", "--args", "symbol=connect"],
        },
        {
            "description": "Find markdown headers matching a pattern (uppercase -tH)",
            "args": ["--canned", "docs-headers", "--args", "pattern=*API*"],
        },
        {
            "description": "Find methods by regex name search",
            "args": ["-mr", "^get_", "-tm"],
        },
        {
            "description": "Find functions or methods matching a glob pattern",
            "args": ["-mg", "parse*", "-tf", "-tm"],
        },
        {
            "description": "Page through a broad class scan",
            "args": ["--canned", "paged-scan", "--args", "pattern=*,slice=0:20", "-tc"],
        },
        {
            "description": "Find all subclasses of a base class (advanced relationship)",
            "args": ["-mg", "BaseClass", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"],
        },
        {
            "description": "Find Dart screen classes",
            "args": ["-mg", "*Screen", "-tc", "--lang", "dart"],
        },
        {
            "description": "Find Flutter build methods as raw source",
            "args": ["-mg", "build", "-tm", "--lang", "dart", "-oR"],
        },
        {
            "description": "Find Flutter StatefulWidget classes",
            "args": [
                "-mg",
                "*",
                "-tc",
                "--lang",
                "dart",
                "--via",
                "inherits-from",
                "-mg",
                "StatefulWidget",
                "-tc",
            ],
        },
        {
            "description": "Find methods that call a function (advanced relationship)",
            "args": ["-mg", "connect", "--via", "calls", "-mg", "*", "-tm"],
        },
        {
            "description": "Find classes that inherit from nothing (advanced --sans negation)",
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
