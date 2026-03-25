**Task**: Web UI + 20 Questions addition to USER_GUIDE
**Status**: COMPLETE (100%)
**Completed**: 2026-03-24

## Changes Made

### README.md
- TLDR: replaced `-Vhas`/`--ref-type`/`--invert` with `--via <rel>`/`--sans <rel>`/`--not`
- Features → Relationship Queries: updated to new flag syntax
- Relationship Queries table: replaced old flags with `--via`/`--sans`/`--not`/`--stale`
- Sprint History: added Sprint 11-12 (Web UI) and Sprint 13 (CLI redesign, 1121 tests)

### docs/USER_GUIDE.md
- TLDR: updated to reflect new relationship flag syntax
- Table of Contents: "Container Queries (-Vhas)" → "Container Queries (--via declares)"
- Relationship Queries section: complete rewrite — new syntax, `--sans`, `--not` explained
- `--ref-type` section: removed (flag no longer exists)
- `--invert`/`-iv`: removed throughout
- All examples: updated from `-Vinh`/`-Vca`/`-Vimp`/`-Vr`/`-Vhas` to `--via <rel>`
- Container Queries section: `-Vhas` → `--via declares`
- Quick Reference: updated relationship commands block

### File Organization
- `DESIGN_RENDER_PIPELINE.md` → moved to `docs/`
- `DESIGN_SPRINT3_INTERNAL_PIPELINE.md` → moved to `docs/`
