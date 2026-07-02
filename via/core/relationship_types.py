"""
Reference type definitions for VIA symbol relationships.

TLDR:
    Class-based relationship type hierarchy. Leaf classes (Calls, CalledBy,
    Imports, ...) each carry the concrete `value` stored in the database and
    an `inverted` flag. Category classes (Any, UpstreamRef, DownstreamRef)
    have no `value` of their own — resolving one expands, via real
    `issubclass`/`__subclasses__` polymorphism, to every concrete leaf class
    beneath it in the hierarchy. This is what lets a single user-facing name
    like `upstream-ref` compile to a query spanning multiple concrete
    relationship types (e.g. blast-radius queries), without the query engine
    hardcoding that expansion as a flat lookup table.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from enum import Enum
from typing import Dict, List, Tuple, Type


class ReferenceType(Enum):
    """Types of references between symbols.

    Each enum value corresponds to a reference_type stored in the database.
    This is the single source of truth for reference type mappings.
    """
    INHERITS_FROM = 'inherits-from'
    CALLS = 'calls'
    IMPORTS = 'imports'
    REFERENCES = 'references'
    DECLARES = 'declares'        # structural containment (file/class/function declares member)
    COVERED_BY = 'covered-by'
    HTTP_CALLS = 'http-calls'

    @classmethod
    def from_value(cls, value: str) -> 'ReferenceType':
        """Get ReferenceType from its string value (e.g., 'inherits-from')."""
        for rt in cls:
            if rt.value == value:
                return rt
        raise ValueError(f"Unknown reference type: {value}")

    @classmethod
    def get_value_map(cls) -> dict:
        """Get mapping from string values to ReferenceType."""
        return {rt.value: rt for rt in cls}


class Relation:
    """Base of the relationship type hierarchy.

    Leaf subclasses set `reference_type` (a ReferenceType) and `inverted`
    (whether this name reads the 'to' side of the underlying reference_type
    rather than the 'from' side). Category subclasses set neither and exist
    purely to be resolved via `is_category()`/`leaves()` — genuine
    polymorphic dispatch (`issubclass`/`__subclasses__`), not a flat dict.

    Every leaf also gets a `value` class attribute (the raw DB string),
    auto-derived from `reference_type` in `__init_subclass__`, so a leaf
    class is a drop-in stand-in anywhere code does `rel.relationship_type.value`
    against the pre-existing `ReferenceType` enum (e.g. `via/pipeline/executor.py`).
    """
    reference_type: 'ReferenceType | None' = None
    inverted: bool = False
    value: 'str | None' = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.value = cls.reference_type.value if cls.reference_type is not None else None

    @classmethod
    def is_category(cls) -> bool:
        """True if this is a category (abstract) node rather than a concrete leaf."""
        return cls.reference_type is None

    @classmethod
    def leaves(cls) -> List[Type['Relation']]:
        """Return every concrete leaf class at or beneath this node in the hierarchy.

        A leaf resolves to itself. A category recursively walks its
        `__subclasses__()` — real polymorphic resolution, so adding a new
        leaf class anywhere under a category automatically makes it part of
        that category's expansion with no lookup table to update.
        """
        if not cls.is_category():
            return [cls]
        result: List[Type['Relation']] = []
        for sub in cls.__subclasses__():
            result.extend(sub.leaves())
        return result

    @classmethod
    def leaf_pairs(cls) -> List[Tuple['ReferenceType', bool]]:
        """Return (reference_type, inverted) for every leaf at or beneath this node."""
        return [(leaf.reference_type, leaf.inverted) for leaf in cls.leaves()]

    @classmethod
    def execute(cls, run_leaf):
        """Run *run_leaf(leaf_class)* for every concrete leaf beneath this node.

        Callers use one uniform interface — `rel.relationship_type.execute(fn)`
        — regardless of whether they hold a leaf or a category; there is no
        `is_category()` branch at the call site. A leaf's `leaves()` is just
        `[cls]`, so it runs `fn` once and returns those results unchanged. A
        category runs `fn` once per leaf and merges (dedupe by identity, sort
        by file/line) before returning — this is the only place that merge
        logic lives, and it's driven by real polymorphism (`leaves()`), not a
        lookup table.
        """
        all_records = [record for leaf in cls.leaves() for record in run_leaf(leaf)]
        if not cls.is_category():
            return all_records
        deduped = {
            (r.file_path, r.line_number, r.symbol_name, r.symbol_type): r
            for r in all_records
        }.values()
        return sorted(deduped, key=lambda r: (r.file_path, r.line_number))


class Any(Relation):
    """Category matching every relationship type, in both directions."""


class UpstreamRef(Any):
    """Category: incoming edges — symbols that depend on the target (callers, importers, subclasses, ...).

    For an anchor T queried with `--via <name> -mg T` (anchor as filter),
    the *forward* (non-inverted) verb query empirically returns symbols that
    point AT T — e.g. `--via calls -mg T` returns T's callers. That's the
    upstream/dependents direction, confirmed by real queries during Cycle 4
    review — not just asserted from the design doc's diagram, which had
    this backwards relative to its own prose definition of "upstream".
    """


class DownstreamRef(Any):
    """Category: outgoing edges — symbols the target depends on (callees, imports, parent classes, ...).

    The *inverted* ("X-by") verb query empirically returns what T points AT
    — e.g. `--via called-by -mg T` returns what T calls. Downstream/dependencies.
    """


# ── Upstream leaves (forward verb: anchor-as-filter finds T's dependents) ───

class Calls(UpstreamRef):
    reference_type = ReferenceType.CALLS
    inverted = False


class References(UpstreamRef):
    reference_type = ReferenceType.REFERENCES
    inverted = False


class Imports(UpstreamRef):
    reference_type = ReferenceType.IMPORTS
    inverted = False


class InheritsFrom(UpstreamRef):
    reference_type = ReferenceType.INHERITS_FROM
    inverted = False


class HttpCalls(UpstreamRef):
    reference_type = ReferenceType.HTTP_CALLS
    inverted = False


# ── Downstream leaves (inverted "X-by" verb: anchor-as-filter finds T's dependencies) ─

class CalledBy(DownstreamRef):
    reference_type = ReferenceType.CALLS
    inverted = True


class ReferencedBy(DownstreamRef):
    reference_type = ReferenceType.REFERENCES
    inverted = True


class ImportedBy(DownstreamRef):
    reference_type = ReferenceType.IMPORTS
    inverted = True


class InheritedBy(DownstreamRef):
    reference_type = ReferenceType.INHERITS_FROM
    inverted = True


class HttpCalledBy(DownstreamRef):
    reference_type = ReferenceType.HTTP_CALLS
    inverted = True


# ── Declares/declared-in are structural containment (which file/class a
# symbol lives in), not call-graph dependency. The design doc's own "Actual
# Requirements" prose never mentions containers/members as part of blast
# radius — only its diagram did. Kept as plain Relation leaves (no category
# parent) per Smith's usability finding: still fully usable standalone via
# --via declares / --via declared-in, just not swept into
# any-ref/upstream-ref/downstream-ref/blast, where they were pure noise.

class Declares(Relation):
    # In the DB, 'declares' is stored member(from) -> container(to); the
    # user-facing 'declares' name (container declares member) targets the
    # 'to' side, hence inverted=True despite being the "forward" name.
    reference_type = ReferenceType.DECLARES
    inverted = True


class DeclaredIn(Relation):
    reference_type = ReferenceType.DECLARES
    inverted = False


# ── covered-by/covers: not in the design doc's diagram at all (test
# coverage, not code dependency) — applying the same verified convention as
# calls/references/etc. for consistency: forward verb = upstream.

class CoveredBy(UpstreamRef):
    reference_type = ReferenceType.COVERED_BY
    inverted = False


class Covers(DownstreamRef):
    reference_type = ReferenceType.COVERED_BY
    inverted = True


# ── Name resolution ──────────────────────────────────────────────────────────

_NAME_MAP: Dict[str, Type[Relation]] = {
    # Leaves — forward
    'calls': Calls,
    'references': References,
    'imports': Imports,
    'inherits-from': InheritsFrom,
    'declares': Declares,
    'http-calls': HttpCalls,
    'covered-by': CoveredBy,
    # Leaves — inverse
    'called-by': CalledBy,
    'referenced-by': ReferencedBy,
    'imported-by': ImportedBy,
    'inherited-by': InheritedBy,
    'declared-in': DeclaredIn,
    'http-called-by': HttpCalledBy,
    'covers': Covers,
    # Categories
    'any-ref': Any,
    'upstream-ref': UpstreamRef,
    'downstream-ref': DownstreamRef,
}


def resolve_relation(name: str) -> Type[Relation]:
    """Resolve a user-facing relationship name to its class in the hierarchy.

    Raises:
        KeyError: If *name* is not a known relationship or category name.
    """
    return _NAME_MAP[name]


def is_category(relationship_type) -> bool:
    """True if *relationship_type* is a category (e.g. UpstreamRef) rather than
    a concrete leaf or the older plain `ReferenceType` enum.

    For guard checks (e.g. rejecting categories with --sans or in a chained
    multi-relationship query) where there's no query to run yet, so
    `execute_relation` doesn't apply.
    """
    return hasattr(relationship_type, 'is_category') and relationship_type.is_category()


def execute_relation(relationship_type, run_leaf):
    """Run *run_leaf* for *relationship_type*, one uniform entry point.

    `relationship_type` may be a `Relation` subclass (leaf or category, from
    the CLI parser) or a plain `ReferenceType` enum member (from the web API
    / `ViaQueryBuilder`, which never produce categories). Callers — e.g.
    `via/pipeline/executor.py` — never branch on which one they have or
    whether it's a category; that's entirely this hierarchy's job.
    """
    if hasattr(relationship_type, 'execute'):
        return relationship_type.execute(run_leaf)
    return list(run_leaf(relationship_type))


def get_relation_names() -> List[str]:
    """Return all valid user-facing relationship/category names, sorted."""
    return sorted(_NAME_MAP.keys())


# Backward-compatibility alias
RelationshipType = ReferenceType
