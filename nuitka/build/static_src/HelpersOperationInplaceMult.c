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

/* C helpers for type in-place "*" (MULT) operations */

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_MULT_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        PyObject *operand1_object = *operand1;
        PyObject *operand2_object = operand2;

        PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
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

bool BINARY_OPERATION_MULT_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_MULT_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_MULT_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_MULT_INT_INT_INPLACE(operand1, operand2);

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
            PyObject *operand1_object = *operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
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

    return __BINARY_OPERATION_MULT_OBJECT_INT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_MULT_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_MULT_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                        binaryfunc slot = mv->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // Special case for "*", also work with sequence repeat from right argument.
        if (type1->tp_as_sequence == NULL) {
            ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, *operand1);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_MULT_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_MULT_INT_INT_INPLACE(operand1, operand2);

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
            PyObject *operand1_object = *operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
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

    return __BINARY_OPERATION_MULT_INT_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_MULT_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_OBJECT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_MULT_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    PyObject *x = PyLong_Type.tp_as_number->nb_multiply(*operand1, operand2);
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

bool BINARY_OPERATION_MULT_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_MULT_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'long'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'int'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_MULT_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_MULT_LONG_LONG_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_multiply(*operand1, operand2);
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

    return __BINARY_OPERATION_MULT_OBJECT_LONG_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_MULT_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_MULT_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                        binaryfunc slot = mv->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // Special case for "*", also work with sequence repeat from right argument.
        if (type1->tp_as_sequence == NULL) {
            ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, *operand1);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and '%s'", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_MULT_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_MULT_LONG_LONG_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_multiply(*operand1, operand2);
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

    return __BINARY_OPERATION_MULT_LONG_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_MULT_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_MULT_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    double r = a * b;

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

bool BINARY_OPERATION_MULT_FLOAT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_FLOAT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_MULT_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyFloat_Type.tp_as_number->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'float'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_MULT_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_MULT_FLOAT_FLOAT_INPLACE(operand1, operand2);

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

        double r = a * b;

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

    return __BINARY_OPERATION_MULT_OBJECT_FLOAT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_MULT_OBJECT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_MULT_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                        binaryfunc slot = mv->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // Special case for "*", also work with sequence repeat from right argument.
        if (type1->tp_as_sequence == NULL) {
            ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, *operand1);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_MULT_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_MULT_FLOAT_FLOAT_INPLACE(operand1, operand2);

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

        double r = a * b;

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

    return __BINARY_OPERATION_MULT_FLOAT_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_MULT_FLOAT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_FLOAT_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_MULT_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
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
    }

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!PyIndex_Check(*operand1))) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = PyNumber_Index(*operand1);

                if (unlikely(index_value == NULL)) {
                    goto exit_inplace_exception;
                }

                {
                    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                    Py_DECREF(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
                        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer",
                                     type1->tp_name);
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'str'", type1->tp_name);
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

bool BINARY_OPERATION_MULT_OBJECT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_STR_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_MULT_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
    }

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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
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
                        binaryfunc slot = mv->nb_multiply;

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

        if (unlikely(!PyIndex_Check(operand2))) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = PyNumber_Index(operand2);

            if (unlikely(index_value == NULL)) {
                goto exit_inplace_exception;
            }

            {
                Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                Py_DECREF(index_value);

                /* Above conversion indicates an error as -1 */
                if (unlikely(count == -1)) {
                    PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_STR_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_STR_OBJECT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_MULT_INT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
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
    }

    PyTypeObject *type1 = &PyInt_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = PyInt_AS_LONG(index_value);
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'str'");
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

bool BINARY_OPERATION_MULT_INT_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_STR_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_MULT_STR_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
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

    PyTypeObject *type1 = &PyString_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = operand2;

            {
                Py_ssize_t count = PyInt_AS_LONG(index_value);
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_STR_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_STR_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "STR" to Python2 'str'. */
static inline bool _BINARY_OPERATION_MULT_LONG_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
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
    }

    PyTypeObject *type1 = &PyLong_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'str'");
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

bool BINARY_OPERATION_MULT_LONG_STR_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_STR_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_MULT_STR_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyString_CheckExact(*operand1));
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

    PyTypeObject *type1 = &PyString_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = operand2;

            {
                Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

                /* Above conversion indicates an error as -1 */
                if (unlikely(count == -1)) {
                    PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyString_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_STR_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_STR_LONG_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
static inline bool _BINARY_OPERATION_MULT_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));
    assert(NEW_STYLE_NUMBER(operand2));

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!PyIndex_Check(*operand1))) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = PyNumber_Index(*operand1);

                if (unlikely(index_value == NULL)) {
                    goto exit_inplace_exception;
                }

                {
                    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                    Py_DECREF(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
                        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer",
                                     type1->tp_name);
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'unicode'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'str'", type1->tp_name);
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

bool BINARY_OPERATION_MULT_OBJECT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_UNICODE_INPLACE(operand1, operand2);
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_MULT_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
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
                        binaryfunc slot = mv->nb_multiply;

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

        if (unlikely(!PyIndex_Check(operand2))) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = PyNumber_Index(operand2);

            if (unlikely(index_value == NULL)) {
                goto exit_inplace_exception;
            }

            {
                Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                Py_DECREF(index_value);

                /* Above conversion indicates an error as -1 */
                if (unlikely(count == -1)) {
                    PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_UNICODE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_UNICODE_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "UNICODE" to Python2 'unicode', Python3 'str'. */
static inline bool _BINARY_OPERATION_MULT_INT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
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

    PyTypeObject *type1 = &PyInt_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = PyInt_AS_LONG(index_value);
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'unicode'");
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

bool BINARY_OPERATION_MULT_INT_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_UNICODE_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_MULT_UNICODE_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyUnicode_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = operand2;

            {
                Py_ssize_t count = PyInt_AS_LONG(index_value);
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_UNICODE_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_UNICODE_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "UNICODE" to Python2 'unicode', Python3
 * 'str'. */
static inline bool _BINARY_OPERATION_MULT_LONG_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
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

    PyTypeObject *type1 = &PyLong_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'unicode'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'str'");
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

bool BINARY_OPERATION_MULT_LONG_UNICODE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_UNICODE_INPLACE(operand1, operand2);
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "LONG" to Python2 'long', Python3
 * 'int'. */
static inline bool _BINARY_OPERATION_MULT_UNICODE_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyUnicode_CheckExact(*operand1));
    assert(NEW_STYLE_NUMBER(*operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyUnicode_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
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
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyUnicode_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_UNICODE_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_UNICODE_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_MULT_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!PyIndex_Check(*operand1))) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = PyNumber_Index(*operand1);

                if (unlikely(index_value == NULL)) {
                    goto exit_inplace_exception;
                }

                {
                    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                    Py_DECREF(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
                        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer",
                                     type1->tp_name);
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'tuple'", type1->tp_name);
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

bool BINARY_OPERATION_MULT_OBJECT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_TUPLE_INPLACE(operand1, operand2);
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_MULT_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
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
                        binaryfunc slot = mv->nb_multiply;

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

        if (unlikely(!PyIndex_Check(operand2))) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = PyNumber_Index(operand2);

            if (unlikely(index_value == NULL)) {
                goto exit_inplace_exception;
            }

            {
                Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                Py_DECREF(index_value);

                /* Above conversion indicates an error as -1 */
                if (unlikely(count == -1)) {
                    PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_TUPLE_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_TUPLE_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_MULT_INT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyInt_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = PyInt_AS_LONG(index_value);
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'tuple'");
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

bool BINARY_OPERATION_MULT_INT_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_TUPLE_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "TUPLE" corresponds to Python 'tuple' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_MULT_TUPLE_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyTuple_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = operand2;

            {
                Py_ssize_t count = PyInt_AS_LONG(index_value);
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_TUPLE_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_TUPLE_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "TUPLE" to Python 'tuple'. */
static inline bool _BINARY_OPERATION_MULT_LONG_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyLong_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'tuple'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'tuple'");
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

bool BINARY_OPERATION_MULT_LONG_TUPLE_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_TUPLE_INPLACE(operand1, operand2);
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_MULT_TUPLE_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyTuple_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyTuple_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
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
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyTuple_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_TUPLE_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_TUPLE_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
static inline bool _BINARY_OPERATION_MULT_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!PyIndex_Check(*operand1))) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = PyNumber_Index(*operand1);

                if (unlikely(index_value == NULL)) {
                    goto exit_inplace_exception;
                }

                {
                    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                    Py_DECREF(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
                        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer",
                                     type1->tp_name);
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_inplace_repeat;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'list'", type1->tp_name);
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

bool BINARY_OPERATION_MULT_OBJECT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_LIST_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_MULT_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
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
                        binaryfunc slot = mv->nb_multiply;

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

        if (unlikely(!PyIndex_Check(operand2))) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = PyNumber_Index(operand2);

            if (unlikely(index_value == NULL)) {
                goto exit_inplace_exception;
            }

            {
                Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                Py_DECREF(index_value);

                /* Above conversion indicates an error as -1 */
                if (unlikely(count == -1)) {
                    PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_inplace_repeat;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_LIST_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LIST_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LIST" to Python 'list'. */
static inline bool _BINARY_OPERATION_MULT_INT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyInt_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyInt_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = PyInt_AS_LONG(index_value);
                    {
                        ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_inplace_repeat;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'list'");
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

bool BINARY_OPERATION_MULT_INT_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_LIST_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LIST" corresponds to Python 'list' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_MULT_LIST_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyList_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = operand2;

            {
                Py_ssize_t count = PyInt_AS_LONG(index_value);
                {
                    ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_inplace_repeat;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_LIST_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LIST_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LIST" to Python 'list'. */
static inline bool _BINARY_OPERATION_MULT_LONG_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyLong_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

        // Statically recognized that coercion is not possible with these types

        {
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
#if PYTHON_VERSION < 0x300
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'long' into an index-sized integer");
#else
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
#endif
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_inplace_repeat;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'list'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'list'");
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

bool BINARY_OPERATION_MULT_LONG_LIST_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_LIST_INPLACE(operand1, operand2);
}

/* Code referring to "LIST" corresponds to Python 'list' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_MULT_LIST_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyList_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyList_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;
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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
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
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = PyList_Type.tp_as_sequence->sq_inplace_repeat;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyList_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_LIST_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LIST_LONG_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION >= 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
static inline bool _BINARY_OPERATION_MULT_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
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
    }

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!PyIndex_Check(*operand1))) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = PyNumber_Index(*operand1);

                if (unlikely(index_value == NULL)) {
                    goto exit_inplace_exception;
                }

                {
                    Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                    Py_DECREF(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
                        PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer",
                                     type1->tp_name);
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and 'bytes'", type1->tp_name);
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

bool BINARY_OPERATION_MULT_OBJECT_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_BYTES_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_MULT_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
    }

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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;
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
                        binaryfunc slot = mv->nb_multiply;

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

        if (unlikely(!PyIndex_Check(operand2))) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = PyNumber_Index(operand2);

            if (unlikely(index_value == NULL)) {
                goto exit_inplace_exception;
            }

            {
                Py_ssize_t count = CONVERT_TO_REPEAT_FACTOR(index_value);

                Py_DECREF(index_value);

                /* Above conversion indicates an error as -1 */
                if (unlikely(count == -1)) {
                    PyErr_Format(PyExc_OverflowError, "cannot fit '%s' into an index-sized integer", type2->tp_name);
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_BYTES_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_BYTES_OBJECT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "BYTES" to Python3 'bytes'. */
static inline bool _BINARY_OPERATION_MULT_LONG_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyLong_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PyLong_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        assert(type2 == NULL || type2->tp_as_number == NULL || type2->tp_as_number->nb_multiply == NULL ||
               type1->tp_as_number->nb_multiply == type2->tp_as_number->nb_multiply);

        if (slot1 != NULL) {
            PyObject *x = slot1(*operand1, operand2);

            if (x != Py_NotImplemented) {
                obj_result = x;
                goto exit_inplace_result_object;
            }

            Py_DECREF(x);
        }

#if PYTHON_VERSION < 0x300
        if (!1 || !0) {
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
                        binaryfunc slot = mv->nb_multiply;

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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        if (type1->tp_as_sequence == NULL) {
            if (unlikely(!1)) {
                PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type1->tp_name);

                goto exit_inplace_exception;
            }

            {
                PyObject *index_value = *operand1;

                {
                    Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

                    /* Above conversion indicates an error as -1 */
                    if (unlikely(count == -1)) {
                        PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
                        goto exit_inplace_exception;
                    }
                    {
                        ssizeargfunc repeatfunc = NULL;
                        if (repeatfunc == NULL) {
                            repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                        }
                        PyObject *r = (*repeatfunc)(operand2, count);

                        obj_result = r;
                        goto exit_inplace_result_object;
                    }
                }
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'bytes'");
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

bool BINARY_OPERATION_MULT_LONG_BYTES_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_BYTES_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_MULT_BYTES_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PyBytes_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
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

    PyTypeObject *type1 = &PyBytes_Type;
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;
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
        if (!0 || !1) {
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
                        binaryfunc slot = mv->nb_multiply;

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

        if (unlikely(!1)) {
            PyErr_Format(PyExc_TypeError, "can't multiply sequence by non-int of type '%s'", type2->tp_name);

            goto exit_inplace_exception;
        }

        {
            PyObject *index_value = operand2;

            {
                Py_ssize_t count = CONVERT_LONG_TO_REPEAT_FACTOR(index_value);

                /* Above conversion indicates an error as -1 */
                if (unlikely(count == -1)) {
                    PyErr_Format(PyExc_OverflowError, "cannot fit 'int' into an index-sized integer");
                    goto exit_inplace_exception;
                }
                {
                    ssizeargfunc repeatfunc = NULL;
                    if (repeatfunc == NULL) {
                        repeatfunc = PyBytes_Type.tp_as_sequence->sq_repeat;
                    }
                    PyObject *r = (*repeatfunc)(*operand1, count);

                    obj_result = r;
                    goto exit_inplace_result_object;
                }
            }
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

exit_inplace_exception:
    return false;
}

bool BINARY_OPERATION_MULT_BYTES_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_BYTES_LONG_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_MULT_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;
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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'long'");
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

bool BINARY_OPERATION_MULT_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_LONG_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_MULT_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_multiply;
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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'int'");
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

bool BINARY_OPERATION_MULT_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_MULT_INT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyFloat_Type.tp_as_number->nb_multiply;
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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'float'");
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

bool BINARY_OPERATION_MULT_INT_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_INT_FLOAT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "FLOAT" corresponds to Python 'float' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_MULT_FLOAT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_multiply;
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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
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

bool BINARY_OPERATION_MULT_FLOAT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_FLOAT_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "FLOAT" to Python 'float'. */
static inline bool _BINARY_OPERATION_MULT_LONG_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyFloat_Type.tp_as_number->nb_multiply;
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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'long' and 'float'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'int' and 'float'");
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

bool BINARY_OPERATION_MULT_LONG_FLOAT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_LONG_FLOAT_INPLACE(operand1, operand2);
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_MULT_FLOAT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_multiply available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_multiply == NULL);

    {
        binaryfunc slot1 = PyFloat_Type.tp_as_number->nb_multiply;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_multiply;
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
            // No sequence repeat slot sq_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_repeat == NULL);
            // No inplace sequence repeat slot sq_inplace_repeat available for this type.
            assert(type1->tp_as_sequence == NULL || type1->tp_as_sequence->sq_inplace_repeat == NULL);
        }
        // No sequence repeat slot sq_repeat available for this type.
        assert(type2->tp_as_sequence == NULL || type2->tp_as_sequence->sq_repeat == NULL);

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'long'");
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: 'float' and 'int'");
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

bool BINARY_OPERATION_MULT_FLOAT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_FLOAT_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_MULT_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
            PyObject *operand1_object = *operand1;
            PyObject *operand2_object = operand2;

            PyObject *r = PyLong_Type.tp_as_number->nb_multiply(operand1_object, operand2_object);
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
    }

    if (Py_TYPE(*operand1) == Py_TYPE(operand2)) {
        if (PyFloat_CheckExact(operand2)) {
            return _BINARY_OPERATION_MULT_FLOAT_FLOAT_INPLACE(operand1, operand2);
        }
#if PYTHON_VERSION >= 0x300
        if (PyLong_CheckExact(operand2)) {
            return _BINARY_OPERATION_MULT_LONG_LONG_INPLACE(operand1, operand2);
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

    binaryfunc islot =
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_multiply : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_multiply : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 =
                (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_multiply : NULL;

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
                        binaryfunc slot = mv->nb_multiply;

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
                        binaryfunc slot = mv->nb_multiply;

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
            ssizeargfunc sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_inplace_repeat : NULL;
            if (sq_slot == NULL) {
                sq_slot = type1->tp_as_sequence != NULL ? type1->tp_as_sequence->sq_repeat : NULL;
            }

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, *operand1, operand2);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }
        // Special case for "*", also work with sequence repeat from right argument.
        if (type1->tp_as_sequence == NULL) {
            ssizeargfunc sq_slot = type2->tp_as_sequence != NULL ? type2->tp_as_sequence->sq_repeat : NULL;

            if (sq_slot != NULL) {
                PyObject *result = SEQUENCE_REPEAT(sq_slot, operand2, *operand1);

                obj_result = result;
                goto exit_inplace_result_object;
            }
        }

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for *: '%s' and '%s'", type1->tp_name,
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

bool BINARY_OPERATION_MULT_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_MULT_OBJECT_OBJECT_INPLACE(operand1, operand2);
}
