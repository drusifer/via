# Sprint 6 - Backlog

**Author**: Cypher (PM)
**Date**: 2026-01-24

## User Stories

### 1. Implement Correct `UsageRenderer` Functionality [COMPLETE]
*   **User Story**: As a developer, I want to quickly see the 'usage' aka docstring/javadoc/manpage etc. for the matched symbols.

*   **Acceptance Criteria**:
    *   The existing `UsageRenderer` is refactored to find and display usages of a symbol.
    *   When a user runs `via -mg 'my_symbol' -t<X> -oU`, the output shows a the rendered docstring for the symbol
    *   The output should be clearly formatted, showing the file, line number, and the line of code containing the symbol definition.
