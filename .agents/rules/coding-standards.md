---
trigger: always_on
description: Python and C coding standards, naming conventions, docstring, and comment rules for Nuitka.
---

# Coding Standards

## Python Coding Rules & Standards

- **Naming Conventions:**

  - **Classes:** `CamelCase` (e.g., `SomeClass`). Abstract base classes must end in `Base`.
  - **Functions/Methods:** `camelCase` (starting lower) (e.g., `doSomething`,
    `getSequenceCreationCode`).
  - **Variables/Arguments:** `snake_case` (e.g., `some_parameter`, `local_var`).
  - **Modules:** `CamelCase` (e.g., `Nodes`, `Options`).
  - **Packages:** `lower_case` (e.g., `nuitka`, `code_generation`). No code in `__init__.py`.
  - **Context Managers:** Must start with `with` (e.g., `withFileLock`, `withDirectoryChange`).

- **Documentation Strings (Nuitka/Google Style):**

  - **When to Write Docstrings:** PyLint runs with `--no-docstring-rgx=.*`, so docstrings are
    **optional** for local helpers, classes, and node overrides whose names and parameters already
    express their behavior. Write a concise docstring (and only include `Args:`, `Returns:`, or
    `Notes:` when non-obvious) for internal API helpers (stating brief purpose and any equivalent
    CPython/standard API plus contract differences), non-obvious contracts (ownership, mutability,
    tri-state returns like `True`/`False`/`None`, tuple layouts, side effects), or public/external
    surfaces (`PluginBase.py`, `Options.py`). Trim verbose prose rather than stripping API docs
    outright, and never write restatements such as `filename: path to the file` or
    `logger: logger to use`.
  - **Single Source of Truth:** Across layered dispatchers (e.g., `PluginBase.py` vs `Hooks.py` vs
    `Plugins.py`), document the hook contract once in `PluginBase.py` rather than duplicating prose
    in internal wrappers where it drifts.
  - **Format (when needed):**
    ```python
    def someFunction(arg1):
        """Brief one-line summary of non-obvious contract.

        Notes:
            Non-code rationale or subtle behavior (optional).

        Args:
            arg1: Non-obvious constraint or ownership detail.

        Returns:
            Non-obvious return semantics or tuple shape.
        """
    ```
  - **Sections:** `Notes:`, `Args:`, `Kwargs:`, `Returns:`, `Yields:`, `Raises:`, `Examples:`.
  - **Quoting:** Use single ticks `'...'` for function names/identifiers in documentation strings
    (e.g., `'os.path.join'`), NOT backticks or double quotes.

- **Coding Practices:**

  - **Strings:** Do not create long strings by implicitly concatenating multiple smaller strings
    across lines or using backslashes between string fragments. Use triple-quoted strings
    (`"""..."""`) for long strings, using `\` escapes inside them if lines become too long.

  - **List Comprehensions:** PREFERRED over `map`, `filter`, `apply`.

  - **Properties:** Avoid using properties for internal APIs; use explicit getters/setters.

  - **Imports:** Sort imports using `isort` (handled by auto-format).

  - **Local imports:** Avoid `import` inside functions or methods. Local imports are only acceptable
    when the alternative would cause a circular import.

  - **Avoid default arguments for internal APIs:** When adding a new argument to a function or
    method, do **not** provide a default value. Callers must explicitly supply the argument unless
    the case is a well-defined exception (e.g., an optional flag that is very unlikely to be used).
    This ensures clarity and prevents hidden behavior.

## C Coding Standards

- **Standard:** Code must adhere to C11 (or C++03 where applicable).
- **Control Structures:**
  - **ALWAYS** use curly braces `{ }` for all conditional instructions (`if`, `else`, `while`,
    `for`), even for single-line statements. This prevents common errors when adding statements
    later.
    - **Incorrect:** `if (condition) return;`
    - **Correct:** `if (condition) { return; }`
- **Generated Helpers (`templates_c` / `templates_python`):**
  - Many specialized C and Python helpers are generated from Jinja2 templates (`*.c.j2`, `*.py.j2`).
    Edit the `.j2` template and regenerate with `./bin/generate-specialized-c-code` or
    `./bin/generate-specialized-python-code` (use `.cmd` on Windows) rather than editing generated
    outputs directly.
- **Formatting:**
  - C code is formatted using `clang-format` as part of `bin/autoformat-nuitka-source`.
- **Comment Syntax:**
  - Prefer `//` line comments over `/* ... */` block comments in C code.

## Comments (Python, C, and Templates)

- **Only Non-Code "Why" Explanations:** Comments may only state facts that live **outside Nuitka's
  code** and cannot be expressed through naming, control flow, or assertions:
  - CPython version, bytecode, AST, or C-API quirks (cite specific versions).
  - OS, compiler, linker, loader, or external tool bugs (e.g., MSVC/GCC pragmas, Rosetta, PE/ELF
    layout, DBCS `depends.exe`).
  - Third-party library runtime hazards or licensing constraints.
  - Deliberate counter-intuitive trade-offs (e.g., an intentional reference leak at shutdown, or why
    a value must not be cached).
- **Never Restate Local Code ("What" / "How"):** Do not narrate assignments, branches, loops,
  returns, or calls (`# Sanity check`, `# Remove the comma`, `// Return the error`). Rename
  variables or extract a well-named helper instead.
- **Never State Conditions Other Nuitka Code Might Have or Not:** Do **not** write comments stating
  or speculating about what callers, earlier passes, other compilation modes, or callees pass,
  check, or skip (e.g., `# Caller already checked X`, `# In standalone mode Y is None`,
  `# Optimization turns empty dicts into constants`). Those facts already exist in other Nuitka code
  and silently rot when that code evolves:
  - **Assert, don't comment:** If a cross-code invariant must hold locally, enforce it with
    `assert ...` (Python) or `assert(...)` / `CHECK_OBJECT(...)` (C), never unverified prose.
  - **Let defensive branches speak for themselves:** When writing `if x is None:`, do not add prose
    guessing which callers produce `None`.
- **Examples:**
  - **Incorrect (code narration):** `# Remove the comma.` above `line = line[:idx] + line[idx + 1:]`
  - **Incorrect (cross-code speculation):** `# Only called for modules built from source.` or
    `# Empty dicts do not reach here because optimization turns them into constants.`
  - **Correct (executable invariant):** `assert pairs_count > 0` /
    `assert source_code is not None, module`
  - **Correct (non-code "why"):**
    `// Python 3.12 stores dict-watcher flags in the low bits of ma_version_tag, so step by DICT_VERSION_INCREMENT.`
- **No Dead Code or Vague `TODO`s:** Delete commented-out code, `# print(...)` calls, and `#if 0`
  debug blocks (git preserves history). Only write `TODO` comments when specific, current, and
  actionable.
- **Templates (`*.c.j2`, `*.py.j2`, `CodeTemplates*.py`):** Use Jinja `{# ... #}` comments for
  template rationale, disabled ideas, and `TODO`s instead of target-language comments (`//`,
  `/* */`, `#`) that get stamped out across generated files. Generated classes should have the same
  concise docstring they would have if hand-written (without `"Generated from ..."` meta-boilerplate
  or duplicating base-method docstrings on overrides). Preserve required tool directives
  (`WARNING, this code is GENERATED`, `# pylint: disable=...`, `# spell-checker: ignore`,
  `# isort:start`, and `# Nuitka:` on `notest_*` in `tests/CPython*`).
- **Mandatory Edit-Time & Copy-Paste Audit:** Whenever editing a function, class, or template - or
  copying an existing node, helper, or plugin as a starting point - re-read **every** comment and
  docstring in the touched scope and fix or delete stale, copy-pasted, or restating text in the same
  edit.
