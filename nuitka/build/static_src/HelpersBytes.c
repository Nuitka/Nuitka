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
/* This helpers is used to quickly create a bytes objects.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION >= 0x300

// Custom allocation to save bytes at the end.
#define PyBytesObject_SIZE (offsetof(PyBytesObject, ob_sval) + 1)

#if NUITKA_BYTES_HAS_FREELIST
static struct _Py_bytes_state *Nuitka_Py_get_bytes_state(void) {
    PyInterpreterState *interp = _PyInterpreterState_GET();
    return &interp->bytes;
}

PyObject *Nuitka_Bytes_FromStringAndSize(const char *data, Py_ssize_t size) {
    assert(size >= 0);
    PyBytesObject *op;

    // For Python3.10 we can use the internal cache.
    if (size == 1) {
        struct _Py_bytes_state *state = Nuitka_Py_get_bytes_state();

        op = state->characters[*data & UCHAR_MAX];

        if (op != NULL) {
            Py_INCREF(op);
            return (PyObject *)op;
        }
    }

    if (size == 0) {
        struct _Py_bytes_state *state = Nuitka_Py_get_bytes_state();

        assert(state->empty_string != NULL);
        Py_INCREF(state->empty_string);

        return state->empty_string;
    }

    op = (PyBytesObject *)PyObject_Malloc(PyBytesObject_SIZE + size);

    Py_SIZE(op) = size;
    Py_SET_TYPE(op, &PyBytes_Type);

    Nuitka_Py_NewReference((PyObject *)op);

    op->ob_shash = -1;
    memcpy(op->ob_sval, data, size);
    op->ob_sval[size] = '\0';

    if (size == 1) {
        struct _Py_bytes_state *state = Nuitka_Py_get_bytes_state();
        Py_INCREF(op);
        state->characters[*data & UCHAR_MAX] = op;
    }

    return (PyObject *)op;
}

#endif

#endif