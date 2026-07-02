# Mouse Next Steps

## Resume Point: Sprint 26 closed, Sprint 27 unblocked but not started

## On Resume
1. Check CHAT.md for the user's decision on what starts next: Sprint 27
   Cycle 1, or resolving Neo's stalled Cycle 4 design review first.
2. If Sprint 27: hand Cycle 1 to Neo (`@Neo *swe impl cycle-1`, Sprint 27 —
   see `agents/mouse.docs/SPRINT_27_TASKS.md`).
3. If Cycle 4: wait for Morpheus/Smith's review of
   `docs/DESIGN_RELATIONSHIP_HIERARCHY.md`, then resume Neo on implementing
   the class hierarchy in `via/core/relationship_types.py`.

## Remember
`make test` is fixed — the Makefile include-order bug that silently shadowed
the real pytest recipe with `unittest discover` is resolved. No need to
re-diagnose if `make test` behaves oddly again; check the include order first.
