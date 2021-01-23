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
/* These slots are still manually coded and are used by the generated code.
 *
 * The plan should be to generate these as well, so e.g. we can have a slot
 * SLOT_nb_add_LONG_INT that is optimal too.
 */

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION < 0x300

static PyObject *SLOT_sq_concat_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyString_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

static PyObject *SLOT_sq_concat_OBJECT_STR_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    // TODO: Could in-line and specialize this too.
    return SLOT_sq_concat_OBJECT_STR_OBJECT(operand1, operand2);
}

static nuitka_bool SLOT_sq_concat_NBOOL_STR_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    return (PyString_GET_SIZE(operand1) != 0 || PyString_GET_SIZE(operand2) != 0) ? NUITKA_BOOL_TRUE
                                                                                  : NUITKA_BOOL_FALSE;
}

#else

static PyObject *SLOT_sq_concat_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

static PyObject *SLOT_sq_concat_OBJECT_BYTES_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    return SLOT_sq_concat_OBJECT_BYTES_OBJECT(operand1, operand2);
}

#endif

static PyObject *SLOT_sq_concat_OBJECT_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    return UNICODE_CONCAT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
static nuitka_bool SLOT_sq_concat_NBOOL_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    return (PyUnicode_GET_LENGTH(operand1) != 0 || PyUnicode_GET_LENGTH(operand2) != 0) ? NUITKA_BOOL_TRUE
                                                                                        : NUITKA_BOOL_FALSE;
}
#endif

static PyObject *SLOT_sq_concat_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyUnicode_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

#if PYTHON_VERSION < 0x300
static PyObject *SLOT_sq_concat_OBJECT_STR_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    // TODO: Could in-line and specialize this too.
    return SLOT_sq_concat_OBJECT_STR_OBJECT(operand1, operand2);
}

static nuitka_bool SLOT_sq_concat_NBOOL_STR_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    return (PyString_GET_SIZE(operand1) != 0 || PyUnicode_GET_LENGTH(operand2) != 0) ? NUITKA_BOOL_TRUE
                                                                                     : NUITKA_BOOL_FALSE;
}

static PyObject *SLOT_sq_concat_OBJECT_UNICODE_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    // TODO: Could in-line and specialize this too.
    return SLOT_sq_concat_OBJECT_UNICODE_OBJECT(operand1, operand2);
}

static nuitka_bool SLOT_sq_concat_NBOOL_UNICODE_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    return (PyUnicode_GET_LENGTH(operand1) != 0 || PyString_GET_SIZE(operand2) != 0) ? NUITKA_BOOL_TRUE
                                                                                     : NUITKA_BOOL_FALSE;
}

#endif

static PyObject *SLOT_sq_concat_OBJECT_LIST_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    Py_ssize_t size = Py_SIZE(operand1) + Py_SIZE(operand2);

    PyListObject *result = (PyListObject *)PyList_New(size);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    PyObject **src = ((PyListObject *)operand1)->ob_item;
    PyObject **dest = result->ob_item;

    for (Py_ssize_t i = 0; i < Py_SIZE(operand1); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    src = ((PyListObject *)operand2)->ob_item;
    dest = result->ob_item + Py_SIZE(operand1);
    for (Py_ssize_t i = 0; i < Py_SIZE(operand2); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    return (PyObject *)result;
}

static nuitka_bool SLOT_sq_concat_NBOOL_LIST_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    return (PyList_GET_SIZE(operand1) || PyList_GET_SIZE(operand2)) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
}

static PyObject *SLOT_sq_concat_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyList_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

static nuitka_bool SLOT_sq_concat_NBOOL_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyList_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);

    if (x == NULL) {
        return NUITKA_BOOL_EXCEPTION;
    }

    nuitka_bool result = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(x);
    return result;
}

static PyObject *SLOT_sq_concat_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

    return TUPLE_CONCAT(operand1, operand2);
}

static PyObject *SLOT_sq_concat_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyTuple_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}
