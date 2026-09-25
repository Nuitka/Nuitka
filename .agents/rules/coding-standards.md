# Coding Standards

## 2. Python Coding Rules & Standards

- **Naming Conventions:**

  - **Classes:** `CamelCase` (e.g., `SomeClass`). Abstract base classes must end in `Base`.
  - **Functions/Methods:** `camelCase` (starting lower) (e.g., `doSomething`,
    `getSequenceCreationCode`).
  - **Variables/Arguments:** `snake_case` (e.g., `some_parameter`, `local_var`).
  - **Modules:** `CamelCase` (e.g., `Nodes`, `Options`).
  - **Packages:** `lower_case` (e.g., `nuitka`, `code_generation`). No code in `__init__.py`.
  - **Context Managers:** Must start with `with` (e.g., `withFileLock`, `withDirectoryChange`).

- **Documentation Strings (Nuitka/Google Style):**

  - **Format:**
    ```python
    def someFunction(arg1):
        """Brief one-line summary.

        Notes:
            Detailed explanation (optional).

        Args:
            arg1: Description of argument.

        Returns:
            Description of return value.
        """
    ```
  - **Sections:** `Notes:`, `Args:`, `Kwargs:`, `Returns:`, `Yields:`, `Raises:`, `Examples:`.
  - **Quoting:** Use single ticks `'...'` for function names/identifiers in documentation strings
    (e.g., `'os.path.join'`), NOT backticks or double quotes.

- **Coding Practices:**

  - **Comments:** Comments shall only state information that is not available in the code it
    comments on.

  - **Strings:** Do not create long strings by implicitly concatenating multiple smaller strings
    across lines or using backslashes between string fragments. Use triple-quoted strings
    (`"""..."""`) for long strings, using `\` escapes inside them if lines become too long.

  - **List Contractions:** PREFERRED over `map`, `filter`, `apply`.

  - **Properties:** Avoid using properties for internal APIs; use explicit getters/setters.

  - **Imports:** Sort imports using `isort` (handled by auto-format).

  - **Local imports:** Avoid `import` inside functions or methods. Local imports are only acceptable
    when the alternative would cause a circular import."

  - **Avoid default arguments for internal APIs:** When adding a new argument to a function or
    method, do **not** provide a default value. Callers must explicitly supply the argument unless
    the case is a well‑defined exception (e.g., a optional flag that is very unlikely to be used).
    This ensures clarity and prevents hidden behavior.

## 3. C Coding Standards

- **Standard:** Code must adhere to C11 (or C++03 where applicable).
- **Control Structures:**
  - **ALWAYS** use curly braces `{ }` for all conditional instructions (`if`, `else`, `while`,
    `for`), even for single-line statements. This prevents common errors when adding statements
    later.
    - **Incorrect:** `if (condition) return;`
    - **Correct:** `if (condition) { return; }`
- **Formatting:**
  - C code is formatted using `clang-format` as part of `bin/autoformat-nuitka-source`.
