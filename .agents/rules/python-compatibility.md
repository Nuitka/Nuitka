# Python Compatibility (STRICT)

## 1. Python Compatibility (STRICT)

- **Python 2.6/2.7 Compatibility:** The Nuitka codebase must remain strictly compatible with Python
  2.6 and 2.7.
  - **Exception:** For Windows, Python 2.7 support is desirable but not mandatory. Use your judgment
    to avoid complex workarounds for niche Windows 2.7 issues (e.g., symlinks need not be
    supported).
- **Syntax Restrictions:**
  - Do NOT use syntax that cannot be parsed by Python 2.6 in Nuitka's own Python implementation
    files. This includes all modern Python 3-only syntax, even when guarded by version checks.
  - Do NOT use f-strings (use `%` formatting or `.format()`).
  - Do NOT use type hints in the source code (use comments if necessary).
  - Do NOT use function annotations or variable annotations.
  - Do NOT use `yield from` or `async/await`.
  - DO NOT use `return` in a generator function (Python3-only feature).
  - DO NOT use set literals (use `set()` instead) - *required for Python 2.6 compatibility*.
  - Do NOT use dict comprehensions or set comprehensions - *required for Python 2.6 compatibility*.
  - Do NOT use assignment expressions (`:=`).
  - Do NOT use structural pattern matching (`match`/`case`).
  - Do NOT use exception chaining syntax (`raise ... from ...`).
  - Do NOT use bare `except:` (use `except Exception:` or `except BaseException:` if intended).
  - Do NOT use `re.VERBOSE` (avoid regular expressions that require runtime overhead or large
    definitions).
  - Do NOT use keyword-only arguments separator `*` (e.g. `def foo(a, *, b)`) - *required for Python
    2 compatibility*.
  - Do NOT use positional-only arguments separator `/` (e.g. `def foo(a, /, b)`) - *required for
    Python < 3.8 compatibility*.
- **Coding Preferences:**
  - **Preferred:** List comprehensions are preferred over `map`, `filter`, and `apply` for
    readability.
  - **Prioritize Readability:** Do not optimize Nuitka's own Python code for performance at the cost
    of readability unless explicitly requested.
