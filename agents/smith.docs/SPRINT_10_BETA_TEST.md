# VIA Full Beta Test Report — All PRD User Stories
**Tester**: Smith (Expert User)
**Date**: 2026-03-22
**VIA version**: Sprint 10 (968 tests)

---

## Summary

**OVERALL: PASS with 2 UX defects filed**

All core user stories across Sprints 1-10 verified. Two documentation/UX issues found:
1. **UX-001**: MCP schema description has stale text ("Full-path matching not yet supported") — `-Q` ships in Sprint 9
2. **UX-002**: `-oD` (Mermaid diagram) with relationship query shows floating classes, no relationship arrows

---

## Sprint 1 — Core Indexing MVP ✅

| Test | Command | Result |
|------|---------|--------|
| Full index | `via index .` | ✅ Indexed 274 files, 6141 symbols |
| Incremental | `via index .` (2nd run) | ✅ Fast (skipped unchanged files) |
| Stats | `via stats` | ✅ Shows totals: 351 classes, 205 fns, 1252 methods, 1108 imports, 106 globals, 2485 headers |

**Observation**: `via index .` output is clean and informative. Incremental is genuinely fast.

---

## Sprint 2 — Pattern Matching & Query CLI ✅

| Test | Command | Result |
|------|---------|--------|
| Glob | `via -mg 'PathFilter' -tc` | ✅ Found class at correct location |
| Regex | `via -mr 'Match.*Record' -tc -n 3` | ✅ Matched TestMatchRecord*, etc. |
| SQL LIKE | `via -ms '%Store%' -tc -n 3` | ✅ Found DatabaseStore and test classes |
| Type: class | `via -mg '*' -tc -n 3` | ✅ 351 classes, cap warning shown |
| Type: function | `via -mg 'test_*' -tf -n 3` | ✅ 30 test functions |
| Type: header | `via -mg '*' -tH -n 3` | ✅ 2485 headers |
| Case-sensitive | `via -mg 'pathfilter' -tc` | ✅ No results (correct) |
| Case-insensitive | `via -mg 'pathfilter' -tc -I` | ✅ Found PathFilter |
| Result cap | `via -mg '*' -tc -n 3` | ✅ "results 1-3 of 351 matches returned (--limit=3) use -n 0 for all results" |
| Unlimited | `via -mg '*' -tc -n 0` | ✅ 351 results |

---

## Sprint 3 — Render Pipeline & Output Formats ✅

| Test | Command | Result |
|------|---------|--------|
| List (default) | `via -mg 'PathFilter' -tc` | ✅ `class:/path/to/file:line:qualified:@offset+len` |
| Table | `via -mg 'PathFilter' -tc -oT` | ✅ Markdown table with Type/Name/File/Line/QName columns |
| JSON | `via -mg 'PathFilter' -tc -oJ` | ✅ Keys: symbol_name, symbol_type, qualified_name, file_path, line_number |
| Raw source | `via -mg 'PathFilter' -tc -oR -C 2` | ✅ Shows source with header comment block |
| Formatted | `via -mg 'PathFilter' -tc -oF` | ✅ ANSI-colored source (pygments) |
| Usage | `via -mg 'PathFilter' -tc -oU` | ✅ Shows docstring/usage block |
| Diagram | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc -oD` | ⚠️ **UX-002** — see below |
| Context lines | `via -mg 'PathFilter' -tc -oR -C 2` | ✅ Shows 2 lines before/after |
| Stats | `via stats` | ✅ Symbol type counts, file count |

---

## Sprint 4 — Markdown Indexing ✅

| Test | Command | Result |
|------|---------|--------|
| Header type | `via -mg '*' -tH -n 3` | ✅ 2485 headers indexed from .md files |

---

## Sprint 5 — Relationship Queries ✅

| Test | Command | Result |
|------|---------|--------|
| Inheritance | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc` | ✅ 7 subclasses found |
| Invert | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc --invert` | ✅ Shows base classes (ArgumentProvider, HelpProvider) |
| Imports | `via -mg 'typing' -Vimp -mg '*' -tF -n 3` | ✅ Files that import typing |
| Calls | `via -mg 'query_relationships' -tm -Vca -mg '*' -tm -n 3` | ✅ Methods calling query_relationships |
| References | `via -mg 'DatabaseStore' -tc -Vr -mg '*' -n 3` | ✅ Functions referencing DatabaseStore |

---

## Sprint 6 — Watch Mode ✅

| Test | Command | Result |
|------|---------|--------|
| Globals type | `via -mg '*' -tg -n 5` | ✅ 106 globals (FAILURE_PATTERNS, ANSI_ESCAPE, etc.) |

*Watch mode not tested live (requires terminal blocking), but watchdog integration verified via test suite (968 passing).*

---

## Sprint 7 — MCP Server Mode ✅ (with UX-001)

| Test | Command | Result |
|------|---------|--------|
| MCP status | `via status mcp` | ✅ "Project: installed, Global: not installed" |
| MCP schema | `via mcp schema` | ⚠️ **UX-001** — stale text, see below |
| JSON output | `via -mg 'PathFilter' -tc -oJ` | ✅ JSON array with correct keys |

---

## Sprint 8 — Line-Level Indexing ✅

*Line-level byte offsets visible in list output format: `@<offset>+<length>` — verified on all results.*

---

## Sprint 9 — Temporal + Container + -Q ✅

| Test | Command | Result |
|------|---------|--------|
| Container | `via -mg 'PathFilter' -tc -Vhas -mg '*' -tm` | ✅ 4 methods (\_\_init\_\_, should_include_dir, should_include_file, _build_spec) |
| Temporal | `via -mg '*' -tc --olderthan 1m -n 3` | ✅ 351 classes (all older than 1 minute, correct) |
| newerthan | `via -mg '*' -tc --newerthan 1d -n 3` | ✅ 64 classes modified recently |
| -Q path match | `via -mg 'via/core/*' -tF -Q -n 5` | ✅ 13 files in via/core/ matched by path |

---

## Sprint 10 — --ref-type + --stale + prep_tldr ✅

| Test | Command | Result |
|------|---------|--------|
| --ref-type | `via -mg 'MatchRecord' -tc --ref-type inherits-from -mg '*' -tc -n 3` | ✅ Same 7 subclasses as -Vinh |
| --stale | `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc --stale -n 0` | ✅ 0 results (subclasses all newer/same age — correct) |
| Error msg | `via -mg '*' -tc --ref-type invalid` | ✅ "Error: Unknown --ref-type 'invalid'. Valid types: calls, declares, imports, inherits-from, references." |
| prep_tldr | `python agents/tools/prep_tldr.py --force` | ✅ Full mode: 135 files |
| prep_tldr incr | `python agents/tools/prep_tldr.py` | ✅ "Processing 0 changed files (135 skipped)" |

---

## UX Defect Report

### UX-001 — MCP Schema: Stale "Full-path matching not yet supported" text
**Severity**: Medium (misleads AI agents using MCP)
**CMD**: `via mcp schema`
**Expected**: Schema description mentions `-Q` for full-path matching
**Actual**: "Note: -mg matches against the symbol name (not file path). For filepath symbols (-tF), the match is against the basename (e.g. 'utils.py'). Full-path matching not yet supported."
**UX Issue**: This note was accurate before Sprint 9 but is now wrong. AI agents reading the schema will think full-path matching is impossible and won't use `-Q`. Since MCP is the primary interface for Claude Code, this misinformation directly harms usability.
**Fix**: Update the note to: "For full-path matching on -tF queries, use `-Q` (e.g. `via -mg 'via/core/*' -tF -Q`)."

### UX-002 — -oD Diagram: No Relationship Arrows in Inheritance Queries
**Severity**: Low (cosmetic but confusing)
**CMD**: `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc -oD`
**Expected**: Mermaid diagram shows `ClassMatchRecord --|> MatchRecord` inheritance arrows
**Actual**: Diagram lists result classes as disconnected nodes — no arrows, no anchor class
**UX Issue**: A user who uses `-oD` to visualize an inheritance tree gets a diagram that looks like a bug. The chart shows the right classes but hides the entire relationship they asked for. Compare: `-oT` correctly shows results (you know MatchRecord is the anchor), but `-oD` loses this context entirely.
**Fix**: For relationship queries, include the anchor class in the diagram and draw the appropriate relationship arrows.

---

## Overall UX Observations

**Strengths:**
1. **Pipeline syntax is intuitive** — `via -mg PATTERN -t<Y> -V<X> -mg PATTERN -t<Y>` reads like plain English once you know it
2. **Error messages are excellent** — `--ref-type invalid` lists all valid options, no guessing
3. **Cap warning is perfect** — "results 1-3 of 351 matches returned (--limit=3) use -n 0 for all results" is exactly right
4. **`-I` case-insensitive** — clean, works exactly as expected
5. **`-Q` full-path matching** — `via -mg 'via/core/*' -tF -Q` feels natural, great addition
6. **JSON output (-oJ)** — keys are well-named, stable format for agents
7. **prep_tldr incremental** — "Processing 0 changed files (135 skipped)" is satisfying and informative
8. **MCP status output** — clear two-line format (project vs global) is exactly right

**Minor rough edges (not filing as bugs):**
- List output format includes `@offset+length` which is useful for editors but looks noisy in casual use — a `--no-offsets` flag could be nice (future sprint)
- `via -oF` ANSI output in a non-TTY context shows escape codes (expected, but worth noting for piped workflows)
