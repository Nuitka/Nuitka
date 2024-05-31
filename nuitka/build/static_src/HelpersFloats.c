//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* These helpers are used to work with float values.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *TO_FLOAT(PyObject *value) {
    PyObject *result;

#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(value)) {
        result = PyFloat_FromString(value, NULL);
    }
#else
    if (PyUnicode_CheckExact(value)) {
        result = PyFloat_FromString(value);
    }
#endif
    else {
        result = PyNumber_Float(value);
    }

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

#if NUITKA_FLOAT_HAS_FREELIST

static PyFloatObject *_Nuitka_AllocatePyFloatObject(PyThreadState *tstate) {
    // This is the CPython name, spell-checker: ignore numfree

#if PYTHON_VERSION < 0x3d0
    struct _Py_float_state *state = &tstate->interp->float_state;
    PyFloatObject **free_list = &state->free_list;
    int *numfree = &state->numfree;
#else
    struct _Py_object_freelists *freelists = _Nuitka_object_freelists_GET(tstate);
    struct _Py_float_freelist *state = &freelists->floats;
    PyFloatObject **free_list = &state->items;
    int *numfree = &state->numfree;
#endif
    PyFloatObject *result_float = *free_list;

    if (result_float) {
        (*numfree) -= 1;
        *free_list = (PyFloatObject *)Py_TYPE(result_float);
    } else {
        result_float = (PyFloatObject *)NuitkaObject_Malloc(sizeof(PyFloatObject));
    }

    Py_SET_TYPE(result_float, &PyFloat_Type);
    Nuitka_Py_NewReference((PyObject *)result_float);

    assert(result_float != NULL);

    return result_float;
}

PyObject *MAKE_FLOAT_FROM_DOUBLE(double value) {
    PyThreadState *tstate = PyThreadState_GET();

    PyFloatObject *result = _Nuitka_AllocatePyFloatObject(tstate);

    PyFloat_SET_DOUBLE(result, value);
    return (PyObject *)result;
}

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
