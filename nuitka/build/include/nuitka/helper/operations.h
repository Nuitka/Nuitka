//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_OPERATIONS_H__
#define __NUITKA_OPERATIONS_H__

#if PYTHON_VERSION >= 300
extern PyObject *UNICODE_CONCAT(PyObject *left, PyObject *right);
extern bool UNICODE_APPEND(PyObject **p_left, PyObject *right);
#else
// TODO: Specialize for Python2 too.
NUITKA_MAY_BE_UNUSED static PyObject *UNICODE_CONCAT(PyObject *left, PyObject *right) {
    return PyUnicode_Concat(left, right);
}
#endif

// This macro is necessary for Python2 to determine if the "coerce" slot
// will have to be considered or not.
#if PYTHON_VERSION < 300
#define NEW_STYLE_NUMBER(o) PyType_HasFeature(Py_TYPE(o), Py_TPFLAGS_CHECKTYPES)
#define NEW_STYLE_NUMBER_TYPE(t) PyType_HasFeature(t, Py_TPFLAGS_CHECKTYPES)
#else
#define NEW_STYLE_NUMBER(o) (true)
#define NEW_STYLE_NUMBER_TYPE(t) (true)
#endif

typedef PyObject *(unary_api)(PyObject *);

NUITKA_MAY_BE_UNUSED static PyObject *UNARY_OPERATION(unary_api api, PyObject *operand) {
    CHECK_OBJECT(operand);
    PyObject *result = api(operand);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(result);

    return result;
}

typedef PyObject *(binary_api)(PyObject *, PyObject *);

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION(binary_api api, PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

    PyObject *result = api(operand1, operand2);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

// Generated helpers to execute operations on fully or partially known types.
#include "nuitka/helper/operations_binary_add.h"
#include "nuitka/helper/operations_binary_bitand.h"
#include "nuitka/helper/operations_binary_bitor.h"
#include "nuitka/helper/operations_binary_bitxor.h"
#include "nuitka/helper/operations_binary_floordiv.h"
#include "nuitka/helper/operations_binary_lshift.h"
#include "nuitka/helper/operations_binary_mod.h"
#include "nuitka/helper/operations_binary_mul.h"
#include "nuitka/helper/operations_binary_pow.h"
#include "nuitka/helper/operations_binary_rshift.h"
#include "nuitka/helper/operations_binary_sub.h"
#include "nuitka/helper/operations_binary_truediv.h"

#if PYTHON_VERSION < 300
// Classical division is Python2 only.
#include "nuitka/helper/operations_binary_olddiv.h"
#endif

#if PYTHON_VERSION >= 350
// Matrix multiplication is Python3.5 or higher only.
#include "nuitka/helper/operations_binary_matmult.h"
#endif

NUITKA_MAY_BE_UNUSED static bool BINARY_OPERATION_INPLACE(binary_api api, PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);

    // TODO: There is not really much point in these things.
    PyObject *result = BINARY_OPERATION(api, *operand1, operand2);

    if (unlikely(result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = result;

    return true;
}

// Helpers to execute "+=" on fully or partially known types.
extern bool BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_LIST_LIST_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_STR_STR_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(PyObject **operand1, PyObject *operand2);
extern bool BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2);

static bool FLOAT_MUL_INCREMENTAL(PyObject **operand1, PyObject *operand2) {
    assert(PyFloat_CheckExact(*operand1));
    assert(PyFloat_CheckExact(operand2));

    PyFloat_AS_DOUBLE(*operand1) *= PyFloat_AS_DOUBLE(operand2);

    return true;
}

NUITKA_MAY_BE_UNUSED static bool BINARY_OPERATION_MUL_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        if (PyFloat_CheckExact(*operand1) && PyFloat_CheckExact(operand2)) {
            return FLOAT_MUL_INCREMENTAL(operand1, operand2);
        }
    }

    PyObject *result = PyNumber_InPlaceMultiply(*operand1, operand2);

    if (unlikely(result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = result;

    return true;
}

#if PYTHON_VERSION < 300
NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_DIV(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_divide;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_divide;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }
    }

    if (slot1 != NULL) {
        if (slot2 && PyType_IsSubtype(type2, type1)) {
            PyObject *x = slot2(operand1, operand2);

            if (x != Py_NotImplemented) {
                if (unlikely(x == NULL)) {
                    return NULL;
                }

                return x;
            }

            Py_DECREF(x);
            slot2 = NULL;
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NULL;
            }

            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NULL;
            }

            return x;
        }

        Py_DECREF(x);
    }

    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_divide;

                if (slot != NULL) {
                    PyObject *x = slot(operand1, operand2);

                    Py_DECREF(operand1);
                    Py_DECREF(operand2);

                    if (unlikely(x == NULL)) {
                        return NULL;
                    }

                    return x;
                }
            }

            // CoerceEx did that
            Py_DECREF(operand1);
            Py_DECREF(operand2);
        }
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *POWER_OPERATION2(PyObject *operand1, PyObject *operand2) {
    PyObject *result = PyNumber_InPlacePower(operand1, operand2, Py_None);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static bool POWER_OPERATION_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyObject *result = PyNumber_InPlacePower(*operand1, operand2, Py_None);

    if (unlikely(result == NULL)) {
        return false;
    }

    if (result != *operand1) {
        Py_DECREF(*operand1);
        *operand1 = result;
    }

    return true;
}

#endif
