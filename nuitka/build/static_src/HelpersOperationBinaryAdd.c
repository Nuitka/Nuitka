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
/* C helpers for type specialized "+" (Add) operations */

#if PYTHON_VERSION < 300
// This is Python2 int, for Python3 the LONG variant is to be used.
PyObject *BINARY_OPERATION_ADD_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (PyInt_CheckExact(operand1)) {
        long a = PyInt_AS_LONG(operand1);
        long b = PyInt_AS_LONG(operand2);

        long i = (long)((unsigned long)a + b);

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here.
        if ((i ^ a) >= 0 || (i ^ b) >= 0) {
            return PyInt_FromLong(i);
        }
    }

    PyTypeObject *type1 = Py_TYPE(operand1);

    binaryfunc slot1 = NULL;
    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NULL;
            }

            return x;
        }

        Py_DECREF(x);
    }

    // In-lined nb_add slot from Python int type.
    if (PyInt_Check(operand1)) {
        long a = PyInt_AS_LONG(operand1);
        long b = PyInt_AS_LONG(operand2);

        long i = (long)((unsigned long)a + b);

        if ((i ^ a) >= 0 || (i ^ b) >= 0) {
            return PyInt_FromLong(i);
        }

        // TODO: Could in-line and specialize this too.
        PyObject *x = PyLong_Type.tp_as_number->nb_add((PyObject *)operand1, (PyObject *)operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NULL;
            }

            return x;
        }

        Py_DECREF(x);
    }

    if (!NEW_STYLE_NUMBER(operand1)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'int'", type1->tp_name);
    return NULL;
}

// This is Python2 int, for Python3 the LONG variant is to be used.
PyObject *BINARY_OPERATION_ADD_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));

    if (PyInt_CheckExact(operand2)) {
        long a, b, i;

        a = PyInt_AS_LONG(operand1);
        b = PyInt_AS_LONG(operand2);

        i = a + b;

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here.
        if (likely(!((i ^ a) < 0 && (i ^ b) < 0))) {
            return PyInt_FromLong(i);
        }
    }

    PyTypeObject *type2 = Py_TYPE(operand2);

    binaryfunc slot2 = NULL;
    if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
        slot2 = type2->tp_as_number->nb_add;

        if (slot2 == PyInt_Type.tp_as_number->nb_add) {
            slot2 = NULL;
        }
    }

    if (slot2 && PyType_IsSubtype(type2, &PyInt_Type)) {
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

    // In-lined nb_add slot from Python int type.
    if (PyInt_Check(operand2)) {
        long a = PyInt_AS_LONG(operand1);
        long b = PyInt_AS_LONG(operand2);

        long i = (long)((unsigned long)a + b);

        if ((i ^ a) >= 0 || (i ^ b) >= 0) {
            return PyInt_FromLong(i);
        }

        // TODO: Could in-line and specialize this too.
        PyObject *x = PyLong_Type.tp_as_number->nb_add((PyObject *)operand1, (PyObject *)operand2);

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

    if (!NEW_STYLE_NUMBER(operand2)) {
        int err = PYNUMBER_COERCE2(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'int' and '%s'", type2->tp_name);
    return NULL;
}

// This is Python2 int, for Python3 the LONG variant is to be used.
PyObject *BINARY_OPERATION_ADD_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long a = PyInt_AS_LONG(operand1);
    long b = PyInt_AS_LONG(operand2);

    long i = (long)((unsigned long)a + b);

    // Detect overflow, in which case, a "long" object would have to be
    // created, which we won't handle here.
    if ((i ^ a) >= 0 || (i ^ b) >= 0) {
        return PyInt_FromLong(i);
    }

    // TODO: Could in-line and specialize this too.
    PyObject *x = PyLong_Type.tp_as_number->nb_add((PyObject *)operand1, (PyObject *)operand2);
    assert(x != Py_NotImplemented);
    return x;
}

#endif

#if PYTHON_VERSION < 300
// This is Python2 str, for Python3 the UNICODE variant is to be used.
PyObject *BINARY_OPERATION_ADD_OBJECT_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Ought to hard code stuff about type2.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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
                binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand1));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Ought to hard code stuff about type1.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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
                binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_STR_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand1));
    assert(PyString_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Ought to hard code stuff about type1, type2

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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
                binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

#endif

PyObject *BINARY_OPERATION_ADD_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyUnicode_Type;

    if (type1 == type2) {
        return UNICODE_CONCAT(operand1, operand2);
    }

    binaryfunc slot1 = NULL;
    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NULL;
            }

            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));

    if (!NEW_STYLE_NUMBER(operand1)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;
#else
    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = type1->tp_as_sequence;
#endif

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand1));

    PyTypeObject *type1 = &PyUnicode_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            binaryfunc slot2 = type2->tp_as_number->nb_add;

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
        }
    } else {
        return UNICODE_CONCAT(operand1, operand2);
    }

#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));

    if (!NEW_STYLE_NUMBER(operand2)) {
        assert(NEW_STYLE_NUMBER(operand1));

        int err = PYNUMBER_COERCE2(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
#else
    return PyUnicode_Concat(operand1, operand2);
#endif
}

PyObject *BINARY_OPERATION_ADD_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand1));
    assert(PyUnicode_CheckExact(operand2));

    return UNICODE_CONCAT(operand1, operand2);
}

PyObject *BINARY_OPERATION_ADD_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Should hardcode type2 knowledge.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand1));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Should hardcode type1 knowledge.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_LONG_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand1));
    assert(PyFloat_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Should hardcode type1, type2 knowledge.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand1));
    assert(PyLong_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Should hardcode type1, type2 knowledge.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand1));
    assert(PyFloat_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Should hardcode type1, type2 knowledge.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyTuple_Type;

    if (type1 == type2) {
        return TUPLE_CONCAT(operand1, operand2);
    }

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        binaryfunc slot1 = type1->tp_as_number->nb_add;

        if (slot1 != NULL) {
            PyObject *x = slot1(operand1, operand2);

            if (x != Py_NotImplemented) {
                if (unlikely(x == NULL)) {
                    return NULL;
                }

                return x;
            }

            Py_DECREF(x);
        }
    }

#if PYTHON_VERSION < 300
    int err = PYNUMBER_COERCE1(&operand1, &operand2);

    if (unlikely(err < 0)) {
        return NULL;
    }

    if (err == 0) {
        PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

        if (mv) {
            binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;
#else
    PySequenceMethods *seq_methods = type1->tp_as_sequence;
#endif

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand1));

    PyTypeObject *type1 = &PyTuple_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    // The object type may still have a way to add us.
    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            binaryfunc slot2 = type2->tp_as_number->nb_add;

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
        }
    } else {
        return TUPLE_CONCAT(operand1, operand2);
    }

#if PYTHON_VERSION < 300
    // Tuples are not new style numbers, therefore must attempt coerce with
    // second argument in charge.
    assert(!NEW_STYLE_NUMBER(operand1));

    int err = PYNUMBER_COERCE2(&operand1, &operand2);

    if (unlikely(err < 0)) {
        return NULL;
    }

    if (err == 0) {
        PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

        if (mv) {
            binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);
    return NULL;
#else
    // Without coerce and known tuple type, we can hard code this.
    return PyTuple_Type.tp_as_sequence->sq_concat(operand1, operand2);
#endif
}

PyObject *BINARY_OPERATION_ADD_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand1));
    assert(PyTuple_CheckExact(operand2));

    return TUPLE_CONCAT(operand1, operand2);
}

PyObject *BINARY_OPERATION_ADD_OBJECT_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyList_Type;

    if (type1 == type2) {
        return LIST_CONCAT(operand1, operand2);
    }

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        binaryfunc slot1 = type1->tp_as_number->nb_add;

        if (slot1 != NULL) {
            PyObject *x = slot1(operand1, operand2);

            if (x != Py_NotImplemented) {
                if (unlikely(x == NULL)) {
                    return NULL;
                }

                return x;
            }

            Py_DECREF(x);
        }
    }

#if PYTHON_VERSION < 300
    int err = PYNUMBER_COERCE1(&operand1, &operand2);

    if (unlikely(err < 0)) {
        return NULL;
    }

    if (err == 0) {
        PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

        if (mv) {
            binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;
#else
    PySequenceMethods *seq_methods = type1->tp_as_sequence;
#endif

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand1));

    PyTypeObject *type1 = &PyList_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            binaryfunc slot2 = type2->tp_as_number->nb_add;

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
        }
    } else {
        return LIST_CONCAT(operand1, operand2);
    }

#if PYTHON_VERSION < 300
    // List are not new style numbers, therefore must attempt coerce with
    assert(!NEW_STYLE_NUMBER(operand1));

    int err = PYNUMBER_COERCE2(&operand1, &operand2);

    if (unlikely(err < 0)) {
        return NULL;
    }

    if (err == 0) {
        PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

        if (mv) {
            binaryfunc slot = mv->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
#else
    return PyList_Type.tp_as_sequence->sq_concat(operand1, operand2);
#endif
}

PyObject *BINARY_OPERATION_ADD_LIST_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand1));
    assert(PyList_CheckExact(operand2));

    return LIST_CONCAT(operand1, operand2);
}

#if PYTHON_VERSION >= 300
PyObject *BINARY_OPERATION_ADD_OBJECT_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Hardcode type2 knowledge.

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyBytes_Type;

    if (type1->tp_as_number != NULL) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL) {
            slot2 = type2->tp_as_number->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand1));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Hardcode type1 knowledge.

    PyTypeObject *type1 = &PyBytes_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL) {
            slot2 = type2->tp_as_number->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_BYTES_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand1));
    assert(PyBytes_CheckExact(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    // TODO: Hardcode type1/type2 knowledge.
    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL) {
            slot2 = type2->tp_as_number->nb_add;

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

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}
#endif

PyObject *BINARY_OPERATION_ADD_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}

PyObject *BINARY_OPERATION_ADD_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand1));
    assert(PyLong_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand1));
    assert(NEW_STYLE_NUMBER(operand2));

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_add;

    PyObject *x = slot1(operand1, operand2);

    if (unlikely(x == NULL)) {
        return NULL;
    }

    return x;
}

PyObject *BINARY_OPERATION_ADD_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 300
    // Something similar for Python3 should exist too.
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        long a, b, i;

        a = PyInt_AS_LONG(operand1);
        b = PyInt_AS_LONG(operand2);

        i = a + b;

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here.
        if (likely(!((i ^ a) < 0 && (i ^ b) < 0))) {
            return PyInt_FromLong(i);
        }
    }
#endif

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1->tp_as_number != NULL && NEW_STYLE_NUMBER(operand1)) {
        slot1 = type1->tp_as_number->nb_add;
    }

    if (type1 != type2) {
        if (type2->tp_as_number != NULL && NEW_STYLE_NUMBER(operand2)) {
            slot2 = type2->tp_as_number->nb_add;

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

#if PYTHON_VERSION < 300
    if (!NEW_STYLE_NUMBER(operand1) || !NEW_STYLE_NUMBER(operand2)) {
        int err = PyNumber_CoerceEx(&operand1, &operand2);

        if (unlikely(err < 0)) {
            return NULL;
        }

        if (err == 0) {
            PyNumberMethods *mv = Py_TYPE(operand1)->tp_as_number;

            if (mv) {
                binaryfunc slot = mv->nb_add;

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
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE(operand1)->tp_as_sequence;

    if (seq_methods && seq_methods->sq_concat) {
        PyObject *result = (*seq_methods->sq_concat)(operand1, operand2);

        if (unlikely(result == NULL)) {
            return NULL;
        }

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name, type2->tp_name);

    return NULL;
}
