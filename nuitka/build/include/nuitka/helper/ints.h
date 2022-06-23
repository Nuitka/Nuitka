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
#ifndef __NUITKA_HELPER_INTS_H__
#define __NUITKA_HELPER_INTS_H__

typedef enum {
    NUITKA_INT_UNASSIGNED = 0,
    NUITKA_INT_OBJECT_VALID = 1,
    NUITKA_INT_VALUE_VALID = 2,
    NUITKA_INT_BOTH_VALID = 3
} nuitka_int_validity;

typedef struct {
    nuitka_int_validity validity;

    PyObject *int_object;
    long int_value;
} nuitka_int;

typedef enum {
    NUITKA_LONG_UNASSIGNED = 0,
    NUITKA_LONG_OBJECT_VALID = 1,
    NUITKA_LONG_VALUE_VALID = 2,
    NUITKA_LONG_BOTH_VALID = 3
} nuitka_long_validity;

typedef struct {
    nuitka_long_validity validity;

    PyObject *long_object;
    long long_value;
} nuitka_long;

#if PYTHON_VERSION < 0x300
typedef enum {
    NUITKA_ILONG_UNASSIGNED = 0,
    NUITKA_ILONG_OBJECT_VALID = 1,
    NUITKA_ILONG_VALUE_VALID = 2,
    NUITKA_ILONG_BOTH_VALID = 3
} nuitka_ilong_validity;

typedef struct {
    nuitka_ilong_validity validity;

    PyObject *ilong_object;
    long ilong_value;
} nuitka_ilong;

NUITKA_MAY_BE_UNUSED static void ENFORCE_ILONG_OBJECT_VALUE(nuitka_ilong *value) {
    assert(value->validity != NUITKA_ILONG_UNASSIGNED);

    if ((value->validity & NUITKA_ILONG_OBJECT_VALID) == 0) {
        value->ilong_object = PyLong_FromLong(value->ilong_value);

        value->validity = NUITKA_ILONG_BOTH_VALID;
    }
}

#endif

#define NUITKA_STATIC_SMALLINT_VALUE_MIN -5
#define NUITKA_STATIC_SMALLINT_VALUE_MAX 257

#define NUITKA_TO_SMALL_VALUE_OFFSET(value) (value - NUITKA_STATIC_SMALLINT_VALUE_MIN)

extern PyObject *Nuitka_Long_SmallValues[NUITKA_STATIC_SMALLINT_VALUE_MAX - NUITKA_STATIC_SMALLINT_VALUE_MIN + 1];

#endif
