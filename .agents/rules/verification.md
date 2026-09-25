# Code Quality & Workflow

## 4. Code Quality & Verification

Before marking a task as complete, you must verify the changes using the project's custom tools in
this order:

- **Auto-Formatting:** Apply auto-formatting to any file you touch (Python or C).

  - Command: `./bin/autoformat-nuitka-source --un-pushed --assume-yes-for-downloads`
  - On Windows, use `.\bin\autoformat-nuitka-source.cmd --un-pushed --assume-yes-for-downloads`
    instead.
  - Prefer this exact repo-root command by default. Do not replace it with file-specific arguments
    unless the user explicitly asks for that or there is a demonstrated need to narrow the run for
    diagnosis.
  - Can be run on the entire project with
    `./bin/autoformat-nuitka-source --assume-yes-for-downloads`
  - This script applies `black`, `isort` (for Python), and `clang-format` (for C) as well as other
    tools.
  - On Windows, if the command fails with "Python not found", run
    `{Python.exe} misc\vscode_config_gen.py` first to generate the config files needed.

- **Linting:** You must run the project's pylint script after auto-formatting.

  - Command: `./bin/check-nuitka-with-pylint --un-pushed`
  - On Windows, use `.\bin\check-nuitka-with-pylint.cmd --un-pushed` instead.
  - Prefer this exact repo-root command by default. Do not replace it with file-specific arguments
    unless the user explicitly asks for that or there is a demonstrated need to narrow the run for
    diagnosis.
  - Can be run on the entire project with `./bin/check-nuitka-with-pylint`
  - *Constraint:* If pylint fails, fix the errors before asking for review. Do not suppress warnings
    without a very strong reason.

### Change-Type Verification Matrix

Always run the required auto-formatting and pylint commands first. Then add focused verification for
the changed area:

| Change type           | Additional verification                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| Python change         | Run the affected test, reproducer, or nearest repository test through `bin/nuitka`.                      |
| C change              | Compile and run a representative program that exercises the changed helper or runtime path.              |
| Package config change | Build a standalone MRE for the affected package and confirm the compiled binary imports/runs correctly.  |
| SCons change          | Run `bin/nuitka --version` and exercise `tests/basics/AssertsTest.py` in the relevant compilation modes. |
| Release/OBS issue     | Fetch the raw OBS/build log, identify the terminal failure, and verify the changed release tooling path. |
| CPython-suite change  | Use the matching `tests/CPython*` submodule workflow and run the changed CPython comparison test.        |

- **Temporary Verification Files:**

  - All temporary test scripts, reproduction scripts, and their artifacts created during
    verification MUST be placed in `tests/scratch/`.
  - This directory is git-ignored and ensures the repository remains clean.

## 5. Workflow

- **Bugs & Implementation:**

  - When fixing bugs in C code, analyze the specific Nuitka internal C-API usage. Often Python C-API
    has safer or more optimized replacements in Nuitka.
  - Calls to Python C-API are slow and generally avoided in Nuitka where we can.
  - For file operations, prefer functions in `nuitka.utils.FileOperations` and add them if missing.

- **Tests:**

  - On Windows, ensure a suitable Python version is installed (e.g.,
    `~/AppData/Local/Programs/Python/Python313`). Prompt the user to install if missing a suitable
    version.
  - When you only need to vary Nuitka command line flags for an existing repository test case,
    prefer reusing it via `NUITKA_EXTRA_OPTIONS`.
  - For **scons** level changes:
    - Run `bin/nuitka --version` to check basic sanity.
    - Compile `tests/basics/AssertsTest.py` to verify correctness.
    - Exercise modes: `--mode=accelerated`, `--mode=standalone`, `--mode=module`, `--mode=onefile`.
    - Verify that output with `--run` matches the direct Python execution.

- **Execution:**

  - Use `bin/nuitka` to execute Nuitka, avoiding the need to manually set `PYTHONPATH`.

## 6. Documentation & Conduct

- Refer to the [Nuitka Developer Manual](https://nuitka.net/doc/developer-manual.html) for detailed
  coding standards.
- Refer to the [Nuitka User Manual](https://nuitka.net/doc/user-manual.html) for usage context.
