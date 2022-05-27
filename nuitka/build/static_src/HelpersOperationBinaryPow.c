//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "HelpersOperationBinaryPowUtils.c"
/* C helpers for type specialized "**" (POW) operations */

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static PyObject *_BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
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

    double a = PyFloat_AS_DOUBLE(operand1);
    double b = PyFloat_AS_DOUBLE(operand2);

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
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ZeroDivisionError, "0.0 cannot be raised to a negative power");
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
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError,
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
    result = PyFloat_FromDouble(cfloat_result);
    goto exit_result_ok;

exit_result_ok_left:
    result = operand1;
    Py_INCREF(result);
    goto exit_result_ok;

exit_result_ok_right:
    result = operand2;
    Py_INCREF(result);
    goto exit_result_ok;

exit_result_ok_const_float_0_0:
    Py_INCREF(const_float_0_0);
    result = const_float_0_0;
    goto exit_result_ok;

exit_result_ok_const_float_1_0:
    Py_INCREF(const_float_1_0);
    result = const_float_1_0;
    goto exit_result_ok;

exit_result_ok_const_float_minus_1_0:
    Py_INCREF(const_float_minus_1_0);
    result = const_float_minus_1_0;
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
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

    double a = PyFloat_AS_DOUBLE(operand1);
    double b = PyFloat_AS_DOUBLE(operand2);

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
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ZeroDivisionError, "0.0 cannot be raised to a negative power");
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
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError,
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
    result = cfloat_result != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok_left:
    result = PyFloat_AS_DOUBLE(operand1) != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok_right:
    result = PyFloat_AS_DOUBLE(operand2) != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok_const_float_0_0:
    result = 0.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok_const_float_1_0:
    result = 1.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok_const_float_minus_1_0:
    result = -1.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NUITKA_BOOL_EXCEPTION;
}

nuitka_bool BINARY_OPERATION_POW_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_POW_OBJECT_OBJECT_FLOAT(PyObject *operand1,
                                                                                PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyFloat_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_power;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'float'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_POW_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyFloat_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        PyObject *result;

        // return _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1, operand2);

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

        double a = PyFloat_AS_DOUBLE(operand1);
        double b = PyFloat_AS_DOUBLE(operand2);

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
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ZeroDivisionError, "0.0 cannot be raised to a negative power");
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
                    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError,
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
        result = PyFloat_FromDouble(cfloat_result);
        goto exit_result_ok;

    exit_result_ok_left:
        result = operand1;
        Py_INCREF(result);
        goto exit_result_ok;

    exit_result_ok_right:
        result = operand2;
        Py_INCREF(result);
        goto exit_result_ok;

    exit_result_ok_const_float_0_0:
        Py_INCREF(const_float_0_0);
        result = const_float_0_0;
        goto exit_result_ok;

    exit_result_ok_const_float_1_0:
        Py_INCREF(const_float_1_0);
        result = const_float_1_0;
        goto exit_result_ok;

    exit_result_ok_const_float_minus_1_0:
        Py_INCREF(const_float_minus_1_0);
        result = const_float_minus_1_0;
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NULL;
    }

    return __BINARY_OPERATION_POW_OBJECT_OBJECT_FLOAT(operand1, operand2);
}

PyObject *BINARY_OPERATION_POW_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_OBJECT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_POW_NBOOL_OBJECT_FLOAT(PyObject *operand1,
                                                                                 PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyFloat_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyFloat_Type.tp_as_number->nb_power;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'float'", type1->tp_name);
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
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyFloat_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        nuitka_bool result;

        // return _BINARY_OPERATION_POW_NBOOL_FLOAT_FLOAT(operand1, operand2);

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

        double a = PyFloat_AS_DOUBLE(operand1);
        double b = PyFloat_AS_DOUBLE(operand2);

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
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ZeroDivisionError, "0.0 cannot be raised to a negative power");
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
                    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError,
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
        result = cfloat_result != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_left:
        result = PyFloat_AS_DOUBLE(operand1) != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_right:
        result = PyFloat_AS_DOUBLE(operand2) != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_const_float_0_0:
        result = 0.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_const_float_1_0:
        result = 1.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_const_float_minus_1_0:
        result = -1.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NUITKA_BOOL_EXCEPTION;
    }

    return __BINARY_OPERATION_POW_NBOOL_OBJECT_FLOAT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_POW_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_OBJECT_FLOAT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_POW_OBJECT_FLOAT_OBJECT(PyObject *operand1,
                                                                                PyObject *operand2) {
    PyTypeObject *type1 = &PyFloat_Type;
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

    ternaryfunc slot1 = PyFloat_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'float' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_POW_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyFloat_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        PyObject *result;

        // return _BINARY_OPERATION_POW_OBJECT_FLOAT_FLOAT(operand1, operand2);

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

        double a = PyFloat_AS_DOUBLE(operand1);
        double b = PyFloat_AS_DOUBLE(operand2);

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
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ZeroDivisionError, "0.0 cannot be raised to a negative power");
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
                    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError,
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
        result = PyFloat_FromDouble(cfloat_result);
        goto exit_result_ok;

    exit_result_ok_left:
        result = operand1;
        Py_INCREF(result);
        goto exit_result_ok;

    exit_result_ok_right:
        result = operand2;
        Py_INCREF(result);
        goto exit_result_ok;

    exit_result_ok_const_float_0_0:
        Py_INCREF(const_float_0_0);
        result = const_float_0_0;
        goto exit_result_ok;

    exit_result_ok_const_float_1_0:
        Py_INCREF(const_float_1_0);
        result = const_float_1_0;
        goto exit_result_ok;

    exit_result_ok_const_float_minus_1_0:
        Py_INCREF(const_float_minus_1_0);
        result = const_float_minus_1_0;
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NULL;
    }

    return __BINARY_OPERATION_POW_OBJECT_FLOAT_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_POW_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_FLOAT_OBJECT(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_POW_NBOOL_FLOAT_OBJECT(PyObject *operand1,
                                                                                 PyObject *operand2) {
    PyTypeObject *type1 = &PyFloat_Type;
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

    ternaryfunc slot1 = PyFloat_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'float' and '%s'", type2->tp_name);
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
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyFloat_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        nuitka_bool result;

        // return _BINARY_OPERATION_POW_NBOOL_FLOAT_FLOAT(operand1, operand2);

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

        double a = PyFloat_AS_DOUBLE(operand1);
        double b = PyFloat_AS_DOUBLE(operand2);

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
                SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ZeroDivisionError, "0.0 cannot be raised to a negative power");
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
                    SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_ValueError,
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
        result = cfloat_result != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_left:
        result = PyFloat_AS_DOUBLE(operand1) != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_right:
        result = PyFloat_AS_DOUBLE(operand2) != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_const_float_0_0:
        result = 0.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_const_float_1_0:
        result = 1.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_const_float_minus_1_0:
        result = -1.0 != 0.0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NUITKA_BOOL_EXCEPTION;
    }

    return __BINARY_OPERATION_POW_NBOOL_FLOAT_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_POW_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_FLOAT_OBJECT(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_POW_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyObject *result;

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = PyLong_Type.tp_as_number->nb_power(operand1, operand2, Py_None);
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

PyObject *BINARY_OPERATION_POW_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    nuitka_bool result;

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = PyLong_Type.tp_as_number->nb_power(operand1, operand2, Py_None);
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

nuitka_bool BINARY_OPERATION_POW_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_POW_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyLong_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_power;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'int'", type1->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_POW_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyLong_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        PyObject *result;

        // return _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_power(operand1, operand2, Py_None);
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

    return __BINARY_OPERATION_POW_OBJECT_OBJECT_LONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_POW_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_POW_NBOOL_OBJECT_LONG(PyObject *operand1,
                                                                                PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyLong_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_power;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'int'", type1->tp_name);
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
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyLong_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        nuitka_bool result;

        // return _BINARY_OPERATION_POW_NBOOL_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_power(operand1, operand2, Py_None);
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

    return __BINARY_OPERATION_POW_NBOOL_OBJECT_LONG(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_POW_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_POW_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyLong_Type;
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

    ternaryfunc slot1 = PyLong_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'int' and '%s'", type2->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_POW_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyLong_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        PyObject *result;

        // return _BINARY_OPERATION_POW_OBJECT_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_power(operand1, operand2, Py_None);
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

    return __BINARY_OPERATION_POW_OBJECT_LONG_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_POW_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_LONG_OBJECT(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_POW_NBOOL_LONG_OBJECT(PyObject *operand1,
                                                                                PyObject *operand2) {
    PyTypeObject *type1 = &PyLong_Type;
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

    ternaryfunc slot1 = PyLong_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'int' and '%s'", type2->tp_name);
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
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyLong_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        nuitka_bool result;

        // return _BINARY_OPERATION_POW_NBOOL_LONG_LONG(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_power(operand1, operand2, Py_None);
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

    return __BINARY_OPERATION_POW_NBOOL_LONG_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_POW_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_LONG_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_POW_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    if (b < 0) {
        // TODO: Use CFLOAT once available.
        PyObject *operand1_float = PyFloat_FromDouble(a);
        PyObject *operand2_float = PyFloat_FromDouble(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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
                PyObject *operand1_long = PyLong_FromLong(a);
                PyObject *operand2_long = PyLong_FromLong(b);

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
    result = PyInt_FromLong(clong_result);
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

PyObject *BINARY_OPERATION_POW_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    if (b < 0) {
        // TODO: Use CFLOAT once available.
        PyObject *operand1_float = PyFloat_FromDouble(a);
        PyObject *operand2_float = PyFloat_FromDouble(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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
                PyObject *operand1_long = PyLong_FromLong(a);
                PyObject *operand2_long = PyLong_FromLong(b);

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

nuitka_bool BINARY_OPERATION_POW_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_POW_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyInt_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_power;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'int'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_POW_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyInt_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        PyObject *result;

        // return _BINARY_OPERATION_POW_OBJECT_INT_INT(operand1, operand2);

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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

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
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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
        result = PyInt_FromLong(clong_result);
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

    return __BINARY_OPERATION_POW_OBJECT_OBJECT_INT(operand1, operand2);
}

PyObject *BINARY_OPERATION_POW_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_POW_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyInt_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_power;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and 'int'", type1->tp_name);
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
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyInt_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        nuitka_bool result;

        // return _BINARY_OPERATION_POW_NBOOL_INT_INT(operand1, operand2);

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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

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
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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

    return __BINARY_OPERATION_POW_NBOOL_OBJECT_INT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_POW_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_POW_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyInt_Type;
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

    ternaryfunc slot1 = PyInt_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'int' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_POW_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        PyObject *result;

        // return _BINARY_OPERATION_POW_OBJECT_INT_INT(operand1, operand2);

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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

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
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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
        result = PyInt_FromLong(clong_result);
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

    return __BINARY_OPERATION_POW_OBJECT_INT_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_POW_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_POW_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyInt_Type;
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

    ternaryfunc slot1 = PyInt_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'int' and '%s'", type2->tp_name);
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
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        nuitka_bool result;

        // return _BINARY_OPERATION_POW_NBOOL_INT_INT(operand1, operand2);

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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

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
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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

    return __BINARY_OPERATION_POW_NBOOL_INT_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_POW_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_POW_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = &PyLong_Type;
    PyTypeObject *type2 = &PyInt_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 = PyLong_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_power;
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    // Statically recognized that coercion is not possible with these types

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'long' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_POW_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = &PyLong_Type;
    PyTypeObject *type2 = &PyInt_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 = PyLong_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyInt_Type.tp_as_number->nb_power;
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    // Statically recognized that coercion is not possible with these types

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'long' and 'int'");
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

nuitka_bool BINARY_OPERATION_POW_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_POW_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = &PyLong_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 = PyInt_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_power;
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    // Statically recognized that coercion is not possible with these types

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'int' and 'long'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_POW_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = &PyLong_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    ternaryfunc slot1 = PyInt_Type.tp_as_number->nb_power;
    ternaryfunc slot2 = NULL;

    if (!(0)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = PyLong_Type.tp_as_number->nb_power;
    }

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    // Statically recognized that coercion is not possible with these types

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): 'int' and 'long'");
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

nuitka_bool BINARY_OPERATION_POW_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_INT_LONG(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_POW_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

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
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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
        result = PyInt_FromLong(clong_result);
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

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and '%s'", type1->tp_name,
                 type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_POW_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_OBJECT_OBJECT_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_POW_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
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

        if (b < 0) {
            // TODO: Use CFLOAT once available.
            PyObject *operand1_float = PyFloat_FromDouble(a);
            PyObject *operand2_float = PyFloat_FromDouble(b);

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
                        PyObject *operand1_long = PyLong_FromLong(a);
                        PyObject *operand2_long = PyLong_FromLong(b);

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
                    PyObject *operand1_long = PyLong_FromLong(a);
                    PyObject *operand2_long = PyLong_FromLong(b);

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

    ternaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_power : NULL;
    ternaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        assert(type1 != type2);
        /* Different types, need to consider second value slot. */

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_power : NULL;

        if (slot1 == slot2) {
            slot2 = NULL;
        }
    }

    if (slot1 != NULL) {
        if (slot2 != NULL) {
            if (PyType_IsSubtype(type2, type1)) {
                PyObject *x = slot2(operand1, operand2, Py_None);

                if (x != Py_NotImplemented) {
                    obj_result = x;
                    goto exit_binary_result_object;
                }

                Py_DECREF(x);
                slot2 = NULL;
            }
        }

        PyObject *x = slot1(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2, Py_None);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF(x);
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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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
                    ternaryfunc slot = mv->nb_power;

                    if (likely(slot != NULL)) {
                        PyObject *x = slot(coerced1, coerced2, Py_None);

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for ** or pow(): '%s' and '%s'", type1->tp_name,
                 type2->tp_name);
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

nuitka_bool BINARY_OPERATION_POW_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_POW_NBOOL_OBJECT_OBJECT(operand1, operand2);
}
