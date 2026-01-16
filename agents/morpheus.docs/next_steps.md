# Morpheus Next Steps

## Immediate Next Steps (For Other Personas)

### For @Neo (Implementation)
**Priority**: P0
**Task**: Implement Sprint 2 Match Command

**Files to Create/Modify**:
1. `via/core/types.py` - SymbolType enum, MatchOp enum, MatchResult dataclass
2. `via/database/store.py` - Add _QUERY_TEMPLATES dict and match() method
3. `via/__main__.py` - Add match subcommand with CLI flags

**Implementation Order**:
1. Story 1: Create types.py with enums and dataclass (S1.1-S1.7)
2. Story 2: Add match() to DatabaseStore with SQL templates (S2.1-S2.7)
3. Story 3: Wire CLI match command (S3.1-S3.6)

**Reference Documents**:
- Architecture: `/home/drusifer/Projects/via/agents/morpheus.docs/MATCH_COMMAND_ARCHITECTURE.md`
- User Stories: `/home/drusifer/Projects/via/agents/cypher.docs/SPRINT_2_USER_STORIES.md`
- Requirements: `/home/drusifer/Projects/via/agents/cypher.docs/SPRINT_2_REQUIREMENTS_FINAL.md`

### For @Mouse (Optional - Task Breakdown)
If more detailed task breakdown needed before implementation, create Sprint 2 task board with individual tickets.

### For @Morpheus (Future Sprints)
- Sprint 3: Design render command architecture (syntax highlighting, context lines)
- Sprint 4: Design query pipeline architecture (AND/OR/NOT operators)

## No Current Blockers
Architecture is complete and ready for implementation. All design questions resolved.

## Long-term Architectural Considerations
- Byte offset/length will enable efficient rendering in Sprint 3
- SQL template pattern scales well for future query complexity
- Enum pattern makes adding new types/operators trivial
