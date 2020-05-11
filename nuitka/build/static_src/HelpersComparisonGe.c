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
/* WARNING, this code is GENERATED. Modify the template HelperOperationComparison.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized ">=" (GE) comparions */

#if PYTHON_VERSION < 300
static PyObject *COMPARE_GE_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    bool r = a >= b;

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
}
#endif
#if PYTHON_VERSION < 300
static bool COMPARE_GE_CBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    bool r = a >= b;

    // Convert to target type.
    bool result = r;

    return result;
}
#endif
#if PYTHON_VERSION < 300
static nuitka_bool COMPARE_GE_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
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

    bool r = a >= b;

    // Convert to target type.
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
}
#endif
/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_GE_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {

#if PYTHON_VERSION < 300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return COMPARE_GE_OBJECT_INT_INT(operand1, operand2);
    }
#endif

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        bool r = true;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !PyInstance_Check(operand1)) {

        richcmpfunc frich = RICHCOMPARE(type1);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = type1->tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            PyObject *result = BOOL_FROM(r);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= %s()", type1->tp_name, type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and '%s'", type1->tp_name,
                     type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
bool RICH_COMPARE_GE_CBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {

#if PYTHON_VERSION < 300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return COMPARE_GE_CBOOL_INT_INT(operand1, operand2);
    }
#endif

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        bool r = true;
        bool result = r;

        return result;
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return false;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return false;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !PyInstance_Check(operand1)) {

        richcmpfunc frich = RICHCOMPARE(type1);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = type1->tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return false;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            bool result = r;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return false;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    bool result = r;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        bool result = r;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        bool result = r;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= %s()", type1->tp_name, type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and '%s'", type1->tp_name,
                     type2->tp_name);
#endif
        return false;
    }
#endif
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_GE_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {

#if PYTHON_VERSION < 300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return COMPARE_GE_NBOOL_INT_INT(operand1, operand2);
    }
#endif

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        bool r = true;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !PyInstance_Check(operand1)) {

        richcmpfunc frich = RICHCOMPARE(type1);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = type1->tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= %s()", type1->tp_name, type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and '%s'", type1->tp_name,
                     type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
PyObject *RICH_COMPARE_GE_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
bool RICH_COMPARE_GE_CBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_CBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
nuitka_bool RICH_COMPARE_GE_NBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_NBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
PyObject *RICH_COMPARE_GE_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyInt_Type) {
        return COMPARE_GE_OBJECT_INT_INT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyInt_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyInt_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            PyObject *result = BOOL_FROM(r);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = NULL;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= int()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'int'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
bool RICH_COMPARE_GE_CBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyInt_Type) {
        return COMPARE_GE_CBOOL_INT_INT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return false;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return false;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyInt_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyInt_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return false;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            bool result = r;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return false;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    bool result = r;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = NULL;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        bool result = r;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        bool result = r;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= int()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'int'", type1->tp_name);
#endif
        return false;
    }
#endif
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
nuitka_bool RICH_COMPARE_GE_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyInt_Type) {
        return COMPARE_GE_NBOOL_INT_INT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyInt_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyInt_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = NULL;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= int()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'int'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_GE_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyInt_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_OBJECT_INT_INT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyInt_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            PyObject *result = BOOL_FROM(r);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = NULL;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: int() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'int' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
bool RICH_COMPARE_GE_CBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyInt_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_CBOOL_INT_INT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return false;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return false;
    }
#endif

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyInt_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return false;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            bool result = r;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return false;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    bool result = r;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = NULL;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        bool result = r;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        bool result = r;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: int() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'int' and '%s'", type2->tp_name);
#endif
        return false;
    }
#endif
}
#endif

#if PYTHON_VERSION < 300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_GE_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyInt_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_NBOOL_INT_INT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = &PyInt_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyInt_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = NULL;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: int() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'int' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

static PyObject *COMPARE_GE_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
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

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    bool r = a >= b;

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
PyObject *RICH_COMPARE_GE_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_OBJECT_FLOAT_FLOAT(operand1, operand2);
}

static bool COMPARE_GE_CBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
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

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    bool r = a >= b;

    // Convert to target type.
    bool result = r;

    return result;
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
bool RICH_COMPARE_GE_CBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_CBOOL_FLOAT_FLOAT(operand1, operand2);
}

static nuitka_bool COMPARE_GE_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
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

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    bool r = a >= b;

    // Convert to target type.
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
nuitka_bool RICH_COMPARE_GE_NBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_NBOOL_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
PyObject *RICH_COMPARE_GE_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyFloat_Type) {
        return COMPARE_GE_OBJECT_FLOAT_FLOAT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyFloat_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            PyObject *result = BOOL_FROM(r);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= float()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'float'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
bool RICH_COMPARE_GE_CBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyFloat_Type) {
        return COMPARE_GE_CBOOL_FLOAT_FLOAT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return false;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return false;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyFloat_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return false;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            bool result = r;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return false;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    bool result = r;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        bool result = r;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        bool result = r;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= float()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'float'", type1->tp_name);
#endif
        return false;
    }
#endif
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
nuitka_bool RICH_COMPARE_GE_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyFloat_Type) {
        return COMPARE_GE_NBOOL_FLOAT_FLOAT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyFloat_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= float()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'float'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_GE_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyFloat_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_OBJECT_FLOAT_FLOAT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = &PyFloat_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            PyObject *result = BOOL_FROM(r);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: float() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'float' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
bool RICH_COMPARE_GE_CBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyFloat_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_CBOOL_FLOAT_FLOAT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return false;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return false;
    }
#endif

    PyTypeObject *type1 = &PyFloat_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return false;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            bool result = r;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return false;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    bool result = r;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        bool result = r;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        bool result = r;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: float() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'float' and '%s'", type2->tp_name);
#endif
        return false;
    }
#endif
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_GE_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyFloat_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_NBOOL_FLOAT_FLOAT(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = &PyFloat_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: float() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'float' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

static PyObject *COMPARE_GE_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTupleObject *a = (PyTupleObject *)operand1;
    PyTupleObject *b = (PyTupleObject *)operand2;

    Py_ssize_t len_a = Py_SIZE(a);
    Py_ssize_t len_b = Py_SIZE(b);

    bool found = false;
    nuitka_bool res = NUITKA_BOOL_TRUE;

    Py_ssize_t i;
    for (i = 0; i < len_a && i < len_b; i++) {
        PyObject *aa = a->ob_item[i];
        PyObject *bb = b->ob_item[i];

        if (aa == bb) {
            continue;
        }

        res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(aa, bb);

        if (res == NUITKA_BOOL_EXCEPTION) {
            return NULL;
        }

        if (res == NUITKA_BOOL_FALSE) {
            found = true;
            break;
        }
    }

    if (found == false) {
        bool r = len_a >= len_b;

        // Convert to target type.
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }

    return RICH_COMPARE_GE_OBJECT_OBJECT_OBJECT(a->ob_item[i], b->ob_item[i]);
}
/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
PyObject *RICH_COMPARE_GE_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_OBJECT_TUPLE_TUPLE(operand1, operand2);
}

static bool COMPARE_GE_CBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTupleObject *a = (PyTupleObject *)operand1;
    PyTupleObject *b = (PyTupleObject *)operand2;

    Py_ssize_t len_a = Py_SIZE(a);
    Py_ssize_t len_b = Py_SIZE(b);

    bool found = false;
    nuitka_bool res = NUITKA_BOOL_TRUE;

    Py_ssize_t i;
    for (i = 0; i < len_a && i < len_b; i++) {
        PyObject *aa = a->ob_item[i];
        PyObject *bb = b->ob_item[i];

        if (aa == bb) {
            continue;
        }

        res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(aa, bb);

        if (res == NUITKA_BOOL_EXCEPTION) {
            return false;
        }

        if (res == NUITKA_BOOL_FALSE) {
            found = true;
            break;
        }
    }

    if (found == false) {
        bool r = len_a >= len_b;

        // Convert to target type.
        bool result = r;

        return result;
    }

    return RICH_COMPARE_GE_CBOOL_OBJECT_OBJECT(a->ob_item[i], b->ob_item[i]);
}
/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
bool RICH_COMPARE_GE_CBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_CBOOL_TUPLE_TUPLE(operand1, operand2);
}

static nuitka_bool COMPARE_GE_NBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand1));
#endif
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));
#if PYTHON_VERSION < 300
    assert(!NEW_STYLE_NUMBER(operand2));
#endif

    PyTupleObject *a = (PyTupleObject *)operand1;
    PyTupleObject *b = (PyTupleObject *)operand2;

    Py_ssize_t len_a = Py_SIZE(a);
    Py_ssize_t len_b = Py_SIZE(b);

    bool found = false;
    nuitka_bool res = NUITKA_BOOL_TRUE;

    Py_ssize_t i;
    for (i = 0; i < len_a && i < len_b; i++) {
        PyObject *aa = a->ob_item[i];
        PyObject *bb = b->ob_item[i];

        if (aa == bb) {
            continue;
        }

        res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(aa, bb);

        if (res == NUITKA_BOOL_EXCEPTION) {
            return NUITKA_BOOL_EXCEPTION;
        }

        if (res == NUITKA_BOOL_FALSE) {
            found = true;
            break;
        }
    }

    if (found == false) {
        bool r = len_a >= len_b;

        // Convert to target type.
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }

    return RICH_COMPARE_GE_NBOOL_OBJECT_OBJECT(a->ob_item[i], b->ob_item[i]);
}
/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
nuitka_bool RICH_COMPARE_GE_NBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {

    return COMPARE_GE_NBOOL_TUPLE_TUPLE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
PyObject *RICH_COMPARE_GE_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyTuple_Type) {
        return COMPARE_GE_OBJECT_TUPLE_TUPLE(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyTuple_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            PyObject *result = BOOL_FROM(r);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= tuple()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'tuple'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
bool RICH_COMPARE_GE_CBOOL_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyTuple_Type) {
        return COMPARE_GE_CBOOL_TUPLE_TUPLE(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return false;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return false;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyTuple_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return false;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            bool result = r;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return false;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    bool result = r;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        bool result = r;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        bool result = r;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= tuple()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'tuple'", type1->tp_name);
#endif
        return false;
    }
#endif
}

/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
nuitka_bool RICH_COMPARE_GE_NBOOL_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyTuple_Type) {
        return COMPARE_GE_NBOOL_TUPLE_TUPLE(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);
    PyTypeObject *type2 = &PyTuple_Type;

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && 0) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (0) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() >= tuple()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of '%s' and 'tuple'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_GE_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyTuple_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_OBJECT_TUPLE_TUPLE(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = &PyTuple_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            PyObject *result = BOOL_FROM(r);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    PyObject *result = BOOL_FROM(r);
    Py_INCREF(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: tuple() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'tuple' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
bool RICH_COMPARE_GE_CBOOL_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyTuple_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_CBOOL_TUPLE_TUPLE(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return false;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return false;
    }
#endif

    PyTypeObject *type1 = &PyTuple_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return false;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            bool result = r;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return false;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    bool result = r;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return false;
            }

            bool r = CHECK_IF_TRUE(result);
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return false;
                }

                bool r = CHECK_IF_TRUE(result);
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        bool result = r;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        bool result = r;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: tuple() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'tuple' and '%s'", type2->tp_name);
#endif
        return false;
    }
#endif
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_GE_NBOOL_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyTuple_Type == Py_TYPE(operand2)) {
        return COMPARE_GE_NBOOL_TUPLE_TUPLE(operand1, operand2);
    }

// TODO: Get hint from recursion control if that's needed and have variants
// with and without.
#if PYTHON_VERSION < 300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = &PyTuple_Type;
    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 300
    // If the types are equal, we may get away immediately.
    if (type1 == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = NULL;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_GE) {
            case Py_LT:
                c = c < 0;
                break;
            case Py_LE:
                c = c <= 0;
                break;
            case Py_EQ:
                c = c == 0;
                break;
            case Py_NE:
                c = c != 0;
                break;
            case Py_GT:
                c = c > 0;
                break;
            case Py_GE:
                c = c >= 0;
                break;
            default:
                NUITKA_CANNOT_GET_HERE("wrong op_code");
            }

            bool r = c != 0;
            nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    int c;

    if (0) {
        c = (*type1->tp_compare)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        c = (*type2->tp_compare)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == type2) {
            Py_uintptr_t aa = (Py_uintptr_t)operand1;
            Py_uintptr_t bb = (Py_uintptr_t)operand2;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (operand1 == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (operand2 == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(operand1)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(operand2)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // TODO: Could be hard coded if one is known.
            int s = strcmp(type1->tp_name, type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_GE) {
    case Py_LT:
        c = c < 0;
        break;
    case Py_LE:
        c = c <= 0;
        break;
    case Py_EQ:
        c = c == 0;
        break;
    case Py_NE:
        c = c != 0;
        break;
    case Py_GT:
        c = c > 0;
        break;
    case Py_GE:
        c = c >= 0;
        break;
    }

    bool r = c != 0;
    nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && PyType_IsSubtype(type2, type1)) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }

            Py_DECREF(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
            Py_DECREF(result);
            return r;
        }

        Py_DECREF(result);
    }

    if (checked_reverse_op == false) {
        f = RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_GE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }
    default:
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: tuple() >= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'>=' not supported between instances of 'tuple' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
