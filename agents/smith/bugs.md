# Catalog of Query Engine Bugs

**Date**: 2026-06-20  
**Evaluator**: Smith (HCI Expert & UX Advocate)

This document catalogs the query engine bugs identified during the evaluation of the via gauntlet trace run on 2026-06-20. These bugs caused Scenarios 3, 7, and 14 to return empty outputs.

---

## BUG-1
- **Defect**: The `qualified_name` of class and function symbols is stored as absolute (e.g., starting with `.home.drusifer...`) because `_calculate_qualified_name` is passed the absolute `file_info.path` instead of relative path during indexing. Also, inversion logic overrides in `_get_actual_inverted` map types/joins incorrectly for declares relationships.
- **Impact**: Causes Scenario 3 to fail and return an empty output.

---

## BUG-2
- **Defect**: The query engine fails to resolve file-level imports (`-tF --via imports -mg 'sqlite3' -ti`) and file-to-file imports (`-tF --via imports -mg '*executor*' -tF -Q`) because external module symbols are stored with `file_path = '<external>'` and lack `declares` relationships in the database, causing the `declares` join constraint to fail on the filter side of imports queries.
- **Impact**: Causes Scenarios 7 and 14 to fail and return empty outputs.
