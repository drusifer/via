# Neo Next Steps

## Resume Point: Sprint 25 Cycle 2 implementation complete

### On Resume
1. Read the bottom 20-40 lines of `agents/CHAT.md`.
2. Wait for Trin QA on Sprint 25 Cycle 2.
3. If QA fails, fix only the failing relationship, docs/schema, or mixed-language regression issue.
4. If Smith rejects wording, update docs/MCP examples only.
5. If Morpheus review fails, address only the Cycle 2 architecture finding.

### Current Known Status
- `tree-sitter-language-pack>=1.6.2` is in `pyproject.toml`.
- `via/parsers/dart_parser.py` provides Dart parser foundation plus simple body call extraction.
- `tests/unit/test_sprint25_c2.py` covers Flutter fixture relationships, docs/MCP examples, and parser syntax-error behavior.
- README, user guide, and MCP schema now document Dart/Flutter examples and structural-only boundaries.
- Latest targeted result: `make test FILE=tests/unit/test_sprint25_c2.py` — 3 passed.
