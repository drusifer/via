"""
User-facing pipeline error types.

TLDR: Defines a structured query error contract shared by CLI, MCP, and
programmatic query paths.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryError:
    """Structured user-facing query error."""

    code: str
    message: str
    hint: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Return JSON-serializable error fields."""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.hint:
            result["hint"] = self.hint
        return result


class PipelineParseError(Exception):
    """Raised when pipeline parsing fails with a user-facing query error."""

    def __init__(
        self,
        message: str,
        code: str = "invalid_query",
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error = QueryError(code=code, message=message, hint=hint)

    @property
    def code(self) -> str:
        """Stable machine-readable error code."""
        return self.error.code

    @property
    def hint(self) -> str | None:
        """Optional user recovery hint."""
        return self.error.hint

    def to_query_error(self) -> QueryError:
        """Return the structured query error."""
        return self.error
