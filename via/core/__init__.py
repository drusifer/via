"""
Core utilities and shared components for the VIA system.

TLDR:
    Package namespace for via/core. Exposes constants, discovery, flag_groups,
    gitignore, interfaces, logging, match_record, relationship_types, types, and
    utils as sibling modules. No symbols are re-exported here; consumers import
    directly from the submodules (e.g., from via.core.match_record import
    MatchRecord). Role: foundational layer consumed by parsers, pipeline, db,
    renderers, services, and commands.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
