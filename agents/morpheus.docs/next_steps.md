# Morpheus Next Steps

## Resume Point: Sprint 21 shipped

### On Resume
1. Read bottom 20 lines of `agents/CHAT.md`
2. Keep executor refactors/CLI parser replacement separate unless a new sprint explicitly plans them
3. If _js_body unit tests are requested, confirm they test collect() entry point only — not internal _walk()
4. ViaRunner.run_cli_args() is now the canonical CLI-args seam; any future callers should use it

### Key Decisions (Sprint 21)
- S21-1: ABC in `via/parsers/_js_body.py`, 3 concrete subclasses, keyword-only `collect()` args
- S21-2: `ViaRunner.run_cli_args(args: list[str])`, MCP creates ViaRunner once at startup
- `redirect_stdout` stays in MCP server — ViaRunner does not own stdout
