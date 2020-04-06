//     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* WARNING, this code is GENERATED. Modify the template HelperOperationBinary.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized "&" (BITAND) operations */

static PyObject *SLOT_nb_and_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    PyObject *x = PyLong_Type.tp_as_number->nb_and(operand1, operand2);
    assert(x != Py_NotImplemented);
    return x;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_and_OBJECT_LONG_LONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_and;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_LONG_LONG(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'int'", type1->tp_name);
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_LONG_LONG(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and '%s'", type2->tp_name);
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_LONG_OBJECT(operand1, operand2);
}

static nuitka_bool SLOT_nb_and_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    PyObject *x = PyLong_Type.tp_as_number->nb_and(operand1, operand2);
    assert(x != Py_NotImplemented);
    if (unlikely(x == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(x);
    return r;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_and_NBOOL_LONG_LONG(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_and;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_NBOOL_LONG_LONG(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    if (unlikely(x == NULL)) {
                        return NUITKA_BOOL_EXCEPTION;
                    }

                    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(x);
                    return r;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'int'", type1->tp_name);
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_NBOOL_LONG_LONG(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    if (unlikely(x == NULL)) {
                        return NUITKA_BOOL_EXCEPTION;
                    }

                    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(x);
                    return r;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and '%s'", type2->tp_name);
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_LONG_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 300
static PyObject *SLOT_nb_and_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    const long a = PyInt_AS_LONG(operand1);
    const long b = PyInt_AS_LONG(operand2);

    const long result = a & b;
    return PyInt_FromLong(result);

    PyObject *op1 = operand1;
    PyObject *op2 = operand2;

    // TODO: Could in-line and specialize these as well.
    PyObject *o = PyLong_Type.tp_as_number->nb_and(op1, op2);
    assert(o != Py_NotImplemented);

    return o;
}
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_and_OBJECT_INT_INT(operand1, operand2);
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_and;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_INT_INT(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'int'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_INT_INT(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
static nuitka_bool SLOT_nb_and_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    const long a = PyInt_AS_LONG(operand1);
    const long b = PyInt_AS_LONG(operand2);

    const long result = a & b;
    return result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    PyObject *op1 = operand1;
    PyObject *op2 = operand2;

    // TODO: Could in-line and specialize these as well.
    PyObject *o = PyLong_Type.tp_as_number->nb_and(op1, op2);
    assert(o != Py_NotImplemented);

    if (unlikely(o == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    nuitka_bool r = CHECK_IF_TRUE(o) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(o);
    return r;
}
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_and_NBOOL_INT_INT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_and;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_NBOOL_INT_INT(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    if (unlikely(x == NULL)) {
                        return NUITKA_BOOL_EXCEPTION;
                    }

                    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(x);
                    return r;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'int'", type1->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_NBOOL_INT_INT(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    if (unlikely(x == NULL)) {
                        return NUITKA_BOOL_EXCEPTION;
                    }

                    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(x);
                    return r;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and '%s'", type2->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_and;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_INT_INT(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !1) {
        coercion c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_and;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_NBOOL_INT_INT(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    if (unlikely(x == NULL)) {
                        return NUITKA_BOOL_EXCEPTION;
                    }

                    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(x);
                    return r;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !1) {
        coercion c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and 'int'");
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_and;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_LONG_LONG(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !1) {
        coercion c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'long' and 'int'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_and;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_and;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_NBOOL_LONG_LONG(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    if (unlikely(x == NULL)) {
                        return NUITKA_BOOL_EXCEPTION;
                    }

                    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(x);
                    return r;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!1 || !1) {
        coercion c = PyLong_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = PyInt_Type.tp_as_number->nb_coerce;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'long' and 'int'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and 'int'");
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_LONG_INT(operand1, operand2);
}
#endif

static PyObject *SLOT_nb_and_OBJECT_SET_SET(PyObject *operand1, PyObject *operand2) {
    PyObject *x = PySet_Type.tp_as_number->nb_and(operand1, operand2);
    assert(x != Py_NotImplemented);
    return x;
}
/* Code referring to "SET" corresponds to Python 'set' and "SET" to Python 'set'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_SET_SET(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PySet_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PySet_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_and_OBJECT_SET_SET(operand1, operand2);
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_SET_SET(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_SET_SET(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "SET" to Python 'set'. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_OBJECT_SET(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PySet_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;

    PyTypeObject *type2 = &PySet_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_SET_SET(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (0) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 0)
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !0) {
        coercion c =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'set'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_OBJECT_SET(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_OBJECT_SET(operand1, operand2);
}

/* Code referring to "SET" corresponds to Python 'set' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_SET_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PySet_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PySet_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_and_OBJECT_SET_SET(operand1, operand2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!0 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c = NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'set' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_SET_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_SET_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_BITAND_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return _BINARY_OPERATION_BITAND_OBJECT_INT_INT(operand1, operand2);
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    return x;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            return x;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NULL;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        return x;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and '%s'", type1->tp_name, type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_BITAND_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_OBJECT_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_BITAND_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return _BINARY_OPERATION_BITAND_NBOOL_INT_INT(operand1, operand2);
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2);

                if (x != Py_NotImplemented) {
                    if (unlikely(x == NULL)) {
                        return NUITKA_BOOL_EXCEPTION;
                    }

                    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(x);
                    return r;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            if (unlikely(x == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(x);
            return r;
        }

        Py_DECREF(x);
    }

#if PYTHON_VERSION < 300 && (1 || 1)
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }

        c = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_and;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        if (unlikely(x == NULL)) {
                            return NUITKA_BOOL_EXCEPTION;
                        }

                        nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                        Py_DECREF(x);
                        return r;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and '%s'", type1->tp_name, type2->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_BITAND_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_NBOOL_OBJECT_OBJECT(operand1, operand2);
}
