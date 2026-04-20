---
description: Create a Minimally Reproducible Example (MRE) from a larger file triggering a Nuitka bug.
---

# MRE Extraction Workflow

This workflow guides the process of reducing a source file to its absolute minimum while preserving
a specific bug (e.g., a compiler crash).

## 1. Setup and Verification

- **Identify the target file** to reduce. If this file is deep inside an installed library (e.g., in
  `site-packages`), **copy it to `tests/scratch/`** (e.g. `tests/scratch/MRE.py`) to avoid
  accidentally corrupting your Python environment during the destructive reduction process and to
  keep temporary reduction artifacts out of the repository root.
- **Identify the specific command** that triggers the issue if possible.
- **Augment the reproduction command** so it always writes
  `--report=tests/scratch/compilation-report.xml`. If the command already uses `--report=...`,
  redirect it to this path. Keep the rest of the invocation as close as possible to the original
  failure as you can.
- **Define the reproduction oracle** before reducing. For crash bugs, this can be the same exception
  type, the same failing statement location, or the same relevant `<exception>` entry in
  `tests/scratch/compilation-report.xml`. For non-crash bugs, this should be a specific preserved
  signal such as an output line, warning text, optimization message, exit code, or diff against
  expected output. The oracle does not need to be byte-for-byte identical output; it needs to
  reliably indicate that the same bug is still present. For example, an extra-pass bug may use
  `Module(s) '__main__' necessitate pass 3` as the oracle.
- **Run the reproduction command** to confirm the issue. If the crash occurs during a massive
  standalone build, it's highly recommended to pipe the output to a file
  (`> tests/scratch/out.txt 2>&1`) to easily search for the crash location while also inspecting
  `tests/scratch/compilation-report.xml`.

### Handling Standalone Optimization Crashes

If the crash happens during optimization in standalone mode (often a Python traceback below
`nuitka/optimizations`):

1. **Check the output** or `tests/scratch/out.txt` for lines starting with
   `Problem with statement at ...`, or inspect the `<exception>` tag in
   `tests/scratch/compilation-report.xml`.
2. **Identify the filename** involved.
3. **Copy that file to `tests/scratch/`** (e.g.
   `cp /path/to/ProblematicFile.py tests/scratch/MRE.py`).
4. **Run Nuitka in module mode** on that copied file (e.g.,
   `bin/nuitka --mode=module --generate-c-only --report=tests/scratch/compilation-report.xml tests/scratch/MRE.py`).
   Preserve the original failing invocation as closely as possible while reducing, while keeping the
   report output in `tests/scratch/`. *Note*: Use `--generate-c-only` to skip the C compilation
   phase, which is unnecessary if the crash occurs during Nuitka's optimization (Python) phase. This
   significantly speeds up the reduction cycle.
5. **If the oracle still matches**, specific reduction in module mode as described below is the best
   path forward.

## 2. Analysis

- Read the target file.
- Identify the core components suspected to be involved in the bug (e.g., specific imports like
  `ctypes`, specific Python constructs like classes or conditionals).

## 3. Iterative Reduction Loop

Repeat this process until the file is minimal:

1. **Propose a reduction**: Select a block of code to remove or simplify.
   - *Strategy 1*: Remove unused imports and helper functions.
   - *Strategy 2*: Mock external dependencies (e.g., replace `import other_package` with a dummy
     class/function) to allow removing the dependency.
   - *Strategy 3*: Simplify control flow (replace `if complex_condition:` with `if True:` or
     removing the branch entirely if possible, replace complex objects with simple ones).
   - *Strategy 4*: Rename long functions/variables to single letters (e.g., `original_name` -> `f`)
     once context is lost.
   - *Strategy 5*: For optimization issues, prioritize reducing the number of functions and methods.
     This is often crucial for isolating issues that occur during inter-procedural optimization or
     complex scope analysis.
   - *Strategy 6*: Remove default arguments from functions. This simplifies the function signature
     and can help isolate issues related to default value evaluation or parameter handling.
   - *Strategy 7*: **Structural and Scoping Mutations**. When dealing with compiler/optimization
     crashes, the bug is sometimes tied to the *shape* of the AST or variable scoping. Test subtle
     structural changes:
     - Replace attribute lookups in decorators (e.g., `@module.decorator`) with direct names
       (`@decorator`).
     - Remove or simplify `locals()` or `globals()` updates.
     - Simplify variable capturing in `lambda` functions, especially inside list/dict
       comprehensions.
     - Replace generator expressions with equivalent `for` loops to see if the implicit function
       scope is the trigger.
   - *Consider Simplification*: Don't assume the entire block must be removed.
     - Replace complex expressions with constants/literals.
     - Replace variable usage with direct values.
     - Replace function bodies with `pass` or a simple valid statement.
   - *Avoid Confounding Variables*: Ensure you are changing only one thing at a time. (e.g., don't
     remove an import *and* a global assignment in one step).
2. **Apply the change**.
3. **Run the reproduction command** and re-check the same reproduction oracle.
4. **Evaluate result**:
   - **If the oracle still matches**: Great! The removed code was irrelevant.

   - **If the oracle no longer matches, disappears, or becomes ambiguous**: The removed code was
     relevant. **IMMEDIATELY REVERT** the change to the scratch copy only. Never reset unrelated
     repository changes.

   - **Validation**:

     - *Maximize Reduction*: Even if you think a construct (like a function or loop) is needed, try
       to remove it or flatten it to verify.
     - *Renaming*: Always rename functions, variables, and classes to single short letters (e.g.,
       `f`, `x`, `C`) to remove semantic meaning and ensure no special string-based handling is at
       play.

## 4. Final Polish

- Ensure the code is self-contained (no external requirements beyond standard library if possible).
- Format clean.
- Verify one last time.

## 5. Report

- Present the final MRE code block to the user.
