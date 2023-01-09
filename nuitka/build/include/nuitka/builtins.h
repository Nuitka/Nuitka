//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
//
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
//
#ifndef __NUITKA_BUILTINS_H__
#define __NUITKA_BUILTINS_H__

extern PyModuleObject *builtin_module;
extern PyDictObject *dict_builtin;

#include "nuitka/calling.h"

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_BUILTIN(PyObject *name) {
    CHECK_OBJECT(dict_builtin);
    CHECK_OBJECT(name);
    assert(Nuitka_String_CheckExact(name));

    PyObject *result = GET_STRING_DICT_VALUE(dict_builtin, (Nuitka_StringObject *)name);

    // This is assumed to not fail, abort if it does.
    if (unlikely(result == NULL)) {
        PyErr_PrintEx(0);
        Py_Exit(1);
    }

    CHECK_OBJECT(result);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_BUILTIN_STR(char const *name) {
    CHECK_OBJECT(dict_builtin);

    PyObject *result = PyDict_GetItemString((PyObject *)dict_builtin, name);

    // This is assumed to not fail, abort if it does.
    if (unlikely(result == NULL)) {
        PyErr_PrintEx(0);
        Py_Exit(1);
    }

    CHECK_OBJECT(result);

    return result;
}

extern void _initBuiltinModule(void);

#define NUITKA_DECLARE_BUILTIN(name) extern PyObject *_python_original_builtin_value_##name;
#define NUITKA_DEFINE_BUILTIN(name) PyObject *_python_original_builtin_value_##name = NULL;
#define NUITKA_ASSIGN_BUILTIN(name)                                                                                    \
    if (_python_original_builtin_value_##name == NULL)                                                                 \
        _python_original_builtin_value_##name = LOOKUP_BUILTIN_STR(#name);
#define NUITKA_UPDATE_BUILTIN(name, value) _python_original_builtin_value_##name = value;
#define NUITKA_ACCESS_BUILTIN(name) (_python_original_builtin_value_##name)

#ifdef _NUITKA_EXE
// Original builtin values, currently only used for assertions.
NUITKA_DECLARE_BUILTIN(type);
NUITKA_DECLARE_BUILTIN(len);
NUITKA_DECLARE_BUILTIN(range);
NUITKA_DECLARE_BUILTIN(repr);
NUITKA_DECLARE_BUILTIN(int);
NUITKA_DECLARE_BUILTIN(iter);
#if PYTHON_VERSION < 0x300
NUITKA_DECLARE_BUILTIN(long);
#endif

extern void _initBuiltinOriginalValues(void);
#endif

// Avoid the casts needed for older Python, as it's easily forgotten and
// potentially have our own better implementation later. Gives no reference.
// TODO: Can do it ourselves once DICT_GET_ITEM_WITH_ERROR becomes available.
NUITKA_MAY_BE_UNUSED static PyObject *Nuitka_SysGetObject(char const *name) { return PySys_GetObject((char *)name); }

NUITKA_MAY_BE_UNUSED static void Nuitka_SysSetObject(char const *name, PyObject *value) {
    // TODO: Check error in debug mode at least.
    PySys_SetObject((char *)name, value);
}

#endif
