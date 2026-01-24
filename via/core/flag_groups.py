"""Flag group definitions for CLI.

Defines consistent prefix-based flag groups:
- Match: -mg (glob), -mr (regex), -ms (sql)
- Type: -tc (class), -tf (function), -tm (method), etc.
- Output: -oL (list), -oT (table), -oD (diagram), etc.
- Format: -fa (ascii), -fm (markdown), -fh (html), -fp (png)
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
    Flag(FlagGroup.MATCH, 'g', 'match-glob', 'pattern', None, 'Glob pattern (*, ?)'),
    Flag(FlagGroup.MATCH, 'r', 'match-regex', 'pattern', None, 'Regex pattern'),
    Flag(FlagGroup.MATCH, 's', 'match-sql', 'pattern', None, 'SQL LIKE pattern (%, _)'),
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
