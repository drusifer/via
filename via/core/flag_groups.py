"""
Flag group definitions for the VIA CLI.

TLDR:
    Defines the canonical set of prefix-based CLI flags used throughout VIA.
    Flag, FlagGroup, and four flag lists (MATCH_FLAGS, TYPE_FLAGS, OUTPUT_FLAGS,
    FORMAT_FLAGS) encode short/long names, dest attributes, and help text.
    Helper functions (get_match_short_flags, get_type_short_flags, etc.) return
    sets used by the pipeline parser for stage detection. Relationship flags
    (--via/--sans/--not) are handled directly in the parser, not as Flag objects.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class FlagGroup(Enum):
    """Flag group categories."""
    MATCH = 'm'
    TYPE = 't'
    OUTPUT = 'o'
    FORMAT = 'f'


@dataclass
class Flag:
    """Definition for a single CLI flag."""
    group: FlagGroup
    suffix: str
    long_name: str
    dest: str
    const: Optional[str]
    help: str

    @property
    def short(self) -> str:
        """Return short flag like -mg."""
        return f"-{self.group.value}{self.suffix}"

    @property
    def long(self) -> str:
        """Return long flag like --match-glob."""
        return f"--{self.long_name}"


# Match syntax flags
MATCH_FLAGS: List[Flag] = [
    Flag(FlagGroup.MATCH, 'g', 'match-glob', 'pattern', None, 'Glob pattern (*, ?) — case-sensitive; use -I to ignore case'),
    Flag(FlagGroup.MATCH, 'r', 'match-regex', 'pattern', None, 'Regex pattern — case-sensitive; use -I to ignore case'),
    Flag(FlagGroup.MATCH, 's', 'match-sql', 'pattern', None, 'SQL LIKE pattern (%%, _) — case-sensitive; use -I to ignore case'),
]

# Symbol type flags
TYPE_FLAGS: List[Flag] = [
    Flag(FlagGroup.TYPE, 'c', 'type-class', 'symbol_type', 'class', 'Classes'),
    Flag(FlagGroup.TYPE, 'f', 'type-function', 'symbol_type', 'function', 'Functions'),
    Flag(FlagGroup.TYPE, 'm', 'type-method', 'symbol_type', 'method', 'Methods'),
    Flag(FlagGroup.TYPE, 'i', 'type-import', 'symbol_type', 'import', 'Imports'),
    Flag(FlagGroup.TYPE, 'g', 'type-global', 'symbol_type', 'global', 'Globals'),
    Flag(FlagGroup.TYPE, 'F', 'type-filepath', 'symbol_type', 'filepath', 'File paths'),
    Flag(FlagGroup.TYPE, 'N', 'type-filename', 'symbol_type', 'filename', 'File names'),
    Flag(FlagGroup.TYPE, 'H', 'type-header', 'symbol_type', 'header', 'Markdown headers'),
]

# Output type flags (already exist as -oX)
OUTPUT_FLAGS: List[Flag] = [
    Flag(FlagGroup.OUTPUT, 'L', 'output-list', 'render_type', 'list', 'List format'),
    Flag(FlagGroup.OUTPUT, 'T', 'output-table', 'render_type', 'table', 'Table format'),
    Flag(FlagGroup.OUTPUT, 'D', 'output-diagram', 'render_type', 'diagram', 'Mermaid diagram'),
    Flag(FlagGroup.OUTPUT, 'U', 'output-usage', 'render_type', 'usage', 'Usage references'),
    Flag(FlagGroup.OUTPUT, 'R', 'output-raw', 'render_type', 'raw', 'Raw source code'),
    Flag(FlagGroup.OUTPUT, 'F', 'output-formatted', 'render_type', 'formatted', 'Syntax highlighted'),
    Flag(FlagGroup.OUTPUT, 'J', 'output-json', 'render_type', 'json', 'JSON array of symbol objects'),
]

# Format flags
FORMAT_FLAGS: List[Flag] = [
    Flag(FlagGroup.FORMAT, 'a', 'format-ascii', 'format', 'ascii', 'Terminal colors'),
    Flag(FlagGroup.FORMAT, 'm', 'format-markdown', 'format', 'md', 'Markdown'),
    Flag(FlagGroup.FORMAT, 'h', 'format-html', 'format', 'html', 'HTML'),
    Flag(FlagGroup.FORMAT, 'p', 'format-png', 'format', 'png', 'PNG image'),
]

def get_all_flags() -> List[Flag]:
    """Return all flag definitions."""
    return MATCH_FLAGS + TYPE_FLAGS + OUTPUT_FLAGS + FORMAT_FLAGS


def get_match_short_flags() -> set:
    """Return set of short match flags for stage detection."""
    return {f.short for f in MATCH_FLAGS}


def get_type_short_flags() -> set:
    """Return set of short type flags for stage detection."""
    return {f.short for f in TYPE_FLAGS}


def get_output_short_flags() -> set:
    """Return set of short output flags for stage detection."""
    return {f.short for f in OUTPUT_FLAGS}


def get_format_short_flags() -> set:
    """Return set of short format flags for stage detection."""
    return {f.short for f in FORMAT_FLAGS}
