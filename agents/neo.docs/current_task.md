# Neo Current Task

**Task**: UX fixes UX-WEB-001 through 005
**Status**: COMPLETE
**Updated**: 2026-03-23

## Done
- UX-WEB-001: Pluralised result count (`result`/`results`) in `app.js`
- UX-WEB-002: Fixed misleading placeholders `1h`/`2d` → `e.g. 1h`/`e.g. 2d` in `template.py`
- UX-WEB-003: Made `.actions` sticky (bottom:0) in `template.py` CSS
- UX-WEB-004: Added `relPath()` helper in `app.js`; strips `lastStatus.directory` from paths in list + table renderers
- UX-WEB-005: Added `#initial-state` div ("Enter a pattern and click Run Query to search.") in `template.py`; `showLoading()` hides it
- Fixed `showLoading` test + DOM fixture in `dom.test.js` to include `#initial-state`
- All tests pass: 1121 Python, 74 JS

## Next
- Trin: update E2E tests to cover Smith's 5 findings (per user request)
