# Sprint 23 Cycle 2 HCI Review — Help And Schema Wording

**Persona**: Smith  
**Date**: 2026-04-12  
**Verdict**: APPROVED WITH NOTES

## Surfaces Tested

- `.venv/bin/python -m via --help`
- `.venv/bin/python -m via mcp schema`
- `via/mcp/schema.py`

## HCI Findings

### Approved: Recognition Over Recall

The new `Common Tasks` section gives users task-language commands before exposing low-level relationship syntax. This directly supports Nielsen #6, recognition rather than recall.

### Approved: Error Prevention

The schema explicitly calls out uppercase `-tH` and invalid lowercase `-th`. This prevents a known command-entry mistake before the user makes it.

### Approved: Progressive Disclosure

The help now separates common tasks from `Advanced Relationship Queries`. This is the right HCI shape: novice users can copy common tasks, while expert users still have access to raw relationship primitives.

### Approved: Minimalism

The help remains compact at 121 lines, within the 137-line budget. The new content adds high-value examples without turning `--help` into a manual.

## Note For Future Work

The phrase "Current runtime positive relationship lookups" is technically accurate but still somewhat implementation-facing. It is acceptable in the advanced section for this sprint because it prevents misleading users. A later relationship-orientation reconciliation should replace this with a simpler stable command model.

## Decision

Cycle 2 passes the HCI gate. Proceed to Cycle 3.
