<!--     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file -->

---
description: Create a Minimally Reproducible Example (MRE) from a larger file triggering
  a Nuitka bug.
---

# MRE Extraction Workflow

This workflow guides the process of reducing a source file to its absolute minimum while preserving
a specific bug (e.g., a compiler crash).

## 1. Setup and Verification

- **Identify the target file** to reduce.
- **Identify the specific command** that triggers the issue (e.g., `python bin/nuitka Target.py`).
- **Run the reproduction command** immediately to confirm the issue exists and capture the exact
  error message/output.

### Handling Standalone Optimization Crashes

If the crash happens during optimization in standalone mode (often a Python traceback below
`nuitka/optimizations`:

1. **Check the output** for lines starting with `Problem with statement at ...`.
2. **Identify the filename** mentioned in the next line.
3. **Run Nuitka in module mode** on that specific file (e.g.,
   `python bin/nuitka --mode=module path/to/ProblematicFile.py`).
4. **If the crash reproduces**, specific reduction in module mode as described below is the best
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
   - *Consider Simplification*: Don't assume the entire block must be removed.
     - Replace complex expressions with constants/literals.
     - Replace variable usage with direct values.
     - Replace function bodies with `pass` or a simple valid statement.
   - *Avoid Confounding Variables*: Ensure you are changing only one thing at a time. (e.g., don't
     remove an import *and* a global assignment in one step).
2. **Apply the change**.
3. **Run the reproduction command**.
4. **Evaluate result**:
   - **If the exact same error persists**: Great! The removed code was irrelevant.

   - **If the error disappears or changes**: The removed code was relevant. **IMMEDIATELY REVERT**
     the change.

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

<!--     Part of "Nuitka", an optimizing Python compiler that is compatible and -->
<!--     integrates with CPython, but also works on its own. -->
<!-- -->
<!--     Licensed under the GNU Affero General Public License, Version 3 (the "License"); -->
<!--     you may not use this file except in compliance with the License. -->
<!--     You may obtain a copy of the License at -->
<!-- -->
<!--        http://www.gnu.org/licenses/agpl.txt -->
<!-- -->
<!--     Unless required by applicable law or agreed to in writing, software -->
<!--     distributed under the License is distributed on an "AS IS" BASIS, -->
<!--     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. -->
<!--     See the License for the specific language governing permissions and -->
<!--     limitations under the License. -->
