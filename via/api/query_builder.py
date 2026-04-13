"""Fluent query builder for programmatic VIA queries."""

from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass, field
from typing import Iterator, Optional

from via.core.match_record import MatchRecord, RenderType
from via.core.relationship_types import ReferenceType
from via.core.types import SymbolType
from via.pipeline.executor import PipelineExecutor
from via.pipeline.parser import PipelineParser
from via.pipeline.stage_builder import build_match_stage, build_relationship_filter
from via.pipeline.types import PipelineStage


@dataclass
class _MatchSpec:
    pattern: str = "*"
    match_syntax: str = "g"
    symbol_types: list[str] = field(default_factory=list)
    case_insensitive: bool = False
    match_qualified: bool = False
    negate_pattern: bool = False
    language_filter: Optional[str] = None
    symbol_subtype_filter: Optional[str] = None
    contains_pattern: Optional[str] = None
    limit: Optional[int] = None
    result_slice: Optional[str] = None
    render_type: Optional[str] = None
    newerthan: Optional[str] = None
    olderthan: Optional[str] = None
    stale: bool = False


@dataclass
class _RelationshipSpec:
    relationship_type: ReferenceType
    is_negative: bool
    object_query: _MatchSpec = field(default_factory=_MatchSpec)


def _normalize_symbol_type(symbol_type: str | SymbolType) -> str:
    """Return the canonical symbol type string."""
    if isinstance(symbol_type, SymbolType):
        return symbol_type.value
    return str(symbol_type)


def _normalize_render_type(render_type: str | RenderType) -> str:
    """Return the canonical render type string."""
    if isinstance(render_type, RenderType):
        return render_type.value
    return str(render_type)


def _normalize_relationship(relationship_type: str | ReferenceType) -> ReferenceType:
    """Return the canonical relationship enum."""
    if isinstance(relationship_type, ReferenceType):
        return relationship_type
    return ReferenceType.from_value(str(relationship_type))


def _emit_optional_cli_flags(args, out: list) -> None:
    """Append optional match flags to *out* based on *args* attributes."""
    if getattr(args, "case_insensitive", False):
        out.append("-I")
    if getattr(args, "match_qualified", False):
        out.append("-Q")
    if getattr(args, "contains_pattern", None):
        out.extend(["--contains", args.contains_pattern])
    if getattr(args, "language_filter", None):
        out.extend(["--lang", args.language_filter])
    if getattr(args, "symbol_subtype_filter", None):
        out.extend(["--subtype", args.symbol_subtype_filter])
    if getattr(args, "result_slice", None):
        out.extend(["--slice", args.result_slice])
    elif getattr(args, "limit", None) is not None:
        out.extend(["-n", str(args.limit)])


class _QueryBuilderBase:
    """Shared fluent methods for subject and relationship-side query specs."""

    def __init__(self, spec: _MatchSpec):
        self._spec = spec

    def glob(self, pattern: str):
        self._spec.pattern = pattern
        self._spec.match_syntax = "g"
        return self

    def regex(self, pattern: str):
        self._spec.pattern = pattern
        self._spec.match_syntax = "r"
        return self

    def sql(self, pattern: str):
        self._spec.pattern = pattern
        self._spec.match_syntax = "s"
        return self

    def types(self, *symbol_types: str | SymbolType):
        self._spec.symbol_types = [_normalize_symbol_type(t) for t in symbol_types]
        return self

    def classes(self):
        return self.types(SymbolType.CLASS)

    def functions(self):
        return self.types(SymbolType.FUNCTION)

    def methods(self):
        return self.types(SymbolType.METHOD)

    def files(self):
        return self.types(SymbolType.FILEPATH)

    def filenames(self):
        return self.types(SymbolType.FILENAME)

    def imports(self):
        return self.types(SymbolType.IMPORT)

    def globals(self):
        return self.types(SymbolType.GLOBAL)

    def headers(self):
        return self.types(SymbolType.HEADER)

    def strings(self):
        return self.types(SymbolType.STRING_CONSTANT)

    def links(self):
        return self.types(SymbolType.LINK)

    def case_insensitive(self, enabled: bool = True):
        self._spec.case_insensitive = enabled
        return self

    def qualified(self, enabled: bool = True):
        self._spec.match_qualified = enabled
        return self

    def negate(self, enabled: bool = True):
        self._spec.negate_pattern = enabled
        return self

    def language(self, name: str):
        self._spec.language_filter = name
        return self

    def subtype(self, name: str):
        self._spec.symbol_subtype_filter = name
        return self

    def contains(self, pattern: str):
        self._spec.contains_pattern = pattern
        return self

    def limit(self, n: int):
        self._spec.limit = n
        return self

    def slice(self, start: Optional[int], end: Optional[int] = None):
        if start is None and end is None:
            self._spec.result_slice = None
        elif end is None:
            self._spec.result_slice = f"{start}:"
        else:
            prefix = "" if start is None else str(start)
            self._spec.result_slice = f"{prefix}:{end}"
        return self

    def render(self, render_type: str | RenderType):
        self._spec.render_type = _normalize_render_type(render_type)
        return self

    def newerthan(self, duration: str):
        self._spec.newerthan = duration
        return self

    def olderthan(self, duration: str):
        self._spec.olderthan = duration
        return self

    def stale(self, enabled: bool = True):
        self._spec.stale = enabled
        return self


@dataclass(frozen=True)
class ViaQuery:
    """Immutable compiled VIA query."""

    stages: tuple[PipelineStage, ...]

    def to_stages(self) -> list[PipelineStage]:
        """Return a mutable list of pipeline stages."""
        return list(self.stages)

    def to_cli_args(self) -> list[str]:
        """Best-effort CLI-style representation for debugging."""
        if not self.stages:
            return []

        args = self.stages[0].args
        out: list[str] = []
        match_flag = {"g": "-mg", "r": "-mr", "s": "-ms"}.get(getattr(args, "match_syntax", "g"), "-mg")
        out.extend([match_flag, args.pattern])

        _TYPE_FLAGS = {
            "class": "-tc", "function": "-tf", "method": "-tm", "import": "-ti",
            "global": "-tg", "string_constant": "-ts", "link": "-tl",
            "filepath": "-tF", "filename": "-tN", "header": "-tH",
        }
        for symbol_type in getattr(args, "symbol_types", []) or []:
            flag = _TYPE_FLAGS.get(symbol_type)
            if flag:
                out.append(flag)

        _emit_optional_cli_flags(args, out)

        rel = getattr(args, "relationship", None)
        if rel:
            out.extend(["--sans" if rel.is_negative else "--via", rel.relationship_type.value])
            object_flag = {"g": "-mg", "r": "-mr", "s": "-ms"}.get(rel.filter_match_syntax, "-mg")
            out.extend([object_flag, rel.filter_pattern])
        return out


class RelationshipQueryBuilder(_QueryBuilderBase):
    """Fluent builder for the right-hand side of a relationship query."""

    def __init__(self, parent: "ViaQueryBuilder", relationship: _RelationshipSpec):
        super().__init__(relationship.object_query)
        self._parent = parent
        self._relationship = relationship

    def done(self) -> "ViaQueryBuilder":
        """Return control to the parent builder."""
        return self._parent


class ViaQueryBuilder(_QueryBuilderBase):
    """Fluent builder for VIA match and relationship queries."""

    def __init__(self):
        self._subject = _MatchSpec()
        self._relationship: Optional[_RelationshipSpec] = None
        super().__init__(self._subject)

    def via(self, relationship_type: str | ReferenceType) -> RelationshipQueryBuilder:
        """Start a positive relationship query."""
        self._relationship = _RelationshipSpec(
            relationship_type=_normalize_relationship(relationship_type),
            is_negative=False,
        )
        return RelationshipQueryBuilder(self, self._relationship)

    def sans(self, relationship_type: str | ReferenceType) -> RelationshipQueryBuilder:
        """Start a negative relationship query."""
        self._relationship = _RelationshipSpec(
            relationship_type=_normalize_relationship(relationship_type),
            is_negative=True,
        )
        return RelationshipQueryBuilder(self, self._relationship)

    def build(self) -> ViaQuery:
        """Compile the fluent builder into an immutable query."""
        if self._subject.limit is not None and self._subject.result_slice is not None:
            raise ValueError("--limit and --slice are mutually exclusive")

        relationship_filter = None
        if self._relationship is not None:
            object_query = self._relationship.object_query
            object_args = Namespace(
                pattern=object_query.pattern,
                match_syntax=object_query.match_syntax,
                symbol_types=list(object_query.symbol_types),
                newerthan=object_query.newerthan,
                olderthan=object_query.olderthan,
                stale=object_query.stale,
            )
            relationship_filter = build_relationship_filter(
                self._relationship.relationship_type,
                object_args,
                self._relationship.is_negative,
            )

        args = Namespace(
            pattern=self._subject.pattern,
            match_syntax=self._subject.match_syntax,
            symbol_types=list(self._subject.symbol_types),
            case_insensitive=self._subject.case_insensitive,
            limit=self._subject.limit,
            result_slice=self._subject.result_slice,
            match_qualified=self._subject.match_qualified,
            newerthan=self._subject.newerthan,
            olderthan=self._subject.olderthan,
            render_type=self._subject.render_type,
            relationship=relationship_filter,
            line_slice=None,
            negate_pattern=self._subject.negate_pattern,
            language_filter=self._subject.language_filter,
            symbol_subtype_filter=self._subject.symbol_subtype_filter,
            contains_pattern=self._subject.contains_pattern,
            format=None,
            after_context=0,
            before_context=0,
            context=None,
            theme=None,
            nodelims=False,
            stale=self._subject.stale,
        )
        return ViaQuery((build_match_stage(args, relationship=relationship_filter, negate_pattern=self._subject.negate_pattern),))


class ViaRunner:
    """Thin execution adapter for compiled VIA queries."""

    def __init__(self, db_store):
        self._executor = PipelineExecutor(db_store)

    def run(self, query: ViaQuery) -> Optional[Iterator[MatchRecord]]:
        """Execute a compiled query through the existing pipeline executor."""
        return self._executor.execute(query.to_stages())

    def run_cli_args(self, args: list[str]) -> Optional[Iterator[MatchRecord]]:
        """Parse a CLI argument list and execute through the shared pipeline seam."""
        stages = PipelineParser().parse(args)
        return self._executor.execute(stages)
