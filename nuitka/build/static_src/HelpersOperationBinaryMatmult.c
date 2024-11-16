//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationBinary.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized "@" (MATMULT) operations */

#if PYTHON_VERSION >= 0x350
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MATMULT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Statically recognized that coercion is not possible with Python3 only operator '@'

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: 'long' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: 'int' and 'int'");
#endif
    goto exit_binary_exception;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MATMULT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MATMULT_OBJECT_LONG_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MATMULT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_matrix_multiply : NULL;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with Python3 only operator '@'

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: '%s' and 'int'", type1->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MATMULT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MATMULT_OBJECT_OBJECT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MATMULT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot2 = NULL;

    if (!(&PyLong_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_matrix_multiply
                                                                              : NULL;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with Python3 only operator '@'

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: 'int' and '%s'", type2->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MATMULT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MATMULT_OBJECT_LONG_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_MATMULT_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Statically recognized that coercion is not possible with Python3 only operator '@'

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: 'float' and 'float'");
    goto exit_binary_exception;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MATMULT_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MATMULT_OBJECT_FLOAT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_MATMULT_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_matrix_multiply : NULL;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with Python3 only operator '@'

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: '%s' and 'float'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MATMULT_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MATMULT_OBJECT_OBJECT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MATMULT_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot2 = NULL;

    if (!(&PyFloat_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_matrix_multiply
                                                                              : NULL;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with Python3 only operator '@'

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: 'float' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MATMULT_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MATMULT_OBJECT_FLOAT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x350
/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MATMULT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        PyObject *result;

        // Not every code path will make use of all possible results.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED bool cbool_result;
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        CHECK_OBJECT(operand1);
        assert(PyInt_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(operand1);
        const long b = PyInt_AS_LONG(operand2);

#error Operator @ not implemented

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_matrix_multiply(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        result = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_matrix_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_matrix_multiply
                                                                              : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (Nuitka_Type_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF_IMMORTAL(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with Python3 only operator '@'

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for @: '%s' and '%s'", type1->tp_name, type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MATMULT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MATMULT_OBJECT_OBJECT_OBJECT(operand1, operand2);
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
