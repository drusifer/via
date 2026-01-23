"""
Base parser interface for language parsers.

TLDR:
    Defines ParserABC abstract base class and entity dataclasses (ParseResult,
    FunctionEntity, ClassEntity, ImportEntity, etc.) for representing parsed
    code elements. All parsers must implement can_parse() and parse() methods.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from abc import ABC, abstractmethod
from ..core.interfaces import ArgumentProvider, HelpProvider
from dataclasses import dataclass, field
from typing import List, Optional, Set
@dataclass
class ParseResult:
    """Result of parsing a file."""

    file_path: str
    language: str
    functions: List["FunctionEntity"] = field(default_factory=list)
    classes: List["ClassEntity"] = field(default_factory=list)
    imports: List["ImportEntity"] = field(default_factory=list)
    globals: List["GlobalEntity"] = field(default_factory=list)
    log_statements: List["LogStatementEntity"] = field(default_factory=list)
    markdown_headings: List["MarkdownHeadingEntity"] = field(default_factory=list)
    parse_error: Optional[str] = None
@dataclass
class FunctionEntity:
    """Represents a function or method."""

    name: str
    line_start: int
    line_end: int
    byte_offset: int
    byte_length: int
    class_id: Optional[int] = None  # Set later when linking to class
    args: Optional[str] = None
    decorators: Optional[str] = None
    docstring: Optional[str] = None
@dataclass
class ClassEntity:
    """Represents a class definition."""

    name: str
    line_start: int
    line_end: int
    byte_offset: int
    byte_length: int
    bases: Optional[str] = None
    decorators: Optional[str] = None
    docstring: Optional[str] = None
    methods: List[FunctionEntity] = field(default_factory=list)  # Methods defined in this class
@dataclass
class ImportEntity:
    """Represents an import statement."""

    module: str
    line_number: int
    byte_offset: int
    byte_length: int
    name: Optional[str] = None  # For 'from X import Y'
    alias: Optional[str] = None  # For 'import X as Y'
@dataclass
class GlobalEntity:
    """Represents a global variable."""

    name: str
    line_number: int
    byte_offset: int
    byte_length: int
    value: Optional[str] = None
    type_hint: Optional[str] = None
@dataclass
class LogStatementEntity:
    """Represents a logging or print statement."""

    call_name: str  # e.g., 'print', 'logger.info', 'log.debug'
    line_number: int
    byte_offset: int
    byte_length: int
    message: Optional[str] = None
@dataclass
class MarkdownHeadingEntity:
    """Represents a markdown heading."""

    level: int  # 1-6 for h1-h6
    text: str
    line_number: int
    byte_offset: int
    byte_length: int

class ParserABC(ABC, ArgumentProvider, HelpProvider):
    """Abstract base class for language parsers."""

    @classmethod
    def add_arguments(cls, parser):
        # Placeholder: to be implemented per parser
        pass

    @classmethod
    def get_help(cls) -> str:
        return getattr(cls, "HELP", f"{cls.__name__}: parser.")

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can parse the given file.

        Args:
            file_path: Path to the file

        Returns:
            True if parser supports this file type
        """
        pass

    @abstractmethod
    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """
        Parse a file and extract code entities.

        Args:
            file_path: Path to the file being parsed
            content: File content as bytes

        Returns:
            ParseResult containing extracted entities
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> Set[str]:
        """
        Get file extensions supported by this parser.

        Returns:
            Set of file extensions (e.g., {'.py', '.pyx', '.pyi'})
        """
        pass

    @property
    @abstractmethod
    def language_name(self) -> str:
        """
        Get the name of the language this parser handles.

        Returns:
            Language name (e.g., 'python', 'javascript')
        """
        pass
