//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationBinary.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized "<<" (LSHIFT) operations */

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
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

    PyObject *x = PyLong_Type.tp_as_number->nb_lshift(operand1, operand2);
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

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_LONG(PyObject *operand1,
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_lshift : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyLong_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyLong_Type.tp_as_number->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and 'int'", type1->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyLong_Type) {
        PyObject *result;

        // return _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1, operand2);

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

        PyObject *x = PyLong_Type.tp_as_number->nb_lshift(operand1, operand2);
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

    return __BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_LONG(operand1, operand2);
}

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_LSHIFT_OBJECT_LONG_OBJECT(PyObject *operand1,
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_lshift;
    binaryfunc slot2 = NULL;

    if (!(&PyLong_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_lshift : NULL;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'int' and '%s'", type2->tp_name);
#endif
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyLong_Type == type2) {
        PyObject *result;

        // return _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1, operand2);

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

        PyObject *x = PyLong_Type.tp_as_number->nb_lshift(operand1, operand2);
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

    return __BINARY_OPERATION_LSHIFT_OBJECT_LONG_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_LONG_OBJECT(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
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

    PyObject *x = PyLong_Type.tp_as_number->nb_lshift(operand1, operand2);
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

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_LONG(PyObject *operand1,
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_lshift : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyLong_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyLong_Type.tp_as_number->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and 'long'", type1->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and 'int'", type1->tp_name);
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
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyLong_Type) {
        nuitka_bool result;

        // return _BINARY_OPERATION_LSHIFT_NBOOL_LONG_LONG(operand1, operand2);

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

        PyObject *x = PyLong_Type.tp_as_number->nb_lshift(operand1, operand2);
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

    return __BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_LONG(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_LONG(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_LSHIFT_NBOOL_LONG_OBJECT(PyObject *operand1,
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_lshift;
    binaryfunc slot2 = NULL;

    if (!(&PyLong_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_lshift : NULL;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'long' and '%s'", type2->tp_name);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'int' and '%s'", type2->tp_name);
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
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyLong_Type == type2) {
        nuitka_bool result;

        // return _BINARY_OPERATION_LSHIFT_NBOOL_LONG_LONG(operand1, operand2);

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

        PyObject *x = PyLong_Type.tp_as_number->nb_lshift(operand1, operand2);
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

    return __BINARY_OPERATION_LSHIFT_NBOOL_LONG_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_LONG_OBJECT(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    if (unlikely(b < 0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
        goto exit_result_exception;
    }
    /* Short cut for zero shift or shifting zero. */
    if (a == 0 || b == 0) {
        goto exit_result_ok_left;
    } else if (b >= LONG_BIT) {
        PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
        PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

        // TODO: Change this to using CLONG once we specialize that too.
        PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

        Py_DECREF(operand1_long);
        Py_DECREF(operand2_long);

        obj_result = r;
        goto exit_result_object;
    } else {
        long c = a << b;

        if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            clong_result = c;
            goto exit_result_ok_clong;
        }
    }

exit_result_ok_clong:
    result = Nuitka_PyInt_FromLong(clong_result);
    goto exit_result_ok;

exit_result_ok_left:
    result = operand1;
    Py_INCREF(result);
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

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_INT(PyObject *operand1,
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_lshift : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyInt_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyInt_Type.tp_as_number->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and 'int'", type1->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyInt_Type) {
        PyObject *result;

        // return _BINARY_OPERATION_LSHIFT_OBJECT_INT_INT(operand1, operand2);

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

        if (unlikely(b < 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
            goto exit_result_exception;
        }
        /* Short cut for zero shift or shifting zero. */
        if (a == 0 || b == 0) {
            goto exit_result_ok_left;
        } else if (b >= LONG_BIT) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            long c = a << b;

            if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
                PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                // TODO: Change this to using CLONG once we specialize that too.
                PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

                Py_DECREF(operand1_long);
                Py_DECREF(operand2_long);

                obj_result = r;
                goto exit_result_object;
            } else {
                clong_result = c;
                goto exit_result_ok_clong;
            }
        }

    exit_result_ok_clong:
        result = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok_left:
        result = operand1;
        Py_INCREF(result);
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

    return __BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_INT(operand1, operand2);
}

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE PyObject *__BINARY_OPERATION_LSHIFT_OBJECT_INT_OBJECT(PyObject *operand1,
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

    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_lshift;
    binaryfunc slot2 = NULL;

    if (!(&PyInt_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_lshift : NULL;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'int' and '%s'", type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyInt_Type == type2) {
        PyObject *result;

        // return _BINARY_OPERATION_LSHIFT_OBJECT_INT_INT(operand1, operand2);

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

        if (unlikely(b < 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
            goto exit_result_exception;
        }
        /* Short cut for zero shift or shifting zero. */
        if (a == 0 || b == 0) {
            goto exit_result_ok_left;
        } else if (b >= LONG_BIT) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            long c = a << b;

            if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
                PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                // TODO: Change this to using CLONG once we specialize that too.
                PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

                Py_DECREF(operand1_long);
                Py_DECREF(operand2_long);

                obj_result = r;
                goto exit_result_object;
            } else {
                clong_result = c;
                goto exit_result_ok_clong;
            }
        }

    exit_result_ok_clong:
        result = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok_left:
        result = operand1;
        Py_INCREF(result);
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

    return __BINARY_OPERATION_LSHIFT_OBJECT_INT_OBJECT(operand1, operand2);
}

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    if (unlikely(b < 0)) {
        PyThreadState *tstate = PyThreadState_GET();

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
        goto exit_result_exception;
    }
    /* Short cut for zero shift or shifting zero. */
    if (a == 0 || b == 0) {
        goto exit_result_ok_left;
    } else if (b >= LONG_BIT) {
        PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
        PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

        // TODO: Change this to using CLONG once we specialize that too.
        PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

        Py_DECREF(operand1_long);
        Py_DECREF(operand2_long);

        obj_result = r;
        goto exit_result_object;
    } else {
        long c = a << b;

        if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            clong_result = c;
            goto exit_result_ok_clong;
        }
    }

exit_result_ok_clong:
    result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    goto exit_result_ok;

exit_result_ok_left:
    result = PyInt_AS_LONG(operand1) != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
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

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_INT(PyObject *operand1,
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_lshift : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == &PyInt_Type)) {
        // Different types, need to consider second value slot.

        slot2 = PyInt_Type.tp_as_number->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and 'int'", type1->tp_name);
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
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    PyTypeObject *type1 = Py_TYPE(operand1);

    if (type1 == &PyInt_Type) {
        nuitka_bool result;

        // return _BINARY_OPERATION_LSHIFT_NBOOL_INT_INT(operand1, operand2);

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

        if (unlikely(b < 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
            goto exit_result_exception;
        }
        /* Short cut for zero shift or shifting zero. */
        if (a == 0 || b == 0) {
            goto exit_result_ok_left;
        } else if (b >= LONG_BIT) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            long c = a << b;

            if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
                PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                // TODO: Change this to using CLONG once we specialize that too.
                PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

                Py_DECREF(operand1_long);
                Py_DECREF(operand2_long);

                obj_result = r;
                goto exit_result_object;
            } else {
                clong_result = c;
                goto exit_result_ok_clong;
            }
        }

    exit_result_ok_clong:
        result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_left:
        result = PyInt_AS_LONG(operand1) != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
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

    return __BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_INT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE nuitka_bool __BINARY_OPERATION_LSHIFT_NBOOL_INT_OBJECT(PyObject *operand1,
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

    binaryfunc slot1 = PyInt_Type.tp_as_number->nb_lshift;
    binaryfunc slot2 = NULL;

    if (!(&PyInt_Type == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_lshift : NULL;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'int' and '%s'", type2->tp_name);
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
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);

    PyTypeObject *type2 = Py_TYPE(operand2);

    if (&PyInt_Type == type2) {
        nuitka_bool result;

        // return _BINARY_OPERATION_LSHIFT_NBOOL_INT_INT(operand1, operand2);

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

        if (unlikely(b < 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
            goto exit_result_exception;
        }
        /* Short cut for zero shift or shifting zero. */
        if (a == 0 || b == 0) {
            goto exit_result_ok_left;
        } else if (b >= LONG_BIT) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            long c = a << b;

            if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
                PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                // TODO: Change this to using CLONG once we specialize that too.
                PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

                Py_DECREF(operand1_long);
                Py_DECREF(operand2_long);

                obj_result = r;
                goto exit_result_object;
            } else {
                clong_result = c;
                goto exit_result_ok_clong;
            }
        }

    exit_result_ok_clong:
        result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_left:
        result = PyInt_AS_LONG(operand1) != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
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

    return __BINARY_OPERATION_LSHIFT_NBOOL_INT_OBJECT(operand1, operand2);
}

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_INT_OBJECT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_lshift;
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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'long' and 'int'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
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

    // Slot1 ignored on purpose, type2 takes precedence.
    binaryfunc slot2 = NULL;

    if (!(0)) {
        // Different types, need to consider second value slot.

        slot2 = PyLong_Type.tp_as_number->nb_lshift;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'int' and 'long'");
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_INT_LONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
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

    binaryfunc slot1 = PyLong_Type.tp_as_number->nb_lshift;
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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'long' and 'int'");
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

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_LONG_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
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

    // Slot1 ignored on purpose, type2 takes precedence.
    binaryfunc slot2 = NULL;

    if (!(0)) {
        // Different types, need to consider second value slot.

        slot2 = PyLong_Type.tp_as_number->nb_lshift;
    }

    if (slot2 != NULL) {
        PyObject *x = slot2(operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_binary_result_object;
        }

        Py_DECREF_IMMORTAL(x);
    }

    // Statically recognized that coercion is not possible with these types

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: 'int' and 'long'");
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

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_INT_LONG(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_INT_LONG(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static PyObject *_BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
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

        if (unlikely(b < 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
            goto exit_result_exception;
        }
        /* Short cut for zero shift or shifting zero. */
        if (a == 0 || b == 0) {
            goto exit_result_ok_left;
        } else if (b >= LONG_BIT) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            long c = a << b;

            if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
                PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                // TODO: Change this to using CLONG once we specialize that too.
                PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

                Py_DECREF(operand1_long);
                Py_DECREF(operand2_long);

                obj_result = r;
                goto exit_result_object;
            } else {
                clong_result = c;
                goto exit_result_ok_clong;
            }
        }

    exit_result_ok_clong:
        result = Nuitka_PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok_left:
        result = operand1;
        Py_INCREF(result);
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_lshift : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_lshift : NULL;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and '%s'", type1->tp_name, type2->tp_name);
    goto exit_binary_exception;

exit_binary_result_object:
    return obj_result;

exit_binary_exception:
    return NULL;
}

PyObject *BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_OBJECT_OBJECT_OBJECT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static nuitka_bool _BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
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

        if (unlikely(b < 0)) {
            PyThreadState *tstate = PyThreadState_GET();

            SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "negative shift count");
            goto exit_result_exception;
        }
        /* Short cut for zero shift or shifting zero. */
        if (a == 0 || b == 0) {
            goto exit_result_ok_left;
        } else if (b >= LONG_BIT) {
            PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
            PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

            // TODO: Change this to using CLONG once we specialize that too.
            PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

            Py_DECREF(operand1_long);
            Py_DECREF(operand2_long);

            obj_result = r;
            goto exit_result_object;
        } else {
            long c = a << b;

            if (a != Py_ARITHMETIC_RIGHT_SHIFT(long, c, b)) {
                PyObject *operand1_long = Nuitka_PyLong_FromLong(a);
                PyObject *operand2_long = Nuitka_PyLong_FromLong(b);

                // TODO: Change this to using CLONG once we specialize that too.
                PyObject *r = _BINARY_OPERATION_LSHIFT_OBJECT_LONG_LONG(operand1_long, operand2_long);

                Py_DECREF(operand1_long);
                Py_DECREF(operand2_long);

                obj_result = r;
                goto exit_result_object;
            } else {
                clong_result = c;
                goto exit_result_ok_clong;
            }
        }

    exit_result_ok_clong:
        result = clong_result != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
        goto exit_result_ok;

    exit_result_ok_left:
        result = PyInt_AS_LONG(operand1) != 0 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_lshift : NULL;
    binaryfunc slot2 = NULL;

    if (!(type1 == type2)) {
        // Different types, need to consider second value slot.

        slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_lshift : NULL;

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
                    binaryfunc slot = mv->nb_lshift;

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
                    binaryfunc slot = mv->nb_lshift;

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

    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for <<: '%s' and '%s'", type1->tp_name, type2->tp_name);
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

nuitka_bool BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return _BINARY_OPERATION_LSHIFT_NBOOL_OBJECT_OBJECT(operand1, operand2);
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
