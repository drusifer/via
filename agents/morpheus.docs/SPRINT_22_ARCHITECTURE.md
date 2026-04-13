# Sprint 22 Architecture — Query Confidence And Error Recovery

**Author**: Morpheus  
**Date**: 2026-04-12  
**Stories**: `agents/cypher.docs/SPRINT_22_24_HCI_UX_USER_STORIES.md`  
**Smith Gate 1**: `agents/smith.docs/SPRINT_22_24_GATE1_REVIEW.md`  
**Theme**: Make VIA query failures explicit and teach the correct stage model.

---

## Sprint Goal

Sprint 22 should make query behavior diagnosable without changing VIA's query engine semantics. The target is confidence: users must be able to tell valid empty results from invalid syntax, unsupported composition, and stale documentation.

Non-goals:

- No new relationship model.
- No shortcut syntax in Sprint 22.
- No executor strategy refactor.
- No broad CLI parser replacement.

---

## User-Facing Command Model

Documentation and help should teach this model:

```text
via <result stage> [--via|--sans <relationship> <filter stage>]
```

The first stage defines the candidate result set: what symbols/files/headers VIA returns. Relationship stages filter that result set by requiring, or excluding, a relationship to another matched set.

Examples:

```bash
via -mg '*handler*' -tf --via calls -mg 'parse_args' -tf
```

Return functions matching `*handler*`, filtered to those that call functions matching `parse_args`.

```bash
via -mg '*' -tf --sans calls -mg '*' -tf
```

Return functions, filtered to those that do not call any function.

This replaces "known anchor left, wildcard right" as the primary teaching model. Relationship direction still matters, but it should be taught through examples after the result-stage-first model is established.

---

## Architecture Decisions

### Decision 1: Introduce A Structured Query Error Contract

Add a small shared error representation for user-facing query failures:

```python
@dataclass(frozen=True)
class QueryError:
    code: str
    message: str
    hint: str | None = None
```

Recommended location: `via/pipeline/errors.py`.

`PipelineParseError` should carry the same fields:

```python
class PipelineParseError(Exception):
    def __init__(self, message: str, code: str = "invalid_query", hint: str | None = None):
        ...
```

Rationale:

- Parser failures are already the common choke point for invalid arguments.
- MCP needs a structured response, while CLI needs readable stderr.
- A typed internal shape prevents every caller from inventing its own error mapping.

MCP response shape:

```json
{
  "output_type": "error",
  "result": [],
  "total": 0,
  "shown": 0,
  "error": {
    "code": "invalid_argument",
    "message": "Unknown argument '--bad'.",
    "hint": "Run via --help or use one of: -mg, -mr, -ms."
  }
}
```

CLI behavior should remain conventional: print the message and hint to stderr, return `EXIT_ERROR`, and avoid raw tracebacks for expected parse failures.

---

### Decision 2: Validate Match Flags Before Argparse Stores Them

`argparse` mutually exclusive groups catch mixed flags such as `-mg` plus `-mr`, but repeated store-style flags can silently become last-one-wins. Sprint 22 should explicitly validate match flags before `parse_args()`.

Add a parser helper:

```python
def _validate_single_matcher(self, args: list[str], stage_label: str) -> None:
    ...
```

It should count occurrences of:

- `-mg`, `--match-glob`
- `-mr`, `--match-regex`
- `-ms`, `--match-sql`

Validation rules:

- zero matchers is valid only where current behavior already defaults to `*`.
- one matcher is valid.
- repeated or mixed matchers in one stage are invalid.
- subject/result and object/filter sides of a relationship are separate stages for validation.

Error message:

```text
Use one match flag per stage. Compose with relationship stages or rerun a narrower query.
```

Implementation points:

- In a normal match stage, validate the full stage args after removing `--not`.
- In a relationship query, validate `subject_args` and `object_args` separately.
- Preserve multi-type OR behavior (`-tf -tm -tc`) unchanged.

---

### Decision 3: Validate Regex At Parse Time

`-mr` should compile the regex during parsing or immediately after namespace finalization. Invalid regex is a syntax error, not a valid empty result.

Recommended helper:

```python
def _validate_regex_pattern(self, parsed_args: Namespace, stage_label: str) -> None:
    ...
```

Only run it when `parsed_args.match_syntax == "regex"` and `parsed_args.pattern` is not `None`.

Error response should include the regex compiler message in a safe, concise form.

---

### Decision 4: S22-4 Is Documentation Correction, Not New Query Power

Under the clarified command model, this documented quick reference is misleading:

```json
["-mg", "path/to/file.py", "-tF", "-Q", "--via", "declares", "-mg", "*"]
```

It presents the first stage as a file but labels the task "find all symbols in a file." Since the first stage determines returned results, the query cannot be documented as returning declared symbols.

Sprint 22 should correct documentation and MCP examples rather than implementing inverse `declares` behavior.

Required docs correction:

- Remove or rewrite the `agents/PROJECT.md` "Find all symbols in a file" quick reference.
- Update MCP schema examples to avoid this pattern.
- User guide/help must explain that relationship stages filter the initial result set.

If a user asks for "symbols declared in file," that belongs in Sprint 23 shortcut design as a task-oriented affordance. It may expand to a supported inverse query, a new canned query, or a dedicated runner helper, but not in Sprint 22.

---

## Implementation Plan By Story

### S22-1 Structured MCP Errors

Files:

- `via/pipeline/errors.py` — new `QueryError` shape and enhanced `PipelineParseError`
- `via/pipeline/parser.py` — raise structured parse errors
- `via/mcp/server.py` — convert expected query errors into `output_type: "error"`
- `via/__main__.py` — preserve clean CLI stderr behavior

Expected exceptions:

- `PipelineParseError`: user-facing `invalid_query` / `invalid_argument`
- `ValueError` from known query validation: wrap into `PipelineParseError` at the parser boundary where possible
- unexpected exceptions: log internally; MCP returns `internal_error` without swallowing diagnostics in logs

### S22-2 Multi-Match Semantics

Files:

- `via/pipeline/parser.py`
- `via/mcp/schema.py`
- `via/__main__.py` help text

Add parser-level pre-validation and docs. Tests should cover:

- repeated `-mg`
- `-mg` plus `-mr`
- repeated matcher on relationship object side
- valid result-stage matcher plus filter-stage matcher
- multi-type query remains valid

### S22-3 Regex UX

Files:

- `via/pipeline/parser.py`
- `via/mcp/schema.py`
- `via/__main__.py` help text

Add regex examples and invalid-regex structured errors.

### S22-4 Documentation Correction

Files:

- `agents/PROJECT.md`
- `via/mcp/schema.py`
- `docs/USER_GUIDE.md` if the incorrect pattern appears there
- `via/__main__.py` help text if examples need adjustment

No executor or database changes for this story.

---

## Test Strategy

Use focused unit and integration tests:

- Parser tests for structured errors and matcher validation.
- MCP tests for error response shape.
- CLI tests for clean stderr and non-zero exit.
- Documentation/schema tests asserting the result-stage-first model appears.
- Regression tests confirming multi-type OR remains valid.

Do not expand full-suite scope unless touched modules require it. Existing test naming can use `test_sprint22_*`.

---

## Open Questions For Smith Gate 2

1. Is `output_type: "error"` the clearest MCP response shape, or should errors be top-level while preserving prior `output_type`?
2. Is "result stage" / "filter stage" the right user-facing vocabulary?
3. Should the docs explicitly say that "symbols declared in file" is deferred to Sprint 23 shortcut design?

---

## Sprint 22 Phase Recommendation

1. **Phase 1**: Query error contract and MCP error response shape.
2. **Phase 2**: Match-stage validation and regex validation.
3. **Phase 3**: Documentation/schema/help corrections for the result-stage-first model and `declares` quick reference.

This keeps implementation slices small and reviewable while preserving the Sprint 22 goal.
