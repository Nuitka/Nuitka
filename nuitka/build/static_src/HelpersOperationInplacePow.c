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

/* C helpers for type in-place "**" (POW) operations */

/* Disable warnings about unused goto targets for compilers */

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4102)
#endif
#ifdef __GNUC__
#pragma GCC diagnostic ignored "-Wunused-label"
#endif

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_POW_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
    }

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_FLOAT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_POW_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
    }

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_POW_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
    }

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_FLOAT_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_POW_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_LONG_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_POW_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_POW_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_LONG_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_POW_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

            PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

            Py_DECREF(operand1_float);
            Py_DECREF(operand2_float);

            result = r;
            goto exit_result;
        } else {

            long temp = a;
            long ix = 1;
            long bb = b;

            while (bb > 0) {
                long prev = ix;
                if (bb & 1) {
                    ix = (unsigned long)ix * temp;
                    if (temp == 0) {
                        break;
                    }
                    if (ix / temp != prev) {
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

                        PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                        Py_DECREF(operand1_long);
                        Py_DECREF(operand2_long);

                        result = r;
                        goto exit_result;
                    }
                }
                bb >>= 1;
                if (bb == 0) {
                    break;
                }
                prev = temp;
                temp = (unsigned long)temp * temp;

                if (prev != 0 && temp / prev != prev) {
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    result = r;
                    goto exit_result;
                }
            }

            result = PyInt_FromLong(ix);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_power(operand1_object, operand2_object, Py_None);
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_INT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_POW_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

            PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

            Py_DECREF(operand1_float);
            Py_DECREF(operand2_float);

            result = r;
            goto exit_result;
        } else {

            long temp = a;
            long ix = 1;
            long bb = b;

            while (bb > 0) {
                long prev = ix;
                if (bb & 1) {
                    ix = (unsigned long)ix * temp;
                    if (temp == 0) {
                        break;
                    }
                    if (ix / temp != prev) {
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

                        PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                        Py_DECREF(operand1_long);
                        Py_DECREF(operand2_long);

                        result = r;
                        goto exit_result;
                    }
                }
                bb >>= 1;
                if (bb == 0) {
                    break;
                }
                prev = temp;
                temp = (unsigned long)temp * temp;

                if (prev != 0 && temp / prev != prev) {
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    result = r;
                    goto exit_result;
                }
            }

            result = PyInt_FromLong(ix);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_power(operand1_object, operand2_object, Py_None);
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_POW_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

            PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

            Py_DECREF(operand1_float);
            Py_DECREF(operand2_float);

            result = r;
            goto exit_result;
        } else {

            long temp = a;
            long ix = 1;
            long bb = b;

            while (bb > 0) {
                long prev = ix;
                if (bb & 1) {
                    ix = (unsigned long)ix * temp;
                    if (temp == 0) {
                        break;
                    }
                    if (ix / temp != prev) {
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

                        PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                        Py_DECREF(operand1_long);
                        Py_DECREF(operand2_long);

                        result = r;
                        goto exit_result;
                    }
                }
                bb >>= 1;
                if (bb == 0) {
                    break;
                }
                prev = temp;
                temp = (unsigned long)temp * temp;

                if (prev != 0 && temp / prev != prev) {
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    result = r;
                    goto exit_result;
                }
            }

            result = PyInt_FromLong(ix);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_power(operand1_object, operand2_object, Py_None);
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_INT_OBJECT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_POW_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_LONG_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_POW_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_INT_LONG_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_POW_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

            PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

            Py_DECREF(operand1_float);
            Py_DECREF(operand2_float);

            result = r;
            goto exit_result;
        } else {

            long temp = a;
            long ix = 1;
            long bb = b;

            while (bb > 0) {
                long prev = ix;
                if (bb & 1) {
                    ix = (unsigned long)ix * temp;
                    if (temp == 0) {
                        break;
                    }
                    if (ix / temp != prev) {
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

                        PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                        Py_DECREF(operand1_long);
                        Py_DECREF(operand2_long);

                        result = r;
                        goto exit_result;
                    }
                }
                bb >>= 1;
                if (bb == 0) {
                    break;
                }
                prev = temp;
                temp = (unsigned long)temp * temp;

                if (prev != 0 && temp / prev != prev) {
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    result = r;
                    goto exit_result;
                }
            }

            result = PyInt_FromLong(ix);
            goto exit_result_ok;
        }

        {
            PyObject *operand1_object = op1;
            PyObject *operand2_object = operand2;

            PyObject *o = PyLong_Type.tp_as_number->nb_power(operand1_object, operand2_object, Py_None);
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

    PyObject *result = PyNumber_InPlacePow(*operand1, operand2);

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

bool BINARY_OPERATION_POW_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_OBJECT_INPLACE(operand1, operand2);
}

/* Reneable warnings about unused goto targets for compilers */
#ifdef _MSC_VER
#pragma warning(pop)
#endif
#ifdef __GNUC__
#pragma GCC diagnostic warning "-Wunused-label"
#endif
