//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_INTS_H__
#define __NUITKA_HELPER_INTS_H__

// Our "PyLong_FromLong" replacement.
extern PyObject *Nuitka_PyLong_FromLong(long ival);

// Our "PyInt_FromLong" replacement, not done (yet?).
#if PYTHON_VERSION >= 0x300
#define Nuitka_PyInt_FromLong(ival) Nuitka_PyLong_FromLong(ival)
#else
#define Nuitka_PyInt_FromLong(ival) PyInt_FromLong(ival)
#endif

// We are using this mixed type for both Python2 and Python3, since then we
// avoid the complexity of overflowed integers for Python2 to switch over.

typedef enum {
    NUITKA_ILONG_UNASSIGNED = 0,
    NUITKA_ILONG_OBJECT_VALID = 1,
    NUITKA_ILONG_CLONG_VALID = 2,
    NUITKA_ILONG_BOTH_VALID = 3,
    NUITKA_ILONG_EXCEPTION = 4
} nuitka_ilong_validity;

typedef struct {
    nuitka_ilong_validity validity;

    PyObject *python_value;
    long c_value;
} nuitka_ilong;

#define IS_NILONG_OBJECT_VALUE_VALID(value) (((value)->validity & NUITKA_ILONG_OBJECT_VALID) != 0)
#define IS_NILONG_C_VALUE_VALID(value) (((value)->validity & NUITKA_ILONG_CLONG_VALID) != 0)

NUITKA_MAY_BE_UNUSED static void SET_NILONG_OBJECT_VALUE(nuitka_ilong *dual_value, PyObject *python_value) {
    dual_value->validity = NUITKA_ILONG_OBJECT_VALID;
    dual_value->python_value = python_value;
}

NUITKA_MAY_BE_UNUSED static void SET_NILONG_C_VALUE(nuitka_ilong *dual_value, long c_value) {
    dual_value->validity = NUITKA_ILONG_CLONG_VALID;
    dual_value->c_value = c_value;
}

NUITKA_MAY_BE_UNUSED static void SET_NILONG_OBJECT_AND_C_VALUE(nuitka_ilong *dual_value, PyObject *python_value,
                                                               long c_value) {
    dual_value->validity = NUITKA_ILONG_BOTH_VALID;
    dual_value->python_value = python_value;
    dual_value->c_value = c_value;
}

NUITKA_MAY_BE_UNUSED static void RELEASE_NILONG_VALUE(nuitka_ilong *dual_value) {
    if (IS_NILONG_OBJECT_VALUE_VALID(dual_value)) {
        CHECK_OBJECT(dual_value);
        Py_DECREF(dual_value->python_value);
    }

    dual_value->validity = NUITKA_ILONG_UNASSIGNED;
}

NUITKA_MAY_BE_UNUSED static void INCREF_NILONG_VALUE(nuitka_ilong *dual_value) {
    if (IS_NILONG_OBJECT_VALUE_VALID(dual_value)) {
        CHECK_OBJECT(dual_value);
        Py_INCREF(dual_value->python_value);
    }
}

NUITKA_MAY_BE_UNUSED static long GET_NILONG_C_VALUE(nuitka_ilong const *dual_value) {
    assert(IS_NILONG_C_VALUE_VALID(dual_value));
    return dual_value->c_value;
}

NUITKA_MAY_BE_UNUSED static PyObject *GET_NILONG_OBJECT_VALUE(nuitka_ilong const *dual_value) {
    assert(IS_NILONG_OBJECT_VALUE_VALID(dual_value));
    return dual_value->python_value;
}

NUITKA_MAY_BE_UNUSED static void ENFORCE_NILONG_OBJECT_VALUE(nuitka_ilong *dual_value) {
    assert(dual_value->validity != NUITKA_ILONG_UNASSIGNED);

    if (!IS_NILONG_OBJECT_VALUE_VALID(dual_value)) {
        dual_value->python_value = Nuitka_PyLong_FromLong(dual_value->c_value);

        dual_value->validity = NUITKA_ILONG_BOTH_VALID;
    }
}

NUITKA_MAY_BE_UNUSED static void CHECK_NILONG_OBJECT(nuitka_ilong const *dual_value) {
    assert(dual_value->validity != NUITKA_ILONG_UNASSIGNED);

    if (IS_NILONG_OBJECT_VALUE_VALID(dual_value)) {
        CHECK_OBJECT(dual_value);
    }
}

NUITKA_MAY_BE_UNUSED static void PRINT_NILONG(nuitka_ilong const *dual_value) {
    PRINT_FORMAT("NILONG: %d", dual_value->validity);
    if (IS_NILONG_C_VALUE_VALID(dual_value)) {
        PRINT_FORMAT("C=%d", dual_value->c_value);
    }
    if (IS_NILONG_OBJECT_VALUE_VALID(dual_value)) {
        PRINT_STRING("Python=");
        PRINT_ITEM(dual_value->python_value);
    }
}

#if PYTHON_VERSION < 0x3c0
// Convert single digit to sdigit (int32_t),
// spell-checker: ignore sdigit,stwodigits
typedef long medium_result_value_t;
#define MEDIUM_VALUE(x)                                                                                                \
    (Py_SIZE(x) < 0 ? -(sdigit)((PyLongObject *)(x))->ob_digit[0]                                                      \
                    : (Py_SIZE(x) == 0 ? (sdigit)0 : (sdigit)((PyLongObject *)(x))->ob_digit[0]))

#else
typedef stwodigits medium_result_value_t;
#define MEDIUM_VALUE(x) ((stwodigits)_PyLong_CompactValue((PyLongObject *)x))

#endif

// TODO: Use this from header files, although they have changed.
#define NUITKA_STATIC_SMALLINT_VALUE_MIN -5
#define NUITKA_STATIC_SMALLINT_VALUE_MAX 257

#define NUITKA_TO_SMALL_VALUE_OFFSET(value) (value - NUITKA_STATIC_SMALLINT_VALUE_MIN)

#if PYTHON_VERSION < 0x3b0

#if PYTHON_VERSION >= 0x300

#if PYTHON_VERSION >= 0x390
extern PyObject **Nuitka_Long_SmallValues;
#else
extern PyObject *Nuitka_Long_SmallValues[NUITKA_STATIC_SMALLINT_VALUE_MAX - NUITKA_STATIC_SMALLINT_VALUE_MIN + 1];
#endif

NUITKA_MAY_BE_UNUSED static inline PyObject *Nuitka_Long_GetSmallValue(int ival) {
    return Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(ival)];
}

#endif

#else
NUITKA_MAY_BE_UNUSED static inline PyObject *Nuitka_Long_GetSmallValue(medium_result_value_t ival) {
    return (PyObject *)&_PyLong_SMALL_INTS[NUITKA_TO_SMALL_VALUE_OFFSET(ival)];
}
#endif

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
