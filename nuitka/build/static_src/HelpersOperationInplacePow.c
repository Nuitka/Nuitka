//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type in-place "**" (POW) operations */

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static inline bool _INPLACE_OPERATION_POW_FLOAT_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

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

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    double a = PyFloat_AS_DOUBLE(*operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    if (b == 0) {
        goto exit_result_ok_const_float_1_0;
    }

    if (Py_IS_NAN(a)) {
        goto exit_result_ok_left;
    }

    if (Py_IS_NAN(b)) {
        if (a == 1.0) {
            goto exit_result_ok_const_float_1_0;
        } else {
            goto exit_result_ok_right;
        }
    }

    if (Py_IS_INFINITY(b)) {
        a = fabs(a);
        if (a == 1.0) {
            goto exit_result_ok_const_float_1_0;
        } else if ((b > 0.0) == (a > 1.0)) {
            long r = (long)fabs(b);

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        } else {
            goto exit_result_ok_const_float_0_0;
        }
    }

    if (Py_IS_INFINITY(a)) {
        bool b_is_odd = DOUBLE_IS_ODD_INTEGER(b);
        double r;

        if (b > 0.0) {
            r = b_is_odd ? a : fabs(a);
        } else {
            r = b_is_odd ? copysign(0.0, a) : 0.0;
        }

        cfloat_result = r;
        goto exit_result_ok_cfloat;
    }

    if (a == 0.0) {
        if (unlikely(b < 0.0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError,
                                            "0.0 cannot be raised to a negative power");
            goto exit_result_exception;
        }

        bool b_is_odd = DOUBLE_IS_ODD_INTEGER(b);
        double r = b_is_odd ? a : 0.0;

        cfloat_result = r;
        goto exit_result_ok_cfloat;
    }

    {
        bool negate_result = false;

        if (a < 0.0) {
            if (unlikely(b != floor(b))) {
                PyThreadState *tstate = PyThreadState_GET();

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError,
                                                "negative number cannot be raised to a fractional power");
                goto exit_result_exception;
            }

            a = -a;
            negate_result = DOUBLE_IS_ODD_INTEGER(b);
        }

        if (a == 1.0) {
            if (negate_result) {
                goto exit_result_ok_const_float_minus_1_0;
            } else {
                goto exit_result_ok_const_float_1_0;
            }
        } else {
            errno = 0;
            double r = pow(a, b);

            if (unlikely(errno != 0)) {
                PyErr_SetFromErrno(errno == ERANGE ? PyExc_OverflowError : PyExc_ValueError);
                goto exit_result_exception;
            }

            r = negate_result ? -r : r;

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        }
    }

exit_result_ok_cfloat:
    if (Py_REFCNT(*operand1) == 1) {
        PyFloat_SET_DOUBLE(*operand1, cfloat_result);
    } else {
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        *operand1 = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    }
    goto exit_result_ok;

exit_result_ok_left:
    goto exit_result_ok;

exit_result_ok_right:
    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);
    *operand1 = operand2;
    goto exit_result_ok;

exit_result_ok_const_float_0_0:
    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);
    *operand1 = MAKE_FLOAT_FROM_DOUBLE(0.0);
    goto exit_result_ok;

exit_result_ok_const_float_1_0:
    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);
    *operand1 = MAKE_FLOAT_FROM_DOUBLE(1.0);
    goto exit_result_ok;

exit_result_ok_const_float_minus_1_0:
    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);
    *operand1 = MAKE_FLOAT_FROM_DOUBLE(-1.0);
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_POW_FLOAT_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_POW_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_power : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        ternaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
        ternaryfunc slot2 = NULL;

        if (!(type1 == &PyFloat_Type)) {
            // Different types, need to consider second value slot.

            slot2 = PyFloat_Type.tp_as_number->nb_power;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: '%s' and 'float'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_POW_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyFloat_Type) {
        // return _BINARY_OPERATION_POW_FLOAT_FLOAT_INPLACE(operand1, operand2);

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

        CHECK_OBJECT(*operand1);
        assert(PyFloat_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        double a = PyFloat_AS_DOUBLE(*operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        if (b == 0) {
            goto exit_result_ok_const_float_1_0;
        }

        if (Py_IS_NAN(a)) {
            goto exit_result_ok_left;
        }

        if (Py_IS_NAN(b)) {
            if (a == 1.0) {
                goto exit_result_ok_const_float_1_0;
            } else {
                goto exit_result_ok_right;
            }
        }

        if (Py_IS_INFINITY(b)) {
            a = fabs(a);
            if (a == 1.0) {
                goto exit_result_ok_const_float_1_0;
            } else if ((b > 0.0) == (a > 1.0)) {
                long r = (long)fabs(b);

                cfloat_result = r;
                goto exit_result_ok_cfloat;
            } else {
                goto exit_result_ok_const_float_0_0;
            }
        }

        if (Py_IS_INFINITY(a)) {
            bool b_is_odd = DOUBLE_IS_ODD_INTEGER(b);
            double r;

            if (b > 0.0) {
                r = b_is_odd ? a : fabs(a);
            } else {
                r = b_is_odd ? copysign(0.0, a) : 0.0;
            }

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        }

        if (a == 0.0) {
            if (unlikely(b < 0.0)) {
                PyThreadState *tstate = PyThreadState_GET();

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError,
                                                "0.0 cannot be raised to a negative power");
                goto exit_result_exception;
            }

            bool b_is_odd = DOUBLE_IS_ODD_INTEGER(b);
            double r = b_is_odd ? a : 0.0;

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        }

        {
            bool negate_result = false;

            if (a < 0.0) {
                if (unlikely(b != floor(b))) {
                    PyThreadState *tstate = PyThreadState_GET();

                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError,
                                                    "negative number cannot be raised to a fractional power");
                    goto exit_result_exception;
                }

                a = -a;
                negate_result = DOUBLE_IS_ODD_INTEGER(b);
            }

            if (a == 1.0) {
                if (negate_result) {
                    goto exit_result_ok_const_float_minus_1_0;
                } else {
                    goto exit_result_ok_const_float_1_0;
                }
            } else {
                errno = 0;
                double r = pow(a, b);

                if (unlikely(errno != 0)) {
                    PyErr_SetFromErrno(errno == ERANGE ? PyExc_OverflowError : PyExc_ValueError);
                    goto exit_result_exception;
                }

                r = negate_result ? -r : r;

                cfloat_result = r;
                goto exit_result_ok_cfloat;
            }
        }

    exit_result_ok_cfloat:
        if (Py_REFCNT(*operand1) == 1) {
            PyFloat_SET_DOUBLE(*operand1, cfloat_result);
        } else {
            // We got an object handed, that we have to release.
            Py_DECREF(*operand1);

            *operand1 = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        }
        goto exit_result_ok;

    exit_result_ok_left:
        goto exit_result_ok;

    exit_result_ok_right:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = operand2;
        goto exit_result_ok;

    exit_result_ok_const_float_0_0:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = MAKE_FLOAT_FROM_DOUBLE(0.0);
        goto exit_result_ok;

    exit_result_ok_const_float_1_0:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = MAKE_FLOAT_FROM_DOUBLE(1.0);
        goto exit_result_ok;

    exit_result_ok_const_float_minus_1_0:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = MAKE_FLOAT_FROM_DOUBLE(-1.0);
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_POW_OBJECT_FLOAT(operand1, operand2);
}

bool INPLACE_OPERATION_POW_OBJECT_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_OBJECT_FLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_POW_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_power available for this type.

    {
        ternaryfunc slot1 = PyFloat_Type.tp_as_number->nb_power;
        ternaryfunc slot2 = NULL;

        if (!(&PyFloat_Type == type2)) {
            // Different types, need to consider second value slot.

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
                    PyObject *x = slot2(*operand1, operand2, Py_None);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'float' and '%s'", type2->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_POW_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyFloat_Type == type2) {
        // return _BINARY_OPERATION_POW_FLOAT_FLOAT_INPLACE(operand1, operand2);

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

        CHECK_OBJECT(*operand1);
        assert(PyFloat_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        double a = PyFloat_AS_DOUBLE(*operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        if (b == 0) {
            goto exit_result_ok_const_float_1_0;
        }

        if (Py_IS_NAN(a)) {
            goto exit_result_ok_left;
        }

        if (Py_IS_NAN(b)) {
            if (a == 1.0) {
                goto exit_result_ok_const_float_1_0;
            } else {
                goto exit_result_ok_right;
            }
        }

        if (Py_IS_INFINITY(b)) {
            a = fabs(a);
            if (a == 1.0) {
                goto exit_result_ok_const_float_1_0;
            } else if ((b > 0.0) == (a > 1.0)) {
                long r = (long)fabs(b);

                cfloat_result = r;
                goto exit_result_ok_cfloat;
            } else {
                goto exit_result_ok_const_float_0_0;
            }
        }

        if (Py_IS_INFINITY(a)) {
            bool b_is_odd = DOUBLE_IS_ODD_INTEGER(b);
            double r;

            if (b > 0.0) {
                r = b_is_odd ? a : fabs(a);
            } else {
                r = b_is_odd ? copysign(0.0, a) : 0.0;
            }

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        }

        if (a == 0.0) {
            if (unlikely(b < 0.0)) {
                PyThreadState *tstate = PyThreadState_GET();

                SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError,
                                                "0.0 cannot be raised to a negative power");
                goto exit_result_exception;
            }

            bool b_is_odd = DOUBLE_IS_ODD_INTEGER(b);
            double r = b_is_odd ? a : 0.0;

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        }

        {
            bool negate_result = false;

            if (a < 0.0) {
                if (unlikely(b != floor(b))) {
                    PyThreadState *tstate = PyThreadState_GET();

                    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError,
                                                    "negative number cannot be raised to a fractional power");
                    goto exit_result_exception;
                }

                a = -a;
                negate_result = DOUBLE_IS_ODD_INTEGER(b);
            }

            if (a == 1.0) {
                if (negate_result) {
                    goto exit_result_ok_const_float_minus_1_0;
                } else {
                    goto exit_result_ok_const_float_1_0;
                }
            } else {
                errno = 0;
                double r = pow(a, b);

                if (unlikely(errno != 0)) {
                    PyErr_SetFromErrno(errno == ERANGE ? PyExc_OverflowError : PyExc_ValueError);
                    goto exit_result_exception;
                }

                r = negate_result ? -r : r;

                cfloat_result = r;
                goto exit_result_ok_cfloat;
            }
        }

    exit_result_ok_cfloat:
        if (Py_REFCNT(*operand1) == 1) {
            PyFloat_SET_DOUBLE(*operand1, cfloat_result);
        } else {
            // We got an object handed, that we have to release.
            Py_DECREF(*operand1);

            *operand1 = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        }
        goto exit_result_ok;

    exit_result_ok_left:
        goto exit_result_ok;

    exit_result_ok_right:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = operand2;
        goto exit_result_ok;

    exit_result_ok_const_float_0_0:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = MAKE_FLOAT_FROM_DOUBLE(0.0);
        goto exit_result_ok;

    exit_result_ok_const_float_1_0:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = MAKE_FLOAT_FROM_DOUBLE(1.0);
        goto exit_result_ok;

    exit_result_ok_const_float_minus_1_0:
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = MAKE_FLOAT_FROM_DOUBLE(-1.0);
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_POW_FLOAT_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_POW_FLOAT_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_FLOAT_OBJECT(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _INPLACE_OPERATION_POW_LONG_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

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

    PyObject *x = PyLong_Type.tp_as_number->nb_power(*operand1, operand2, Py_None);
    assert(x != Py_NotImplemented);

    obj_result = x;
    goto exit_result_object;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);
    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_POW_LONG_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_POW_OBJECT_LONG(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_power : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        ternaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
        ternaryfunc slot2 = NULL;

        if (!(type1 == &PyLong_Type)) {
            // Different types, need to consider second value slot.

            slot2 = PyLong_Type.tp_as_number->nb_power;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: '%s' and 'long'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: '%s' and 'int'", type1->tp_name);
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_POW_OBJECT_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyLong_Type) {
        // return _BINARY_OPERATION_POW_LONG_LONG_INPLACE(operand1, operand2);

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

        PyObject *x = PyLong_Type.tp_as_number->nb_power(*operand1, operand2, Py_None);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_POW_OBJECT_LONG(operand1, operand2);
}

bool INPLACE_OPERATION_POW_OBJECT_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_POW_LONG_OBJECT(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_power available for this type.

    {
        ternaryfunc slot1 = PyLong_Type.tp_as_number->nb_power;
        ternaryfunc slot2 = NULL;

        if (!(&PyLong_Type == type2)) {
            // Different types, need to consider second value slot.

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
                    PyObject *x = slot2(*operand1, operand2, Py_None);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'long' and '%s'", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'int' and '%s'", type2->tp_name);
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_POW_LONG_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyLong_Type == type2) {
        // return _BINARY_OPERATION_POW_LONG_LONG_INPLACE(operand1, operand2);

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

        PyObject *x = PyLong_Type.tp_as_number->nb_power(*operand1, operand2, Py_None);
        assert(x != Py_NotImplemented);

        obj_result = x;
        goto exit_result_object;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);
        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_POW_LONG_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_POW_LONG_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_LONG_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static inline bool _INPLACE_OPERATION_POW_INT_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

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

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    const long a = PyInt_AS_LONG(*operand1);
    const long b = PyInt_AS_LONG(operand2);

    if (b < 0) {
        // TODO: Use CFLOAT once available.
        PyObject *operand1_float = MAKE_FLOAT_FROM_DOUBLE(a);
        PyObject *operand2_float = MAKE_FLOAT_FROM_DOUBLE(b);

        PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

        Py_DECREF(operand1_float);
        Py_DECREF(operand2_float);

        obj_result = r;
        goto exit_result_object;
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
                    PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                    PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    obj_result = r;
                    goto exit_result_object;
                }
            }
            bb >>= 1;
            if (bb == 0) {
                break;
            }
            prev = temp;
            temp = (unsigned long)temp * temp;

            if (prev != 0 && temp / prev != prev) {
                PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                Py_DECREF(operand1_long);
                Py_DECREF(operand2_long);

                obj_result = r;
                goto exit_result_object;
            }
        }

        clong_result = ix;
        goto exit_result_ok_clong;
    }

exit_result_ok_clong:

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = Nuitka_PyInt_FromLong(clong_result);
    goto exit_result_ok;

exit_result_object:
    if (unlikely(obj_result == NULL)) {
        goto exit_result_exception;
    }
    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    *operand1 = obj_result;
    goto exit_result_ok;

exit_result_ok:
    return true;

exit_result_exception:
    return false;
}

bool INPLACE_OPERATION_POW_INT_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_POW_OBJECT_INT(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_power : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        ternaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
        ternaryfunc slot2 = NULL;

        if (!(type1 == &PyInt_Type)) {
            // Different types, need to consider second value slot.

            slot2 = PyInt_Type.tp_as_number->nb_power;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: '%s' and 'int'", type1->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_POW_OBJECT_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(*operand1);

    if (type1 == &PyInt_Type) {
        // return _BINARY_OPERATION_POW_INT_INT_INPLACE(operand1, operand2);

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

        CHECK_OBJECT(*operand1);
        assert(PyInt_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(*operand1);
        const long b = PyInt_AS_LONG(operand2);

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = MAKE_FLOAT_FROM_DOUBLE(a);
            PyObject *operand2_float = MAKE_FLOAT_FROM_DOUBLE(b);

            PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

            Py_DECREF(operand1_float);
            Py_DECREF(operand2_float);

            obj_result = r;
            goto exit_result_object;
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
                        PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                        PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                        PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                        Py_DECREF(operand1_long);
                        Py_DECREF(operand2_long);

                        obj_result = r;
                        goto exit_result_object;
                    }
                }
                bb >>= 1;
                if (bb == 0) {
                    break;
                }
                prev = temp;
                temp = (unsigned long)temp * temp;

                if (prev != 0 && temp / prev != prev) {
                    PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                    PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    obj_result = r;
                    goto exit_result_object;
                }
            }

            clong_result = ix;
            goto exit_result_ok_clong;
        }

    exit_result_ok_clong:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_POW_OBJECT_INT(operand1, operand2);
}

bool INPLACE_OPERATION_POW_OBJECT_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __INPLACE_OPERATION_POW_INT_OBJECT(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_power available for this type.

    {
        ternaryfunc slot1 = PyInt_Type.tp_as_number->nb_power;
        ternaryfunc slot2 = NULL;

        if (!(&PyInt_Type == type2)) {
            // Different types, need to consider second value slot.

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
                    PyObject *x = slot2(*operand1, operand2, Py_None);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'int' and '%s'", type2->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}
static inline bool _INPLACE_OPERATION_POW_INT_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyInt_Type == type2) {
        // return _BINARY_OPERATION_POW_INT_INT_INPLACE(operand1, operand2);

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

        CHECK_OBJECT(*operand1);
        assert(PyInt_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(*operand1);
        const long b = PyInt_AS_LONG(operand2);

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = MAKE_FLOAT_FROM_DOUBLE(a);
            PyObject *operand2_float = MAKE_FLOAT_FROM_DOUBLE(b);

            PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

            Py_DECREF(operand1_float);
            Py_DECREF(operand2_float);

            obj_result = r;
            goto exit_result_object;
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
                        PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                        PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                        PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                        Py_DECREF(operand1_long);
                        Py_DECREF(operand2_long);

                        obj_result = r;
                        goto exit_result_object;
                    }
                }
                bb >>= 1;
                if (bb == 0) {
                    break;
                }
                prev = temp;
                temp = (unsigned long)temp * temp;

                if (prev != 0 && temp / prev != prev) {
                    PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                    PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    obj_result = r;
                    goto exit_result_object;
                }
            }

            clong_result = ix;
            goto exit_result_ok_clong;
        }

    exit_result_ok_clong:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }

    return __INPLACE_OPERATION_POW_INT_OBJECT(operand1, operand2);
}

bool INPLACE_OPERATION_POW_INT_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_INT_OBJECT(operand1, operand2);
}
#endif

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _INPLACE_OPERATION_POW_FLOAT_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
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

    // No inplace number slot nb_inplace_power available for this type.

    {
        ternaryfunc slot1 = PyFloat_Type.tp_as_number->nb_power;
        // Slot2 ignored on purpose, type1 takes precedence.

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        // Statically recognized that coercion is not possible with these types

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'float' and 'long'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'float' and 'int'");
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_POW_FLOAT_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_FLOAT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "FLOAT" to Python 'float'. */
static inline bool _INPLACE_OPERATION_POW_LONG_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // No inplace number slot nb_inplace_power available for this type.

    {
        // Slot1 ignored on purpose, type2 takes precedence.
        ternaryfunc slot2 = NULL;

        if (!(0)) {
            // Different types, need to consider second value slot.

            slot2 = PyFloat_Type.tp_as_number->nb_power;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        // Statically recognized that coercion is not possible with these types

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'long' and 'float'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'int' and 'float'");
#endif
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_POW_LONG_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_LONG_FLOAT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static inline bool _INPLACE_OPERATION_POW_FLOAT_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
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

    // No inplace number slot nb_inplace_power available for this type.

    {
        ternaryfunc slot1 = PyFloat_Type.tp_as_number->nb_power;
        // Slot2 ignored on purpose, type1 takes precedence.

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        // Statically recognized that coercion is not possible with these types

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'float' and 'int'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_POW_FLOAT_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_FLOAT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "FLOAT" to Python 'float'. */
static inline bool _INPLACE_OPERATION_POW_INT_FLOAT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // No inplace number slot nb_inplace_power available for this type.

    {
        // Slot1 ignored on purpose, type2 takes precedence.
        ternaryfunc slot2 = NULL;

        if (!(0)) {
            // Different types, need to consider second value slot.

            slot2 = PyFloat_Type.tp_as_number->nb_power;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        // Statically recognized that coercion is not possible with these types

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'int' and 'float'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_POW_INT_FLOAT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_INT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static inline bool _INPLACE_OPERATION_POW_LONG_INT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
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

    // No inplace number slot nb_inplace_power available for this type.

    {
        ternaryfunc slot1 = PyLong_Type.tp_as_number->nb_power;
        // Slot2 ignored on purpose, type1 takes precedence.

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        // Statically recognized that coercion is not possible with these types

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'long' and 'int'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_POW_LONG_INT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _INPLACE_OPERATION_POW_INT_LONG(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
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

    // No inplace number slot nb_inplace_power available for this type.

    {
        // Slot1 ignored on purpose, type2 takes precedence.
        ternaryfunc slot2 = NULL;

        if (!(0)) {
            // Different types, need to consider second value slot.

            slot2 = PyLong_Type.tp_as_number->nb_power;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        // Statically recognized that coercion is not possible with these types

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: 'int' and 'long'");
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_POW_INT_LONG(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_INT_LONG(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static inline bool _INPLACE_OPERATION_POW_OBJECT_OBJECT(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(*operand1) && PyInt_CheckExact(operand2)) {

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

        CHECK_OBJECT(*operand1);
        assert(PyInt_CheckExact(*operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(*operand1);
        const long b = PyInt_AS_LONG(operand2);

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = MAKE_FLOAT_FROM_DOUBLE(a);
            PyObject *operand2_float = MAKE_FLOAT_FROM_DOUBLE(b);

            PyObject *r = _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1_float, operand2_float);

            Py_DECREF(operand1_float);
            Py_DECREF(operand2_float);

            obj_result = r;
            goto exit_result_object;
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
                        PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                        PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                        PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                        Py_DECREF(operand1_long);
                        Py_DECREF(operand2_long);

                        obj_result = r;
                        goto exit_result_object;
                    }
                }
                bb >>= 1;
                if (bb == 0) {
                    break;
                }
                prev = temp;
                temp = (unsigned long)temp * temp;

                if (prev != 0 && temp / prev != prev) {
                    PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                    PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                    PyObject *r = _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1_long, operand2_long);

                    Py_DECREF(operand1_long);
                    Py_DECREF(operand2_long);

                    obj_result = r;
                    goto exit_result_object;
                }
            }

            clong_result = ix;
            goto exit_result_ok_clong;
        }

    exit_result_ok_clong:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_object:
        if (unlikely(obj_result == NULL)) {
            goto exit_result_exception;
        }
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        *operand1 = obj_result;
        goto exit_result_ok;

    exit_result_ok:
        return true;

    exit_result_exception:
        return false;
    }
#endif

    if (Py_TYPE(*operand1) == Py_TYPE(operand2)) {
        if (PyFloat_CheckExact(operand2)) {
            return _INPLACE_OPERATION_POW_FLOAT_FLOAT(operand1, operand2);
        }
#if PYTHON_VERSION >= 0x300
        if (PyLong_CheckExact(operand2)) {
            return _INPLACE_OPERATION_POW_LONG_LONG(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
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

    ternaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_power : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    {
        ternaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
        ternaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            // Different types, need to consider second value slot.

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (Nuitka_Type_IsSubtype(type2, type1)) {
                    PyObject *x = slot2(*operand1, operand2, Py_None);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF_IMMORTAL(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2, Py_None);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF_IMMORTAL(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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
                        ternaryfunc slot = mv->nb_power;

                        if (likely(slot != NULL)) {
                            PyObject *x = slot(coerced1, coerced2, Py_None);

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for **=: '%s' and '%s'", type1->tp_name,
                     type2->tp_name);
        goto exit_inplace_exception;
    }

exit_inplace_result_object:
    if (unlikely(obj_result == NULL)) {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

exit_inplace_exception:
    return false;
}

bool INPLACE_OPERATION_POW_OBJECT_OBJECT(PyObject **operand1, PyObject *operand2) {
    return _INPLACE_OPERATION_POW_OBJECT_OBJECT(operand1, operand2);
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
