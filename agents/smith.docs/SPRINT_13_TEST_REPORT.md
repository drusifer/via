# Sprint 13 User Test Report

_Author: Smith | Date: 2026-03-24_

## Feature Tests: PASS

| Command | Result |
|---------|--------|
| `via -mg "*" -tc --via inherits-from -mg "*" -tc` | ✅ Returns subclasses |
| `via -mg "DatabaseStore" -tc --via inherits-from -mg "*" -tc` | ✅ Empty (no subclasses) |
| `via -mg "*" -tc --sans inherits-from -mg "*" -tc` | ✅ Returns root classes |
| `via -mg "*" -tf --sans calls -mg "*" -tf` | ✅ Returns uncalled functions |
| `via --not -mg "_*" -tm` | ✅ Returns non-underscore methods |
| `via -mg "*" -tc -V inherits-from -mg "*" -tc` | ✅ Short form works |
| `via -mg "*" -tc -V foobar -mg "*"` | ✅ Error: "Unknown relationship type 'foobar'. Valid: calls, declares, imports, inherits-from, references" |
| `via -Vinh "BaseHandler" -mg "*"` | ✅ Error: old flag rejected |

## Bug: Stale Agent SKILL.md Files (HIGH PRIORITY)

**Affected files:**
- `agents/neo.docs/SKILL.md` — uses `-Vca`, `-iv`, `-Vimp`, `-Vinh`
- `agents/trin.docs/SKILL.md` — uses `-Vca`, `-iv`, `-Vinh`, `-Vr`
- `agents/morpheus.docs/SKILL.md` — uses `-Vinh`, `-iv`, `-Vimp`, `-Vr`, `-Vca`
- `agents/oracle.docs/SKILL.md` — uses `-Vr`, `-iv`, `-Vimp`, `-Vinh`
- `agents/smith.docs/USE_CASES_20_QUESTIONS.md` — uses `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`, `--invert`

**Impact**: Every agent that consults its SKILL.md for via query examples will generate broken commands that return "Error: Invalid match stage arguments". This silently breaks codebase navigation for all agents.

**Fix needed**: Update all via-query example tables in affected SKILL.md files to use new flags:
- `-Vinh` → `--via inherits-from`
- `-Vca` → `--via calls`
- `-Vimp` → `--via imports`
- `-Vr` → `--via references`
- `-Vhas` → `--via has`
- `--invert` / `-iv` → restructure query (no direct replacement)

**Routing**: @Bob *prompt — this is a SKILL.md reprompt task.
