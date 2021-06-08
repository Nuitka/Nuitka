//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
/* WARNING, this code is GENERATED. Modify the template HelperOperationInplace.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#include "HelpersOperationInplaceAddUtils.c"
/* C helpers for type in-place "+" (ADD) operations */

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_ADD_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

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
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = PyInt_FromLong(clong_result);
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

bool BINARY_OPERATION_ADD_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
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

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

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

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'int'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyInt_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_INT_INT_INPLACE(operand1, operand2);

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
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(*operand1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

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

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = PyInt_FromLong(clong_result);
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

    return __BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (PyType_IsSubtype(type2, type1)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'int' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_INT_INT_INPLACE(operand1, operand2);

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
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(*operand1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

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

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = PyInt_FromLong(clong_result);
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

    return __BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_OBJECT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_ADD_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    if (Py_ABS(Py_SIZE(*operand1)) <= 1 && Py_ABS(Py_SIZE(operand2)) <= 1) {
        if (Py_REFCNT(*operand1) == 1) {
            Nuitka_LongUpdateFromCLong(&*operand1, MEDIUM_VALUE(*operand1) + MEDIUM_VALUE(operand2));
            goto exit_result_ok;
        }
        PyObject *r = Nuitka_LongFromCLong(MEDIUM_VALUE(*operand1) + MEDIUM_VALUE(operand2));
        obj_result = r;
        goto exit_result_object;
    }

    if (Py_REFCNT(*operand1) == 1) {
        digit const *b = Nuitka_LongGetDigitPointer(operand2);
        Py_ssize_t size_b = Nuitka_LongGetDigitSize(operand2);

#if 0
        PyObject *r = BINARY_OPERATION_ADD_OBJECT_LONG_LONG( *operand1, operand2 );
#endif
        if (Py_SIZE(*operand1) < 0) {
            if (Py_SIZE(operand2) < 0) {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b, size_b);
                Py_SIZE(*operand1) = -Py_ABS(Py_SIZE(*operand1));
            } else {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b, size_b, -1);
            }
        } else {
            if (Py_SIZE(operand2) < 0) {
                *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b, size_b, 1);
            } else {
                *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b, size_b);
            }
        }

#if 0
        assert(PyObject_RichCompareBool(r, *operand1, Py_EQ) == 1);
        Py_DECREF(r);
#endif

        goto exit_result_ok;
    }
    {
        PyLongObject *z;

        digit const *a = Nuitka_LongGetDigitPointer(*operand1);
        Py_ssize_t size_a = Nuitka_LongGetDigitSize(*operand1);
        digit const *b = Nuitka_LongGetDigitPointer(operand2);
        Py_ssize_t size_b = Nuitka_LongGetDigitSize(operand2);

        if (Py_SIZE(*operand1) < 0) {
            if (Py_SIZE(operand2) < 0) {
                z = _Nuitka_LongAddDigits(a, size_a, b, size_b);

                Py_SIZE(z) = -(Py_SIZE(z));
            } else {
                z = _Nuitka_LongSubDigits(b, size_b, a, size_a);
            }
        } else {
            if (Py_SIZE(operand2) < 0) {
                z = _Nuitka_LongSubDigits(a, size_a, b, size_b);
            } else {
                z = _Nuitka_LongAddDigits(a, size_a, b, size_b);
            }
        }

        obj_result = (PyObject *)z;
        goto exit_result_object;
    }

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

bool BINARY_OPERATION_ADD_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
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

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

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

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'long'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'int'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyLong_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_LONG_LONG_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        if (Py_ABS(Py_SIZE(*operand1)) <= 1 && Py_ABS(Py_SIZE(operand2)) <= 1) {
            if (Py_REFCNT(*operand1) == 1) {
                Nuitka_LongUpdateFromCLong(&*operand1, MEDIUM_VALUE(*operand1) + MEDIUM_VALUE(operand2));
                goto exit_result_ok;
            }
            PyObject *r = Nuitka_LongFromCLong(MEDIUM_VALUE(*operand1) + MEDIUM_VALUE(operand2));
            obj_result = r;
            goto exit_result_object;
        }

        if (Py_REFCNT(*operand1) == 1) {
            digit const *b = Nuitka_LongGetDigitPointer(operand2);
            Py_ssize_t size_b = Nuitka_LongGetDigitSize(operand2);

#if 0
        PyObject *r = BINARY_OPERATION_ADD_OBJECT_LONG_LONG( *operand1, operand2 );
#endif
            if (Py_SIZE(*operand1) < 0) {
                if (Py_SIZE(operand2) < 0) {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b, size_b);
                    Py_SIZE(*operand1) = -Py_ABS(Py_SIZE(*operand1));
                } else {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b, size_b, -1);
                }
            } else {
                if (Py_SIZE(operand2) < 0) {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b, size_b, 1);
                } else {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b, size_b);
                }
            }

#if 0
        assert(PyObject_RichCompareBool(r, *operand1, Py_EQ) == 1);
        Py_DECREF(r);
#endif

            goto exit_result_ok;
        }
        {
            PyLongObject *z;

            digit const *a = Nuitka_LongGetDigitPointer(*operand1);
            Py_ssize_t size_a = Nuitka_LongGetDigitSize(*operand1);
            digit const *b = Nuitka_LongGetDigitPointer(operand2);
            Py_ssize_t size_b = Nuitka_LongGetDigitSize(operand2);

            if (Py_SIZE(*operand1) < 0) {
                if (Py_SIZE(operand2) < 0) {
                    z = _Nuitka_LongAddDigits(a, size_a, b, size_b);

                    Py_SIZE(z) = -(Py_SIZE(z));
                } else {
                    z = _Nuitka_LongSubDigits(b, size_b, a, size_a);
                }
            } else {
                if (Py_SIZE(operand2) < 0) {
                    z = _Nuitka_LongSubDigits(a, size_a, b, size_b);
                } else {
                    z = _Nuitka_LongAddDigits(a, size_a, b, size_b);
                }
            }

            obj_result = (PyObject *)z;
            goto exit_result_object;
        }

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

    return __BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (PyType_IsSubtype(type2, type1)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'long' and '%s'", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'int' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyLong_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_LONG_LONG_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        if (Py_ABS(Py_SIZE(*operand1)) <= 1 && Py_ABS(Py_SIZE(operand2)) <= 1) {
            if (Py_REFCNT(*operand1) == 1) {
                Nuitka_LongUpdateFromCLong(&*operand1, MEDIUM_VALUE(*operand1) + MEDIUM_VALUE(operand2));
                goto exit_result_ok;
            }
            PyObject *r = Nuitka_LongFromCLong(MEDIUM_VALUE(*operand1) + MEDIUM_VALUE(operand2));
            obj_result = r;
            goto exit_result_object;
        }

        if (Py_REFCNT(*operand1) == 1) {
            digit const *b = Nuitka_LongGetDigitPointer(operand2);
            Py_ssize_t size_b = Nuitka_LongGetDigitSize(operand2);

#if 0
        PyObject *r = BINARY_OPERATION_ADD_OBJECT_LONG_LONG( *operand1, operand2 );
#endif
            if (Py_SIZE(*operand1) < 0) {
                if (Py_SIZE(operand2) < 0) {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b, size_b);
                    Py_SIZE(*operand1) = -Py_ABS(Py_SIZE(*operand1));
                } else {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b, size_b, -1);
                }
            } else {
                if (Py_SIZE(operand2) < 0) {
                    *operand1 = _Nuitka_LongSubInplaceDigits(*operand1, b, size_b, 1);
                } else {
                    *operand1 = _Nuitka_LongAddInplaceDigits(*operand1, b, size_b);
                }
            }

#if 0
        assert(PyObject_RichCompareBool(r, *operand1, Py_EQ) == 1);
        Py_DECREF(r);
#endif

            goto exit_result_ok;
        }
        {
            PyLongObject *z;

            digit const *a = Nuitka_LongGetDigitPointer(*operand1);
            Py_ssize_t size_a = Nuitka_LongGetDigitSize(*operand1);
            digit const *b = Nuitka_LongGetDigitPointer(operand2);
            Py_ssize_t size_b = Nuitka_LongGetDigitSize(operand2);

            if (Py_SIZE(*operand1) < 0) {
                if (Py_SIZE(operand2) < 0) {
                    z = _Nuitka_LongAddDigits(a, size_a, b, size_b);

                    Py_SIZE(z) = -(Py_SIZE(z));
                } else {
                    z = _Nuitka_LongSubDigits(b, size_b, a, size_a);
                }
            } else {
                if (Py_SIZE(operand2) < 0) {
                    z = _Nuitka_LongSubDigits(a, size_a, b, size_b);
                } else {
                    z = _Nuitka_LongAddDigits(a, size_a, b, size_b);
                }
            }

            obj_result = (PyObject *)z;
            goto exit_result_object;
        }

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

    return __BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

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
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    double a = PyFloat_AS_DOUBLE(*operand1);
    double b = PyFloat_AS_DOUBLE(operand2);

    double r = a + b;

    cfloat_result = r;
    goto exit_result_ok_cfloat;

exit_result_ok_cfloat:
    if (Py_REFCNT(*operand1) == 1) {
        PyFloat_AS_DOUBLE(*operand1) = cfloat_result;
    } else {
        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        *operand1 = PyFloat_FromDouble(cfloat_result);
    }
    goto exit_result_ok;

exit_result_ok:
    return true;
}

bool BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
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

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_add : NULL;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

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

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'float'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyFloat_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(operand1, operand2);

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
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(*operand1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

        double a = PyFloat_AS_DOUBLE(*operand1);
        double b = PyFloat_AS_DOUBLE(operand2);

        double r = a + b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        if (Py_REFCNT(*operand1) == 1) {
            PyFloat_AS_DOUBLE(*operand1) = cfloat_result;
        } else {
            // We got an object handed, that we have to release.
            Py_DECREF(*operand1);

            *operand1 = PyFloat_FromDouble(cfloat_result);
        }
        goto exit_result_ok;

    exit_result_ok:
        return true;
    }

    return __BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (PyType_IsSubtype(type2, type1)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'float' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyFloat_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(operand1, operand2);

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
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(*operand1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

        double a = PyFloat_AS_DOUBLE(*operand1);
        double b = PyFloat_AS_DOUBLE(operand2);

        double r = a + b;

        cfloat_result = r;
        goto exit_result_ok_cfloat;

    exit_result_ok_cfloat:
        if (Py_REFCNT(*operand1) == 1) {
            PyFloat_AS_DOUBLE(*operand1) = cfloat_result;
        } else {
            // We got an object handed, that we have to release.
            Py_DECREF(*operand1);

            *operand1 = PyFloat_FromDouble(cfloat_result);
        }
        goto exit_result_ok;

    exit_result_ok:
        return true;
    }

    return __BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_ADD_STR_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (1 && !PyString_CHECK_INTERNED(*operand1) && 1) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    // Python2 strings are to be treated differently, fall back to Python API here.
    if (1 && 1) {
        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
    }
#endif

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = PyString_Type.tp_as_sequence->sq_concat(*operand1, operand2);
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

bool BINARY_OPERATION_ADD_STR_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_STR_STR_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyString_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
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

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'str'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (PyString_CheckExact(*operand1) && !PyString_CHECK_INTERNED(*operand1) && 1) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyString_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_STR_STR_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyString_Type.tp_as_sequence->sq_concat(*operand1, operand2);
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

    return __BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_STR_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyString_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (1 && !PyString_CHECK_INTERNED(*operand1) && PyString_CheckExact(operand2)) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = &PyString_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_STR_STR_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyString_Type.tp_as_sequence->sq_concat(*operand1, operand2);
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

    return __BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_STR_OBJECT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "UNICODE" to Python2 'unicode',
 * Python3 'str'. */
static inline bool _BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && !PyUnicode_CHECK_INTERNED(*operand1) && 1) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = UNICODE_CONCAT(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyUnicode_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
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

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'unicode'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'str'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (PyUnicode_CheckExact(*operand1) && !PyUnicode_CHECK_INTERNED(*operand1) && 1) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyUnicode_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = UNICODE_CONCAT(*operand1, operand2);

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

    return __BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_UNICODE_INPLACE(operand1, operand2);
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyUnicode_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && !PyUnicode_CHECK_INTERNED(*operand1) && PyUnicode_CheckExact(operand2)) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = &PyUnicode_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_UNICODE_UNICODE_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = UNICODE_CONCAT(*operand1, operand2);

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

    return __BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_UNICODE_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "BYTES" to Python3 'bytes'. */
static inline bool _BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyBytes_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && 1) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat(*operand1, operand2);
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

bool BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyBytes_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
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

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'bytes'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (PyBytes_CheckExact(*operand1) && 1) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyBytes_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat(*operand1, operand2);
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

    return __BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_BYTES_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyBytes_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyBytes_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.

#if PYTHON_VERSION >= 0x300
        if (1 && PyBytes_CheckExact(operand2)) {
            return BYTES_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    PyTypeObject *type1 = &PyBytes_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_BYTES_BYTES_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyBytes_Type.tp_as_sequence->sq_concat(*operand1, operand2);
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

    return __BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_BYTES_OBJECT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = TUPLE_CONCAT(*operand1, operand2);

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

bool BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyTuple_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
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

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'tuple'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if ((PyTuple_CheckExact(*operand1) || PySequence_Check(*operand1)) && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyTuple_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = TUPLE_CONCAT(*operand1, operand2);

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

    return __BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_TUPLE_INPLACE(operand1, operand2);
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyTuple_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (1 && (PyTuple_CheckExact(operand2) || PySequence_Check(operand2))) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyTypeObject *type1 = &PyTuple_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_TUPLE_TUPLE_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = TUPLE_CONCAT(*operand1, operand2);

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

    return __BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_TUPLE_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "LIST" to Python 'list'. */
static inline bool _BINARY_OPERATION_ADD_LIST_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

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

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = LIST_CONCAT(*operand1, operand2);
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

bool BINARY_OPERATION_ADD_LIST_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LIST_LIST_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyList_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
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

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and 'list'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (PyList_CheckExact(*operand1) && 1) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    if (PySequence_Check(*operand1) && 1) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PyList_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_LIST_LIST_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = LIST_CONCAT(*operand1, operand2);
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

    return __BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_LIST_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PyList_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;

#if PYTHON_VERSION < 0x300
exit_inplace_exception:
    return false;
#endif
}
static inline bool _BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (1 && PyList_CheckExact(operand2)) {
        return LIST_EXTEND_FROM_LIST(*operand1, operand2);
    }

    if (1 && PySequence_Check(operand2)) {
        PyObject *result = PySequence_InPlaceConcat(*operand1, operand2);

        if (unlikely(result == NULL)) {
            return false;
        }

        Py_DECREF(*operand1);
        *operand1 = result;

        return true;
    }

    PyTypeObject *type1 = &PyList_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_ADD_LIST_LIST_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = LIST_CONCAT(*operand1, operand2);
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

    return __BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LIST_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_ADD_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_add;
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'int' and 'long'");
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

bool BINARY_OPERATION_ADD_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_LONG_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_ADD_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_add;
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'long' and 'int'");
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

bool BINARY_OPERATION_ADD_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_ADD_INT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyInt_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyFloat_Type.tp_as_number->nb_add;
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'int' and 'float'");
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

bool BINARY_OPERATION_ADD_INT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_INT_FLOAT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_ADD_FLOAT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyFloat_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_add;
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'float' and 'int'");
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

bool BINARY_OPERATION_ADD_FLOAT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_ADD_LONG_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyLong_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyFloat_Type.tp_as_number->nb_add;
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'long' and 'float'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'int' and 'float'");
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

bool BINARY_OPERATION_ADD_LONG_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LONG_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_ADD_FLOAT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyFloat_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyFloat_Type;
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

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_add;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_add;
        }

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_concat == NULL);
            // No inplace sequence repeat slot sq_inplace_concat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_concat == NULL);
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'float' and 'long'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: 'float' and 'int'");
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

bool BINARY_OPERATION_ADD_FLOAT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_FLOAT_LONG_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "UNICODE" to Python2 'unicode', Python3 'str'. */
static inline bool _BINARY_OPERATION_ADD_STR_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyString_Type;
    PyTypeObject *type2 = &PyUnicode_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        // Statically recognized that coercion is not possible with these types

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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;
}

bool BINARY_OPERATION_ADD_STR_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_STR_UNICODE_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_ADD_UNICODE_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyUnicode_Type;
    PyTypeObject *type2 = &PyString_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        // Statically recognized that coercion is not possible with these types

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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;
}

bool BINARY_OPERATION_ADD_UNICODE_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_UNICODE_STR_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(*operand1));
#endif
        CHECK_OBJECT(operand2);
        assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
        assert(NEW_STYLE_NUMBER(operand2));
#endif

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

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = PyInt_FromLong(clong_result);
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

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
#if PYTHON_VERSION < 0x300
        if (PyString_CheckExact(*operand1) && !PyString_CHECK_INTERNED(*operand1) && PyString_CheckExact(operand2)) {
            return STRING_ADD_INPLACE(operand1, operand2);
        }
#endif

#if PYTHON_VERSION >= 0x300
        if (PyUnicode_CheckExact(*operand1) && !PyUnicode_CHECK_INTERNED(*operand1) && PyUnicode_CheckExact(operand2)) {
            return UNICODE_ADD_INCREMENTAL(operand1, operand2);
        }
#endif
    }

    if (Py_TYPE(*operand1) == Py_TYPE(operand2)) {
        if (PyFloat_CheckExact(operand2)) {
            return _BINARY_OPERATION_ADD_FLOAT_FLOAT_INPLACE(operand1, operand2);
        }
#if PYTHON_VERSION >= 0x300
        if (PyLong_CheckExact(operand2)) {
            return _BINARY_OPERATION_ADD_LONG_LONG_INPLACE(operand1, operand2);
        }
#endif
    }

#if PYTHON_VERSION < 0x300
    // Python2 strings are to be treated differently, fall back to Python API here.
    if (PyString_CheckExact(*operand1) && PyString_CheckExact(operand2)) {
        PyString_Concat(operand1, operand2);
        return !ERROR_OCCURRED();
    }
#endif
#if PYTHON_VERSION >= 0x300
    // Python3 Strings are to be treated differently.
    if (PyUnicode_CheckExact(*operand1) && PyUnicode_CheckExact(operand2)) {
        PyObject *result = UNICODE_CONCAT(*operand1, operand2);

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

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
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

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 =
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_add : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_add : NULL;

            if (slot1 == slot2) {
                slot2 = NULL;
            }
        }

        if (slot1 != NULL) {
            if (slot2 != NULL) {
                if (PyType_IsSubtype(type2, type1)) {
                    PyObject *x = slot2(*operand1, operand2);

                    if (x != Py_NotImplemented) {
                        obj_result = x;
                        goto exit_inplace_result_object;
                    }

                    Py_DECREF(x);
                    slot2 = NULL;
                }
            }

            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        if (slot2 != NULL) {
            PyObject *x = slot2(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
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
            // Special case for "+" and "*", also works as sequence concat/repeat.
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for +: '%s' and '%s'", type1->tp_name,
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

bool BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_OBJECT_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_ADD_LIST_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
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

    PyTypeObject *type1 = &PyList_Type;
    PyTypeObject *type2 = &PyTuple_Type;

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4101)
#endif
    NUITKA_MAY_BE_UNUSED bool cbool_result;
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;
#ifdef _MSC_VER
#pragma warning(pop)
#endif

    // No inplace number slot nb_inplace_add available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_add == NULL);

    {
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_add == NULL ||
               type1->tp_as_number->nb_add == type2->tp_as_number->nb_add);

        // Statically recognized that coercion is not possible with these types

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

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = obj_result;

    return true;
}

bool BINARY_OPERATION_ADD_LIST_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_ADD_LIST_TUPLE_INPLACE(operand1, operand2);
}
