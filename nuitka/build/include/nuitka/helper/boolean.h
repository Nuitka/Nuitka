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
#ifndef __NUITKA_HELPER_BOOLEAN_H__
#define __NUITKA_HELPER_BOOLEAN_H__

// The slot in Python3 got renamed, compensate it like this.
#if PYTHON_VERSION >= 0x300
#define nb_nonzero nb_bool
#endif

NUITKA_MAY_BE_UNUSED static int CHECK_IF_TRUE(PyObject *object) {
    CHECK_OBJECT(object);

    if (object == Py_True) {
        return 1;
    } else if (object == Py_False || object == Py_None) {
        return 0;
    } else {
        Py_ssize_t result;

        if (Py_TYPE(object)->tp_as_number != NULL && Py_TYPE(object)->tp_as_number->nb_nonzero != NULL) {
            result = (*Py_TYPE(object)->tp_as_number->nb_nonzero)(object);
        } else if (Py_TYPE(object)->tp_as_mapping != NULL && Py_TYPE(object)->tp_as_mapping->mp_length != NULL) {
            result = (*Py_TYPE(object)->tp_as_mapping->mp_length)(object);
        } else if (Py_TYPE(object)->tp_as_sequence != NULL && Py_TYPE(object)->tp_as_sequence->sq_length != NULL) {
            result = (*Py_TYPE(object)->tp_as_sequence->sq_length)(object);
        } else {
            return 1;
        }

        if (result > 0) {
            return 1;
        } else if (result == 0) {
            return 0;
        } else {
            return -1;
        }
    }
}

NUITKA_MAY_BE_UNUSED static int CHECK_IF_FALSE(PyObject *object) {
    int result = CHECK_IF_TRUE(object);

    if (result == 0) {
        return 1;
    }
    if (result == 1) {
        return 0;
    }
    return -1;
}

NUITKA_MAY_BE_UNUSED static inline PyObject *BOOL_FROM(bool value) {
    CHECK_OBJECT(Py_True);
    CHECK_OBJECT(Py_False);

    return value ? Py_True : Py_False;
}

#undef nb_nonzero

typedef enum {
    NUITKA_BOOL_FALSE = 0,
    NUITKA_BOOL_TRUE = 1,
    NUITKA_BOOL_UNASSIGNED = 2,
    NUITKA_BOOL_EXCEPTION = -1
} nuitka_bool;

typedef enum { NUITKA_VOID_OK = 0, NUITKA_VOID_EXCEPTION = 1 } nuitka_void;

#endif
