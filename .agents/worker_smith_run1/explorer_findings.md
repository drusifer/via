# Explorer Findings: Investigation of Scenarios 3, 7, and 14

This report details the read-only investigation of the empty results in Scenarios 3, 7, and 14 from the `via` gauntlet trace.

---

## 1. Observation
We observed the following from the codebase, gauntlet trace logs, and database schema:
- **Scenario 3 (File Exclusions)**:
  - Command: `via -mg '*' -tf --via declares -mg 'via/core/*' -tF -Q -n 5`
  - Output: `(empty output)`
- **Scenario 7 (Import Check)**:
  - Command: `via -mg '*' -tF --via imports -mg 'sqlite3' -ti`
  - Output: `(empty output)`
- **Scenario 14 (Test Coverage Mapping)**:
  - Command: `via -mg '*' -tF --via imports -mg '*executor*' -tF -Q`
  - Output: `(empty output)`
- **Codebase Definitions**:
  - `via/services/indexing.py` stores file path symbols under `_store_file_path_symbols()`. The `filepath` symbol is stored with `symbol_type = 'filepath'`, `file_path = file_info.path` (which is absolute), and `qualified_name = rel_path` (which is relative to the index root).
  - Module symbols (external or resolved imports) are created under `DatabaseStore._get_or_create_module_symbol()`, stored with `file_path = '<external>'`, `line_number = 0`, and no `declares` relationship back to any source files.
  - The `'imports'` relationship is stored in `symbol_references` between the `import` symbol (type `'import'`) and the `module` symbol (type `'module'`).
  - In `via/pipeline/executor.py`, `_get_actual_inverted()` returns `False` when result is `'function'` and filter is `'filepath'` for `'declares'` relationships, overriding `rel.inverted = True`.

---

## 2. Logic Chain

### Scenario 3 (File Exclusions)
1. **Directory Symbols Layout**:
   In the `symbols` table, files inside `via/core/` are stored as two symbol types:
   - `'filepath'`: `symbol_name` is the filename (e.g. `utils.py`), `qualified_name` is the relative path (e.g. `via/core/utils.py`), and `file_path` is the absolute path (e.g. `/home/drusifer/Projects/via/via/core/utils.py`).
   - `'filename'`: `symbol_name` and `qualified_name` are the filename (e.g. `utils.py`), and `file_path` is absolute.
2. **Why `-mg 'via/core/*' -tF -Q` returns empty**:
   - If the database was indexed using absolute paths or if the workspace root resolved differently during indexing, the `qualified_name` column for `filepath` symbols might store absolute paths (e.g., `/home/drusifer/Projects/via/via/core/utils.py`).
   - If `qualified_name` starts with `/home/drusifer/Projects/...`, a glob pattern of `via/core/*` (lacking a leading `/` or wildcard) will not match. A pattern with a leading wildcard like `*via/core/*` (similar to Scenario 9's `'*/executor.py'`) is necessary.
   - Alternatively, the type-checking override in `_get_actual_inverted` sets `actual_inverted = False` for `--via declares`. If the query direction maps the result (`function`) to target `t` and the filter (`filepath`) to source `s`, the columns get mismatched against their stored database values (which store `declares` as `member (from) -> container (to)`), leading to a type mismatch and empty results.

### Scenario 7 (Import Check)
1. **sqlite3 imports**: `sqlite3` is imported in `via/db/store.py` and test suites (like `test_documented_queries_uat.py`).
2. **Why Scenario 7 returns empty**:
   - The `'imports'` relationship exists only between the `import` symbol (type `'import'`, e.g., the `sqlite3` import at line 847) and the module symbol (type `'module'`). It is NOT stored directly between `filepath` symbols.
   - The query `via -mg '*' -tF --via imports -mg 'sqlite3' -ti` specifies `subject_type = 'filepath'` and `object_type = 'import'`.
   - On the subject side, `is_subject_file` joins `symbol_references rs ON rs.from_symbol_id = s.id AND rs.reference_type = 'declares'` to find the file `fs` declaring the import symbol `s`.
   - On the object side, because `object_type = 'import'` (`-ti`), `is_object_file` is `False`. The query engine expects the target `t` of the `imports` relationship to be of type `'import'` or `'module'`.
   - However, the target module `sqlite3` is stored in the database as type `'module'`. Although `query_relationships` attempts to accommodate this via `(t.symbol_type = 'import' OR t.symbol_type = 'module')`, the query returns empty because it fails to perform the transitive lookup correctly or due to type-checking/join mismatches on the filter side of the query.

### Scenario 14 (Test Coverage Mapping)
1. **Why Scenario 14 returns empty**:
   - The command `via -mg '*' -tF --via imports -mg '*executor*' -tF -Q` specifies `-tF` (filepath) on both sides of the `--via imports` relationship.
   - Because `object_type = 'filepath'`, `is_object_file` evaluates to `True`.
   - This causes the SQL builder to join `symbol_references rt ON rt.from_symbol_id = t.id AND rt.reference_type = 'declares'` and `symbols ft ON rt.to_symbol_id = ft.id` to find the declaring file for the imported symbol `t`.
   - However, the target of the `imports` relationship is the module symbol `via.pipeline.executor` (type `'module'`).
   - Module symbols are external symbols created on-the-fly and stored with `file_path = '<external>'` and `line_number = 0`. They **do not have declares relationships** in the database.
   - As a result, the join `rt ON rt.from_symbol_id = t.id AND rt.reference_type = 'declares'` fails completely, causing the query to return empty.

---

## 3. Caveats
- No queries could be run directly via `sqlite3` or python script because the non-interactive execution environment timed out on command permission prompts.
- All conclusions were synthesized using codebase static analysis and comparing execution logs in `via_gauntlet_trace.log`.

---

## 4. Conclusion
- Scenario 3 fails because either the database uses absolute path prefixes in `qualified_name`, requiring a leading wildcard (e.g. `*via/core/*`), or due to declares inversion logic overriding type-mapping.
- Scenario 7 fails because the query engine fails to properly map the transitive `File --declares--> Import --imports--> Module` path when a file is matched against an import.
- Scenario 14 fails because module symbols (targets of imports) are stored with `file_path = '<external>'` and do not have `declares` relationships in the database, causing the file-to-file imports join query to fail.

---

## 5. Verification Method
- **Verification Command**: Run `make test` to verify the synthetic tests for Story 5 and declares relationships continue to pass.
- **Inspect Files**: Compare queries and schema in `via/db/store.py` and `via/pipeline/executor.py` to trace the joins.
