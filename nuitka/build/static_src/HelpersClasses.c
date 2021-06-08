//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
/** For creating classes.
 *
 * Currently only the Python3 meta class selection is here, but more will be
 * added later, should be choose to have our own "__slots__" special metaclass.
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION >= 0x300
PyObject *SELECT_METACLASS(PyObject *metaclass, PyObject *bases) {
    CHECK_OBJECT(metaclass);
    CHECK_OBJECT(bases);

    if (likely(PyType_Check(metaclass))) {
        // Determine the proper metaclass type
        Py_ssize_t nbases = PyTuple_GET_SIZE(bases);
        PyTypeObject *winner = (PyTypeObject *)metaclass;

#if _DEBUG_CLASSES
        PRINT_STRING("Bases:");
        PRINT_ITEM((PyObject *)bases);
        PRINT_NEW_LINE();
#endif

        for (int i = 0; i < nbases; i++) {
            PyObject *base = PyTuple_GET_ITEM(bases, i);

            PyTypeObject *base_type = Py_TYPE(base);

            if (PyType_IsSubtype(winner, base_type)) {
                // Ignore if current winner is already a subtype.
                continue;
            } else if (PyType_IsSubtype(base_type, winner)) {
                // Use if, if it's a subtype of the current winner.
                winner = base_type;
                continue;
            } else {
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError,
                                                "metaclass conflict: the metaclass of a derived class must be a "
                                                "(non-strict) subclass of the metaclasses of all its bases");

                return NULL;
            }
        }

        if (unlikely(winner == NULL)) {
            return NULL;
        }

#if _DEBUG_CLASSES
        PRINT_STRING("Metaclass winner:");
        PRINT_ITEM((PyObject *)winner);
        PRINT_NEW_LINE();
#endif

        Py_INCREF(winner);
        return (PyObject *)winner;
    } else {
#if _DEBUG_CLASSES
        PRINT_STRING("Metaclass not a type is used:");
        PRINT_ITEM((PyObject *)metaclass);
        PRINT_NEW_LINE();
#endif

        Py_INCREF(metaclass);
        return metaclass;
    }
}
#endif
