"""Natural language parser mapping English queries to standard VIA pipeline arguments.

TLDR:
    Implements Lark-based grammar translation of English-like query strings.
    Key classes: LarkNaturalQueryParser (compiles query to AST and transforms it
    to standard arguments using Lark and EBNF), QueryTransformer (walks parsed AST),
    and NaturalQueryParserBase (abstract parser interface).
    Role: EBNF natural query compiler. Consumed by AskCommandHandler.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from lark import Lark, Transformer
from lark.exceptions import LarkError, UnexpectedInput

from via.pipeline.errors import PipelineParseError

# Target Nouns mapping to standard VIA flags
NOUN_MAP = {
    "classes": "-tc",
    "class": "-tc",
    "functions": "-tf",
    "function": "-tf",
    "methods": "-tm",
    "method": "-tm",
    "files": "-tF",
    "file": "-tF",
    "globals": "-tg",
    "global": "-tg",
    "variables": "-tg",
    "variable": "-tg",
    "constants": "-tg",
    "constant": "-tg",
    "imports": "-ti",
    "import": "-ti",
    "headers": "-tH",
    "header": "-tH",
    "sections": "-tH",
    "section": "-tH",
}

# Relation verbs mapping to standard relationship type strings and flags
RELATION_MAP = {
    # Positive (via)
    "calls": ("--via", "calls"),
    "call": ("--via", "calls"),
    "calling": ("--via", "calls"),
    
    "called by": ("--via", "called-by"),
    "are called by": ("--via", "called-by"),
    
    "references": ("--via", "references"),
    "reference": ("--via", "references"),
    "referencing": ("--via", "references"),
    
    "referenced by": ("--via", "referenced-by"),
    "mentioned by": ("--via", "referenced-by"),
    
    "declares": ("--via", "declares"),
    "declare": ("--via", "declares"),
    "declaring": ("--via", "declares"),
    
    "declared in": ("--via", "declared-in"),
    "are declared in": ("--via", "declared-in"),
    
    "inherits from": ("--via", "inherits-from"),
    "inherit from": ("--via", "inherits-from"),
    "inheriting from": ("--via", "inherits-from"),
    "extends": ("--via", "inherits-from"),
    "extend": ("--via", "inherits-from"),
    "extending": ("--via", "inherits-from"),
    
    "inherited by": ("--via", "inherited-by"),
    "are inherited by": ("--via", "inherited-by"),
    "extended by": ("--via", "inherited-by"),
    
    "imports": ("--via", "imports"),
    "import": ("--via", "imports"),
    "importing": ("--via", "imports"),
    
    "imported by": ("--via", "imported-by"),
    "are imported by": ("--via", "imported-by"),
    
    "covered by": ("--via", "covered-by"),
    "are covered by": ("--via", "covered-by"),
    
    "covering": ("--via", "covers"),
    "that cover": ("--via", "covers"),
    
    "http calls to": ("--via", "http-calls"),
    "http call to": ("--via", "http-calls"),
    "call endpoint": ("--via", "http-calls"),
    
    "http called by": ("--via", "http-called-by"),
    
    # Negated (sans)
    "do not call": ("--sans", "calls"),
    "not calling": ("--sans", "calls"),
    
    "do not reference": ("--sans", "references"),
    "not referencing": ("--sans", "references"),
    
    "do not inherit from": ("--sans", "inherits-from"),
    "not extending": ("--sans", "inherits-from"),
    "do not extend": ("--sans", "inherits-from"),
    
    "do not import": ("--sans", "imports"),
    "not importing": ("--sans", "imports"),
}


class QueryTransformer(Transformer):
    """Walks the parsed Lark AST and transforms it into list of VIA CLI arguments."""

    def quoted_string(self, args):
        val = str(args[0])
        if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
            return val[1:-1]
        return val

    def pattern(self, args):
        return str(args[0])

    def glob_matcher(self, args):
        verb = str(args[0]).lower()
        pattern = args[1]
        if "contains" in verb:
            if not pattern.startswith("*") and not pattern.endswith("*"):
                pattern = f"*{pattern}*"
            elif pattern.startswith("*") and not pattern.endswith("*"):
                pattern = f"{pattern}*"
            elif not pattern.startswith("*") and pattern.endswith("*"):
                pattern = f"*{pattern}"
        return ("-mg", pattern)

    def regex_matcher(self, args):
        pattern = args[1]
        return ("-mr", pattern)

    def matcher_clause(self, args):
        return args[0]

    def target_noun(self, args):
        noun = str(args[0]).lower()
        if noun not in NOUN_MAP:
            valid_str = "classes, functions, methods, files, globals, variables, constants, imports, headers, sections"
            raise PipelineParseError(
                f"Unknown symbol target '{noun}'. Valid options are: {valid_str}."
            )
        return NOUN_MAP[noun]

    def limit_modifier(self, args):
        return "all"

    def first_bounds(self, args):
        n = [int(x) for x in args if str(x).isdigit()][0]
        return ("-n", str(n))

    def last_bounds(self, args):
        n = [int(x) for x in args if str(x).isdigit()][0]
        return ("--slice", f"-{n}:")

    def between_bounds(self, args):
        nums = [int(x) for x in args if str(x).isdigit()]
        return ("--slice", f"{nums[0]-1}:{nums[1]}")

    def range_bounds(self, args):
        nums = [int(x) for x in args if str(x).isdigit()]
        return ("--slice", f"{nums[0]-1}:{nums[1]}")

    def offset_bounds(self, args):
        x = [int(x) for x in args if str(x).isdigit()][0]
        return ("--slice", f"{x-1}:")

    def bounds_clause(self, args):
        return args[0]

    def target_stage(self, args):
        stage_data = {
            "limit_modifier": None,
            "target_noun": None,
            "matcher": None,
            "bounds": None,
            "modifier": None,
        }
        for arg in args:
            if arg is None:
                continue
            if arg == "all":
                stage_data["limit_modifier"] = "all"
            elif isinstance(arg, tuple) and arg[0] in ("-mg", "-mr"):
                stage_data["matcher"] = arg
            elif isinstance(arg, tuple) and arg[0] in ("-n", "--slice"):
                stage_data["bounds"] = arg
            elif isinstance(arg, str) and arg.startswith("-t"):
                stage_data["target_noun"] = arg
        return stage_data

    def positive_relation(self, args):
        return str(args[0])

    def negated_relation(self, args):
        return str(args[0])

    def relation_verb(self, args):
        verb_text = " ".join(str(args[0]).lower().split())
        if verb_text in RELATION_MAP:
            return RELATION_MAP[verb_text]
        return ("--via", verb_text)

    def relational_stage(self, args):
        relation_val = None
        stage_val = None
        for arg in args:
            if isinstance(arg, tuple) and len(arg) == 2 and arg[0] in ("--via", "--sans"):
                relation_val = arg
            elif isinstance(arg, dict):
                stage_val = arg
        return {
            "relation": relation_val,
            "stage": stage_val,
        }

    def query(self, args):
        primary_stage = None
        relational_stages = []
        for arg in args:
            if isinstance(arg, dict) and "target_noun" in arg:
                primary_stage = arg
            elif isinstance(arg, dict) and "relation" in arg:
                relational_stages.append(arg)

        if primary_stage is None:
            raise PipelineParseError("No valid primary stage found in query.")

        cli_args = []

        # 1. Primary stage matcher
        if primary_stage["matcher"]:
            cli_args.extend(list(primary_stage["matcher"]))
        else:
            cli_args.extend(["-mg", "*"])
            
        # Primary stage target noun
        if primary_stage["target_noun"]:
            cli_args.append(primary_stage["target_noun"])

        # 2. Relational chaining stages
        for rel in relational_stages:
            rel_flag, rel_name = rel["relation"]
            cli_args.append(rel_flag)
            cli_args.append(rel_name)

            stage_info = rel["stage"]
            if stage_info["matcher"]:
                cli_args.extend(list(stage_info["matcher"]))
            else:
                cli_args.extend(["-mg", "*"])

            if stage_info["target_noun"]:
                cli_args.append(stage_info["target_noun"])

        # 3. Append Markdown output default
        cli_args.append("-fm")

        # 4. Append overall limit / bounds
        has_all = primary_stage["limit_modifier"] == "all"
        bounds = primary_stage["bounds"]

        if bounds:
            cli_args.extend(list(bounds))
        elif has_all:
            cli_args.extend(["-n", "0"])

        return cli_args


class NaturalQueryParserBase(ABC):
    """Abstract base class establishing the natural query translation seam."""

    @abstractmethod
    def parse(self, query: str) -> list[str]:
        """Translate natural language query into VIA CLI arguments list."""
        pass


# Case-insensitive EBNF Lark grammar mapping English queries to AST
GRAMMAR = """
?start: query

query: [action_prefix] target_stage (relational_stage)*

action_prefix: (FIND | SHOW_ME | LIST | LOCATE | GET | SEARCH_FOR) [article]
FIND: /find/i
SHOW_ME: /show\\s+me/i
LIST: /list/i
LOCATE: /locate/i
GET: /get/i
SEARCH_FOR: /search\\s+for/i

article: THE | A | AN
THE: /the/i
A: /\\ba\\b/i
AN: /\\ban\\b/i

target_stage: [limit_modifier] [bounds_clause] target_noun [matcher_clause] [bounds_clause] [modifier_clause]

limit_modifier: ALL
ALL: /all/i

target_noun: CLASSES | FUNCTIONS | METHODS | FILES | GLOBALS | VARIABLES | CONSTANTS | IMPORTS | HEADERS | SECTIONS
CLASSES: /class(es)?/i
FUNCTIONS: /functions?/i
METHODS: /methods?/i
FILES: /files?/i
GLOBALS: /globals?/i
VARIABLES: /variables?/i
CONSTANTS: /constants?/i
IMPORTS: /imports?/i
HEADERS: /headers?/i
SECTIONS: /sections?/i

matcher_clause: glob_matcher | regex_matcher
glob_matcher: (MATCHING | NAMED | WHOSE_NAME_CONTAINS) pattern
MATCHING: /matching/i
NAMED: /named/i
WHOSE_NAME_CONTAINS: /whose\\s+name\\s+contains/i

regex_matcher: MATCHING_REGEX pattern
MATCHING_REGEX: /matching\\s+regex/i

pattern: quoted_string | UNQUOTED_PATTERN
UNQUOTED_PATTERN: /[a-zA-Z0-9_*.\\/\\:-]+/

bounds_clause: first_bounds | last_bounds | between_bounds | range_bounds | offset_bounds
first_bounds: (FIRST | TOP) NUMBER [ROWS | MATCHES | RESULTS]
FIRST: /first/i
TOP: /top/i
ROWS: /rows/i
MATCHES: /matches/i
RESULTS: /results/i

last_bounds: LAST NUMBER [ROWS | MATCHES | RESULTS]
LAST: /last/i

between_bounds: BETWEEN [ROWS | MATCHES | RESULTS] NUMBER AND NUMBER
BETWEEN: /between/i
AND: /and/i

range_bounds: [ROWS | MATCHES | RESULTS] NUMBER TO NUMBER
TO: /to/i

offset_bounds: FROM [ROW | MATCH | RESULT] NUMBER
FROM: /from/i
ROW: /row/i
MATCH: /match/i
RESULT: /result/i

modifier_clause: IGNORING_CASE
IGNORING_CASE: /ignoring\\s+case/i

relational_stage: [connector] relation_verb target_stage

connector: THAT | WHICH | AND
THAT: /that/i
WHICH: /which/i

relation_verb: positive_relation | negated_relation

positive_relation: CALL_VERB | CALLED_BY_VERB | REFERENCE_VERB | REFERENCED_BY_VERB | DECLARE_VERB | DECLARED_IN_VERB | INHERIT_VERB | INHERITED_BY_VERB | IMPORT_VERB | IMPORTED_BY_VERB | COVERED_BY_VERB | COVERING_VERB | HTTP_CALL_VERB | HTTP_CALLED_BY_VERB

CALL_VERB: /\\bcalls?\\b/i | /\\bcalling\\b/i
CALLED_BY_VERB: /\\bare\\s+called\\s+by\\b/i | /\\bcalled\\s+by\\b/i
REFERENCE_VERB: /\\breferences?\\b/i | /\\breferencing\\b/i
REFERENCED_BY_VERB: /\\breferenced\\s+by\\b/i | /\\bmentioned\\s+by\\b/i
DECLARE_VERB: /\\bdeclares?\\b/i | /\\bdeclaring\\b/i
DECLARED_IN_VERB: /\\bare\\s+declared\\s+in\\b/i | /\\bdeclared\\s+in\\b/i
INHERIT_VERB: /\\binherits?\\s+from\\b/i | /\\binheriting\\s+from\\b/i | /\\bextends?\\b/i | /\\bextending\\b/i
INHERITED_BY_VERB: /\\bare\\s+inherited\\s+by\\b/i | /\\binherited\\s+by\\b/i | /\\bextended\\s+by\\b/i
IMPORT_VERB: /\\bimports?\\b/i | /\\bimporting\\b/i
IMPORTED_BY_VERB: /\\bare\\s+imported\\s+by\\b/i | /\\bimported\\s+by\\b/i
COVERED_BY_VERB: /\\bcovered\\s+by\\b/i | /\\bare\\s+covered\\s+by\\b/i
COVERING_VERB: /\\bcovering\\b/i | /\\bthat\\s+cover\\b/i
HTTP_CALL_VERB: /\\bhttp\\s+calls?\\s+to\\b/i | /\\bcall\\s+endpoint\\b/i
HTTP_CALLED_BY_VERB: /\\bhttp\\s+called\\s+by\\b/i

negated_relation: NOT_CALL_VERB | NOT_REFERENCE_VERB | NOT_INHERIT_VERB | NOT_IMPORT_VERB

NOT_CALL_VERB: /\\bdo\\s+not\\s+call\\b/i | /\\bnot\\s+calling\\b/i
NOT_REFERENCE_VERB: /\\bdo\\s+not\\s+reference\\b/i | /\\bnot\\s+referencing\\b/i
NOT_INHERIT_VERB: /\\bdo\\s+not\\s+inherit\\s+from\\b/i | /\\bnot\\s+extending\\b/i | /\\bdo\\s+not\\s+extend\\b/i
NOT_IMPORT_VERB: /\\bdo\\s+not\\s+import\\b/i | /\\bnot\\s+importing\\b/i

quoted_string: QUOTED_STRING
QUOTED_STRING: /'[^']*'/ | /"[^"]*"/

NUMBER: /\\d+/

%import common.WS
%import common.WORD
%ignore WS
"""


class LarkNaturalQueryParser(NaturalQueryParserBase):
    """Lark-based EBNF grammar compiler mapping English queries to standard VIA arguments."""

    def __init__(self):
        # Initialize Lark parser with LALR(1) algorithm and our custom grammar
        self._lark = Lark(GRAMMAR, parser="lalr", start="query")
        self._transformer = QueryTransformer()

    def parse(self, query: str) -> list[str]:
        """Translate natural query by compiling to AST and transforming stages.

        Args:
            query: Natural language English-like query

        Returns:
            List of compiled VIA CLI argument strings

        Raises:
            PipelineParseError: On parsing or target validation errors
        """
        # Strip trailing/leading spaces and whitespace
        clean_query = query.strip()
        if not clean_query:
            raise PipelineParseError("Empty natural query.")

        try:
            # Parse query string to Lark AST
            tree = self._lark.parse(clean_query)
            # Walk AST via Transformer to yield argument segments list
            return self._transformer.transform(tree)
        except UnexpectedInput as e:
            # Check if this unexpected token/character is an unknown target noun
            import re
            token_val = None
            if hasattr(e, 'token') and e.token:
                token_val = str(e.token)
            elif hasattr(e, 'pos_in_stream') and e.pos_in_stream is not None:
                remaining = clean_query[e.pos_in_stream:]
                m = re.match(r'^[a-zA-Z0-9_*-]+', remaining)
                if m:
                    token_val = m.group(0)

            if token_val and token_val.lower() not in NOUN_MAP:
                # If it's a simple word/identifier, treat it as unknown target noun
                # e.g. "widgets" or "controllers"
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token_val):
                    valid_str = "classes, functions, methods, files, globals, variables, constants, imports, headers, sections"
                    raise PipelineParseError(
                        f"Unknown symbol target '{token_val}'. Valid options are: {valid_str}.",
                        code="unknown_target_symbol"
                    )

            # Informative token location feedback
            raise PipelineParseError(
                f"Syntax error in natural query: {str(e)}",
                code="invalid_query_syntax"
            ) from e
        except LarkError as e:
            raise PipelineParseError(
                f"Failed to parse natural query: {str(e)}",
                code="invalid_query"
            ) from e
        except PipelineParseError:
            # Re-raise target noun validation errors
            raise
        except Exception as e:
            raise PipelineParseError(
                f"Unexpected error while compiling natural query: {str(e)}",
                code="unexpected_query_error"
            ) from e
