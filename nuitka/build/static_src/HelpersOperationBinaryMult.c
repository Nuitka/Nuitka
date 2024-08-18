//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationBinary.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#include "HelpersOperationBinaryMultUtils.c"
/* C helpers for type specialized "*" (MULT) operations */

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

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

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        clong_result = longprod;
        goto exit_result_ok_clong;
    } else {
        const double diff = doubled_longprod - doubleprod;
        const double absdiff = diff >= 0.0 ? diff : -diff;
        const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

        if (likely(32.0 * absdiff <= absprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        }
    }

    {
        PyObject *operand1_object = operand1;
        PyObject *operand2_object = operand2;

        PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
        assert(r != Py_NotImplemented);

        obj_result = r;
        goto exit_result_object;
    }

exit_result_ok_clong:
    result = Nuitka_PyInt_FromLong(clong_result);
    goto exit_result_ok;

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

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyInt_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 = PyInt_Type.tp_as_number->nb_coerce;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyInt_Type) {
        PyObject *result;

        // return _BINARY_OPERATION_MULT_OBJECT_INT_INT(operand1, operand2);

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

        const long longprod = (long)((unsigned long)a * b);
        const double doubleprod = (double)a * (double)b;
        const double doubled_longprod = (double)longprod;

        if (likely(doubled_longprod == doubleprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        } else {
            const double diff = doubled_longprod - doubleprod;
            const double absdiff = diff >= 0.0 ? diff : -diff;
            const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

            if (likely(32.0 * absdiff <= absprod)) {
                clong_result = longprod;
                goto exit_result_ok_clong;
            }
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        result = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

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

    return __BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
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

    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
    binaryfunc slot2 = NULL;

    if (!(&PyInt_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
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

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 = PyInt_Type.tp_as_number->nb_coerce;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyInt_Type == type2) {
        PyObject *result;

        // return _BINARY_OPERATION_MULT_OBJECT_INT_INT(operand1, operand2);

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

        const long longprod = (long)((unsigned long)a * b);
        const double doubleprod = (double)a * (double)b;
        const double doubled_longprod = (double)longprod;

        if (likely(doubled_longprod == doubleprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        } else {
            const double diff = doubled_longprod - doubleprod;
            const double absdiff = diff >= 0.0 ? diff : -diff;
            const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

            if (likely(32.0 * absdiff <= absprod)) {
                clong_result = longprod;
                goto exit_result_ok_clong;
            }
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        result = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

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

    return __BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    nuitka_bool result;

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

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        clong_result = longprod;
        goto exit_result_ok_clong;
    } else {
        const double diff = doubled_longprod - doubleprod;
        const double absdiff = diff >= 0.0 ? diff : -diff;
        const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

        if (likely(32.0 * absdiff <= absprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        }
    }

    {
        PyObject *operand1_object = operand1;
        PyObject *operand2_object = operand2;

        PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
        assert(r != Py_NotImplemented);

        obj_result = r;
        goto exit_result_object;
    }

exit_result_ok_clong:
    result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(obj_result);
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(PyObject *operand1,
                                                                                PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyInt_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyInt_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 = PyInt_Type.tp_as_number->nb_coerce;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyInt_Type) {
        nuitka_bool result;

        // return _BINARY_OPERATION_MULT_NBOOL_INT_INT(operand1, operand2);

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

        const long longprod = (long)((unsigned long)a * b);
        const double doubleprod = (double)a * (double)b;
        const double doubled_longprod = (double)longprod;

        if (likely(doubled_longprod == doubleprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        } else {
            const double diff = doubled_longprod - doubleprod;
            const double absdiff = diff >= 0.0 ? diff : -diff;
            const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

            if (likely(32.0 * absdiff <= absprod)) {
                clong_result = longprod;
                goto exit_result_ok_clong;
            }
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NUITKA_BOOL_EXCEPTION;
    }

    return __BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(PyObject *operand1,
                                                                                PyObject *operand2) {
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

    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
    binaryfunc slot2 = NULL;

    if (!(&PyInt_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
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

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 = PyInt_Type.tp_as_number->nb_coerce;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyInt_Type == type2) {
        nuitka_bool result;

        // return _BINARY_OPERATION_MULT_NBOOL_INT_INT(operand1, operand2);

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

        const long longprod = (long)((unsigned long)a * b);
        const double doubleprod = (double)a * (double)b;
        const double doubled_longprod = (double)longprod;

        if (likely(doubled_longprod == doubleprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        } else {
            const double diff = doubled_longprod - doubleprod;
            const double absdiff = diff >= 0.0 ? diff : -diff;
            const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

            if (likely(32.0 * absdiff <= absprod)) {
                clong_result = longprod;
                goto exit_result_ok_clong;
            }
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NUITKA_BOOL_EXCEPTION;
    }

    return __BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_INT_OBJECT(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyObject *result;

    // Not every code path will make use of all possible results.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
    assert(x != Py_NotImplemented);

    obj_result = x;
    goto exit_result_object;

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

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(PyObject *operand1,
                                                                                PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyLong_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 = PyLong_Type.tp_as_number->nb_coerce;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // No sequence repeat slot sq_repeat available for this type.

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyLong_Type) {
        PyObject *result;

        // return _BINARY_OPERATION_MULT_OBJECT_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

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

    return __BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(PyObject *operand1,
                                                                                PyObject *operand2) {
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
    binaryfunc slot2 = NULL;

    if (!(&PyLong_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
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

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 = PyLong_Type.tp_as_number->nb_coerce;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyLong_Type == type2) {
        PyObject *result;

        // return _BINARY_OPERATION_MULT_OBJECT_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

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

    return __BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_OBJECT(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    nuitka_bool result;

    // Not every code path will make use of all possible results.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
    assert(x != Py_NotImplemented);

    obj_result = x;
    goto exit_result_object;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(obj_result);
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(PyObject *operand1,
                                                                                 PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyLong_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyLong_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 = PyLong_Type.tp_as_number->nb_coerce;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // No sequence repeat slot sq_repeat available for this type.

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyLong_Type) {
        nuitka_bool result;

        // return _BINARY_OPERATION_MULT_NBOOL_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NUITKA_BOOL_EXCEPTION;
    }

    return __BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(PyObject *operand1,
                                                                                 PyObject *operand2) {
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
    binaryfunc slot2 = NULL;

    if (!(&PyLong_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
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

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 = PyLong_Type.tp_as_number->nb_coerce;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyLong_Type == type2) {
        nuitka_bool result;

        // return _BINARY_OPERATION_MULT_NBOOL_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        PyObject *x = PyLong_Type.tp_as_number->nb_multiply(operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NUITKA_BOOL_EXCEPTION;
    }

    return __BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_LONG_OBJECT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyObject *result;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    double r = a * b;

    cfloat_result = r;
    goto exit_result_ok_cfloat;

exit_result_ok_cfloat:
    result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    goto exit_result_ok;

exit_result_ok:
    return result;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(PyObject *operand1,
                                                                                 PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyFloat_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 = PyFloat_Type.tp_as_number->nb_coerce;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'float'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyFloat_Type) {
        PyObject *result;

        // return _BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(operand1, operand2);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        CHECK_OBJECT(operand1);
        assert(PyFloat_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        double r = a * b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;
    }

    return __BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_FLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(PyObject *operand1,
                                                                                 PyObject *operand2) {
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

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
    binaryfunc slot2 = NULL;

    if (!(&PyFloat_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
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

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 = PyFloat_Type.tp_as_number->nb_coerce;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyFloat_Type == type2) {
        PyObject *result;

        // return _BINARY_OPERATION_MULT_OBJECT_FLOAT_FLOAT(operand1, operand2);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        CHECK_OBJECT(operand1);
        assert(PyFloat_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        double r = a * b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;
    }

    return __BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_OBJECT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    nuitka_bool result;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    double r = a * b;

    cfloat_result = r;
    goto exit_result_ok_cfloat;

exit_result_ok_cfloat:
    result = cfloat_result != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok:
    return result;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(PyObject *operand1,
                                                                                  PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyFloat_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyFloat_Type.tp_as_number->nb_multiply;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 = PyFloat_Type.tp_as_number->nb_coerce;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'float'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyFloat_Type) {
        nuitka_bool result;

        // return _BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(operand1, operand2);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        CHECK_OBJECT(operand1);
        assert(PyFloat_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        double r = a * b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        result = cfloat_result != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok:
        return result;
    }

    return __BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_FLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(PyObject *operand1,
                                                                                  PyObject *operand2) {
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

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
    binaryfunc slot2 = NULL;

    if (!(&PyFloat_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
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

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 = PyFloat_Type.tp_as_number->nb_coerce;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyFloat_Type == type2) {
        nuitka_bool result;

        // return _BINARY_OPERATION_MULT_NBOOL_FLOAT_FLOAT(operand1, operand2);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

        CHECK_OBJECT(operand1);
        assert(PyFloat_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        double r = a * b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        result = cfloat_result != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok:
        return result;
    }

    return __BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_OBJECT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
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

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
    // Slot2 ignored on purpose, type1 takes precedence.

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // No sequence repeat slot sq_repeat available for this type.

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_LONG(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
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

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
    // Slot2 ignored on purpose, type1 takes precedence.

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // No sequence repeat slot sq_repeat available for this type.

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_LONG(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
    // Slot2 ignored on purpose, type1 takes precedence.

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
    // Slot2 ignored on purpose, type1 takes precedence.

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
    // Slot2 ignored on purpose, type1 takes precedence.

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
    // Slot2 ignored on purpose, type1 takes precedence.

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    // No sequence repeat slot sq_repeat available for this type.

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));

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

    const long a = PyInt_AS_LONG(operand1);
    const long b = operand2;

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        clong_result = longprod;
        goto exit_result_ok_clong;
    } else {
        const double diff = doubled_longprod - doubleprod;
        const double absdiff = diff >= 0.0 ? diff : -diff;
        const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

        if (likely(32.0 * absdiff <= absprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        }
    }

    {
        PyObject *operand1_object = operand1;
        PyObject *operand2_object = Nuitka_PyLong_FromLong(operand2);

        PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
        assert(r != Py_NotImplemented);

        Py_DECREF(operand2_object);

        obj_result = r;
        goto exit_result_object;
    }

exit_result_ok_clong:
    result = Nuitka_PyInt_FromLong(clong_result);
    goto exit_result_ok;

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

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_CLONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_INT_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));

    nuitka_bool result;

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

    const long a = PyInt_AS_LONG(operand1);
    const long b = operand2;

    const long longprod = (long)((unsigned long)a * b);
    const double doubleprod = (double)a * (double)b;
    const double doubled_longprod = (double)longprod;

    if (likely(doubled_longprod == doubleprod)) {
        clong_result = longprod;
        goto exit_result_ok_clong;
    } else {
        const double diff = doubled_longprod - doubleprod;
        const double absdiff = diff >= 0.0 ? diff : -diff;
        const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

        if (likely(32.0 * absdiff <= absprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        }
    }

    {
        PyObject *operand1_object = operand1;
        PyObject *operand2_object = Nuitka_PyLong_FromLong(operand2);

        PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
        assert(r != Py_NotImplemented);

        Py_DECREF(operand2_object);

        obj_result = r;
        goto exit_result_object;
    }

exit_result_ok_clong:
    result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    Py_DECREF(obj_result);
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_INT_CLONG(PyObject *operand1, long operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_INT_CLONG(operand1, operand2);
}
#endif

/* Code referring to "FLOAT" corresponds to Python 'float' and "CFLOAT" to C platform float value. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    PyObject *result;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = operand2;

    double r = a * b;

    cfloat_result = r;
    goto exit_result_ok_cfloat;

exit_result_ok_cfloat:
    result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    goto exit_result_ok;

exit_result_ok:
    return result;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_CFLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "CFLOAT" to C platform float value. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    nuitka_bool result;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = operand2;

    double r = a * b;

    cfloat_result = r;
    goto exit_result_ok_cfloat;

exit_result_ok_cfloat:
    result = cfloat_result != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok:
    return result;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_FLOAT_CFLOAT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_STR_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_STR_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_STR_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "STR" to Python2 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_STR(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_UNICODE_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_UNICODE_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "UNICODE" to Python2 'unicode', Python3 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_UNICODE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_UNICODE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "TUPLE" corresponds to Python 'tuple' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_TUPLE_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_TUPLE_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "TUPLE" to Python 'tuple'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_TUPLE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_TUPLE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LIST" corresponds to Python 'list' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LIST_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LIST_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LIST" to Python 'list'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_INT_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = PyInt_AS_LONG(index_value);
            {
                ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_INT_LIST(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_LIST(operand1, operand2);
}
#endif

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "LONG" to Python2 'long', Python3
 * 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
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

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "UNICODE" to Python2 'unicode', Python3
 * 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE(operand1, operand2);
}

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_BYTES_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
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

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_BYTES_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_BYTES_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "BYTES" to Python3 'bytes'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_BYTES(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_BYTES(operand1, operand2);
}
#endif

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
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

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "TUPLE" to Python 'tuple'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LIST_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
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

    // Slot2 ignored on purpose, type1 takes precedence.

    // Statically recognized that coercion is not possible with these types

    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand2;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LIST_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LIST" to Python 'list'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LONG_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // Slot1 ignored on purpose, type2 takes precedence.

    // Statically recognized that coercion is not possible with these types

    {
        // No sequence repeat slot sq_repeat available for this type.
    }
    if (unlikely(!1)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = operand1;

        {
            Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LONG_LIST(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_LIST(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    if (unlikely(!Nuitka_Index_Check(operand1))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand1);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type1->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
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

    if (!(&PyString_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    if (unlikely(!Nuitka_Index_Check(operand2))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand2);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_STR_OBJECT(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    if (unlikely(!Nuitka_Index_Check(operand1))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand1);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type1->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE(operand1, operand2);
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
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

    if (!(&PyUnicode_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    if (unlikely(!Nuitka_Index_Check(operand2))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand2);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION >= 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !0) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    if (unlikely(!Nuitka_Index_Check(operand1))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand1);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type1->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
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

    if (!(&PyBytes_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!0 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    if (unlikely(!Nuitka_Index_Check(operand2))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand2);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !0) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    if (unlikely(!Nuitka_Index_Check(operand1))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand1);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type1->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE(operand1, operand2);
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
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

    if (!(&PyTuple_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!0 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    if (unlikely(!Nuitka_Index_Check(operand2))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand2);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !0) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    if (unlikely(!Nuitka_Index_Check(operand1))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand1);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand1);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type1->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand2, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
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

    if (!(&PyList_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    if (!0 || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    if (unlikely(!Nuitka_Index_Check(operand2))) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("can't multiply sequence by non-int of type '%s'", operand2);

        goto exit_binary_exception;
    }

    {
        PyObject *index_value = Nuitka_Number_Index(operand2);

        if (unlikely(index_value == NULL)) {
            goto exit_binary_exception;
        }

        {
            Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

            Py_DECREF(index_value);

            /* Above conversion indicates an error as -1 */
            if (unlikely(count == -1)) {
                PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                goto exit_binary_exception;
            }
            {
                ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                PyObject *r = (*repeatfunc)(operand1, count);

                obj_result = r;
                goto exit_binary_result_object;
            }
        }
    }

    NUITKA_CANNOT_GET_HERE("missing error exit annotation");

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_MULT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
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

        const long longprod = (long)((unsigned long)a * b);
        const double doubleprod = (double)a * (double)b;
        const double doubled_longprod = (double)longprod;

        if (likely(doubled_longprod == doubleprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        } else {
            const double diff = doubled_longprod - doubleprod;
            const double absdiff = diff >= 0.0 ? diff : -diff;
            const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

            if (likely(32.0 * absdiff <= absprod)) {
                clong_result = longprod;
                goto exit_result_ok_clong;
            }
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        result = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and '%s'", type1->tp_name, type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_MULT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_MULT_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        nuitka_bool result;

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

        const long longprod = (long)((unsigned long)a * b);
        const double doubleprod = (double)a * (double)b;
        const double doubled_longprod = (double)longprod;

        if (likely(doubled_longprod == doubleprod)) {
            clong_result = longprod;
            goto exit_result_ok_clong;
        } else {
            const double diff = doubled_longprod - doubleprod;
            const double absdiff = diff >= 0.0 ? diff : -diff;
            const double absprod = doubleprod >= 0.0 ? doubleprod : -doubleprod;

            if (likely(32.0 * absdiff <= absprod)) {
                clong_result = longprod;
                goto exit_result_ok_clong;
            }
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        result = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NUITKA_BOOL_EXCEPTION;
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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

#if PYTHON_VERSION < 0x300
    if (!NEW_STYLE_NUMBER_TYPE(type1) || !NEW_STYLE_NUMBER_TYPE(type2)) {
        coercion c1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

        if (c1 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c1(&coerced1, &coerced2);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
        coercion c2 =
            (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

        if (c2 != NULL) {
            PyObject *coerced1 = operand1;
            PyObject *coerced2 = operand2;

            int err = c2(&coerced2, &coerced1);

            if (unlikely(err < 0)) {
                goto exit_binary_exception;
            }

            if (err == 0) {
                PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                if (likely(mv == NULL)) {
                    binaryfunc slot = mv->nb_multiply;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2);

                        Py_DECREF(coerced1);
                        Py_DECREF(coerced2);

                        obj_result = x;
                        goto exit_binary_result_object;
                    }
                }

                // nb_coerce took a reference.
                Py_DECREF(coerced1);
                Py_DECREF(coerced2);
            }
        }
    }
#endif

    {
        // Special case for "+" and "*", also works as sequence concat/repeat.
        ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand1, operand2);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }
    // Special case for "*", also work with sequence repeat from right argument.
    {
        ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

        if (sq_slot != NULL) {
            PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, operand1);

            obj_result = result;
            goto exit_binary_result_object;
        }
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and '%s'", type1->tp_name, type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    if (unlikely(obj_result == NULL)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    {
        nuitka_bool r = CHECK_IF_TRUE(obj_result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        Py_DECREF(obj_result);
        return r;
    }

exit_binary_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_MULT_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_NBOOL_OBJECT_OBJECT(operand1, operand2);
}

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
