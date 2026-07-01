import os
import re

workspace_dir = "/home/drusifer/Projects/via"

tldrs = {
    "via/api/__init__.py": '''"""Programmatic VIA query construction and execution helpers.

TLDR:
    Exposes query builders and execution runners for programmatic queries.
    Key classes: ViaQueryBuilder (fluent query builder), RelationshipQueryBuilder,
    ViaQuery (compiled immutable query), and ViaRunner (executes compiled queries).

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/api/query_builder.py": '''"""Fluent query builders and execution adapters for programmatic VIA queries.

TLDR:
    Implements a fluent API for building and executing VIA search pipeline stages.
    Key classes: ViaQueryBuilder (constructs queries), RelationshipQueryBuilder
    (constructs relationship filters), ViaQuery (holds compiled query stages),
    and ViaRunner (runs compiled queries against DatabaseStore).
    Role: Programmatic entry point, consumed by external tools and scripts.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/canned.py": '''"""Loading and expanding of predefined 'canned' search queries.

TLDR:
    Handles built-in and user-defined canned queries from JSON configuration files.
    Key functions: load_canned_queries() (reads queries from disk),
    expand_canned_query() (expands a canned name into CLI arguments).
    Role: Consumed by CLI routing to support canned search shortcuts.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/cli/__init__.py": '''"""CLI command implementations and routing.

TLDR:
    Exposes command handlers and argument configurations for CLI subcommands.
    Key modules: commands/ (ask, base, index, mcp, stats).
    Role: Main router for the CLI application.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/commands/ask.py": '''"""Command handler for natural language search queries.

TLDR:
    Implements the 'via ask' / 'via q' CLI command.
    Key class: AskCommandHandler (translates natural language to standard via args
    using LarkNaturalQueryParser, then executes the compiled pipeline).
    Role: Natural language query handler. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/commands/base.py": '''"""Abstract base class for all CLI command handlers.

TLDR:
    Defines the standard interface for implementing CLI command executors.
    Key class: CommandHandlerABC (defines run() method returning exit codes).
    Role: Base class for CLI subcommands. Consumed by command registration.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/commands/index.py": '''"""Command handler for indexing and watch mode triggers.

TLDR:
    Implements the 'via index' CLI command.
    Key class: IndexCommandHandler (drives indexing using IndexingService and
    starts watch mode triggers using WatchService).
    Role: Triggers indexing and watch mode. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/commands/mcp.py": '''"""Command handler for starting the Model Context Protocol (MCP) server.

TLDR:
    Implements the 'via mcp' CLI command.
    Key class: McpCommandHandler (starts the stdio MCP server using McpServer).
    Role: Model Context Protocol command handler. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/commands/stats.py": '''"""Command handler for displaying database statistics.

TLDR:
    Implements the 'via stats' CLI command.
    Key class: StatsCommand (gathers record counts, language breakdowns, and
    indexing details from DatabaseStore, outputting as text or JSON).
    Role: Database statistics reporter. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/parsers/dart_parser.py": '''"""Parser for Dart and Flutter source files using tree-sitter.

TLDR:
    Extracts structural code entities and relationships from Dart (.dart) files.
    Key class: DartParser (implements parse() using tree-sitter-language-pack to
    extract classes, mixins, enums, constructors, methods, globals, calls, and imports).
    Role: Dart parser plugin. Consumed by ParserRegistry.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/pipeline/handlers.py": '''"""Registry and executors for pipeline execution stages.

TLDR:
    Implements stage handlers that orchestrate execution of individual pipeline steps.
    Key classes: StageHandlerABC (handler interface), MatchStageHandler (performs database
    matching), RenderStageHandler (formats results), StatsStageHandler (displays stats),
    and StageHandlerRegistry (maps StageTypes to handlers).
    Role: Stage executor registry. Consumed by PipelineExecutor.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/pipeline/natural_query.py": '''"""Natural language parser mapping English queries to standard VIA pipeline arguments.

TLDR:
    Implements Lark-based grammar translation of English-like query strings.
    Key classes: LarkNaturalQueryParser (compiles query to AST and transforms it
    to standard arguments using Lark and EBNF), QueryTransformer (walks parsed AST),
    and NaturalQueryParserBase (abstract parser interface).
    Role: EBNF natural query compiler. Consumed by AskCommandHandler.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/pipeline/stage_builder.py": '''"""Helper utilities to construct normalized match stages and relationship filters.

TLDR:
    Provides construction helper functions for building match stages and filters.
    Key functions: finalize_match_namespace() (normalizes CLI options),
    build_relationship_filter() (builds filters), and build_match_stage()
    (constructs match pipeline stages).
    Role: Builder helper functions. Consumed by parser.py and query_builder.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""''',

    "via/web/api/__init__.py": '''"""Web API handlers for the via Web UI.

TLDR:
    API handlers routing endpoints for the interactive query browser.
    Key modules: query (runs queries), status (re-indexing and database stats).

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""'''
}

def update_file_docstring(rel_path, new_docstring):
    full_path = os.path.join(workspace_dir, rel_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for shebang
    shebang_match = re.match(r'^(#![^\n]*\n)', content)
    shebang = shebang_match.group(1) if shebang_match else ''
    if shebang:
        content = content[len(shebang):]
        
    # Check if there is an existing docstring at the beginning of the file (ignoring empty space)
    # Match any initial block starting with """
    docstring_pattern = re.compile(r'^\s*"""(.*?)"""', re.DOTALL)
    docstring_match = docstring_pattern.match(content)
    
    if docstring_match:
        # Replace existing docstring
        replaced_content = docstring_pattern.sub(new_docstring, content, count=1)
    else:
        # Prepend new docstring
        # Keep leading whitespace/newlines, strip it, and prepend docstring
        replaced_content = new_docstring + "\n\n" + content.lstrip()
        
    final_content = shebang + replaced_content
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"Updated TLDR docstring in: {rel_path}")

for rel_path, docstring in tldrs.items():
    update_file_docstring(rel_path, docstring)

print("TLDR updates complete.")
