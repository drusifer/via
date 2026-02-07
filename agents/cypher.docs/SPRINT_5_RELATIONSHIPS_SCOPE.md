# Sprint 5 - Relationships Scope

**Author**: Cypher (PM)
**Date**: 2026-01-24

## 1. Vision

This feature will introduce a powerful new capability to the \`via\` tool: the ability to understand and query the relationships between symbols in the codebase. This will allow users to navigate the code in a more intuitive and powerful way, moving beyond simple pattern matching to a deeper understanding of the code's structure and dependencies.

## 2. Scope

The initial scope of this feature will be to index and query a core set of relationships. The system should be designed to be extensible, allowing for the addition of new relationship types in the future.

### 2.1. Relationship Types to Index

The following relationship types will be indexed in the first iteration:

*   **Inheritance**: A class inherits from a parent class.
    *   Example: \`class MyClass(BaseClass):\`
*   **Function/Method Calls**: A function or method calls another function or method.
    *   Example: \`my_function()\` inside another function.
*   **Imports**: A file imports a module or a symbol from a module.
    *   Example: \`from my_module import my_function\`
*   **References**: A generic relationship type that indicates a symbol is referenced. This will serve as a baseline for more specific relationship types.

### 2.2. Querying Relationships

The syntax for querying relationships will extend the existing pipeline construct. A new \`--invert\` flag will be introduced to simplify the relationship types by allowing for bidirectional queries.

**Syntax:**
\`RELATE_TO_QUERY --via RELATIONSHIP [RESULTS_FILTER] [--invert] [options]\`

**Key Concepts:**

*   **Pattern BEFORE \`--via\`**: Filters what you're **relating TO** (the "known" thing you're querying about)
*   **Pattern AFTER \`--via\`** (optional): Filters the **results** (defaults to \`*\` = all matches)
*   **\`--invert\` flag** (short form: \`-iv\`): Flips the relationship direction (e.g., "inherits-from" becomes "inherited-by")

This design provides good defaults - you typically only need to specify one pattern (what you're looking for), and the tool returns all related symbols. You can optionally add a second pattern to filter the results.

**Relationship Types & Flags:**

| Relationship | Long Form | Short Form | Default Direction | With \`--invert\` |
|---|---|---|---|---|
| Inheritance | \`--via inherits-from\` | \`-Vinh\` | Find children of X | Find parents of X |
| Calls | \`--via calls\` | \`-Vca\` | Find callers of X | Find callees of X |
| Imports | \`--via imports\` | \`-Vimp\` | Find importers of X | Find imports by X |
| References | \`--via references\` | \`-Vr\` | Find referencers of X | Find references by X |

**Examples:**

*   **Find all classes that inherit from \`BaseClass\`:**
    \`\`\`bash
    via -mg 'BaseClass' -tc --via inherits-from
    \`\`\`

*   **Find all classes that inherit from any class matching \`*Base*\`:**
    \`\`\`bash
    via -mg '*Base*' -tc --via inherits-from
    \`\`\`

*   **Find all classes that inherit from \`BaseClass\`, but only show ones matching \`Child*\`:**
    \`\`\`bash
    via -mg 'BaseClass' -tc --via inherits-from -mg 'Child*'
    \`\`\`

*   **Find the parents of \`MyClass\` (what does MyClass inherit from?):**
    \`\`\`bash
    via -mg 'MyClass' -tc --via inherits-from --invert
    \`\`\`

*   **Find all functions that call \`helper_func\`:**
    \`\`\`bash
    via -mg 'helper_func' -tf --via calls
    \`\`\`

*   **Find all functions called by \`main_func\`:**
    \`\`\`bash
    via -mg 'main_func' -tf --via calls --invert
    \`\`\`

## 3. User Stories

### For Developers:

*   **As a developer, I want to find all children of a base class so that I can understand its inheritance hierarchy.**
    *   \`via -mg 'BaseClass' -tc --via inherits-from\`
*   **As a developer, I want to find all functions that call a specific utility function so that I can assess the impact of changing its signature.**
    *   \`via -mg 'utility_function' -tf --via calls\`
*   **As a developer, I want to find where a module is imported to understand its usage.**
    *   \`via -mg 'my_module' --via imports\`

### For Agents (to shortcut code reads):

*   **As an agent, I want to quickly find the parent class of a given class to understand its core behavior.**
    *   \`via -mg 'MyClass' -tc --via inherits-from --invert\`
*   **As an agent, before modifying a method, I want to see a list of all other methods that call it.**
    *   \`via -mg 'my_method' -tm --via calls\`
*   **As an agent, I want to identify all test classes that inherit from a specific test base class.**
    *   \`via -mg 'BaseTest' -tc --via inherits-from -mg 'Test*'\`

## 4. Out of Scope for Initial Release

The following items are considered out of scope for the initial implementation, but may be considered for future iterations:

*   **Complex queries** involving multiple relationship types.

## 5. Next Steps

*   **Engage Morpheus** for a technical feasibility assessment.
*   **Engage Neo** for a discussion on implementation details.
*   **Create detailed user stories** based on the outcome of the technical assessment.
