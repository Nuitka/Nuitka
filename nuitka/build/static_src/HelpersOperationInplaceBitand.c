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

/* C helpers for type in-place "&" (BITAND) operations */

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_BITAND_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    PyObject *x = PyLong_Type.tp_as_number->nb_and(*operand1, operand2);
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

bool BINARY_OPERATION_BITAND_LONG_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_LONG_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_BITAND_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_and : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'long'", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'int'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_BITAND_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_BITAND_LONG_LONG_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_and(*operand1, operand2);
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

    return __BINARY_OPERATION_BITAND_OBJECT_LONG_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_BITAND_OBJECT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_LONG_INPLACE(operand1, operand2);
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_BITAND_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_and available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_and == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_and;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

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
                        binaryfunc slot = mv->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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

#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'long' and '%s'", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_BITAND_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_BITAND_LONG_LONG_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PyLong_Type.tp_as_number->nb_and(*operand1, operand2);
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

    return __BINARY_OPERATION_BITAND_LONG_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_BITAND_LONG_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_LONG_OBJECT_INPLACE(operand1, operand2);
}

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_BITAND_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    const long r = a & b;

    clong_result = r;
    goto exit_result_ok_clong;

exit_result_ok_clong:

    // We got an object handed, that we have to release.
    Py_DECREF(*operand1);

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = PyInt_FromLong(clong_result);
    goto exit_result_ok;

exit_result_ok:
    return true;
}

bool BINARY_OPERATION_BITAND_INT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_INT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_BITAND_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_and : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'int'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_BITAND_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_BITAND_INT_INT_INPLACE(operand1, operand2);

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

        const long r = a & b;

        clong_result = r;
        goto exit_result_ok_clong;

    exit_result_ok_clong:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok:
        return true;
    }

    return __BINARY_OPERATION_BITAND_OBJECT_INT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_BITAND_OBJECT_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_INT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_BITAND_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_and available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_and == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_and;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

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
                        binaryfunc slot = mv->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_BITAND_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        // return _BINARY_OPERATION_BITAND_INT_INT_INPLACE(operand1, operand2);

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

        const long r = a & b;

        clong_result = r;
        goto exit_result_ok_clong;

    exit_result_ok_clong:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok:
        return true;
    }

    return __BINARY_OPERATION_BITAND_INT_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_BITAND_INT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_INT_OBJECT_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "LONG" to Python2 'long', Python3 'int'. */
static inline bool _BINARY_OPERATION_BITAND_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_and available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_and == NULL);

    {
        binaryfunc slot1 = PyInt_Type.tp_as_number->nb_and;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyLong_Type.tp_as_number->nb_and;
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'int' and 'long'");
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

bool BINARY_OPERATION_BITAND_INT_LONG_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_INT_LONG_INPLACE(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
static inline bool _BINARY_OPERATION_BITAND_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

    // No inplace number slot nb_inplace_and available for this type.
    assert(type1->tp_as_number == NULL || type1->tp_as_number->nb_inplace_and == NULL);

    {
        binaryfunc slot1 = PyLong_Type.tp_as_number->nb_and;
        binaryfunc slot2 = NULL;

        if (!(0)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PyInt_Type.tp_as_number->nb_and;
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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'long' and 'int'");
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

bool BINARY_OPERATION_BITAND_LONG_INT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_LONG_INT_INPLACE(operand1, operand2);
}
#endif

/* Code referring to "SET" corresponds to Python 'set' and "SET" to Python 'set'. */
static inline bool _BINARY_OPERATION_BITAND_SET_SET_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PySet_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PySet_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    // Not every code path will make use of all possible results.
    NUITKA_MAY_BE_UNUSED PyObject *obj_result;

    PyObject *x = PySet_Type.tp_as_number->nb_inplace_and(*operand1, operand2);

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

bool BINARY_OPERATION_BITAND_SET_SET_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_SET_SET_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "SET" to Python 'set'. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_BITAND_OBJECT_SET_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PySet_Type;

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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_and : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = PySet_Type.tp_as_number->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and 'set'", type1->tp_name);
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
static inline bool _BINARY_OPERATION_BITAND_OBJECT_SET_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    CHECK_OBJECT(operand2);
    assert(PySet_CheckExact(operand2));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = Py_TYPE(*operand1);
    PyTypeObject *type2 = &PySet_Type;

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_BITAND_SET_SET_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PySet_Type.tp_as_number->nb_inplace_and(*operand1, operand2);

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

    return __BINARY_OPERATION_BITAND_OBJECT_SET_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_BITAND_OBJECT_SET_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_SET_INPLACE(operand1, operand2);
}

/* Code referring to "SET" corresponds to Python 'set' and "OBJECT" to any Python object. */
static HEDLEY_NEVER_INLINE bool __BINARY_OPERATION_BITAND_SET_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    PyTypeObject *type1 = &PySet_Type;
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

    binaryfunc islot = PySet_Type.tp_as_number->nb_inplace_and;

    if (islot != NULL) {
        PyObject *x = islot(*operand1, operand2);

        if (x != Py_NotImplemented) {
            obj_result = x;
            goto exit_inplace_result_object;
        }

        Py_DECREF(x);
    }

    {
        binaryfunc slot1 = PySet_Type.tp_as_number->nb_and;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

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
                        binaryfunc slot = mv->nb_and;

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: 'set' and '%s'", type2->tp_name);
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
static inline bool _BINARY_OPERATION_BITAND_SET_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    assert(operand1); // Pointer must be non-null.

    CHECK_OBJECT(*operand1);
    assert(PySet_CheckExact(*operand1));
#if PYTHON_VERSION < 0x300
    assert(!NEW_STYLE_NUMBER(*operand1));
#endif
    CHECK_OBJECT(operand2);

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    PyTypeObject *type1 = &PySet_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

    if (type1 == type2) {
        assert(type1 == type2);

        // return _BINARY_OPERATION_BITAND_SET_SET_INPLACE(operand1, operand2);

        // Not every code path will make use of all possible results.
        NUITKA_MAY_BE_UNUSED PyObject *obj_result;

        PyObject *x = PySet_Type.tp_as_number->nb_inplace_and(*operand1, operand2);

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

    return __BINARY_OPERATION_BITAND_SET_OBJECT_INPLACE(operand1, operand2);
}

bool BINARY_OPERATION_BITAND_SET_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_SET_OBJECT_INPLACE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
static inline bool _BINARY_OPERATION_BITAND_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
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

        const long r = a & b;

        clong_result = r;
        goto exit_result_ok_clong;

    exit_result_ok_clong:

        // We got an object handed, that we have to release.
        Py_DECREF(*operand1);

        // That's our return value then. As we use a dedicated variable, it's
        // OK that way.
        *operand1 = PyInt_FromLong(clong_result);
        goto exit_result_ok;

    exit_result_ok:
        return true;
    }
#endif

    if (Py_REFCNT(*operand1) == 1) {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
    }

    if (Py_TYPE(*operand1) == Py_TYPE(operand2)) {
#if PYTHON_VERSION >= 0x300
        if (PyLong_CheckExact(operand2)) {
            return _BINARY_OPERATION_BITAND_LONG_LONG_INPLACE(operand1, operand2);
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
        (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_inplace_and : NULL;

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
            (type1->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type1)) ? type1->tp_as_number->nb_and : NULL;
        binaryfunc slot2 = NULL;

        if (!(type1 == type2)) {
            assert(type1 != type2);
            /* Different types, need to consider second value slot. */

            slot2 = (type2->tp_as_number != NULL && NEW_STYLE_NUMBER_TYPE(type2)) ? type2->tp_as_number->nb_and : NULL;

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
                        binaryfunc slot = mv->nb_and;

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
                        binaryfunc slot = mv->nb_and;

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

        PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for &: '%s' and '%s'", type1->tp_name,
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

bool BINARY_OPERATION_BITAND_OBJECT_OBJECT_INPLACE(PyObject **operand1, PyObject *operand2) {
    return _BINARY_OPERATION_BITAND_OBJECT_OBJECT_INPLACE(operand1, operand2);
}
