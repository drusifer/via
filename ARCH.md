Architecture update introducing polymorphic parameter parsing and help output to VIA's CLI.

TLDR:
    Change: Replace ad-hoc argparse setup with ArgumentProvider/HelpProvider
    interfaces so each command registers its own flags and help text. Refactoring
    plan for Neo covers the steps to migrate existing commands to the new pattern.

# VIA Architecture Update: Polymorphic Parameter Parsing & Help Output

**Date:** 2026-01-22
**Author:** Morpheus (SE)

## Change Summary

Parameter parsing and --help output will be refactored to leverage the polymorphic type system. All core types, MatchRecords, and Renderers will expose interfaces for argument parsing and help output. This ensures CLI help and argument handling remain in sync with the evolving type system and renderer capabilities.

- **Motivation:** Avoid drift between CLI help, argument parsing, and actual type/renderer capabilities. Enable future extensibility and reduce maintenance overhead.
- **Approach:** Use Python's ABCs and interface patterns. Each type/renderer/record will provide:
  - `add_arguments(parser: argparse.ArgumentParser)`
  - `get_help() -> str`
- **Integration:** Standard argparse subcommand implementation will be used as the base. If limitations arise, a custom dispatcher or metaclass-based registry will be considered.

## Refactoring Plan for Neo

1. **Define Interfaces**
   - Create ABCs for argument parsing and help output (e.g., `ArgumentProvider`, `HelpProvider`).
   - Add `add_arguments` and `get_help` methods to all relevant types, MatchRecords, and Renderers.

2. **Update CLI Entrypoints**
   - Refactor CLI and subcommand setup to delegate argument registration to the type/renderer interfaces.
   - Ensure `--help` output is composed from all registered providers.

3. **Synchronize Help Output**
   - Remove hardcoded help strings from CLI entrypoints.
   - Use `get_help()` from each provider to build unified help output.

4. **Testing**
   - Add/expand unit tests to verify that all argument providers register their options and help correctly.
   - Add integration tests to ensure CLI help output matches the actual argument set.

5. **Documentation**
   - Update developer docs to describe the new interface pattern and extension process.

---

*This change will keep CLI, types, and renderers in sync and future-proof the argument parsing system.*
