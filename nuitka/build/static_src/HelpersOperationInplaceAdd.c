//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */
#pragma once

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"

// Includes below require definitions from the prelude.
#include "nuitka/helper/long_helpers.h"
#endif

#include "HelpersOperationInplaceAddUtils.c"
/* C helpers for type in-place "+" (ADD) operations */

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_INT_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    const long a = PyInt_AS_LONG(*operand1);
    const long b = PyInt_AS_LONG(operand2);

    const long x = (long)((unsigned long)a + b);
    bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
    if (likely(no_overflow)) {
        clong_result = x;
        goto exit_result_ok_clong;
    }

    {
        PyObject *operand1_object = *operand1;
        PyObject *operand2_object = operand2;

        PyObject *r = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
        assert(r != Py_NotImplemented);

        obj_result = r;
        goto exit_result_object;
    }

exit_result_ok_clong:
    Py_DECREF(*operand1);
    *operand1 = Nuitka_PyInt_FromLong(clong_result);
    goto exit_result_ok;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_INT_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_INT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == &PyInt_Type)) {
            slot2 = PyInt_Type.tp_as_number->nb_add;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
                        }
                    }

                    // nb_coerce took a reference.
                    Py_DECREF(coerced1);
                    Py_DECREF(coerced2);
                }
            }
            coercion c2 = PyInt_Type.tp_as_number->nb_coerce;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'int'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyInt_Type) {

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED bool cbool_result;
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        CHECK_OBJECT(*operand1);
        assert(PyInt_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(*operand1);
        const long b = PyInt_AS_LONG(operand2);

        const long x = (long)((unsigned long)a + b);
        bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
        if (likely(no_overflow)) {
            clong_result = x;
            goto exit_result_ok_clong;
        }

        {
            PyObject *operand1_object = *operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        Py_DECREF(*operand1);
        *operand1 = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_INT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_INT_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(&PyInt_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c1 = PyInt_Type.tp_as_number->nb_coerce;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'int' and '%s'", type2->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_INT_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyInt_Type == type2) {

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED bool cbool_result;
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        CHECK_OBJECT(*operand1);
        assert(PyInt_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(*operand1);
        const long b = PyInt_AS_LONG(operand2);

        const long x = (long)((unsigned long)a + b);
        bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
        if (likely(no_overflow)) {
            clong_result = x;
            goto exit_result_ok_clong;
        }

        {
            PyObject *operand1_object = *operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        Py_DECREF(*operand1);
        *operand1 = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_INT_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_INT_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_INT_OBJECT(operand1, operand2);
}
#endif

static inline bool _INPLACE_OPERATION_ADD_LONG_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    PyLongObject *operand1_long_object = (PyLongObject *)*operand1;

    PyLongObject *operand2_long_object = (PyLongObject *)operand2;

    if (Nuitka_LongGetDigitSize(operand1_long_object) <= 1 && Nuitka_LongGetDigitSize(operand2_long_object) <= 1) {
        long r = (long)(MEDIUM_VALUE(operand1_long_object) + MEDIUM_VALUE(operand2_long_object));

        if (_PyObject_IsUniquelyReferenced(*operand1)) {
            Nuitka_LongUpdateFromCLong(&*operand1, (long)r);
            goto exit_result_ok;
        } else {
            PyObject *obj = Nuitka_LongFromCLong(r);

            obj_result = obj;
            goto exit_result_object;
        }
        clong_result = r;
        goto exit_result_ok_clong;
    }

    if (_PyObject_IsUniquelyReferenced(*operand1)) {
        digit const *b_digits = Nuitka_LongGetDigitPointer(operand2_long_object);
        Py_ssize_t b_digit_count = Nuitka_LongGetDigitSize(operand2_long_object);

        bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
        bool b_negative = Nuitka_LongIsNegative(operand2_long_object);

        if (a_negative) {
            if (b_negative) {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
                Nuitka_LongSetSignNegative(*operand1);
            } else {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, -1);
            }
        } else {
            if (b_negative) {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, 1);
            } else {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
            }
        }

        goto exit_result_ok;
    }
    {
        PyLongObject *z;

        digit const *a_digits = Nuitka_LongGetDigitPointer(operand1_long_object);
        Py_ssize_t a_digit_count = Nuitka_LongGetDigitSize(operand1_long_object);
        bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
        digit const *b_digits = Nuitka_LongGetDigitPointer(operand2_long_object);
        Py_ssize_t b_digit_count = Nuitka_LongGetDigitSize(operand2_long_object);
        bool b_negative = Nuitka_LongIsNegative(operand2_long_object);

        if (a_negative) {
            if (b_negative) {
                z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                Nuitka_LongFlipSign(z);
            } else {
                z = _Nuitka_LongSubDigits(b_digits, b_digit_count, a_digits, a_digit_count);
            }
        } else {
            if (b_negative) {
                z = _Nuitka_LongSubDigits(a_digits, a_digit_count, b_digits, b_digit_count);
            } else {
                z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
            }
        }

        obj_result = (PyObject *)z;
        goto exit_result_object;
    }

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);
    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok_clong:
    Py_DECREF(*operand1);
    *operand1 = Nuitka_PyLong_FromLong(clong_result);
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_LONG_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_LONG_LONG(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_LONG(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == &PyLong_Type)) {
            slot2 = PyLong_Type.tp_as_number->nb_add;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
                        }
                    }

                    // nb_coerce took a reference.
                    Py_DECREF(coerced1);
                    Py_DECREF(coerced2);
                }
            }
            coercion c2 = PyLong_Type.tp_as_number->nb_coerce;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'long'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'int'", type1->tp_name);
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyLong_Type) {
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        PyLongObject *operand1_long_object = (PyLongObject *)*operand1;

        PyLongObject *operand2_long_object = (PyLongObject *)operand2;

        if (Nuitka_LongGetDigitSize(operand1_long_object) <= 1 && Nuitka_LongGetDigitSize(operand2_long_object) <= 1) {
            long r = (long)(MEDIUM_VALUE(operand1_long_object) + MEDIUM_VALUE(operand2_long_object));

            if (_PyObject_IsUniquelyReferenced(*operand1)) {
                Nuitka_LongUpdateFromCLong(&*operand1, (long)r);
                goto exit_result_ok;
            } else {
                PyObject *obj = Nuitka_LongFromCLong(r);

                obj_result = obj;
                goto exit_result_object;
            }
            clong_result = r;
            goto exit_result_ok_clong;
        }

        if (_PyObject_IsUniquelyReferenced(*operand1)) {
            digit const *b_digits = Nuitka_LongGetDigitPointer(operand2_long_object);
            Py_ssize_t b_digit_count = Nuitka_LongGetDigitSize(operand2_long_object);

            bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
            bool b_negative = Nuitka_LongIsNegative(operand2_long_object);

            if (a_negative) {
                if (b_negative) {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
                    Nuitka_LongSetSignNegative(*operand1);
                } else {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, -1);
                }
            } else {
                if (b_negative) {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, 1);
                } else {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
                }
            }

            goto exit_result_ok;
        }
        {
            PyLongObject *z;

            digit const *a_digits = Nuitka_LongGetDigitPointer(operand1_long_object);
            Py_ssize_t a_digit_count = Nuitka_LongGetDigitSize(operand1_long_object);
            bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
            digit const *b_digits = Nuitka_LongGetDigitPointer(operand2_long_object);
            Py_ssize_t b_digit_count = Nuitka_LongGetDigitSize(operand2_long_object);
            bool b_negative = Nuitka_LongIsNegative(operand2_long_object);

            if (a_negative) {
                if (b_negative) {
                    z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                    Nuitka_LongFlipSign(z);
                } else {
                    z = _Nuitka_LongSubDigits(b_digits, b_digit_count, a_digits, a_digit_count);
                }
            } else {
                if (b_negative) {
                    z = _Nuitka_LongSubDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                } else {
                    z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                }
            }

            obj_result = (PyObject *)z;
            goto exit_result_object;
        }

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);
        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok_clong:
        Py_DECREF(*operand1);
        *operand1 = Nuitka_PyLong_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_LONG(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_LONG(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_LONG_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(&PyLong_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c1 = PyLong_Type.tp_as_number->nb_coerce;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'long' and '%s'", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'int' and '%s'", type2->tp_name);
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_LONG_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyLong_Type == type2) {
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        PyLongObject *operand1_long_object = (PyLongObject *)*operand1;

        PyLongObject *operand2_long_object = (PyLongObject *)operand2;

        if (Nuitka_LongGetDigitSize(operand1_long_object) <= 1 && Nuitka_LongGetDigitSize(operand2_long_object) <= 1) {
            long r = (long)(MEDIUM_VALUE(operand1_long_object) + MEDIUM_VALUE(operand2_long_object));

            if (_PyObject_IsUniquelyReferenced(*operand1)) {
                Nuitka_LongUpdateFromCLong(&*operand1, (long)r);
                goto exit_result_ok;
            } else {
                PyObject *obj = Nuitka_LongFromCLong(r);

                obj_result = obj;
                goto exit_result_object;
            }
            clong_result = r;
            goto exit_result_ok_clong;
        }

        if (_PyObject_IsUniquelyReferenced(*operand1)) {
            digit const *b_digits = Nuitka_LongGetDigitPointer(operand2_long_object);
            Py_ssize_t b_digit_count = Nuitka_LongGetDigitSize(operand2_long_object);

            bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
            bool b_negative = Nuitka_LongIsNegative(operand2_long_object);

            if (a_negative) {
                if (b_negative) {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
                    Nuitka_LongSetSignNegative(*operand1);
                } else {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, -1);
                }
            } else {
                if (b_negative) {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, 1);
                } else {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
                }
            }

            goto exit_result_ok;
        }
        {
            PyLongObject *z;

            digit const *a_digits = Nuitka_LongGetDigitPointer(operand1_long_object);
            Py_ssize_t a_digit_count = Nuitka_LongGetDigitSize(operand1_long_object);
            bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
            digit const *b_digits = Nuitka_LongGetDigitPointer(operand2_long_object);
            Py_ssize_t b_digit_count = Nuitka_LongGetDigitSize(operand2_long_object);
            bool b_negative = Nuitka_LongIsNegative(operand2_long_object);

            if (a_negative) {
                if (b_negative) {
                    z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                    Nuitka_LongFlipSign(z);
                } else {
                    z = _Nuitka_LongSubDigits(b_digits, b_digit_count, a_digits, a_digit_count);
                }
            } else {
                if (b_negative) {
                    z = _Nuitka_LongSubDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                } else {
                    z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                }
            }

            obj_result = (PyObject *)z;
            goto exit_result_object;
        }

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);
        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok_clong:
        Py_DECREF(*operand1);
        *operand1 = Nuitka_PyLong_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_LONG_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_LONG_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_LONG_OBJECT(operand1, operand2);
}

static inline bool _INPLACE_OPERATION_ADD_FLOAT_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    const double a = PyFloat_AS_DOUBLE(*operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    double r = a + b;

    cfloat_result = r;
    goto exit_result_ok_cfloat;

exit_result_ok_cfloat:
    if (_PyObject_IsUniquelyReferenced(*operand1)) {
        PyFloat_SET_DOUBLE(*operand1, cfloat_result);
    } else {
        Py_DECREF(*operand1);

        *operand1 = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    }
    goto exit_result_ok;

exit_result_ok:
    return true;
}

bool INPLACE_OPERATION_ADD_FLOAT_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_FLOAT_FLOAT(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == &PyFloat_Type)) {
            slot2 = PyFloat_Type.tp_as_number->nb_add;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
                        }
                    }

                    // nb_coerce took a reference.
                    Py_DECREF(coerced1);
                    Py_DECREF(coerced2);
                }
            }
            coercion c2 = PyFloat_Type.tp_as_number->nb_coerce;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'float'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyFloat_Type) {
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        CHECK_OBJECT(*operand1);
        assert(PyFloat_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(*operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        double r = a + b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        if (_PyObject_IsUniquelyReferenced(*operand1)) {
            PyFloat_SET_DOUBLE(*operand1, cfloat_result);
        } else {
            Py_DECREF(*operand1);

            *operand1 = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        }
        goto exit_result_ok;

    exit_result_ok:
        return true;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_FLOAT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_FLOAT(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(&PyFloat_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c1 = PyFloat_Type.tp_as_number->nb_coerce;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'float' and '%s'", type2->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyFloat_Type == type2) {
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        CHECK_OBJECT(*operand1);
        assert(PyFloat_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(*operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        double r = a + b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        if (_PyObject_IsUniquelyReferenced(*operand1)) {
            PyFloat_SET_DOUBLE(*operand1, cfloat_result);
        } else {
            Py_DECREF(*operand1);

            *operand1 = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        }
        goto exit_result_ok;

    exit_result_ok:
        return true;
    }

    return __INPLACE_OPERATION_ADD_FLOAT_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_FLOAT_OBJECT(operand1, operand2);
}

static inline bool _INPLACE_OPERATION_ADD_FLOAT_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_add;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        {
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'float' and 'long'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'float' and 'int'");
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_FLOAT_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_FLOAT_LONG(operand1, operand2);
}

static inline bool _INPLACE_OPERATION_ADD_LONG_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            slot2 = PyFloat_Type.tp_as_number->nb_add;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        {
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'long' and 'float'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'int' and 'float'");
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_LONG_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_LONG_FLOAT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_FLOAT_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_add;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        {
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'float' and 'int'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_FLOAT_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_FLOAT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_INT_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            slot2 = PyFloat_Type.tp_as_number->nb_add;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        {
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'int' and 'float'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_INT_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_INT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_LONG_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_add;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        {
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'long' and 'int'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_LONG_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_INT_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            slot2 = PyLong_Type.tp_as_number->nb_add;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        {
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: 'int' and 'long'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_INT_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_INT_CLONG(PyObject **operand1, long operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));

    const long a = PyInt_AS_LONG(*operand1);
    const long b = operand2;

    const long x = (long)((unsigned long)a + b);
    bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
    if (likely(no_overflow)) {
        clong_result = x;
        goto exit_result_ok_clong;
    }

    {
        PyObject *operand1_object = *operand1;
        PyObject *operand2_object = Nuitka_PyLong_FromLong(operand2);

        PyObject *r = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
        assert(r != Py_NotImplemented);

        Py_DECREF(operand2_object);

        obj_result = r;
        goto exit_result_object;
    }

exit_result_ok_clong:
    Py_DECREF(*operand1);
    *operand1 = Nuitka_PyInt_FromLong(clong_result);
    goto exit_result_ok;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_INT_CLONG(PyObject **operand1, long operand2) {
    return _INPLACE_OPERATION_ADD_INT_CLONG(operand1, operand2);
}
#endif

static inline bool _INPLACE_OPERATION_ADD_LONG_DIGIT(PyObject **operand1, long operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    assert(Py_ABS(operand2) < (1 << PyLong_SHIFT));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    PyLongObject *operand1_long_object = (PyLongObject *)*operand1;

    if (Nuitka_LongGetDigitSize(operand1_long_object) <= 1 && (operand2 == 0 ? 0 : 1) <= 1) {
        long r = (long)(MEDIUM_VALUE(operand1_long_object) + (sdigit)operand2);

        if (_PyObject_IsUniquelyReferenced(*operand1)) {
            Nuitka_LongUpdateFromCLong(&*operand1, (long)r);
            goto exit_result_ok;
        } else {
            PyObject *obj = Nuitka_LongFromCLong(r);

            obj_result = obj;
            goto exit_result_object;
        }
        clong_result = r;
        goto exit_result_ok_clong;
    }

    if (_PyObject_IsUniquelyReferenced(*operand1)) {
        digit const *b_digits = (digit *)&operand2;
        Py_ssize_t b_digit_count = (operand2 == 0 ? 0 : 1);

        bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
        bool b_negative = operand2 < 0;

        if (a_negative) {
            if (b_negative) {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
                Nuitka_LongSetSignNegative(*operand1);
            } else {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, -1);
            }
        } else {
            if (b_negative) {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, 1);
            } else {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
            }
        }

        goto exit_result_ok;
    }
    {
        PyLongObject *z;

        digit const *a_digits = Nuitka_LongGetDigitPointer(operand1_long_object);
        Py_ssize_t a_digit_count = Nuitka_LongGetDigitSize(operand1_long_object);
        bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
        digit const *b_digits = (digit *)&operand2;
        Py_ssize_t b_digit_count = (operand2 == 0 ? 0 : 1);
        bool b_negative = operand2 < 0;

        if (a_negative) {
            if (b_negative) {
                z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                Nuitka_LongFlipSign(z);
            } else {
                z = _Nuitka_LongSubDigits(b_digits, b_digit_count, a_digits, a_digit_count);
            }
        } else {
            if (b_negative) {
                z = _Nuitka_LongSubDigits(a_digits, a_digit_count, b_digits, b_digit_count);
            } else {
                z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
            }
        }

        obj_result = (PyObject *)z;
        goto exit_result_object;
    }

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);
    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok_clong:
    Py_DECREF(*operand1);
    *operand1 = Nuitka_PyLong_FromLong(clong_result);
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_LONG_DIGIT(PyObject **operand1, long operand2) {
    return _INPLACE_OPERATION_ADD_LONG_DIGIT(operand1, operand2);
}

static inline bool _INPLACE_OPERATION_ADD_LONG_CLONG(PyObject **operand1, long operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    PyLongObject *operand1_long_object = (PyLongObject *)*operand1;

    bool operand2_is_negative;
    unsigned long operand2_abs_ival;

    if (operand2 < 0) {
        operand2_abs_ival = (unsigned long)(-1 - operand2) + 1;
        operand2_is_negative = true;
    } else {
        operand2_abs_ival = (unsigned long)operand2;
        operand2_is_negative = false;
    }

    Py_ssize_t operand2_digit_count = 0;
    digit operand2_digits[5] = {0}; // Could be more minimal and depend on sizeof(digit)
    {
        unsigned long t = operand2_abs_ival;

        while (t != 0) {
            assert(operand2_digit_count < (Py_ssize_t)(sizeof(operand2_digits) / sizeof(operand2_digits[0])));

            operand2_digits[operand2_digit_count] = (digit)(t & PyLong_MASK);
            operand2_digit_count += 1;
            t >>= PyLong_SHIFT;
        }
    }

    NUITKA_MAY_BE_UNUSED Py_ssize_t operand2_size =
        operand2_is_negative == false ? operand2_digit_count : -operand2_digit_count;

    if (Nuitka_LongGetDigitSize(operand1_long_object) <= 1 && operand2_digit_count <= 1) {
        long r = (long)(MEDIUM_VALUE(operand1_long_object) + (sdigit)operand2);

        if (_PyObject_IsUniquelyReferenced(*operand1)) {
            Nuitka_LongUpdateFromCLong(&*operand1, (long)r);
            goto exit_result_ok;
        } else {
            PyObject *obj = Nuitka_LongFromCLong(r);

            obj_result = obj;
            goto exit_result_object;
        }
        clong_result = r;
        goto exit_result_ok_clong;
    }

    if (_PyObject_IsUniquelyReferenced(*operand1)) {
        digit const *b_digits = operand2_digits;
        Py_ssize_t b_digit_count = operand2_digit_count;

        bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
        bool b_negative = operand2_is_negative;

        if (a_negative) {
            if (b_negative) {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
                Nuitka_LongSetSignNegative(*operand1);
            } else {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, -1);
            }
        } else {
            if (b_negative) {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b_digits, b_digit_count, 1);
            } else {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b_digits, b_digit_count);
            }
        }

        goto exit_result_ok;
    }
    {
        PyLongObject *z;

        digit const *a_digits = Nuitka_LongGetDigitPointer(operand1_long_object);
        Py_ssize_t a_digit_count = Nuitka_LongGetDigitSize(operand1_long_object);
        bool a_negative = Nuitka_LongIsNegative(operand1_long_object);
        digit const *b_digits = operand2_digits;
        Py_ssize_t b_digit_count = operand2_digit_count;
        bool b_negative = operand2_is_negative;

        if (a_negative) {
            if (b_negative) {
                z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
                Nuitka_LongFlipSign(z);
            } else {
                z = _Nuitka_LongSubDigits(b_digits, b_digit_count, a_digits, a_digit_count);
            }
        } else {
            if (b_negative) {
                z = _Nuitka_LongSubDigits(a_digits, a_digit_count, b_digits, b_digit_count);
            } else {
                z = _Nuitka_LongAddDigits(a_digits, a_digit_count, b_digits, b_digit_count);
            }
        }

        obj_result = (PyObject *)z;
        goto exit_result_object;
    }

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);
    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok_clong:
    Py_DECREF(*operand1);
    *operand1 = Nuitka_PyLong_FromLong(clong_result);
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_LONG_CLONG(PyObject **operand1, long operand2) {
    return _INPLACE_OPERATION_ADD_LONG_CLONG(operand1, operand2);
}

static inline bool _INPLACE_OPERATION_ADD_FLOAT_CFLOAT(PyObject **operand1, double operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
    NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));

    const double a = PyFloat_AS_DOUBLE(*operand1);
    const double b = operand2;

    double r = a + b;

    cfloat_result = r;
    goto exit_result_ok_cfloat;

exit_result_ok_cfloat:
    if (_PyObject_IsUniquelyReferenced(*operand1)) {
        PyFloat_SET_DOUBLE(*operand1, cfloat_result);
    } else {
        Py_DECREF(*operand1);

        *operand1 = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    }
    goto exit_result_ok;

exit_result_ok:
    return true;
}

bool INPLACE_OPERATION_ADD_FLOAT_CFLOAT(PyObject **operand1, double operand2) {
    return _INPLACE_OPERATION_ADD_FLOAT_CFLOAT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_STR_STR(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    if (_PyObject_IsUniquelyReferenced(*operand1)) {
#if PYTHON_VERSION < 0x300
        if (1 && !PyString_CHECK_INTERNED(*operand1) && 1) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    if (1 && 1) {
        PyString_Concat(operand1, operand2);

        PyThreadState *tstate = PyThreadState_GET();

        return !HAS_ERROR_OCCURRED(tstate);
    }
#endif

    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = PyString_Type.tp_as_sequence->sq_concat(*operand1, operand2);
    assert(x != Py_NotImplemented);

    obj_result = x;
    goto exit_result_object;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_STR_STR(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_STR_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_STR(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'str'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_STR(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    if (_PyObject_IsUniquelyReferenced(*operand1)) {
#if PYTHON_VERSION < 0x300
        if (PyString_CheckExact(*operand1) && !PyString_CHECK_INTERNED(*operand1) && 1) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyString_Type) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyString_Type.tp_as_sequence->sq_concat(*operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_STR(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_STR(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_STR_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(&PyString_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            PyObject *o = PyString_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _INPLACE_OPERATION_ADD_STR_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    if (_PyObject_IsUniquelyReferenced(*operand1)) {
#if PYTHON_VERSION < 0x300
        if (1 && !PyString_CHECK_INTERNED(*operand1) && PyString_CheckExact(operand2)) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyString_Type == type2) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyString_Type.tp_as_sequence->sq_concat(*operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_STR_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_STR_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_STR_OBJECT(operand1, operand2);
}
#endif

static inline bool _INPLACE_OPERATION_ADD_UNICODE_UNICODE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    if (_PyObject_IsUniquelyReferenced(*operand1)) {

#if PYTHON_VERSION >= 0x300
        if (1 && !PyUnicode_CHECK_INTERNED(*operand1) && 1) {
            PyThreadState *tstate = PyThreadState_GET();

            return UNICODE_ADD_INCREMENTAL(tstate, operand1, operand2);
        }
#endif
    }

    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *x = UNICODE_CONCAT(tstate, *operand1, operand2);

    obj_result = x;
    goto exit_result_object;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_UNICODE_UNICODE(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_UNICODE_UNICODE(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_UNICODE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !1) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'unicode'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'str'", type1->tp_name);
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_UNICODE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    if (_PyObject_IsUniquelyReferenced(*operand1)) {

#if PYTHON_VERSION >= 0x300
        if (PyUnicode_CheckExact(*operand1) && !PyUnicode_CHECK_INTERNED(*operand1) && 1) {
            PyThreadState *tstate = PyThreadState_GET();

            return UNICODE_ADD_INCREMENTAL(tstate, operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyUnicode_Type) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyThreadState *tstate = PyThreadState_GET();

        PyObject *x = UNICODE_CONCAT(tstate, *operand1, operand2);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_UNICODE(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_UNICODE(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_UNICODE(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_UNICODE_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(&PyUnicode_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!1 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            PyObject *o = PyUnicode_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _INPLACE_OPERATION_ADD_UNICODE_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    if (_PyObject_IsUniquelyReferenced(*operand1)) {

#if PYTHON_VERSION >= 0x300
        if (1 && !PyUnicode_CHECK_INTERNED(*operand1) && PyUnicode_CheckExact(operand2)) {
            PyThreadState *tstate = PyThreadState_GET();

            return UNICODE_ADD_INCREMENTAL(tstate, operand1, operand2);
        }
#endif
    }

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyUnicode_Type == type2) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyThreadState *tstate = PyThreadState_GET();

        PyObject *x = UNICODE_CONCAT(tstate, *operand1, operand2);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_UNICODE_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_UNICODE_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_UNICODE_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION >= 0x300
static inline bool _INPLACE_OPERATION_ADD_BYTES_BYTES(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyBytes_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    if (_PyObject_IsUniquelyReferenced(*operand1)) {

#if PYTHON_VERSION >= 0x300
        if (1 && 1) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat(*operand1, operand2);
    assert(x != Py_NotImplemented);

    obj_result = x;
    goto exit_result_object;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_BYTES_BYTES(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_BYTES_BYTES(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_BYTES(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !0) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'bytes'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_BYTES(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    if (_PyObject_IsUniquelyReferenced(*operand1)) {

#if PYTHON_VERSION >= 0x300
        if (PyBytes_CheckExact(*operand1) && 1) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyBytes_Type) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat(*operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_BYTES(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_BYTES(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_BYTES(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_BYTES_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(&PyBytes_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!0 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            PyObject *o = PyBytes_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _INPLACE_OPERATION_ADD_BYTES_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyBytes_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    if (_PyObject_IsUniquelyReferenced(*operand1)) {

#if PYTHON_VERSION >= 0x300
        if (1 && PyBytes_CheckExact(operand2)) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyBytes_Type == type2) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat(*operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_BYTES_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_BYTES_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_BYTES_OBJECT(operand1, operand2);
}
#endif

static inline bool _INPLACE_OPERATION_ADD_TUPLE_TUPLE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

    if (1 && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *x = TUPLE_CONCAT(tstate, *operand1, operand2);

    assert(x != Py_NotImplemented);
    obj_result = x;
    goto exit_result_object;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_TUPLE_TUPLE(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_TUPLE_TUPLE(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_TUPLE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !0) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'tuple'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_TUPLE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyTuple_Type) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyThreadState *tstate = PyThreadState_GET();

        PyObject *x = TUPLE_CONCAT(tstate, *operand1, operand2);

        assert(x != Py_NotImplemented);
        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_TUPLE(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_TUPLE(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_TUPLE(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_TUPLE_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(&PyTuple_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!0 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            PyObject *o = PyTuple_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _INPLACE_OPERATION_ADD_TUPLE_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    if (1 && (PyTuple_CheckExact(operand2) || PySequence_Check(operand2)) &&
        (Py_TYPE(operand2)->tp_as_number == NULL || Py_TYPE(operand2)->tp_as_number->nb_add == NULL)) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyTuple_Type == type2) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyThreadState *tstate = PyThreadState_GET();

        PyObject *x = TUPLE_CONCAT(tstate, *operand1, operand2);

        assert(x != Py_NotImplemented);
        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_TUPLE_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_TUPLE_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_TUPLE_OBJECT(operand1, operand2);
}

static inline bool _INPLACE_OPERATION_ADD_LIST_LIST(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

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

    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyThreadState *tstate = PyThreadState_GET();

    PyObject *x = LIST_CONCAT(tstate, *operand1, operand2);
    assert(x != Py_NotImplemented);

    obj_result = x;
    goto exit_result_object;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_LIST_LIST(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_LIST_LIST(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_OBJECT_LIST(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !0) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and 'list'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_ADD_OBJECT_LIST(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    if (PyList_CheckExact(*operand1) && 1) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyList_Type) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyThreadState *tstate = PyThreadState_GET();

        PyObject *x = LIST_CONCAT(tstate, *operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_OBJECT_LIST(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_OBJECT_LIST(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_LIST(operand1, operand2);
}

static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_ADD_LIST_OBJECT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {
        binaryfunc slot2 = NULL;

        if (!(&PyList_Type == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!0 || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_coerce : NULL;

            if (c2 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            PyObject *o = PyList_Type.tp_as_sequence->sq_inplace_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }
        {
            PyObject *o = PyList_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _INPLACE_OPERATION_ADD_LIST_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    if (1 && PyList_CheckExact(operand2)) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    if (1 && PySequence_Check(operand2) &&
        (Py_TYPE(operand2)->tp_as_number == NULL || Py_TYPE(operand2)->tp_as_number->nb_add == NULL)) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyList_Type == type2) {
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyThreadState *tstate = PyThreadState_GET();

        PyObject *x = LIST_CONCAT(tstate, *operand1, operand2);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_ADD_LIST_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_ADD_LIST_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_LIST_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_UNICODE_STR(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {

        {
            PyObject *o = PyUnicode_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;
}

bool INPLACE_OPERATION_ADD_UNICODE_STR(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_UNICODE_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static inline bool _INPLACE_OPERATION_ADD_STR_UNICODE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {

        {
            PyObject *o = PyUnicode_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;
}

bool INPLACE_OPERATION_ADD_STR_UNICODE(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_STR_UNICODE(operand1, operand2);
}
#endif

static inline bool _INPLACE_OPERATION_ADD_OBJECT_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(*operand1) && PyInt_CheckExact(operand2)) {

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED bool cbool_result;
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
        NUITKA_MAY_BE_UNUSED double cfloat_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        CHECK_OBJECT(*operand1);
        assert(PyInt_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(*operand1);
        const long b = PyInt_AS_LONG(operand2);

        const long x = (long)((unsigned long)a + b);
        bool no_overflow = ((x ^ a) >= 0 || (x ^ b) >= 0);
        if (likely(no_overflow)) {
            clong_result = x;
            goto exit_result_ok_clong;
        }

        {
            PyObject *operand1_object = *operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_add(operand1_object, operand2_object);
            assert(r != Py_NotImplemented);

            obj_result = r;
            goto exit_result_object;
        }

    exit_result_ok_clong:
        Py_DECREF(*operand1);
        *operand1 = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }
#endif

    if (_PyObject_IsUniquelyReferenced(*operand1)) {
#if PYTHON_VERSION < 0x300
        if (PyString_CheckExact(*operand1) && !PyString_CHECK_INTERNED(*operand1) && PyString_CheckExact(operand2)) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif

#if PYTHON_VERSION >= 0x300
        if (PyUnicode_CheckExact(*operand1) && !PyUnicode_CHECK_INTERNED(*operand1) && PyUnicode_CheckExact(operand2)) {
            PyThreadState *tstate = PyThreadState_GET();

            return UNICODE_ADD_INCREMENTAL(tstate, operand1, operand2);
        }
#endif
    }

    if (Py_TYPE(*operand1) == Py_TYPE(operand2)) {
        if (PyFloat_CheckExact(operand2)) {
            return _INPLACE_OPERATION_ADD_FLOAT_FLOAT(operand1, operand2);
        }
#if PYTHON_VERSION >= 0x300
        if (PyLong_CheckExact(operand2)) {
            return _INPLACE_OPERATION_ADD_LONG_LONG(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    if (PyString_CheckExact(*operand1) && PyString_CheckExact(operand2)) {
        PyString_Concat(operand1, operand2);

        PyThreadState *tstate = PyThreadState_GET();

        return !HAS_ERROR_OCCURRED(tstate);
    }
#endif
#if PYTHON_VERSION >= 0x300
    if (PyUnicode_CheckExact(*operand1) && PyUnicode_CheckExact(operand2)) {
        PyThreadState *tstate = PyThreadState_GET();

        PyObject *result = UNICODE_CONCAT(tstate, *operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, type1)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

#if PYTHON_VERSION < 0x300
        if (!NEW_STYLE_NUMBER_TYPE(type1) || !NEW_STYLE_NUMBER_TYPE(type2)) {
            coercion c1 =
                (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_coerce : NULL;

            if (c1 != NULL) {
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c1(&coerced1, &coerced2);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
                PyObject *coerced1 = *operand1;
                PyObject *coerced2 = operand2;

                int err = c2(&coerced2, &coerced1);

                if (unlikely(err < 0)) {
                    goto exit_inplace_exception;
                }

                if (err == 0) {
                    PyNumberMethods *mv = Py_TYPE(coerced1)->tp_as_number;

                    if (likely(mv == NULL)) {
                        binaryfunc slot = mv->nb_add;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2);

                            Py_DECREF(coerced1);
                            Py_DECREF(coerced2);

                            obj_result = x;
                            goto exit_inplace_result_object;
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
            binaryfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_concat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_concat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = sq_slot(*operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +=: '%s' and '%s'", type1->tp_name,
                     type2->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_ADD_OBJECT_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_OBJECT_OBJECT(operand1, operand2);
}

static inline bool _INPLACE_OPERATION_ADD_LIST_TUPLE(PyObject **operand1, PyObject *operand2) {
    assert(operand1);

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

    if (1 && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    {

        {
            PyObject *o = PyList_Type.tp_as_sequence->sq_inplace_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }
        {
            PyObject *o = PyList_Type.tp_as_sequence->sq_concat(*operand1, operand2);
            obj_result = o;
            goto exit_inplace_result_object;
        }

        NUITKA_CANNOT_GET_HERE("missing error exit annotation");
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    Py_DECREF(*operand1);
    *operand1 = obj_result;

    return true;
}

bool INPLACE_OPERATION_ADD_LIST_TUPLE(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_ADD_LIST_TUPLE(operand1, operand2);
}

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
