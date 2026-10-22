//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#define NO_PYTHON_WARNINGS 1
#endif

#include "nuitka/tracing.h"

// No longer in header files, but still usable.
#if PYTHON_VERSION >= 0x3d0
PyAPI_FUNC(void) PySys_AddWarnOption(const wchar_t *s);
#endif
#if PYTHON_VERSION >= 0x3f0
PyAPI_FUNC(void) PySys_ResetWarnOptions(void);
#endif

#if NO_PYTHON_WARNINGS

// Setup the disabling of Python warnings early, before the interpreter is
// initialized. Starting with Python 3.13 the interpreter imports the
// "warnings" module during start-up when options are set, which cannot work
// before the meta path based loader is setup, so for that version it is
// deferred to "setupWarningsLate" instead.
void setupWarningsEarly(void) {
#if PYTHON_VERSION < 0x3d0
    NUITKA_PRINT_TRACE("main(): Disabling Python warnings.");

#if PYTHON_VERSION >= 0x300
    wchar_t ignore[] = L"ignore";
#else
    char ignore[] = "ignore";
#endif

    PySys_ResetWarnOptions();
    PySys_AddWarnOption(ignore);
#endif
}

// Setup the disabling of Python warnings late, after the meta path based
// loader is setup, where the "warnings" module can be imported. The options
// are applied when the module gets imported on demand, so this must happen
// before anything imports it.
void setupWarningsLate(PyThreadState *tstate) {
#if PYTHON_VERSION >= 0x3d0
    NUITKA_PRINT_TRACE("main(): Disabling Python warnings.");

    PySys_ResetWarnOptions();
    PySys_AddWarnOption(L"ignore");
#endif

#if PYTHON_VERSION >= 0x342 && PYTHON_VERSION < 0x3a0 && defined(_NUITKA_FULL_COMPAT)
    // For full compatibility bump the warnings registry version, otherwise
    // modules "__warningregistry__" will mismatch.
    PyObject *warnings_module = PyImport_ImportModule("warnings");
    PyObject *meth = PyObject_GetAttrString(warnings_module, "_filters_mutated");

    CALL_FUNCTION_NO_ARGS(tstate, meth);
#if PYTHON_VERSION < 0x380
    // Two times, so "__warningregistry__" version matches.
    CALL_FUNCTION_NO_ARGS(tstate, meth);
#endif
#endif
}

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
