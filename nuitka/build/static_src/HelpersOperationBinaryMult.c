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

#include "HelpersOperationBinaryMultUtils.c"
/* C helpers for type specialized "*" (MULT) operations */

#if PYTHON_VERSION < 300
static PyObject *SLOT_nb_multiply_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        return PyInt_FromLong(longprod);
    }

    const double diff = doubled_longprod - doubleprod;
    const double absdiff = diff >= 0.0 ? diff : -diff;
    const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

    if (likely(32.0 * absdiff <= absprod)) {
        return PyInt_FromLong(longprod);
    }

    PyObject *op1 = operand1;
    PyObject *op2 = operand2;

    // TODO: Could in-line and specialize these as well.
    PyObject *o = PyLong_Type.tp_as_number->nb_multiply(op1, op2);
    assert(o != Py_NotImplemented);

    return o;
}
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
static nuitka_bool SLOT_nb_multiply_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        return longprod != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

    const double diff = doubled_longprod - doubleprod;
    const double absdiff = diff >= 0.0 ? diff : -diff;
    const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

    if (likely(32.0 * absdiff <= absprod)) {
        return longprod != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

    PyObject *op1 = operand1;
    PyObject *op2 = operand2;

    // TODO: Could in-line and specialize these as well.
    PyObject *o = PyLong_Type.tp_as_number->nb_multiply(op1, op2);
    assert(o != Py_NotImplemented);

    if (unlikely(o == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    nuitka_bool r = CHECK_IF_TRUE(o) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(o);
    return r;
}
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    return SLOT_nb_multiply_NBOOL_INT_INT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(operand1, operand2);
}
#endif

static PyObject *SLOT_nb_multiply_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
    assert(x != Py_NotImplemented);
    return x;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
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

    return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(operand1, operand2);
}

static nuitka_bool SLOT_nb_multiply_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
    assert(x != Py_NotImplemented);
    if (unlikely(x == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    nuitka_bool r = CHECK_IF_TRUE(x) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(x);
    return r;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
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

    return SLOT_nb_multiply_NBOOL_LONG_LONG(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(operand1, operand2);
}

static PyObject *SLOT_nb_multiply_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    double a = PyFloat_AS_DOUBLE(operand1);
    double b = PyFloat_AS_DOUBLE(operand2);

    double result = a * b;
    return PyFloat_FromDouble(result);
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_multiply_OBJECT_FLOAT_FLOAT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyFloat_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_FLOAT_FLOAT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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

        c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'float'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyFloat_Type;
    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_FLOAT_FLOAT(operand1, operand2);
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
        coercion c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(operand1, operand2);
}

static nuitka_bool SLOT_nb_multiply_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    double a = PyFloat_AS_DOUBLE(operand1);
    double b = PyFloat_AS_DOUBLE(operand2);

    double result = a * b;
    return result == 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_multiply_NBOOL_FLOAT_FLOAT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyFloat_Type;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_FLOAT_FLOAT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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

        c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'float'", type1->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyFloat_Type;
    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_FLOAT_FLOAT(operand1, operand2);
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
        coercion c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and '%s'", type2->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(operand1, operand2);
}

static PyObject *SLOT_nb_multiply_OBJECT_CLONG_CLONG(long operand1, long operand2) {

    const long a = operand1;
    const long b = operand2;

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        return PyInt_FromLong(longprod);
    }

    const double diff = doubled_longprod - doubleprod;
    const double absdiff = diff >= 0.0 ? diff : -diff;
    const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

    if (likely(32.0 * absdiff <= absprod)) {
        return PyInt_FromLong(longprod);
    }

    PyObject *op1 = PyLong_FromLong(operand1);
    PyObject *op2 = PyLong_FromLong(operand2);

    // TODO: Could in-line and specialize these as well.
    PyObject *o = PyLong_Type.tp_as_number->nb_multiply(op1, op2);
    assert(o != Py_NotImplemented);

    Py_DECREF(op1);
    Py_DECREF(op2);

    return o;
}
/* Code referring to "CLONG" corresponds to C platform long value and "CLONG" to C platform long value. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_CLONG_CLONG(long operand1, long operand2) {

    return SLOT_nb_multiply_OBJECT_CLONG_CLONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_CLONG_CLONG(long operand1, long operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_CLONG_CLONG(operand1, operand2);
}

#if PYTHON_VERSION < 300
static PyObject *SLOT_nb_multiply_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif

    const long a = PyInt_AS_LONG(operand1);
    const long b = operand2;

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        return PyInt_FromLong(longprod);
    }

    const double diff = doubled_longprod - doubleprod;
    const double absdiff = diff >= 0.0 ? diff : -diff;
    const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

    if (likely(32.0 * absdiff <= absprod)) {
        return PyInt_FromLong(longprod);
    }

    PyObject *op1 = operand1;
    PyObject *op2 = PyLong_FromLong(operand2);

    // TODO: Could in-line and specialize these as well.
    PyObject *o = PyLong_Type.tp_as_number->nb_multiply(op1, op2);
    assert(o != Py_NotImplemented);

    Py_DECREF(op2);

    return o;
}
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif

    return SLOT_nb_multiply_OBJECT_INT_CLONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_CLONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
static PyObject *SLOT_nb_multiply_OBJECT_CLONG_INT(long operand1, PyObject *operand2) {

    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    const long a = operand1;
    const long b = PyInt_AS_LONG(operand2);

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        return PyInt_FromLong(longprod);
    }

    const double diff = doubled_longprod - doubleprod;
    const double absdiff = diff >= 0.0 ? diff : -diff;
    const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

    if (likely(32.0 * absdiff <= absprod)) {
        return PyInt_FromLong(longprod);
    }

    PyObject *op1 = PyLong_FromLong(operand1);
    PyObject *op2 = operand2;

    // TODO: Could in-line and specialize these as well.
    PyObject *o = PyLong_Type.tp_as_number->nb_multiply(op1, op2);
    assert(o != Py_NotImplemented);

    Py_DECREF(op1);

    return o;
}
/* Code referring to "CLONG" corresponds to C platform long value and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_CLONG_INT(long operand1, PyObject *operand2) {

    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    return SLOT_nb_multiply_OBJECT_CLONG_INT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_CLONG_INT(long operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_CLONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
static PyObject *SLOT_sq_repeat_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    if (unlikely(!PyIndex_Check(operand2))) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = PyNumber_Index(operand2);

    if (unlikely(index_value == NULL)) {
        return NULL;
    }

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    Py_DECREF(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyString_Type;
    ssizeargfunc repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyString_Type;
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_STR_OBJECT(operand2, operand1);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'str'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyString_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_STR_OBJECT(operand1, operand2);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'str' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_STR_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
static PyObject *SLOT_sq_repeat_OBJECT_STR_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = PyInt_AS_LONG(index_value);

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyString_Type;
    ssizeargfunc repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "INT" corresponds to Python2 'int' and "STR" to Python2 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyString_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_STR_INT(operand2, operand1);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'str'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_STR(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "STR" corresponds to Python2 'str' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_STR_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyString_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!1 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_STR_INT(operand1, operand2);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'str' and 'int'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_STR_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_STR_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
static PyObject *SLOT_sq_repeat_OBJECT_STR_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyString_Type;
    ssizeargfunc repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "STR" to Python2 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyString_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_STR_LONG(operand2, operand1);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'str'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'str'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_STR(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "STR" corresponds to Python2 'str' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_STR_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyString_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!1 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_STR_LONG(operand1, operand2);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'str' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'str' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_STR_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_STR_LONG(operand1, operand2);
}
#endif

static PyObject *SLOT_sq_repeat_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));
    CHECK_OBJECT(operand2);

    if (unlikely(!PyIndex_Check(operand2))) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = PyNumber_Index(operand2);

    if (unlikely(index_value == NULL)) {
        return NULL;
    }

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    Py_DECREF(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyUnicode_Type;
    ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyUnicode_Type;
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_UNICODE_OBJECT(operand2, operand1);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'unicode'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'str'", type1->tp_name);
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE(operand1, operand2);
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyUnicode_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_UNICODE_OBJECT(operand1, operand2);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'unicode' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'str' and '%s'", type2->tp_name);
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 300
static PyObject *SLOT_sq_repeat_OBJECT_UNICODE_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = PyInt_AS_LONG(index_value);

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyUnicode_Type;
    ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "INT" corresponds to Python2 'int' and "UNICODE" to Python2 'unicode', Python3 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyUnicode_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_UNICODE_INT(operand2, operand1);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'unicode'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'str'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_UNICODE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_UNICODE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_UNICODE_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyUnicode_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!1 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_UNICODE_INT(operand1, operand2);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'unicode' and 'int'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'str' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_UNICODE_INT(operand1, operand2);
}
#endif

static PyObject *SLOT_sq_repeat_OBJECT_UNICODE_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyUnicode_Type;
    ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "UNICODE" to Python2 'unicode', Python3
 * 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyUnicode_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_UNICODE_LONG(operand2, operand1);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'unicode'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'str'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE(operand1, operand2);
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "LONG" to Python2 'long', Python3
 * 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    assert(NEW_STYLE_NUMBER(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyUnicode_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!1 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_UNICODE_LONG(operand1, operand2);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'unicode' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'str' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG(operand1, operand2);
}

static PyObject *SLOT_sq_repeat_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    if (unlikely(!PyIndex_Check(operand2))) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = PyNumber_Index(operand2);

    if (unlikely(index_value == NULL)) {
        return NULL;
    }

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    Py_DECREF(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyTuple_Type;
    ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyTuple_Type;
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_TUPLE_OBJECT(operand2, operand1);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'tuple'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE(operand1, operand2);
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyTuple_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_TUPLE_OBJECT(operand1, operand2);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'tuple' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 300
static PyObject *SLOT_sq_repeat_OBJECT_TUPLE_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = PyInt_AS_LONG(index_value);

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyTuple_Type;
    ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "INT" corresponds to Python2 'int' and "TUPLE" to Python 'tuple'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyTuple_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
    if (!1 || !0) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_TUPLE_INT(operand2, operand1);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'tuple'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_TUPLE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_TUPLE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "TUPLE" corresponds to Python 'tuple' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_TUPLE_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyTuple_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!0 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_TUPLE_INT(operand1, operand2);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'tuple' and 'int'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_TUPLE_INT(operand1, operand2);
}
#endif

static PyObject *SLOT_sq_repeat_OBJECT_TUPLE_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyTuple_Type;
    ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "TUPLE" to Python 'tuple'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyTuple_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
    if (!1 || !0) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_TUPLE_LONG(operand2, operand1);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'tuple'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'tuple'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE(operand1, operand2);
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyTuple_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!0 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_TUPLE_LONG(operand1, operand2);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'tuple' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'tuple' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG(operand1, operand2);
}

static PyObject *SLOT_sq_repeat_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    if (unlikely(!PyIndex_Check(operand2))) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = PyNumber_Index(operand2);

    if (unlikely(index_value == NULL)) {
        return NULL;
    }

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    Py_DECREF(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyList_Type;
    ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyList_Type;
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_LIST_OBJECT(operand2, operand1);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'list'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyList_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_LIST_OBJECT(operand1, operand2);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'list' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 300
static PyObject *SLOT_sq_repeat_OBJECT_LIST_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = PyInt_AS_LONG(index_value);

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyList_Type;
    ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "INT" corresponds to Python2 'int' and "LIST" to Python 'list'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyList_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
    if (!1 || !0) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_LIST_INT(operand2, operand1);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'list'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_LIST(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_LIST(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "LIST" corresponds to Python 'list' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LIST_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyList_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!0 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_LIST_INT(operand1, operand2);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'list' and 'int'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LIST_INT(operand1, operand2);
}
#endif

static PyObject *SLOT_sq_repeat_OBJECT_LIST_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyList_Type;
    ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LIST" to Python 'list'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyList_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
    if (!1 || !0) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_LIST_LONG(operand2, operand1);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'list'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'list'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_LIST(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_LIST(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LIST_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyList_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!0 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_LIST_LONG(operand1, operand2);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'list' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'list' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LIST_LONG(operand1, operand2);
}

#if PYTHON_VERSION >= 300
static PyObject *SLOT_sq_repeat_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    if (unlikely(!PyIndex_Check(operand2))) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = PyNumber_Index(operand2);

    if (unlikely(index_value == NULL)) {
        return NULL;
    }

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    Py_DECREF(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyBytes_Type;
    ssizeargfunc repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = &PyBytes_Type;
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_BYTES_OBJECT(operand2, operand1);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'bytes'", type1->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyBytes_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_BYTES_OBJECT(operand1, operand2);

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'bytes' and '%s'", type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 300
static PyObject *SLOT_sq_repeat_OBJECT_BYTES_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (unlikely(!1)) {
        PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", Py_TYPE(operand2)->tp_name);

        return NULL;
    }

    PyObject *index_value = operand2;

    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

    /* Above conversion indicates an error as -1 */
    if (unlikely(count == -1)) {
        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", Py_TYPE(operand2)->tp_name);
        return NULL;
    }

    NUITKA_MAY_BE_UNUSED PyTypeObject *type1 = &PyBytes_Type;
    ssizeargfunc repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;

    PyObject *result = (*repeatfunc)(operand1, count);

    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "BYTES" to Python3 'bytes'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyBytes_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = NULL;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
    if (!1 || !0) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    return SLOT_sq_repeat_OBJECT_BYTES_LONG(operand2, operand1);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'bytes'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'bytes'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_BYTES(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_BYTES(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_BYTES_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyBytes_Type;
    binaryfunc slot1 = NULL;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);
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

#if PYTHON_VERSION < 300 && (0 || 1)
    if (!0 || !1) {
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    return SLOT_sq_repeat_OBJECT_BYTES_LONG(operand1, operand2);

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'bytes' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'bytes' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_BYTES_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_BYTES_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
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
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
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
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'int'");
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyFloat_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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

        c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'float'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "FLOAT" to Python 'float'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_INT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyInt_Type;
    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyFloat_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_INT_INT(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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

        c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'float'");
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_INT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
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
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'int'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
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
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'int'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'int'");
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_LONG_INT(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyFloat_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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

        c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'float'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'float'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_FLOAT(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "FLOAT" to Python 'float'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_LONG_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyLong_Type;
    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyFloat_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_LONG_LONG(operand1, operand2);
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
                    binaryfunc slot = mv->nb_multiply;

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

        c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'float'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'float'");
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_LONG_FLOAT(operand1, operand2);
}

#if PYTHON_VERSION < 300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyFloat_Type;
    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_FLOAT_FLOAT(operand1, operand2);
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
        coercion c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyFloat_Type;
    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyInt_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_FLOAT_FLOAT(operand1, operand2);
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
        coercion c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_INT(operand1, operand2);
}
#endif

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyFloat_Type;
    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_OBJECT_FLOAT_FLOAT(operand1, operand2);
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
        coercion c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
#endif
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_LONG(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    PyTypeObject *type1 = &PyFloat_Type;
    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;

    PyTypeObject *type2 = &PyLong_Type;
    binaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (0) {
            slot2 = NULL;
        }
    } else {
        assert(type1 == type2);

        return SLOT_nb_multiply_NBOOL_FLOAT_FLOAT(operand1, operand2);
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
        coercion c = PyFloat_Type.tp_as_number->nb_coerce;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
#endif
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return _BINARY_OPERATION_MULT_OBJECT_INT_INT(operand1, operand2);
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        return result;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        return result;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and '%s'", type1->tp_name, type2->tp_name);
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return _BINARY_OPERATION_MULT_NBOOL_INT_INT(operand1, operand2);
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    PyTypeObject *type2 = Py_TYPE(operand2);
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                    binaryfunc slot = mv->nb_multiply;

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
                    binaryfunc slot = mv->nb_multiply;

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

    // Special case for "+" and "*", also works as sequence concat/repeat.
    ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }
    // Special case for "+" and "*", also works as sequence concat/repeat.
    sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

    if (sq_slot != NULL) {
        PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

        if (unlikely(result == NULL)) {
            return NUITKA_BOOL_EXCEPTION;
        }

        nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(result);
        return r;
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and '%s'", type1->tp_name, type2->tp_name);
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_OBJECT(operand1, operand2);
}
