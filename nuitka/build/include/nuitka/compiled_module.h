//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#pragma once
#ifndef __NUITKA_COMPILED_MODULE_H__
#define __NUITKA_COMPILED_MODULE_H__

#ifdef __IDE_ONLY__
#include "nuitka/cpython_api_compat.h"

#if PYTHON_VERSION >= 0x3a0
#include "internal/pycore_moduleobject.h"
#endif
#endif

// Since 3.10 the module object is hidden.
#if PYTHON_VERSION < 0x3a0
typedef struct {
    PyObject_HEAD PyObject *md_dict;
    struct PyModuleDef *md_def;
    void *md_state;
    PyObject *md_weaklist;
    PyObject *md_name;
} CPythonPyModuleObject;
#else
#define CPythonPyModuleObject PyModuleObject
#endif

struct Nuitka_ModuleObject {
    CPythonPyModuleObject m_module;
};

extern PyTypeObject Nuitka_Module_Type;

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
