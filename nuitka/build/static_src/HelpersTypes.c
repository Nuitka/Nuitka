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
// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// Our replacement for "PyType_IsSubtype"
bool Nuitka_Type_IsSubtype(PyTypeObject *a, PyTypeObject *b) {
    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

#if PYTHON_VERSION < 0x300
    if (!(a->tp_flags & Py_TPFLAGS_HAVE_CLASS)) {
        return b == a || b == &PyBaseObject_Type;
    }
#endif

    PyObject *mro = a->tp_mro;
    CHECK_OBJECT_X(mro);

    if (likely(mro != NULL)) {
        assert(PyTuple_Check(mro));

        Py_ssize_t n = PyTuple_GET_SIZE(mro);

        for (Py_ssize_t i = 0; i < n; i++) {
            if (PyTuple_GET_ITEM(mro, i) == (PyObject *)b) {
                return true;
            }
        }

        return false;
    } else {
        // Fallback for uninitialized classes to API usage
        return PyType_IsSubtype(a, b) != 0;
    }
}