**Context: Sprint 3 Implementation**

**Key Decisions**:
1. Pipeline syntax detection uses flag prefixes (-mg, -mr, -rT, etc.)
2. Legacy syntax (via match -t ...) preserved via subcommand detection
3. --db flag extracted separately for pipeline mode
4. Default database path: ./.via/index.db
5. MatchRecord system uses polymorphism + factory pattern
6. Each MatchRecord subclass knows its supported render types
7. Renderer system uses abstract base class with format support
8. ListRenderer/RawRenderer are streaming, TableRenderer buffers
9. All 6 RenderTypes now have implemented renderers

**Technical Insights**:
- Pipeline parser uses argparse with exit_on_error=False
- Shorthand expansion: -mg → -g, -rTm → -rT -m
- Executor passes Iterator[MatchRecord] between stages (zero-copy)
- Render stages consume iterator and print (terminal)
- Match stages without render return iterator for default list output
- MatchRecordFactory.create_from_dict() creates correct subclass
- DatabaseStore.match() now returns Iterator[MatchRecord]
- get_renderer(RenderType) returns appropriate Renderer instance
- Renderers yield lines lazily for streaming output
- FormattedRenderer reads source files using byte_offset/byte_length
- DiagramRenderer outputs Mermaid format for MD

**Architecture**:
```
via/__main__.py
  ├── _is_pipeline_syntax() → Detect shorthand flags
  ├── _run_pipeline_command() → Pipeline execution
  │     ├── PipelineParser.parse(argv) → List[PipelineStage]
  │     └── PipelineExecutor.execute(stages) → Iterator|None
  └── main() → Routes to pipeline or legacy mode

via/core/match_record.py
  ├── MatchRecord (ABC) → Base class with supports_render_type()
  ├── ClassMatchRecord → Supports all render types
  ├── MethodMatchRecord → No DIAGRAM
  ├── FunctionMatchRecord → No DIAGRAM
  ├── FileMatchRecord → LIST, TABLE, RAW only
  ├── ImportMatchRecord → LIST, TABLE, USAGE, RAW
  ├── GlobalMatchRecord → LIST, TABLE, RAW, FORMATTED
  └── MatchRecordFactory → Creates correct subclass from dict

via/renderers/
  ├── base.py → Abstract Renderer class
  ├── list_renderer.py → ASCII/MD list output
  ├── table_renderer.py → ASCII/MD/HTML table output
  ├── raw_renderer.py → Tab-separated machine output
  ├── diagram_renderer.py → ASCII/Mermaid class diagrams
  ├── usage_renderer.py → Symbol definition info
  ├── formatted_renderer.py → Code snippets from source
  └── __init__.py → get_renderer() factory
```

**Test Patterns**:
- Use indexed_project fixture for temp DB
- subprocess.run for CLI integration tests
- Assert on returncode, stdout, stderr
- TDD: Write tests first, see red, implement, see green

**Phase 1 Complete** - Pipeline routing implemented
**Phase 2 Complete** - MatchRecord system implemented
**Phase 3 Complete** - Streaming renderer pipeline implemented
**Phase 4 Complete** - Advanced renderers implemented
