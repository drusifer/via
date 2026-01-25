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
\`<subject_query> --via <relationship> <object_query> [--invert] [options]\`

This design allows for a powerful and flexible way to compose complex queries, as both the subject and object can be defined using the full \`via\` match syntax. The \`--invert\` flag (short form: \`-iv\`) reverses the direction of the relationship query.

**Relationship Types & Flags:**

| Relationship | Long Form | Short Form | Description (default) | Description with \`--invert\` |
|---|---|---|---|---|
| Inheritance | \`--via inherits-from\` | \`-Vinh\` | Subject inherits from object. | Object inherits from subject. |
| Calls | \`--via calls\` | \`-Vca\` | Subject calls object. | Object calls subject (i.e., "called by"). |
| Imports | \`--via imports\` | \`-Vimp\` | Subject imports object. | Object imports subject (i.e., "imported by"). |
| References | \`--via references\` | \`-Vr\` | Subject references object. | Object references subject (i.e., "referenced by"). |

**Examples:**

*   **Find all classes that inherit from a base class matching \`*Base*\`:**
    \`\`\`bash
    via -mg '*' -tc --via inherits-from -mg '*Base*' -tc
    \`\`\`

*   **Find the parents of a class matching \`*Parser*\` (inverted inheritance):**
    \`\`\`bash
    via -mg '*' -tc --via inherits-from -mg '*Parser*' -tc --invert
    \`\`\`

*   **Find all functions that call a function matching \`*util*\`:**
    \`\`\`bash
    via -mg '*' -tf --via calls -mg '*util*' -tf
    \`\`\`

*   **Find all functions called by a function matching \`*main*\` (inverted calls):**
    \`\`\`bash
    via -mg '*' -tf --via calls -mg '*main*' -tf --invert
    \`\`\`

## 3. User Stories

### For Developers:

*   **As a developer, I want to find all children of a base class so that I can understand its inheritance hierarchy.**
    *   \`via -mg '*' -tc --via inherits-from -mg 'BaseClass' -tc --invert\`
*   **As a developer, I want to find all functions that call a specific utility function so that I can assess the impact of changing its signature.**
    *   \`via -mg '*' -tf --via calls -mg 'utility_function' -tf\`
*   **As a developer, I want to find where a module is imported to understand its usage.**
    *   \`via -mg '*' -tF --via imports -mg 'my_module' --invert\`

### For Agents (to shortcut code reads):

*   **As an agent, I want to quickly find the parent class of a given class to understand its core behavior.**
    *   \`via -mg '*' -tc --via inherits-from -mg 'MyClass' -tc\`
*   **As an agent, before modifying a method, I want to see a list of all other methods that call it.**
    *   \`via -mg '*' -tm --via calls -mg 'my_method' -tm --invert\`
*   **As an agent, I want to identify all test classes that inherit from a specific test base class.**
    *   \`via -mg 'Test*' -tc --via inherits-from -mg 'BaseTest' -tc --invert\`

## 4. Out of Scope for Initial Release

The following items are considered out of scope for the initial implementation, but may be considered for future iterations:

*   **Complex queries** involving multiple relationship types.

## 5. Next Steps

*   **Engage Morpheus** for a technical feasibility assessment.
*   **Engage Neo** for a discussion on implementation details.
*   **Create detailed user stories** based on the outcome of the technical assessment.
