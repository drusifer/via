# Sprint 22 Final HCI Review

**Persona**: Smith  
**Date**: 2026-04-12  
**Scope**: Final HCI wording review for docs/schema/help and query recovery  
**Verdict**: APPROVED

## HCI Criteria

- **#2 Match Between System and Real World**: Query docs must match the user's mental model.
- **#4 Consistency and Standards**: CLI help, MCP schema, and user guide must use the same vocabulary.
- **#5 Error Prevention**: One-matcher-per-stage rule must be visible.
- **#9 Help Users Recover from Errors**: Invalid regex and repeated matcher failures must include hints.
- **#10 Help and Documentation**: Docs must not imply inverse `declares` behavior.

## Live Checks

```bash
.venv/bin/python -m via --help
.venv/bin/python -m via mcp schema
.venv/bin/python -m via -mr '[' -tf
.venv/bin/python -m via -mg '*' -tf -mg 'parse'
.venv/bin/python -m via -mg '*Parser*' -tc -tf -tm -n 1
```

## Findings

- CLI help clearly states: `via <result stage> [--via|--sans REL <filter stage>]`.
- CLI help states that the first stage determines returned records and relationship stages filter them.
- MCP schema uses the same result-stage/filter-stage vocabulary.
- MCP schema includes the one-matcher-per-stage rule and a regex example.
- Invalid regex produces a concise error and recovery hint.
- Repeated match flags produce a concise error and recovery hint.
- Multi-type query remains valid and returns results.
- The misleading `declares` quick reference was removed from project quick reference and user-facing docs.

## Notes

Plain system `python` in this shell lacks project dependencies (`pathspec`), so live checks were run through `.venv/bin/python`, matching the project test environment.

## Decision

Sprint 22 final HCI wording gate is approved.
