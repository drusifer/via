**Next Steps for Neo**:

## Immediate: Phase 5 - Filter Pipeline (3 pts, 16h)

1. **Task 5.1: Filter Stage Parser (4h)**
   - Add filter stage to PipelineParser
   - Support -F flag for filter operations
   - Filter by pattern on output lines

2. **Task 5.2: Filter Operators (8h)**
   - Implement grep-like filtering on output
   - Support pattern matching on formatted output
   - Chain with render stages

3. **Task 5.3: Sort/Unique Operators (4h)**
   - Sort results by various fields (name, file, line)
   - Deduplicate results by qualified_name

## Upcoming: Phase 6 - Output Destinations (2 pts, 6h)

1. **Task 6.1: File Output (4h)**
   - Write rendered output to file (-o flag)
   - Append mode support (-a flag)
   - Auto-detect format from extension

2. **Task 6.2: Clipboard Output (2h)**
   - Copy output to system clipboard
   - Platform-specific handling (xclip/pbcopy)

## Upcoming: Phase 7 - Interactive Mode (3 pts, 16h)

1. **Task 7.1: REPL Mode (8h)**
   - Interactive query mode with persistent DB connection
   - Command history

2. **Task 7.2: Tab Completion (8h)**
   - Complete symbol names from index
   - Complete file paths

## Upcoming: Phase 8 - Stats Command (2 pts, 8h)

1. **Task 8.1: Basic Stats (4h)**
   - Symbol counts by type
   - File counts

2. **Task 8.2: Detailed Stats (4h)**
   - Most referenced symbols
   - Complexity metrics

## TDD Approach
- Write tests FIRST for each task
- Run tests to see them fail (red)
- Implement to make tests pass (green)
- Refactor if needed

## Sprint 3 Progress
- Phase 1 ✅ COMPLETE - Pipeline routing
- Phase 2 ✅ COMPLETE - MatchRecord system
- Phase 3 ✅ COMPLETE - Streaming renderers
- Phase 4 ✅ COMPLETE - Advanced renderers
- Phase 5 🔲 PENDING - Filter pipeline
- Phase 6 🔲 PENDING - Output destinations
