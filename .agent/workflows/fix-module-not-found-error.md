<!--     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file -->

---
description: fix-module-not-found-error
---

# How to fix ModuleNotFoundError in Nuitka

This workflow guides you through resolving `ModuleNotFoundError` when running a Nuitka-compiled
binary, specifically caused by missing implicit dependencies (e.g., hidden imports in Cython
modules).

## 1. Reproduction and Analysis

1. **Isolate the error**: Create a minimal reproduction script (MRE) that triggers the
   `ModuleNotFoundError`.
2. **Verify the crash**: Run the MRE with Nuitka in standalone mode to confirm the error persists.
3. **Analyze the traceback**:
   - Identify the missing module name (e.g., `pandas._libs._cyutility`).
   - Identify the importer module (e.g., `pandas._libs.tslibs.ccalendar`).
   - *Note*: If the importer is a compiled extension (e.g., `.pyx`, `.so`, `.pyd`), Nuitka cannot
     automatically detect imports inside it.

## 2. Locate Configuration

1. **Find the configuration file**: Most package-specific configurations are in
   `nuitka/plugins/standard/standard.nuitka-package.config.yml`.
2. **Search for the package**: Look for the top-level package (e.g., `pandas`) or the specific
   submodule in the YAML file.

## 3. Implement the Fix

1. **Add Implicit Import**:

   - If the importer module already has an entry, add the missing module to its `implicit-imports`
     -> `depends` list.
   - If the importer module is missing, create a new entry for it.

   ```yaml
   - module-name: 'importer.module.name'
     implicit-imports:
       depends:
         - 'missing.module.name'
   ```

2. **Verify the fix**: Re-run the MRE compilation.

   - Ensure the `Nuitka-Plugins:implicit-imports` log shows the dependency being added (if verbose
     logging is enabled).
   - Run the compiled binary and confirm it executes without the `ModuleNotFoundError`.

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
