# Oracle Current Task

**Task**: *ora groom docs
**Status**: COMPLETE (100%)
**Updated**: 2026-07-02

## Completed
- [x] Fixed a real, long-flagged documentation gap: Sprint 26 Cycle 4's
      relationship categories (`any-ref`/`upstream-ref`/`downstream-ref`,
      colloquially "blast radius" queries) and all inverse leaf
      relationships (`called-by`, `referenced-by`, `imported-by`,
      `inherited-by`, `declared-in`, `http-calls`, `http-called-by`,
      `covers`) were completely undocumented — only the 5 forward leaves
      existed in the spec. Extended
      `docs/specs/relationships_and_filters.md` with both tables plus a
      new "Multi-Relationship Categories: Blast-Radius Queries" section
      with real examples and the `declares`/`declared-in`-exclusion note.
- [x] Fixed the other long-flagged gap: the entire `via coverage` /
      Sprint 27 subsystem (capture, querying, and the new Phase 2 web
      Coverage view) had **zero** documentation anywhere in `docs/specs/` —
      old sprint docs still only described the retired
      `import <coverage.xml>` command. Wrote a new
      `docs/specs/test_coverage.md` and linked it from
      `docs/USER_GUIDE.md`'s index (item 8).
- [x] Fixed a broken link in `README.md` (`agents/morpheus/morpheus.docs/...`
      — an extra `morpheus/` path segment — corrected to
      `agents/morpheus.docs/VIA_ARCHITECTURE.md`).
- [x] Relocated 2 stale/misleading root-level orphan files:
      - `ARCH.md` (a one-off Jan 2026 design proposal, not a living
        architecture doc — the real one is
        `agents/morpheus.docs/VIA_ARCHITECTURE.md`) → renamed to
        `docs/DESIGN_POLYMORPHIC_PARAMETER_PARSING.md`, matching the
        existing `docs/DESIGN_*.md` sibling convention.
      - `TEST_STATUS.md` (claimed to be "current" status but frozen at
        Sprint 7 / 794 tests, from 2026-03-20 — actively misleading at
        the project root) → moved to `docs/sprints/sprint_7_test_status.md`
        and linked from `docs/sprints/sprint_7.md`.
      - Verified no code/config (`.py`/Makefile/`.json`/`.yaml`/`.toml`)
        actually loads either file by path before moving (only one test's
        docstring *mentions* "ARCH.md" as a design-comment reference, not
        a functional dependency — left as-is, low priority).
- [x] Confirmed the remaining root markdown files (`AGENTS.md`, `GEMINI.md`,
      `CHATGPT.md`, `.agent.md`, `README.md`, `CHANGELOG.md`, `task.md`,
      `START_HERE.md`) are legitimately root-required (AI tool discovery
      conventions or standard project files) — not orphans, left in place.

## Next
- Noted but did NOT fix (out of scope for a docs-grooming pass): `tldr` has
  no public `make` stub either (same gap class Neo fixed for
  `test-coverage`/`test-js`/`lint` this session) — `make tldr` currently
  does nothing when run outside `MKF_ACTIVE`. Flagging for whoever next
  touches the Makefile.
- No other queued documentation work.
