//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_TYPE_ALIASES_H__
#define __NUITKA_TYPE_ALIASES_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Helpers for type aliases, type variables, and generic base classes.
extern PyObject *MAKE_TYPE_ALIAS(PyObject *name, PyObject *type_params, PyObject *compute_value);
extern PyObject *MAKE_TYPE_VAR(PyThreadState *tstate, PyObject *name);
extern PyObject *MAKE_TYPE_GENERIC(PyThreadState *tstate, PyObject *params);

#endif
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
