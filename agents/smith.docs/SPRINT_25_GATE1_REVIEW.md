# Sprint 25 Gate 1 HCI Review — Dart / Flutter Support

**Reviewer**: Smith  
**Date**: 2026-05-06  
**Artifact**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`  
**Verdict**: APPROVED WITH NOTES

## Summary

The story set gives Flutter and Dart users a useful, believable first sprint: structural indexing, normal VIA queries, basic relationships, and Flutter project hygiene. It avoids the common product trap of promising semantic Flutter analysis or widget tree reconstruction.

## HCI Findings

### Approved

- **Match between system and real world**: The stories use user-facing Dart/Flutter terms (`Widget`, `build`, `.dart`, `StatelessWidget`) while keeping the actual query model consistent with VIA.
- **Consistency and standards**: The stories preserve `--lang`, `-tc`, `-tm`, `--via`, and existing output behavior instead of inventing a Flutter-only surface.
- **Recognition rather than recall**: Documentation/MCP examples for Flutter workflows are included in S25-5.
- **Error prevention**: Default excludes for `.dart_tool/`, `build/`, Gradle, and Pods reduce noisy indexes in real Flutter projects.
- **Help and documentation**: The explicit boundary statement prevents users from assuming VIA is a Dart analyzer.

### Notes For Morpheus

- Keep `--lang dart` as the only language spelling for this sprint unless aliases are already supported by the current language filter. Do not introduce both `dart` and `flutter` as language filters.
- Avoid Flutter-specific flags in Sprint 25. Users should learn normal VIA queries first.
- Architecture should decide whether constructors are stored as normal methods named `ClassName` or with a `constructor` subtype. The user-visible behavior must be documented either way.
- `import`, `export`, and `part` should be clearly explained as directive strings, not resolved package dependencies.
- If the Dart parser dependency is weaker than JS/TS tree-sitter support, docs must say "best-effort Dart parser" until UAT proves stability.

## Gate Decision

Gate 1 is approved. Proceed to Morpheus architecture.

## Handoff

@Morpheus: Design Sprint 25 architecture for Dart/Flutter support. Preserve the structural-indexing boundary and use existing VIA query surfaces.
