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
/* These slots are still manually coded and are used by the generated code.
 *
 * The plan should be to generate these as well, so e.g. we can have a slot
 * SLOT_nb_add_LONG_INT that is optimal too.
 */

#if PYTHON_VERSION < 300

static PyObject *SLOT_nb_add_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    long a = PyInt_AS_LONG(operand1);
    long b = PyInt_AS_LONG(operand2);

    long i = (long)((unsigned long)a + b);

    // Detect overflow, in which case, a "long" object would have to be
    // created, which we won't handle here.
    if (likely((i ^ a) >= 0 || (i ^ b) >= 0)) {
        return PyInt_FromLong(i);
    }

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyLong_Type.tp_as_number->nb_add((PyObject *)operand1, (PyObject *)operand2);
    assert(x != Py_NotImplemented);
    return x;
}

#endif

static PyObject *SLOT_nb_add_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyLong_Type.tp_as_number->nb_add((PyObject *)operand1, (PyObject *)operand2);
    assert(x != Py_NotImplemented);
    return x;
}

static PyObject *SLOT_nb_add_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyFloat_Type.tp_as_number->nb_add((PyObject *)operand1, (PyObject *)operand2);
    assert(x != Py_NotImplemented);
    return x;
}

#if PYTHON_VERSION < 300

static PyObject *SLOT_sq_concat_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyString_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

static PyObject *SLOT_sq_concat_STR_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    // TODO: Could in-line and specialize this too.
    return SLOT_sq_concat_STR_OBJECT(operand1, operand2);
}

#else

static PyObject *SLOT_sq_concat_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

static PyObject *SLOT_sq_concat_BYTES_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    return SLOT_sq_concat_BYTES_OBJECT(operand1, operand2);
}

#endif

static PyObject *SLOT_sq_concat_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    return UNICODE_CONCAT(operand1, operand2);
}

static PyObject *SLOT_sq_concat_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyUnicode_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

static PyObject *SLOT_sq_concat_LIST_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    return LIST_CONCAT(operand1, operand2);
}

static PyObject *SLOT_sq_concat_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyList_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}

static PyObject *SLOT_sq_concat_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

    return TUPLE_CONCAT(operand1, operand2);
}

static PyObject *SLOT_sq_concat_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyTuple_Type.tp_as_sequence->sq_concat((PyObject *)operand1, (PyObject *)operand2);
    return x;
}
