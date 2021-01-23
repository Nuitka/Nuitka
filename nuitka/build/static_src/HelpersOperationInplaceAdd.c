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
/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#include "HelpersOperationInplaceAddUtils.c"
/* C helpers for type in-place "+" (ADD) operations */

/* Disable warnings about unused goto targets for compilers */

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4102)
#endif
#ifdef __GNUC__
#pragma GCC diagnostic ignored "-Wunused-label"
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_ADD_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

#if PYTHON_VERSION < 0x300
    if (1 && 1) {

        PyObject *result;
        PyObject *op1 = *operand1;

        CHECK_OBJECT(op1);
        assert(PyInt_CheckExact(op1));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(op1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

        const long a = PyInt_AS_LONG(op1);
        const long b = PyInt_AS_LONG(operand2);

        const long x = (long)((unsigned long)a + b);
        bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
        if (likely(no_overflow)) {
            result = PyInt_FromLong(x);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
            assert(o != Py_NotImplemented);

            result = o;
            goto exit_result;
        }

    exit_result:

        if (unlikely(result == NULL)) {
            return false;
        }

    exit_result_ok:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = result;

        return true;

    exit_result_exception:
        return false;
    }
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(*operand1) && 1) {

        PyObject *result;
        PyObject *op1 = *operand1;

        CHECK_OBJECT(op1);
        assert(PyInt_CheckExact(op1));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(op1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

        const long a = PyInt_AS_LONG(op1);
        const long b = PyInt_AS_LONG(operand2);

        const long x = (long)((unsigned long)a + b);
        bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
        if (likely(no_overflow)) {
            result = PyInt_FromLong(x);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
            assert(o != Py_NotImplemented);

            result = o;
            goto exit_result;
        }

    exit_result:

        if (unlikely(result == NULL)) {
            return false;
        }

    exit_result_ok:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = result;

        return true;

    exit_result_exception:
        return false;
    }
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 0x300
    if (1 && PyInt_CheckExact(operand2)) {

        PyObject *result;
        PyObject *op1 = *operand1;

        CHECK_OBJECT(op1);
        assert(PyInt_CheckExact(op1));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(op1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

        const long a = PyInt_AS_LONG(op1);
        const long b = PyInt_AS_LONG(operand2);

        const long x = (long)((unsigned long)a + b);
        bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
        if (likely(no_overflow)) {
            result = PyInt_FromLong(x);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
            assert(o != Py_NotImplemented);

            result = o;
            goto exit_result;
        }

    exit_result:

        if (unlikely(result == NULL)) {
            return false;
        }

    exit_result_ok:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = result;

        return true;

    exit_result_exception:
        return false;
    }
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_ADD_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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
    return _BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

        if (1 && 1) {
            PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
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

bool BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

        if (PyFloat_CheckExact(*operand1) && 1) {
            PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
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

bool BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

        if (1 && PyFloat_CheckExact(operand2)) {
            PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
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

bool BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_ADD_STR_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (1 && !PyString_CHECK_INTERNED(*operand1) && 1) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    // Python2 strings are to be treated differently, fall back to Python API here.
    if (1 && 1) {
        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
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

bool BINARY_OPERATION_ADD_STR_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_STR_STR_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (PyString_CheckExact(*operand1) && !PyString_CHECK_INTERNED(*operand1) && 1) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    // Python2 strings are to be treated differently, fall back to Python API here.
    if (PyString_CheckExact(*operand1) && 1) {
        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
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

bool BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (1 && !PyString_CHECK_INTERNED(*operand1) && PyString_CheckExact(operand2)) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    // Python2 strings are to be treated differently, fall back to Python API here.
    if (1 && PyString_CheckExact(operand2)) {
        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
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

bool BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "UNICODE" to Python2 'unicode',
 * Python3 'str'. */
static inline bool _BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && !PyUnicode_CHECK_INTERNED(*operand1) && 1) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    // Python3 Strings are to be treated differently.
    if (1 && 1) {
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
    return _BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (PyUnicode_CheckExact(*operand1) && !PyUnicode_CHECK_INTERNED(*operand1) && 1) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    // Python3 Strings are to be treated differently.
    if (PyUnicode_CheckExact(*operand1) && 1) {
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

bool BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(operand1, operand2);
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && !PyUnicode_CHECK_INTERNED(*operand1) && PyUnicode_CheckExact(operand2)) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    // Python3 Strings are to be treated differently.
    if (1 && PyUnicode_CheckExact(operand2)) {
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
    return _BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "BYTES" to Python3 'bytes'. */
static inline bool _BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyBytes_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && 1) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
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
    return _BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (PyBytes_CheckExact(*operand1) && 1) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
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

bool BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyBytes_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && PyBytes_CheckExact(operand2)) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
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
    return _BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (1 && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if ((PyTuple_CheckExact(*operand1) || PySequence_Check(*operand1)) && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(operand1, operand2);
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (1 && (PyTuple_CheckExact(operand2) || PySequence_Check(operand2))) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "LIST" to Python 'list'. */
static inline bool _BINARY_OPERATION_ADD_LIST_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (1 && 1) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    if (1 && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_LIST_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LIST_LIST_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (PyList_CheckExact(*operand1) && 1) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    if (PySequence_Check(*operand1) && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (1 && PyList_CheckExact(operand2)) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    if (1 && PySequence_Check(operand2)) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_ADD_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_LONG_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_ADD_INT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

        if (0 && 1) {
            PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
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

bool BINARY_OPERATION_ADD_INT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_FLOAT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_ADD_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_ADD_LONG_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

        if (0 && 1) {
            PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
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

bool BINARY_OPERATION_ADD_LONG_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_FLOAT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_ADD_FLOAT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

        if (1 && 0) {
            PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
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

bool BINARY_OPERATION_ADD_FLOAT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_ADD_FLOAT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

        if (1 && 0) {
            PyFloat_AS_DOUBLE(*operand1) += PyFloat_AS_DOUBLE(operand2);
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

bool BINARY_OPERATION_ADD_FLOAT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_LONG_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "UNICODE" to Python2 'unicode', Python3 'str'. */
static inline bool _BINARY_OPERATION_ADD_STR_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_STR_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_STR_UNICODE_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_ADD_UNICODE_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

bool BINARY_OPERATION_ADD_UNICODE_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_UNICODE_STR_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(*operand1) && PyInt_CheckExact(operand2)) {

        PyObject *result;
        PyObject *op1 = *operand1;

        CHECK_OBJECT(op1);
        assert(PyInt_CheckExact(op1));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(op1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

        const long a = PyInt_AS_LONG(op1);
        const long b = PyInt_AS_LONG(operand2);

        const long x = (long)((unsigned long)a + b);
        bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
        if (likely(no_overflow)) {
            result = PyInt_FromLong(x);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
            assert(o != Py_NotImplemented);

            result = o;
            goto exit_result;
        }

    exit_result:

        if (unlikely(result == NULL)) {
            return false;
        }

    exit_result_ok:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = result;

        return true;

    exit_result_exception:
        return false;
    }
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (PyString_CheckExact(*operand1) && !PyString_CHECK_INTERNED(*operand1) && PyString_CheckExact(operand2)) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif

#if PYTHON_VERSION >= 0x300
        if (PyUnicode_CheckExact(*operand1) && !PyUnicode_CHECK_INTERNED(*operand1) && PyUnicode_CheckExact(operand2)) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    // Python2 strings are to be treated differently, fall back to Python API here.
    if (PyString_CheckExact(*operand1) && PyString_CheckExact(operand2)) {
        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
    }
#endif

    // Python3 Strings are to be treated differently.
    if (PyUnicode_CheckExact(*operand1) && PyUnicode_CheckExact(operand2)) {
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

bool BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_ADD_LIST_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (1 && 0) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    if (1 && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_LIST_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LIST_TUPLE_INPLACE(operand1, operand2);
}

/* Reneable warnings about unused goto targets for compilers */
#ifdef _MSC_VER
#pragma warning(pop)
#endif
#ifdef __GNUC__
#pragma GCC diagnostic warning "-Wunused-label"
#endif
