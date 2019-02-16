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
/* C helpers for type specialized "+=" (IAdd) operations */

#if PYTHON_VERSION < 300
#include <stddef.h>

#define PyStringObject_SIZE (offsetof(PyStringObject, ob_sval) + 1)

NUITKA_MAY_BE_UNUSED static bool STRING_RESIZE(PyObject **value, Py_ssize_t newsize) {
    PyStringObject *sv;

    _Py_DEC_REFTOTAL;
    _Py_ForgetReference(*value);

    *value = (PyObject *)PyObject_REALLOC((char *)*value, PyStringObject_SIZE + newsize);

    if (unlikely(*value == NULL)) {
        PyErr_NoMemory();

        return false;
    }
    _Py_NewReference(*value);

    sv = (PyStringObject *)*value;
    Py_SIZE(sv) = newsize;

    sv->ob_sval[newsize] = '\0';
    sv->ob_shash = -1;

    return true;
}

NUITKA_MAY_BE_UNUSED static bool STRING_ADD_INCREMENTAL(PyObject **operand1, PyObject *operand2) {
    assert(PyString_CheckExact(*operand1));
    assert(!PyString_CHECK_INTERNED(*operand1));
    assert(PyString_CheckExact(operand2));

    Py_ssize_t operand1_size = PyString_GET_SIZE(*operand1);
    Py_ssize_t operand2_size = PyString_GET_SIZE(operand2);

    Py_ssize_t new_size = operand1_size + operand2_size;

    if (unlikely(new_size < 0)) {
        PyErr_Format(PyExc_OverflowError, "strings are too large to concat");

        return false;
    }

    if (unlikely(STRING_RESIZE(operand1, new_size) == false)) {
        return false;
    }

    memcpy(PyString_AS_STRING(*operand1) + operand1_size, PyString_AS_STRING(operand2), operand2_size);

    return true;
}
#endif

#if PYTHON_VERSION >= 300
NUITKA_MAY_BE_UNUSED static bool BYTES_ADD_INCREMENTAL(PyObject **operand1, PyObject *operand2) {
    assert(PyBytes_CheckExact(*operand1));
    assert(PyBytes_CheckExact(operand2));

    // Buffer
    Py_buffer wb;
    wb.len = -1;

    if (PyObject_GetBuffer(operand2, &wb, PyBUF_SIMPLE) != 0) {
        PyErr_Format(PyExc_TypeError, "can't concat %s to %s", Py_TYPE(operand2)->tp_name, Py_TYPE(*operand1)->tp_name);

        return false;
    }

    Py_ssize_t oldsize = PyBytes_GET_SIZE(*operand1);

    if (oldsize > PY_SSIZE_T_MAX - wb.len) {
        PyErr_NoMemory();
        PyBuffer_Release(&wb);
        return false;
    }
    if (_PyBytes_Resize(operand1, oldsize + wb.len) < 0) {
        PyBuffer_Release(&wb);
        return false;
    }

    memcpy(PyBytes_AS_STRING(*operand1) + oldsize, wb.buf, wb.len);
    PyBuffer_Release(&wb);
    return true;
}
#endif

NUITKA_MAY_BE_UNUSED static bool UNICODE_ADD_INCREMENTAL(PyObject **operand1, PyObject *operand2) {
    Py_ssize_t operand2_size = PyUnicode_GET_SIZE(operand2);
    if (operand2_size == 0)
        return true;

#if PYTHON_VERSION < 300
    Py_ssize_t operand1_size = PyUnicode_GET_SIZE(*operand1);

    Py_ssize_t new_size = operand1_size + operand2_size;

    if (unlikely(new_size < 0)) {
        PyErr_Format(PyExc_OverflowError, "strings are too large to concat");

        return false;
    }

    if (unlikely(PyUnicode_Resize(operand1, new_size) != 0)) {
        return false;
    }

    memcpy(PyUnicode_AS_UNICODE(*operand1) + operand1_size, PyUnicode_AS_UNICODE(operand2),
           operand2_size * sizeof(Py_UNICODE));

    return true;
#else
    assert(!PyUnicode_CHECK_INTERNED(*operand1));

    return UNICODE_APPEND(operand1, operand2);
#endif
}

static bool FLOAT_ADD_INCREMENTAL(PyObject **operand1, PyObject *operand2) {
    assert(PyFloat_CheckExact(*operand1));
    assert(PyFloat_CheckExact(operand2));

    PyFPE_START_PROTECT("add", return false);
    PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
    PyFPE_END_PROTECT(*operand1);

    return true;
}

bool BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(*operand1));

    PyObject *result;

    if (PyList_CheckExact(operand2)) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    } else if (PySequence_Check(operand2)) {
        result = PySequence_InPlaceConcat(*operand1, operand2);
    } else {
        result = PyNumber_InPlaceAdd(*operand1, operand2);
    }

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

bool BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    PyObject *result;

    if (PyList_CheckExact(*operand1)) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    } else if (PySequence_Check(*operand1)) {
        result = PySequence_InPlaceConcat(*operand1, operand2);
    } else {
        result = PyNumber_InPlaceAdd(*operand1, operand2);
    }

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

bool BINARY_OPERATION_ADD_LIST_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(*operand1));
    assert(PyList_CheckExact(operand2));

    return LIST_EXTEND_FROM_LIST(*operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

    PyObject *result;

    if (PyTuple_CheckExact(*operand1)) {
        // TODO: No tuple specific code, create one and use it, although it
        // is probably not too common to in-place to them.
        result = PySequence_InPlaceConcat(*operand1, operand2);
    } else if (PySequence_Check(*operand1)) {
        result = PySequence_InPlaceConcat(*operand1, operand2);
    } else {
        result = PyNumber_InPlaceAdd(*operand1, operand2);
    }

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

bool BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(*operand1));

    PyObject *result;

    if (PyTuple_CheckExact(operand2)) {
        // TODO: No tuple specific code, create one and use it, although it
        // is probably not too common to in-place to them.
        result = PySequence_InPlaceConcat(*operand1, operand2);
    } else if (PySequence_Check(operand2)) {
        result = PySequence_InPlaceConcat(*operand1, operand2);
    } else {
        result = PyNumber_InPlaceAdd(*operand1, operand2);
    }

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

bool BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(*operand1));
    assert(PyTuple_CheckExact(operand2));

    PyObject *result;

    // TODO: No tuple specific code, create one and use it, although it
    // is probably not too common to in-place to them.
    result = PySequence_InPlaceConcat(*operand1, operand2);

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
// This is Python2 int, for Python3 the LONG variant is to be used.
bool BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    // Something similar for Python3 should exist too.
    if (PyInt_CheckExact(*operand1)) {
        long a, b, i;

        a = PyInt_AS_LONG(*operand1);
        b = PyInt_AS_LONG(operand2);

        i = a + b;

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here. TODO: Add an else for that
        // case.
        if (likely(!((i ^ a) < 0 && (i ^ b) < 0))) {
            PyObject *result = PyInt_FromLong(i);
            Py_DECREF(*operand1);

            *operand1 = result;

            return true;
        }
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

// This is Python2 int, for Python3 the LONG variant is to be used.
bool BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(*operand1));

    // Something similar for Python3 should exist too.
    if (PyInt_CheckExact(operand2)) {
        long a, b, i;

        a = PyInt_AS_LONG(*operand1);
        b = PyInt_AS_LONG(operand2);

        i = a + b;

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here. TODO: Add an else for that
        // case.
        if (likely(!((i ^ a) < 0 && (i ^ b) < 0))) {
            PyObject *result = PyInt_FromLong(i);
            Py_DECREF(*operand1);

            *operand1 = result;

            return true;
        }
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

// This is Python2 int, for Python3 the LONG variant is to be used.
bool BINARY_OPERATION_ADD_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(*operand1));
    assert(PyInt_CheckExact(operand2));

    long a, b, i;

    a = PyInt_AS_LONG(*operand1);
    b = PyInt_AS_LONG(operand2);

    i = a + b;

    // Detect overflow, in which case, a "long" object would have to be
    // created, which we won't handle here. TODO: Add an else for that
    // case.
    if (likely(!((i ^ a) < 0 && (i ^ b) < 0))) {
        PyObject *result = PyInt_FromLong(i);
        Py_DECREF(*operand1);

        *operand1 = result;

        return true;
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

#endif

bool BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    if (PyFloat_CheckExact(*operand1)) {
        // Adding floats to a new float could get special code too.
        if (Py_REFCNT(*operand1) == 1) {
            return FLOAT_ADD_INCREMENTAL(operand1, operand2);
        }
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(*operand1));

    if (Py_REFCNT(*operand1) == 1 && PyFloat_CheckExact(operand2)) {
        return FLOAT_ADD_INCREMENTAL(operand1, operand2);
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(*operand1));
    assert(PyFloat_CheckExact(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        return FLOAT_ADD_INCREMENTAL(operand1, operand2);
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    // TODO: Consider adding this shortcut, we might often be able to use
    // existing values at least in case of smaller right hand side, but it
    // may equally often not work out and not be worth it. CPython doesn't
    // try it.
#if 0
    if (PyLong_CheckExact(*operand1)) {
        // Adding floats to a new float could get special code too.
        if (Py_REFCNT(*operand1) == 1) {
            return LONG_ADD_INCREMENTAL(operand1, operand2);
        }
    }
#endif

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(*operand1));

// TODO: Consider adding this shortcut, we might often be able to use
// existing values at least in case of smaller right hand side, but it
// may equally often not work out and not be worth it. CPython doesn't
// try it.
#if 0
    if (Py_REFCNT(*operand1) == 1 && PyLong_CheckExact(operand2)) {
        return LONG_ADD_INCREMENTAL(operand1, operand2);
    }
#endif

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(*operand1));
    assert(PyLong_CheckExact(operand2));

    // TODO: Consider adding this shortcut, we might often be able to use
    // existing values at least in case of smaller right hand side, but it
    // may equally often not work out and not be worth it. CPython doesn't
    // try it.
#if 0
    // Adding floats to a new float could get special code too.
    if (Py_REFCNT(*operand1) == 1) {
        return LONG_ADD_INCREMENTAL(operand1, operand2);
    }
#endif

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    if (likely(PyUnicode_CheckExact(*operand1))) {
#if PYTHON_VERSION >= 300
        if (Py_REFCNT(*operand1) == 1 && !PyUnicode_CHECK_INTERNED(*operand1)) {
            // We more or less own the operand, so we might re-use its storage and
            // execute stuff in-place.
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif

        PyObject *result = UNICODE_CONCAT(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(*operand1));

    if (likely(PyUnicode_CheckExact(operand2))) {
#if PYTHON_VERSION >= 300
        if (Py_REFCNT(*operand1) == 1 && !PyUnicode_CHECK_INTERNED(*operand1)) {
            // We more or less own the operand, so we might re-use its storage and
            // execute stuff in-place.
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif

        PyObject *result = UNICODE_CONCAT(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(*operand1));
    assert(PyUnicode_CheckExact(operand2));

#if PYTHON_VERSION >= 300
    if (Py_REFCNT(*operand1) == 1 && !PyUnicode_CHECK_INTERNED(*operand1)) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
        return UNICODE_ADD_INCREMENTAL(operand1, operand2);
    }
#endif

    PyObject *result = UNICODE_CONCAT(*operand1, operand2);

    if (unlikely(result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = result;

    return true;
}

#if PYTHON_VERSION < 300
// This is Python2 str, for Python3 the UNICODE variant is to be used.
bool BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    if (likely(PyString_CheckExact(*operand1))) {
        if (!PyString_CHECK_INTERNED(*operand1) && Py_REFCNT(*operand1) == 1) {
            return STRING_ADD_INCREMENTAL(operand1, operand2);
        }

        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(*operand1));

    if (likely(PyString_CheckExact(operand2))) {
        if (!PyString_CHECK_INTERNED(*operand1) && Py_REFCNT(*operand1) == 1) {
            return STRING_ADD_INCREMENTAL(operand1, operand2);
        }

        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_STR_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(*operand1));
    assert(PyString_CheckExact(operand2));

    if (!PyString_CHECK_INTERNED(*operand1) && Py_REFCNT(*operand1) == 1) {
        return STRING_ADD_INCREMENTAL(operand1, operand2);
    }

    PyString_Concat(operand1, operand2);
    return !ERROR_OCCURRED();

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

#endif

#if PYTHON_VERSION >= 300
bool BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    if (Py_REFCNT(*operand1) == 1 && PyBytes_CheckExact(*operand1)) {
        return BYTES_ADD_INCREMENTAL(operand1, operand2);
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(*operand1));

    if (Py_REFCNT(*operand1) == 1 && PyBytes_CheckExact(operand2)) {
        return BYTES_ADD_INCREMENTAL(operand1, operand2);
    }

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(*operand1));
    assert(PyBytes_CheckExact(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        return BYTES_ADD_INCREMENTAL(operand1, operand2);
    }

    // Could concat bytes here more directly.

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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

#endif

bool BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);
    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 300
    // Something similar for Python3 should exist too.
    if (PyInt_CheckExact(*operand1) && PyInt_CheckExact(operand2)) {
        long a, b, i;

        a = PyInt_AS_LONG(*operand1);
        b = PyInt_AS_LONG(operand2);

        i = a + b;

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here. TODO: Add an else for that
        // case.
        if (likely(!((i ^ a) < 0 && (i ^ b) < 0))) {
            PyObject *result = PyInt_FromLong(i);
            Py_DECREF(*operand1);

            *operand1 = result;

            return true;
        }
    }
#endif

#if PYTHON_VERSION < 300
    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
        if (PyString_CheckExact(*operand1) && !PyString_CHECK_INTERNED(*operand1) && PyString_CheckExact(operand2)) {
            return STRING_ADD_INCREMENTAL(operand1, operand2);
        } else if (PyFloat_CheckExact(*operand1) && PyFloat_CheckExact(operand2)) {
            return FLOAT_ADD_INCREMENTAL(operand1, operand2);
        }
    }

    // Strings are to be treated differently.
    if (PyString_CheckExact(*operand1) && PyString_CheckExact(operand2)) {
        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
    }
#else
    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
        if (PyUnicode_CheckExact(*operand1) && !PyUnicode_CHECK_INTERNED(*operand1) && PyUnicode_CheckExact(operand2)) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        } else if (PyFloat_CheckExact(*operand1) && PyFloat_CheckExact(operand2)) {
            return FLOAT_ADD_INCREMENTAL(operand1, operand2);
        }
    }

    // Strings are to be treated differently.
    if (PyUnicode_CheckExact(*operand1) && PyUnicode_CheckExact(operand2)) {
        PyObject *result = UNICODE_CONCAT(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }
#endif

    PyObject *result = PyNumber_InPlaceAdd(*operand1, operand2);

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
