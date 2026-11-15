---
trigger: always_on
description: Formatting, static analysis, verification matrix, and execution workflow for Nuitka.
---

# Code Quality & Workflow

## Code Quality & Verification

### Fast Inner-Loop Checks (During Iteration)

While iterating across multiple edits, avoid re-running full `--un-pushed` `pylint` after every
small edit (especially on branches with many unpushed commits). Instead, use fast targeted checks on
the touched files during iteration:

- **Python checks:** Run `./bin/check-nuitka-with-pylint <file.py>` on just the edited file (and,
  when installed, `./bin/check-nuitka-with-ruff <file.py>` or
  `./bin/check-nuitka-with-pyright <file.py>`; use `.cmd` on Windows).
- **C static checks:** `./bin/check-nuitka-with-clangd --assume-yes-for-downloads <file.c>` (on
  Windows: `.\bin\check-nuitka-with-clangd.cmd ...`). Requires `.clangd` in the checkout root; run
  `python misc/vscode_config_gen.py` once if missing (e.g., in a fresh worktree).
- **Spellcheck & comment directives:** Run `./bin/check-nuitka-with-codespell <file>` (on Windows:
  `.\bin\check-nuitka-with-codespell.cmd <file>`) whenever adding, editing, or deleting comments,
  docstrings, or string literals (`codespell` fails if deleting a comment leaves an unused word in
  `# spell-checker: ignore`).

### Mandatory Final Verification Gate

Before marking a task as complete, you **must** run the repository-wide `--un-pushed` checks once at
the end, in this order:

1. **Auto-Formatting:** Apply auto-formatting to any file you touch (Python, C, YAML, RST, MD,
   JSON).

   - Command: `./bin/autoformat-nuitka-source --un-pushed --assume-yes-for-downloads`
   - On Windows, use `.\bin\autoformat-nuitka-source.cmd --un-pushed --assume-yes-for-downloads`
     instead.
   - For the final gate, prefer this exact repo-root `--un-pushed` command rather than file-specific
     arguments unless the user explicitly asks to narrow it.
   - Can be run on the entire project with
     `./bin/autoformat-nuitka-source --assume-yes-for-downloads`.
   - This script applies `black` (plus Python 2 fixups), `isort`, `clang-format`, `mdformat`, and
     YAML schema/formatting checks.
   - On Windows, if a `.cmd` launcher fails with "Python not found", run
     `{Python.exe} misc\vscode_config_gen.py` first to generate `.vscode\.python_alias_path` and
     `.clangd`.

2. **Linting:** Run the project's pylint script after auto-formatting.

   - Command: `./bin/check-nuitka-with-pylint --un-pushed`
   - On Windows, use `.\bin\check-nuitka-with-pylint.cmd --un-pushed` instead.
   - For the final gate, prefer this exact repo-root `--un-pushed` command rather than file-specific
     arguments unless the user explicitly asks to narrow it.
   - Can be run on the entire project with `./bin/check-nuitka-with-pylint`.
   - *Constraint:* If pylint fails, fix the errors before asking for review. Do not suppress
     warnings without a very strong reason.

3. **Spellcheck & Comment Hygiene:** Run `codespell` and verify comment discipline on touched
   scopes.

   - Command: `./bin/check-nuitka-with-codespell --un-pushed` (on Windows:
     `.\bin\check-nuitka-with-codespell.cmd --un-pushed`).
   - Remove any `# spell-checker: ignore` words made unused by comment or docstring edits.
   - Confirm touched functions, classes, and templates contain no code-restating comments, no
     cross-code condition speculation, and no stale copy-pasted comments or docstrings (per
     [`.agents/rules/coding-standards.md`](./coding-standards.md)).

### Change-Type Verification Matrix

Always run the mandatory auto-formatting and pylint gate, plus focused verification for the changed
area:

| Change type           | Additional verification                                                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python change         | Run the affected test, reproducer, or nearest repository test through `bin/nuitka`.                                                                           |
| C change              | Run `check-nuitka-with-clangd --un-pushed --assume-yes-for-downloads` and compile/run a representative program exercising the changed helper or runtime path. |
| Package config change | Build a standalone MRE for the affected package and confirm the compiled binary imports/runs correctly.                                                       |
| SCons change          | Run `bin/nuitka --version` and exercise `tests/basics/AssertsTest.py` in the relevant compilation modes.                                                      |
| Release/OBS issue     | Fetch the raw OBS/build log, identify the terminal failure, and verify the changed release tooling path.                                                      |
| CPython-suite change  | Use the matching `tests/CPython*` submodule workflow and run the changed CPython comparison test.                                                             |

- **Temporary Verification Files:**

  - All temporary test scripts, reproduction scripts, and their artifacts created during
    verification MUST be placed in `tests/scratch/`.
  - This directory is git-ignored and ensures the repository remains clean.

## Workflow

- **Bugs & Implementation:**

  - When fixing bugs in C code, analyze the specific Nuitka internal C-API usage. Often Python C-API
    has safer or more optimized replacements in Nuitka.
  - Calls to Python C-API are slow and generally avoided in Nuitka where we can.
  - For file operations, prefer functions in `nuitka.utils.FileOperations` and add them if missing.

- **Tests:**

  - On Windows, ensure a suitable Python version is installed (e.g.,
    `~/AppData/Local/Programs/Python/Python313`, or check `.vscode/.python_alias_path`).
  - Under WSL, the Windows host installs are runnable directly through `/mnt/c`, e.g.
    `/mnt/c/Python27/python.exe` for Python 2.7 and `/mnt/c/Python26/python.exe` for Python 2.6;
    those binaries cannot open `/home/...` paths, so copy scratch files to `/mnt/c/tmp` first.
    Prompt the user to install if missing a suitable version.
  - When you only need to vary Nuitka command line flags for an existing repository test case,
    prefer reusing it via `NUITKA_EXTRA_OPTIONS`.
  - For **scons** level changes:
    - Run `bin/nuitka --version` to check basic sanity.
    - Compile `tests/basics/AssertsTest.py` to verify correctness.
    - Exercise modes: `--mode=accelerated`, `--mode=standalone`, `--mode=module`, `--mode=onefile`.
    - Verify that output with `--run` matches the direct Python execution.

- **Execution:**

  - Use `bin/nuitka` to execute Nuitka, avoiding the need to manually set `PYTHONPATH`.
  - On Windows (`cmd` or PowerShell), `bin/nuitka` has no file extension and cannot be executed
    bare; always invoke `<python> bin\nuitka ...` (using `python` or the interpreter path in
    `.vscode\.python_alias_path`).
  - Do not disable ccache or clache by default; they are expected to invalidate correctly, and
    bypassing them is not a general-purpose fix.
  - If a ccache or clache issue is suspected, stop and prompt the user before disabling or clearing
    the cache, including the observed evidence and exact command.

## Documentation & Conduct

- Refer to [`Developer_Manual.rst`](../../Developer_Manual.rst) for detailed coding standards.
- Refer to [`README.rst`](../../README.rst) for User Manual and usage context.
