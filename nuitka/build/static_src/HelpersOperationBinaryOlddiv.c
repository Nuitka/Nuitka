//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationBinary.c.j2 instead! */
#pragma once

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"

#include "nuitka/helper/long_helpers.h"
#endif

/* C helpers for type specialized "/" (OLDDIV) operations */

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyObject *result;

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

    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    const long a = PyInt_AS_LONG(operand1);
    const long b = PyInt_AS_LONG(operand2);

    if (unlikely(b == 0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "integer division or modulo by zero");
        goto exit_result_exception;
    }

    if (likely(b != -1 || !UNARY_NEG_WOULD_OVERFLOW(a))) {
        long a_div_b = a / b;
        long a_mod_b = (long)(a - (unsigned long)a_div_b * b);

        if (a_mod_b && (b ^ a_mod_b) < 0) {
            a_mod_b += b;
            a_div_b -= 1;
        }

        clong_result = a_div_b;
        goto exit_result_ok_clong;
    }

    {
        PyObject *operand1_object = operand1;
        PyObject *operand2_object = operand2;

        PyObject *r = PyLong_Type.tp_as_number->nb_divide(operand1_object, operand2_object);
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

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_INT(PyObject *operand1,
                                                                                 PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_divide : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyInt_Type)) {
        slot2 = PyInt_Type.tp_as_number->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: '%s' and 'int'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyInt_Type) {
        PyObject *result;

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

        CHECK_OBJECT(operand1);
        assert(PyInt_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(operand1);
        const long b = PyInt_AS_LONG(operand2);

        if (unlikely(b == 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "integer division or modulo by zero");
            goto exit_result_exception;
        }

        if (likely(b != -1 || !UNARY_NEG_WOULD_OVERFLOW(a))) {
            long a_div_b = a / b;
            long a_mod_b = (long)(a - (unsigned long)a_div_b * b);

            if (a_mod_b && (b ^ a_mod_b) < 0) {
                a_mod_b += b;
                a_div_b -= 1;
            }

            clong_result = a_div_b;
            goto exit_result_ok_clong;
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_divide(operand1_object, operand2_object);
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

    return __BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_INT(operand1, operand2);
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_OLDDIV_OBJECT_INT_OBJECT(PyObject *operand1,
                                                                                 PyObject *operand2) {
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

    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_divide;
    binaryfunc slot2 = NULL;

    if (!(&PyInt_Type == type2)) {
        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_divide : NULL;

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
                    binaryfunc slot = mv->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'int' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyInt_Type == type2) {
        PyObject *result;

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

        CHECK_OBJECT(operand1);
        assert(PyInt_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(operand1);
        const long b = PyInt_AS_LONG(operand2);

        if (unlikely(b == 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "integer division or modulo by zero");
            goto exit_result_exception;
        }

        if (likely(b != -1 || !UNARY_NEG_WOULD_OVERFLOW(a))) {
            long a_div_b = a / b;
            long a_mod_b = (long)(a - (unsigned long)a_div_b * b);

            if (a_mod_b && (b ^ a_mod_b) < 0) {
                a_mod_b += b;
                a_div_b -= 1;
            }

            clong_result = a_div_b;
            goto exit_result_ok_clong;
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_divide(operand1_object, operand2_object);
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

    return __BINARY_OPERATION_OLDDIV_OBJECT_INT_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyObject *result;

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
    NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    PyObject *x = PyLong_Type.tp_as_number->nb_divide(operand1, operand2);
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

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_LONG_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_LONG(PyObject *operand1,
                                                                                  PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_divide : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyLong_Type)) {
        slot2 = PyLong_Type.tp_as_number->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: '%s' and 'int'", type1->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyLong_Type) {
        PyObject *result;

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        PyObject *x = PyLong_Type.tp_as_number->nb_divide(operand1, operand2);
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

    return __BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_LONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_OLDDIV_OBJECT_LONG_OBJECT(PyObject *operand1,
                                                                                  PyObject *operand2) {
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_divide;
    binaryfunc slot2 = NULL;

    if (!(&PyLong_Type == type2)) {
        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_divide : NULL;

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
                    binaryfunc slot = mv->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'int' and '%s'", type2->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyLong_Type == type2) {
        PyObject *result;

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;
        NUITKA_MAY_BE_UNUSED long clong_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

        PyObject *x = PyLong_Type.tp_as_number->nb_divide(operand1, operand2);
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

    return __BINARY_OPERATION_OLDDIV_OBJECT_LONG_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_LONG_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyObject *result;

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

    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    if (unlikely(b == 0.0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "float division by zero");
        goto exit_result_exception;
    }

    {
        double r = a / b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;
    }

exit_result_ok_cfloat:
    result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_FLOAT(PyObject *operand1,
                                                                                   PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(operand1);

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_divide : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyFloat_Type)) {
        slot2 = PyFloat_Type.tp_as_number->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: '%s' and 'float'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyFloat_Type) {
        PyObject *result;

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

        CHECK_OBJECT(operand1);
        assert(PyFloat_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        if (unlikely(b == 0.0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "float division by zero");
            goto exit_result_exception;
        }

        {
            double r = a / b;

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        }

    exit_result_ok_cfloat:
        result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NULL;
    }

    return __BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_FLOAT(operand1, operand2);
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_OBJECT(PyObject *operand1,
                                                                                   PyObject *operand2) {
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

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_divide;
    binaryfunc slot2 = NULL;

    if (!(&PyFloat_Type == type2)) {
        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_divide : NULL;

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
                    binaryfunc slot = mv->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'float' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyFloat_Type == type2) {
        PyObject *result;

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

        CHECK_OBJECT(operand1);
        assert(PyFloat_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));

        const double a = PyFloat_AS_DOUBLE(operand1);
        const double b = PyFloat_AS_DOUBLE(operand2);

        if (unlikely(b == 0.0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "float division by zero");
            goto exit_result_exception;
        }

        {
            double r = a / b;

            cfloat_result = r;
            goto exit_result_ok_cfloat;
        }

    exit_result_ok_cfloat:
        result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
        goto exit_result_ok;

    exit_result_ok:
        return result;

    exit_result_exception:
        return NULL;
    }

    return __BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
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

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_divide;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

#if PYTHON_VERSION < 0x300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'float' and 'long'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'float' and 'int'");
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_LONG_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
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

    binaryfunc slot2 = NULL;

    if (!(0)) {
        slot2 = PyFloat_Type.tp_as_number->nb_divide;
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
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'long' and 'float'");
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'int' and 'float'");
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_LONG_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_LONG_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
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

    binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_divide;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'float' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_INT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
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

    binaryfunc slot2 = NULL;

    if (!(0)) {
        slot2 = PyFloat_Type.tp_as_number->nb_divide;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'int' and 'float'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_INT_FLOAT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_INT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_divide;

    if (slot1 != NULL) {
        PyObject *x = slot1(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'long' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
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

    binaryfunc slot2 = NULL;

    if (!(0)) {
        slot2 = PyLong_Type.tp_as_number->nb_divide;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: 'int' and 'long'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));

    PyObject *result;

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

    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));

    const long a = PyInt_AS_LONG(operand1);
    const long b = operand2;

    if (unlikely(b == 0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "integer division or modulo by zero");
        goto exit_result_exception;
    }

    if (likely(b != -1 || !UNARY_NEG_WOULD_OVERFLOW(a))) {
        long a_div_b = a / b;
        long a_mod_b = (long)(a - (unsigned long)a_div_b * b);

        if (a_mod_b && (b ^ a_mod_b) < 0) {
            a_mod_b += b;
            a_div_b -= 1;
        }

        clong_result = a_div_b;
        goto exit_result_ok_clong;
    }

    {
        PyObject *operand1_object = operand1;
        PyObject *operand2_object = Nuitka_PyLong_FromLong(operand2);

        PyObject *r = PyLong_Type.tp_as_number->nb_divide(operand1_object, operand2_object);
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

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_INT_CLONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_CLONG_INT(long operand1, PyObject *operand2) {

    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyObject *result;

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

    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    const long a = operand1;
    const long b = PyInt_AS_LONG(operand2);

    if (unlikely(b == 0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "integer division or modulo by zero");
        goto exit_result_exception;
    }

    if (likely(b != -1 || !UNARY_NEG_WOULD_OVERFLOW(a))) {
        long a_div_b = a / b;
        long a_mod_b = (long)(a - (unsigned long)a_div_b * b);

        if (a_mod_b && (b ^ a_mod_b) < 0) {
            a_mod_b += b;
            a_div_b -= 1;
        }

        clong_result = a_div_b;
        goto exit_result_ok_clong;
    }

    {
        PyObject *operand1_object = Nuitka_PyLong_FromLong(operand1);
        PyObject *operand2_object = operand2;

        PyObject *r = PyLong_Type.tp_as_number->nb_divide(operand1_object, operand2_object);
        assert(r != Py_NotImplemented);

        Py_DECREF(operand1_object);

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

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_CLONG_INT(long operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_CLONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    PyObject *result;

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

    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = operand2;

    if (unlikely(b == 0.0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "float division by zero");
        goto exit_result_exception;
    }

    {
        double r = a / b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;
    }

exit_result_ok_cfloat:
    result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_FLOAT_CFLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_CFLOAT_FLOAT(double operand1, PyObject *operand2) {

    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    PyObject *result;

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

    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    const double a = operand1;
    const double b = PyFloat_AS_DOUBLE(operand2);

    if (unlikely(b == 0.0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "float division by zero");
        goto exit_result_exception;
    }

    {
        double r = a / b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;
    }

exit_result_ok_cfloat:
    result = MAKE_FLOAT_FROM_DOUBLE(cfloat_result);
    goto exit_result_ok;

exit_result_ok:
    return result;

exit_result_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_CFLOAT_FLOAT(double operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_CFLOAT_FLOAT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *_BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        PyObject *result;

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

        CHECK_OBJECT(operand1);
        assert(PyInt_CheckExact(operand1));
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));

        const long a = PyInt_AS_LONG(operand1);
        const long b = PyInt_AS_LONG(operand2);

        if (unlikely(b == 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ZeroDivisionError, "integer division or modulo by zero");
            goto exit_result_exception;
        }

        if (likely(b != -1 || !UNARY_NEG_WOULD_OVERFLOW(a))) {
            long a_div_b = a / b;
            long a_mod_b = (long)(a - (unsigned long)a_div_b * b);

            if (a_mod_b && (b ^ a_mod_b) < 0) {
                a_mod_b += b;
                a_div_b -= 1;
            }

            clong_result = a_div_b;
            goto exit_result_ok_clong;
        }

        {
            PyObject *operand1_object = operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_divide(operand1_object, operand2_object);
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

#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

    binaryfunc slot1 =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_divide : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_divide : NULL;

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
                    binaryfunc slot = mv->nb_divide;

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
                    binaryfunc slot = mv->nb_divide;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for /: '%s' and '%s'", type1->tp_name, type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_OLDDIV_OBJECT_OBJECT_OBJECT(operand1, operand2);
}
#endif

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
