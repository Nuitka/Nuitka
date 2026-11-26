---
trigger: always_on
description: Strict Python 2.6/2.7 compatibility rules for Nuitka source code.
---

# Python Compatibility (STRICT)

- **Python 2.6/2.7 Compatibility:** The Nuitka codebase must remain strictly compatible with Python
  2.6 and 2.7.
  - **Windows Exception:** For Windows, Python 2.7 support is desirable but not mandatory. Use your
    judgment to avoid complex workarounds for niche Windows 2.7 issues (e.g., symlinks need not be
    supported).
  - **Developer Tooling Exception:** Standalone developer scripts that explicitly start with
    `#!/usr/bin/env python3` (e.g., `misc/vscode_config_gen.py`, `bin/check-nuitka-with-pyright`,
    `bin/check-nuitka-with-clangd`) target Python 3 only and may use Python 3 syntax.
- **Syntax Restrictions:**
  - Do NOT use syntax that cannot be parsed by Python 2.6 in Nuitka's own Python implementation
    files. This includes all modern Python 3-only syntax, even when guarded by version checks.
  - Do NOT use f-strings (use `%` formatting or `.format()`).
  - Do NOT use type hints in the source code (use comments if necessary).
  - Do NOT use function annotations or variable annotations.
  - Do NOT use zero-argument `super()` (use `super(ClassName, self)...` instead).
  - Do NOT use `nonlocal` statements.
  - Do NOT use extended iterable unpacking (`a, *rest = seq`).
  - Do NOT use dictionary unpacking merges (`{**a, **b}` or `a | b`).
  - Do NOT use `yield from` or `async/await`.
  - Do NOT use `return` with a value in a generator function (Python 3-only feature).
  - Do NOT use set literals (use `set()` instead) - *required for Python 2.6 compatibility*.
  - Do NOT use dict comprehensions or set comprehensions - *required for Python 2.6 compatibility*.
  - Do NOT use assignment expressions (`:=`).
  - Do NOT use structural pattern matching (`match`/`case`).
  - Do NOT use exception chaining syntax (`raise ... from ...`).
  - Do NOT use `print(...)` with Python 3 keyword arguments (`file=`, `flush=`, `end=`); use
    `nuitka.Tracing` (`my_print` or loggers) instead.
  - Do NOT use bare `except:` (use `except Exception:` or `except BaseException:` if intended).
  - Do NOT use keyword-only arguments separator `*` (e.g. `def foo(a, *, b)`) - *required for Python
    2 compatibility*.
  - Do NOT use positional-only arguments separator `/` (e.g. `def foo(a, /, b)`) - *required for
    Python < 3.8 compatibility*.
- **Standard Library & Nuitka Helpers:**
  - Do NOT use Python 3-only standard library modules or flags such as `pathlib`, `subprocess.run`,
    `shutil.which`, or `os.makedirs(..., exist_ok=True)`.
  - Use `nuitka.__past__` for cross-Python builtins/types (`xrange`, `unicode`, `basestring`,
    `iterItems`, `subprocess`, etc.), `nuitka.utils.FileOperations` for filesystem operations, and
    `nuitka.utils.Execution` (`getExecutablePath`, `check_call`, `executeProcess`) for subprocesses.
- **Coding Preferences:**
  - **Preferred:** List comprehensions are preferred over `map`, `filter`, and `apply` for
    readability.
  - **Prioritize Readability:** Do not optimize Nuitka's own Python code for performance at the cost
    of readability unless explicitly requested.
