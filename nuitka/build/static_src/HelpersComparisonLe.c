//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template HelperOperationComparison.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

/* C helpers for type specialized "<=" (LE) comparisons */

#if PYTHON_VERSION < 0x300
static PyObject *COMPARE_LE_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    const long a = PyInt_AS_LONG(operand1);
    const long b = PyInt_AS_LONG(operand2);

    bool r = a <= b;

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
#endif
#if PYTHON_VERSION < 0x300
static bool COMPARE_LE_CBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyInt_CheckExact(operand2));

    const long a = PyInt_AS_LONG(operand1);
    const long b = PyInt_AS_LONG(operand2);

    bool r = a <= b;

    // Convert to target type.
    bool result = r;

    return result;
}
#endif
/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return COMPARE_LE_OBJECT_INT_INT(operand1, operand2);
    }
#endif

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        bool r = true;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }

#if PYTHON_VERSION < 0x300
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

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == type2 && !PyInstance_Check(operand1)) {

        richcmpfunc frich = TP_RICHCOMPARE(type1);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != type2 && Nuitka_Type_IsSubtype(type2, type1)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
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
            // Banking on C compile to optimize "strcmp".
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

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != type2 && Nuitka_Type_IsSubtype(type2, type1)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= %s()", type1->tp_name, type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and '%s'", type1->tp_name,
                     type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "OBJECT" corresponds to any Python object and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {

#if PYTHON_VERSION < 0x300
    if (PyInt_CheckExact(operand1) && PyInt_CheckExact(operand2)) {
        return COMPARE_LE_CBOOL_INT_INT(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }
#endif

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        bool r = true;
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }

#if PYTHON_VERSION < 0x300
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

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == type2 && !PyInstance_Check(operand1)) {

        richcmpfunc frich = TP_RICHCOMPARE(type1);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (type1 != type2 && Nuitka_Type_IsSubtype(type2, type1)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
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
            // Banking on C compile to optimize "strcmp".
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

    switch (Py_LE) {
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

    if (type1 != type2 && Nuitka_Type_IsSubtype(type2, type1)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= %s()", type1->tp_name, type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and '%s'", type1->tp_name,
                     type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

#if PYTHON_VERSION < 0x300
static PyObject *COMPARE_LE_OBJECT_STR_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    PyStringObject *a = (PyStringObject *)operand1;
    PyStringObject *b = (PyStringObject *)operand2;

    // Same object has fast path for all operations.
    if (operand1 == operand2) {
        bool r = true;

        // Convert to target type.
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }

    Py_ssize_t len_a = Py_SIZE(operand1);
    Py_ssize_t len_b = Py_SIZE(operand2);

    Py_ssize_t min_len = (len_a < len_b) ? len_a : len_b;
    int c;

    if (min_len > 0) {
        c = Py_CHARMASK(*a->ob_sval) - Py_CHARMASK(*b->ob_sval);

        if (c == 0) {
            c = memcmp(a->ob_sval, b->ob_sval, min_len);
        }
    } else {
        c = 0;
    }

    if (c == 0) {
        c = (len_a < len_b) ? -1 : (len_a > len_b) ? 1 : 0;
    }

    c = c <= 0;

    // Convert to target type.
    PyObject *result = BOOL_FROM(c != 0);
    Py_INCREF_IMMORTAL(result);
    return result;
}
#endif
#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_STR(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyString_Type) {
        return COMPARE_LE_OBJECT_STR_STR(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyString_Type && !0) {

        richcmpfunc frich = PyString_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyString_Type && 0) {
        f = PyString_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyString_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyString_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyString_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "str");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyString_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyString_Type && Nuitka_Type_IsSubtype(&PyString_Type, type1)) {
        f = PyString_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyString_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= str()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'str'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_STR_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyString_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_STR_STR(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyString_Type == type2 && !0) {

        richcmpfunc frich = PyString_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyString_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyString_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyString_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyString_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyString_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("str", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyString_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyString_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyString_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyString_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: str() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'str' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "STR" to Python2 'str'. */
PyObject *RICH_COMPARE_LE_OBJECT_STR_STR(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_STR_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static bool COMPARE_LE_CBOOL_STR_STR(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyString_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyString_CheckExact(operand2));

    PyStringObject *a = (PyStringObject *)operand1;
    PyStringObject *b = (PyStringObject *)operand2;

    // Same object has fast path for all operations.
    if (operand1 == operand2) {
        bool r = true;

        // Convert to target type.
        bool result = r;

        return result;
    }

    Py_ssize_t len_a = Py_SIZE(operand1);
    Py_ssize_t len_b = Py_SIZE(operand2);

    Py_ssize_t min_len = (len_a < len_b) ? len_a : len_b;
    int c;

    if (min_len > 0) {
        c = Py_CHARMASK(*a->ob_sval) - Py_CHARMASK(*b->ob_sval);

        if (c == 0) {
            c = memcmp(a->ob_sval, b->ob_sval, min_len);
        }
    } else {
        c = 0;
    }

    if (c == 0) {
        c = (len_a < len_b) ? -1 : (len_a > len_b) ? 1 : 0;
    }

    c = c <= 0;

    // Convert to target type.
    bool result = c != 0;

    return result;
}
#endif
#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "STR" to Python2 'str'. */
bool RICH_COMPARE_LE_CBOOL_STR_STR(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_CBOOL_STR_STR(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "STR" to Python2 'str'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_STR(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyString_Type) {
        return COMPARE_LE_CBOOL_STR_STR(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyString_Type && !0) {

        richcmpfunc frich = PyString_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (type1 != &PyString_Type && 0) {
        f = PyString_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyString_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyString_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyString_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "str");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyString_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyString_Type && Nuitka_Type_IsSubtype(&PyString_Type, type1)) {
        f = PyString_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyString_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= str()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'str'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "STR" corresponds to Python2 'str' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_STR_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyString_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_CBOOL_STR_STR(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyString_Type == type2 && !0) {

        richcmpfunc frich = PyString_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (&PyString_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyString_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyString_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyString_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyString_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("str", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyString_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyString_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyString_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyString_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: str() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'str' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

static PyObject *COMPARE_LE_OBJECT_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    PyUnicodeObject *a = (PyUnicodeObject *)operand1;
    PyUnicodeObject *b = (PyUnicodeObject *)operand2;

    // Same object has fast path for all operations.
    if (operand1 == operand2) {
        bool r = true;

        // Convert to target type.
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }

    PyObject *r = PyUnicode_RichCompare((PyObject *)a, (PyObject *)b, Py_LE);
    CHECK_OBJECT(r);

    return r;
}
/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyUnicode_Type) {
        return COMPARE_LE_OBJECT_UNICODE_UNICODE(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyUnicode_Type && !0) {

        richcmpfunc frich = PyUnicode_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyUnicode_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyUnicode_Type && 0) {
        f = PyUnicode_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyUnicode_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = PyUnicode_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyUnicode_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyUnicode_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, (PYTHON_VERSION < 0x300 ? "unicode" : "str"));

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyUnicode_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyUnicode_Type && Nuitka_Type_IsSubtype(&PyUnicode_Type, type1)) {
        f = PyUnicode_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyUnicode_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= unicode()", type1->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= str()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'str'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyUnicode_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_UNICODE_UNICODE(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyUnicode_Type == type2 && !0) {

        richcmpfunc frich = PyUnicode_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyUnicode_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyUnicode_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyUnicode_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyUnicode_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = PyUnicode_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyUnicode_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyUnicode_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp((PYTHON_VERSION < 0x300 ? "unicode" : "str"), type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyUnicode_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyUnicode_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyUnicode_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyUnicode_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: unicode() <= %s()", type2->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: str() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'str' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "UNICODE" to Python2 'unicode',
 * Python3 'str'. */
PyObject *RICH_COMPARE_LE_OBJECT_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_UNICODE_UNICODE(operand1, operand2);
}

static bool COMPARE_LE_CBOOL_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyUnicode_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyUnicode_CheckExact(operand2));

    PyUnicodeObject *a = (PyUnicodeObject *)operand1;
    PyUnicodeObject *b = (PyUnicodeObject *)operand2;

    // Same object has fast path for all operations.
    if (operand1 == operand2) {
        bool r = true;

        // Convert to target type.
        bool result = r;

        return result;
    }

    PyObject *r = PyUnicode_RichCompare((PyObject *)a, (PyObject *)b, Py_LE);
    CHECK_OBJECT(r);

    // Convert to target type if necessary
    bool result = r == Py_True;
    Py_DECREF_IMMORTAL(r);

    return result;
}
/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "UNICODE" to Python2 'unicode',
 * Python3 'str'. */
bool RICH_COMPARE_LE_CBOOL_UNICODE_UNICODE(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_CBOOL_UNICODE_UNICODE(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "UNICODE" to Python2 'unicode', Python3 'str'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_UNICODE(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyUnicode_Type) {
        return COMPARE_LE_CBOOL_UNICODE_UNICODE(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyUnicode_Type && !0) {

        richcmpfunc frich = PyUnicode_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyUnicode_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_LE) {
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

    if (type1 != &PyUnicode_Type && 0) {
        f = PyUnicode_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyUnicode_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = PyUnicode_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyUnicode_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyUnicode_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, (PYTHON_VERSION < 0x300 ? "unicode" : "str"));

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyUnicode_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyUnicode_Type && Nuitka_Type_IsSubtype(&PyUnicode_Type, type1)) {
        f = PyUnicode_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyUnicode_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= unicode()", type1->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= str()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'str'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "UNICODE" corresponds to Python2 'unicode', Python3 'str' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_UNICODE_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyUnicode_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_CBOOL_UNICODE_UNICODE(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyUnicode_Type == type2 && !0) {

        richcmpfunc frich = PyUnicode_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyUnicode_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_LE) {
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

    if (&PyUnicode_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyUnicode_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyUnicode_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = PyUnicode_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyUnicode_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyUnicode_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp((PYTHON_VERSION < 0x300 ? "unicode" : "str"), type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyUnicode_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyUnicode_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyUnicode_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyUnicode_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: unicode() <= %s()", type2->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: str() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'str' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

#if PYTHON_VERSION >= 0x300
static PyObject *COMPARE_LE_OBJECT_BYTES_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    PyBytesObject *a = (PyBytesObject *)operand1;
    PyBytesObject *b = (PyBytesObject *)operand2;

    // Same object has fast path for all operations.
    if (operand1 == operand2) {
        bool r = true;

        // Convert to target type.
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }

    Py_ssize_t len_a = Py_SIZE(operand1);
    Py_ssize_t len_b = Py_SIZE(operand2);

    Py_ssize_t min_len = (len_a < len_b) ? len_a : len_b;
    int c;

    if (min_len > 0) {
        c = Py_CHARMASK(*a->ob_sval) - Py_CHARMASK(*b->ob_sval);

        if (c == 0) {
            c = memcmp(a->ob_sval, b->ob_sval, min_len);
        }
    } else {
        c = 0;
    }

    if (c == 0) {
        c = (len_a < len_b) ? -1 : (len_a > len_b) ? 1 : 0;
    }

    c = c <= 0;

    // Convert to target type.
    PyObject *result = BOOL_FROM(c != 0);
    Py_INCREF_IMMORTAL(result);
    return result;
}
#endif
#if PYTHON_VERSION >= 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_BYTES(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyBytes_Type) {
        return COMPARE_LE_OBJECT_BYTES_BYTES(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyBytes_Type && !0) {

        richcmpfunc frich = PyBytes_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyBytes_Type && 0) {
        f = PyBytes_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyBytes_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyBytes_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyBytes_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "bytes");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyBytes_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyBytes_Type && Nuitka_Type_IsSubtype(&PyBytes_Type, type1)) {
        f = PyBytes_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyBytes_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= bytes()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'bytes'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyBytes_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_BYTES_BYTES(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyBytes_Type == type2 && !0) {

        richcmpfunc frich = PyBytes_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyBytes_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyBytes_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyBytes_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyBytes_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyBytes_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("bytes", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyBytes_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyBytes_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyBytes_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyBytes_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: bytes() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'bytes' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "BYTES" to Python3 'bytes'. */
PyObject *RICH_COMPARE_LE_OBJECT_BYTES_BYTES(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_BYTES_BYTES(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
static bool COMPARE_LE_CBOOL_BYTES_BYTES(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyBytes_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyBytes_CheckExact(operand2));

    PyBytesObject *a = (PyBytesObject *)operand1;
    PyBytesObject *b = (PyBytesObject *)operand2;

    // Same object has fast path for all operations.
    if (operand1 == operand2) {
        bool r = true;

        // Convert to target type.
        bool result = r;

        return result;
    }

    Py_ssize_t len_a = Py_SIZE(operand1);
    Py_ssize_t len_b = Py_SIZE(operand2);

    Py_ssize_t min_len = (len_a < len_b) ? len_a : len_b;
    int c;

    if (min_len > 0) {
        c = Py_CHARMASK(*a->ob_sval) - Py_CHARMASK(*b->ob_sval);

        if (c == 0) {
            c = memcmp(a->ob_sval, b->ob_sval, min_len);
        }
    } else {
        c = 0;
    }

    if (c == 0) {
        c = (len_a < len_b) ? -1 : (len_a > len_b) ? 1 : 0;
    }

    c = c <= 0;

    // Convert to target type.
    bool result = c != 0;

    return result;
}
#endif
#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "BYTES" to Python3 'bytes'. */
bool RICH_COMPARE_LE_CBOOL_BYTES_BYTES(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_CBOOL_BYTES_BYTES(operand1, operand2);
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "BYTES" to Python3 'bytes'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_BYTES(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyBytes_Type) {
        return COMPARE_LE_CBOOL_BYTES_BYTES(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyBytes_Type && !0) {

        richcmpfunc frich = PyBytes_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (type1 != &PyBytes_Type && 0) {
        f = PyBytes_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyBytes_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyBytes_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyBytes_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "bytes");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyBytes_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyBytes_Type && Nuitka_Type_IsSubtype(&PyBytes_Type, type1)) {
        f = PyBytes_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyBytes_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= bytes()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'bytes'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

#if PYTHON_VERSION >= 0x300
/* Code referring to "BYTES" corresponds to Python3 'bytes' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_BYTES_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyBytes_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_CBOOL_BYTES_BYTES(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyBytes_Type == type2 && !0) {

        richcmpfunc frich = PyBytes_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (&PyBytes_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyBytes_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyBytes_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyBytes_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyBytes_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("bytes", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyBytes_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyBytes_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyBytes_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyBytes_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: bytes() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'bytes' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyInt_Type) {
        return COMPARE_LE_OBJECT_INT_INT(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyInt_Type && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyInt_Type && 0) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = PyInt_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyInt_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyInt_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "int");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyInt_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyInt_Type && Nuitka_Type_IsSubtype(&PyInt_Type, type1)) {
        f = NULL;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= int()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'int'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyInt_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_INT_INT(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyInt_Type == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyInt_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = PyInt_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyInt_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyInt_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("int", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyInt_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyInt_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = NULL;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: int() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'int' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
PyObject *RICH_COMPARE_LE_OBJECT_INT_INT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "INT" to Python2 'int'. */
bool RICH_COMPARE_LE_CBOOL_INT_INT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_CBOOL_INT_INT(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "OBJECT" corresponds to any Python object and "INT" to Python2 'int'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_INT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyInt_Type) {
        return COMPARE_LE_CBOOL_INT_INT(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyInt_Type && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (type1 != &PyInt_Type && 0) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = PyInt_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyInt_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyInt_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "int");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyInt_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyInt_Type && Nuitka_Type_IsSubtype(&PyInt_Type, type1)) {
        f = NULL;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = NULL;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= int()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'int'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_INT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyInt_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_CBOOL_INT_INT(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyInt_Type == type2 && !0) {

        richcmpfunc frich = NULL;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (&PyInt_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = NULL;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = PyInt_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyInt_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyInt_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("int", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyInt_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyInt_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyInt_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = NULL;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: int() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'int' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}
#endif

static PyObject *COMPARE_LE_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyLongObject *operand1_long_object = (PyLongObject *)operand1;

    PyLongObject *operand2_long_object = (PyLongObject *)operand2;

    bool r;

    if (operand1_long_object == operand2_long_object) {
        r = true;
    } else if (Nuitka_LongGetSignedDigitSize(operand1_long_object) !=
               Nuitka_LongGetSignedDigitSize(operand2_long_object)) {
        r = Nuitka_LongGetSignedDigitSize(operand1_long_object) - Nuitka_LongGetSignedDigitSize(operand2_long_object) <
            0;
    } else {
        Py_ssize_t i = Nuitka_LongGetDigitSize(operand1_long_object);
        r = true;
        while (--i >= 0) {
            if (Nuitka_LongGetDigitPointer(operand1_long_object)[i] !=
                Nuitka_LongGetDigitPointer(operand2_long_object)[i]) {
                r = Nuitka_LongGetDigitPointer(operand1_long_object)[i] <
                    Nuitka_LongGetDigitPointer(operand2_long_object)[i];
                if (Nuitka_LongIsNegative(operand1_long_object)) {
                    r = !r;
                }
                break;
            }
        }
    }

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyLong_Type) {
        return COMPARE_LE_OBJECT_LONG_LONG(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyLong_Type && !0) {

        richcmpfunc frich = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyLong_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyLong_Type && 0) {
        f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = PyLong_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyLong_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyLong_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, (PYTHON_VERSION < 0x300 ? "long" : "int"));

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyLong_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyLong_Type && Nuitka_Type_IsSubtype(&PyLong_Type, type1)) {
        f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= long()", type1->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= int()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'int'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyLong_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_LONG_LONG(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyLong_Type == type2 && !0) {

        richcmpfunc frich = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyLong_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyLong_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = PyLong_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyLong_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyLong_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp((PYTHON_VERSION < 0x300 ? "long" : "int"), type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyLong_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyLong_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: long() <= %s()", type2->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: int() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'int' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
PyObject *RICH_COMPARE_LE_OBJECT_LONG_LONG(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_LONG_LONG(operand1, operand2);
}

static bool COMPARE_LE_CBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyLong_CheckExact(operand2));

    PyLongObject *operand1_long_object = (PyLongObject *)operand1;

    PyLongObject *operand2_long_object = (PyLongObject *)operand2;

    bool r;

    if (operand1_long_object == operand2_long_object) {
        r = true;
    } else if (Nuitka_LongGetSignedDigitSize(operand1_long_object) !=
               Nuitka_LongGetSignedDigitSize(operand2_long_object)) {
        r = Nuitka_LongGetSignedDigitSize(operand1_long_object) - Nuitka_LongGetSignedDigitSize(operand2_long_object) <
            0;
    } else {
        Py_ssize_t i = Nuitka_LongGetDigitSize(operand1_long_object);
        r = true;
        while (--i >= 0) {
            if (Nuitka_LongGetDigitPointer(operand1_long_object)[i] !=
                Nuitka_LongGetDigitPointer(operand2_long_object)[i]) {
                r = Nuitka_LongGetDigitPointer(operand1_long_object)[i] <
                    Nuitka_LongGetDigitPointer(operand2_long_object)[i];
                if (Nuitka_LongIsNegative(operand1_long_object)) {
                    r = !r;
                }
                break;
            }
        }
    }

    // Convert to target type.
    bool result = r;

    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "LONG" to Python2 'long', Python3 'int'. */
bool RICH_COMPARE_LE_CBOOL_LONG_LONG(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_CBOOL_LONG_LONG(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "LONG" to Python2 'long', Python3 'int'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_LONG(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyLong_Type) {
        return COMPARE_LE_CBOOL_LONG_LONG(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyLong_Type && !0) {

        richcmpfunc frich = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyLong_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_LE) {
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

    if (type1 != &PyLong_Type && 0) {
        f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = PyLong_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyLong_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyLong_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, (PYTHON_VERSION < 0x300 ? "long" : "int"));

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyLong_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyLong_Type && Nuitka_Type_IsSubtype(&PyLong_Type, type1)) {
        f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= long()", type1->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= int()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'int'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_LONG_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyLong_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_CBOOL_LONG_LONG(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyLong_Type == type2 && !0) {

        richcmpfunc frich = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }

        // No rich comparison worked, but maybe compare works.
        cmpfunc fcmp = PyLong_Type.tp_compare;

        if (fcmp != NULL) {
            int c = (*fcmp)(operand1, operand2);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NUITKA_BOOL_EXCEPTION;
            }

            switch (Py_LE) {
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

    if (&PyLong_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = PyLong_Type.tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyLong_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyLong_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp((PYTHON_VERSION < 0x300 ? "long" : "int"), type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyLong_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyLong_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyLong_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = (PYTHON_VERSION < 0x300 ? NULL : PyLong_Type.tp_richcompare);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x300
        PyErr_Format(PyExc_TypeError, "unorderable types: long() <= %s()", type2->tp_name);
#elif PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: int() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'int' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

static PyObject *COMPARE_LE_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    bool r = a <= b;

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyFloat_Type) {
        return COMPARE_LE_OBJECT_FLOAT_FLOAT(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyFloat_Type && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyFloat_Type && 0) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyFloat_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyFloat_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "float");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyFloat_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyFloat_Type && Nuitka_Type_IsSubtype(&PyFloat_Type, type1)) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= float()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'float'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyFloat_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_FLOAT_FLOAT(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyFloat_Type == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyFloat_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyFloat_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyFloat_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("float", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyFloat_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyFloat_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: float() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'float' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
PyObject *RICH_COMPARE_LE_OBJECT_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_FLOAT_FLOAT(operand1, operand2);
}

static bool COMPARE_LE_CBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyFloat_CheckExact(operand2));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = PyFloat_AS_DOUBLE(operand2);

    bool r = a <= b;

    // Convert to target type.
    bool result = r;

    return result;
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "FLOAT" to Python 'float'. */
bool RICH_COMPARE_LE_CBOOL_FLOAT_FLOAT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_CBOOL_FLOAT_FLOAT(operand1, operand2);
}

/* Code referring to "OBJECT" corresponds to any Python object and "FLOAT" to Python 'float'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_FLOAT(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyFloat_Type) {
        return COMPARE_LE_CBOOL_FLOAT_FLOAT(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyFloat_Type && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (type1 != &PyFloat_Type && 0) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyFloat_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyFloat_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "float");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyFloat_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyFloat_Type && Nuitka_Type_IsSubtype(&PyFloat_Type, type1)) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyFloat_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= float()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'float'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "FLOAT" corresponds to Python 'float' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_FLOAT_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyFloat_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_CBOOL_FLOAT_FLOAT(operand1, operand2) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyFloat_Type == type2 && !0) {

        richcmpfunc frich = PyFloat_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (&PyFloat_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyFloat_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyFloat_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("float", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyFloat_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyFloat_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyFloat_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyFloat_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: float() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'float' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

static PyObject *COMPARE_LE_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

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
        bool r = len_a <= len_b;

        // Convert to target type.
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }

    return RICH_COMPARE_LE_OBJECT_OBJECT_OBJECT(a->ob_item[i], b->ob_item[i]);
}
/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyTuple_Type) {
        return COMPARE_LE_OBJECT_TUPLE_TUPLE(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyTuple_Type && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyTuple_Type && 0) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyTuple_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyTuple_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "tuple");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyTuple_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyTuple_Type && Nuitka_Type_IsSubtype(&PyTuple_Type, type1)) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= tuple()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'tuple'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyTuple_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_TUPLE_TUPLE(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyTuple_Type == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyTuple_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyTuple_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyTuple_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyTuple_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("tuple", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyTuple_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyTuple_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyTuple_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: tuple() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'tuple' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
PyObject *RICH_COMPARE_LE_OBJECT_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_TUPLE_TUPLE(operand1, operand2);
}

static nuitka_bool COMPARE_LE_NBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyTuple_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyTuple_CheckExact(operand2));

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
        bool r = len_a <= len_b;

        // Convert to target type.
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }

    return RICH_COMPARE_LE_NBOOL_OBJECT_OBJECT(a->ob_item[i], b->ob_item[i]);
}
/* Code referring to "OBJECT" corresponds to any Python object and "TUPLE" to Python 'tuple'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_TUPLE(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyTuple_Type) {
        return COMPARE_LE_NBOOL_TUPLE_TUPLE(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyTuple_Type && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (type1 != &PyTuple_Type && 0) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyTuple_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyTuple_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "tuple");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyTuple_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyTuple_Type && Nuitka_Type_IsSubtype(&PyTuple_Type, type1)) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyTuple_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= tuple()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'tuple'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_TUPLE_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyTuple_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_NBOOL_TUPLE_TUPLE(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyTuple_Type == type2 && !0) {

        richcmpfunc frich = PyTuple_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (&PyTuple_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyTuple_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyTuple_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyTuple_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("tuple", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyTuple_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyTuple_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyTuple_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyTuple_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: tuple() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'tuple' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "TUPLE" corresponds to Python 'tuple' and "TUPLE" to Python 'tuple'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_TUPLE_TUPLE(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_NBOOL_TUPLE_TUPLE(operand1, operand2);
}

static PyObject *COMPARE_LE_OBJECT_LIST_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    PyListObject *a = (PyListObject *)operand1;
    PyListObject *b = (PyListObject *)operand2;

    bool found = false;
    nuitka_bool res = NUITKA_BOOL_TRUE;

    Py_ssize_t i;
    for (i = 0; i < Py_SIZE(a) && i < Py_SIZE(b); i++) {
        PyObject *aa = a->ob_item[i];
        PyObject *bb = b->ob_item[i];

        if (aa == bb) {
            continue;
        }

        Py_INCREF(aa);
        Py_INCREF(bb);
        res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(aa, bb);
        Py_DECREF(aa);
        Py_DECREF(bb);

        if (res == NUITKA_BOOL_EXCEPTION) {
            return NULL;
        }

        if (res == NUITKA_BOOL_FALSE) {
            found = true;
            break;
        }
    }

    if (found == false) {
        bool r = Py_SIZE(a) <= Py_SIZE(b);

        // Convert to target type.
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }

    return RICH_COMPARE_LE_OBJECT_OBJECT_OBJECT(a->ob_item[i], b->ob_item[i]);
}
/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
PyObject *RICH_COMPARE_LE_OBJECT_OBJECT_LIST(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyList_Type) {
        return COMPARE_LE_OBJECT_LIST_LIST(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyList_Type && !0) {

        richcmpfunc frich = PyList_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (type1 != &PyList_Type && 0) {
        f = PyList_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyList_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyList_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyList_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "list");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyList_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (type1 != &PyList_Type && Nuitka_Type_IsSubtype(&PyList_Type, type1)) {
        f = PyList_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyList_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= list()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'list'", type1->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
PyObject *RICH_COMPARE_LE_OBJECT_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyList_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_OBJECT_LIST_LIST(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyList_Type == type2 && !0) {

        richcmpfunc frich = PyList_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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
            Py_INCREF_IMMORTAL(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (&PyList_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyList_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyList_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyList_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyList_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("list", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyList_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (Py_LE) {
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
    Py_INCREF_IMMORTAL(result);
    return result;
#else
    bool checked_reverse_op = false;
    richcmpfunc f;

    if (&PyList_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyList_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyList_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            return result;
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                return result;
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
    case Py_EQ: {
        bool r = operand1 == operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    case Py_NE: {
        bool r = operand1 != operand2;
        PyObject *result = BOOL_FROM(r);
        Py_INCREF_IMMORTAL(result);
        return result;
    }
    default:
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: list() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'list' and '%s'", type2->tp_name);
#endif
        return NULL;
    }
#endif
}

/* Code referring to "LIST" corresponds to Python 'list' and "LIST" to Python 'list'. */
PyObject *RICH_COMPARE_LE_OBJECT_LIST_LIST(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_LIST_LIST(operand1, operand2);
}

static nuitka_bool COMPARE_LE_NBOOL_LIST_LIST(PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    PyListObject *a = (PyListObject *)operand1;
    PyListObject *b = (PyListObject *)operand2;

    bool found = false;
    nuitka_bool res = NUITKA_BOOL_TRUE;

    Py_ssize_t i;
    for (i = 0; i < Py_SIZE(a) && i < Py_SIZE(b); i++) {
        PyObject *aa = a->ob_item[i];
        PyObject *bb = b->ob_item[i];

        if (aa == bb) {
            continue;
        }

        Py_INCREF(aa);
        Py_INCREF(bb);
        res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(aa, bb);
        Py_DECREF(aa);
        Py_DECREF(bb);

        if (res == NUITKA_BOOL_EXCEPTION) {
            return NUITKA_BOOL_EXCEPTION;
        }

        if (res == NUITKA_BOOL_FALSE) {
            found = true;
            break;
        }
    }

    if (found == false) {
        bool r = Py_SIZE(a) <= Py_SIZE(b);

        // Convert to target type.
        nuitka_bool result = r ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;

        return result;
    }

    return RICH_COMPARE_LE_NBOOL_OBJECT_OBJECT(a->ob_item[i], b->ob_item[i]);
}
/* Code referring to "OBJECT" corresponds to any Python object and "LIST" to Python 'list'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_OBJECT_LIST(PyObject *operand1, PyObject *operand2) {

    if (Py_TYPE(operand1) == &PyList_Type) {
        return COMPARE_LE_NBOOL_LIST_LIST(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type1 = Py_TYPE(operand1);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (type1 == &PyList_Type && !0) {

        richcmpfunc frich = PyList_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (type1 != &PyList_Type && 0) {
        f = PyList_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = PyList_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (PyInstance_Check(operand1)) {
        cmpfunc fcmp = type1->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (type1 == &PyList_Type) {
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
                Py_uintptr_t bb = (Py_uintptr_t)&PyList_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp(type1->tp_name, "list");

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)type1;
                Py_uintptr_t bb = (Py_uintptr_t)&PyList_Type;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (type1 != &PyList_Type && Nuitka_Type_IsSubtype(&PyList_Type, type1)) {
        f = PyList_Type.tp_richcompare;

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = TP_RICHCOMPARE(type1);

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = PyList_Type.tp_richcompare;

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() <= list()", type1->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of '%s' and 'list'", type1->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "LIST" corresponds to Python 'list' and "OBJECT" to any Python object. */
nuitka_bool RICH_COMPARE_LE_NBOOL_LIST_OBJECT(PyObject *operand1, PyObject *operand2) {

    if (&PyList_Type == Py_TYPE(operand2)) {
        return COMPARE_LE_NBOOL_LIST_LIST(operand1, operand2);
    }

#if PYTHON_VERSION < 0x300
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#else
    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NUITKA_BOOL_EXCEPTION;
    }
#endif

    PyTypeObject *type2 = Py_TYPE(operand2);

#if PYTHON_VERSION < 0x300
    // If the types are equal, we may get away immediately except for instances.
    if (&PyList_Type == type2 && !0) {

        richcmpfunc frich = PyList_Type.tp_richcompare;

        if (frich != NULL) {
            PyObject *result = (*frich)(operand1, operand2, Py_LE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
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

            switch (Py_LE) {
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

    if (&PyList_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyList_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyList_Type.tp_richcompare;
    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    f = TP_RICHCOMPARE(type2);
    if (f != NULL) {
        PyObject *result = (*f)(operand2, operand1, Py_GE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    int c;

    if (0) {
        cmpfunc fcmp = NULL;
        c = (*fcmp)(operand1, operand2);
    } else if (PyInstance_Check(operand2)) {
        cmpfunc fcmp = type2->tp_compare;
        c = (*fcmp)(operand1, operand2);
    } else {
        c = try_3way_compare(operand1, operand2);
    }

    if (c >= 2) {
        if (&PyList_Type == type2) {
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
                Py_uintptr_t aa = (Py_uintptr_t)&PyList_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(operand2)) {
            c = 1;
        } else {
            // Banking on C compile to optimize "strcmp".
            int s = strcmp("list", type2->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on type address.
                Py_uintptr_t aa = (Py_uintptr_t)&PyList_Type;
                Py_uintptr_t bb = (Py_uintptr_t)type2;

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NUITKA_BOOL_EXCEPTION;
    }

    switch (Py_LE) {
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

    if (&PyList_Type != type2 && Nuitka_Type_IsSubtype(type2, &PyList_Type)) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            checked_reverse_op = true;

            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    f = PyList_Type.tp_richcompare;

    if (f != NULL) {
        PyObject *result = (*f)(operand1, operand2, Py_LE);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();

            if (unlikely(result == NULL)) {
                return NUITKA_BOOL_EXCEPTION;
            }

            {
                nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                Py_DECREF(result);
                return r;
            }
        }

        Py_DECREF_IMMORTAL(result);
    }

    if (checked_reverse_op == false) {
        f = TP_RICHCOMPARE(type2);

        if (f != NULL) {
            PyObject *result = (*f)(operand2, operand1, Py_GE);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();

                if (unlikely(result == NULL)) {
                    return NUITKA_BOOL_EXCEPTION;
                }

                {
                    nuitka_bool r = CHECK_IF_TRUE(result) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;
                    Py_DECREF(result);
                    return r;
                }
            }

            Py_DECREF_IMMORTAL(result);
        }
    }

    Py_LeaveRecursiveCall();

    // If it is not implemented, do pointer identity checks as "==" and "!=" and
    // otherwise give an error
    switch (Py_LE) {
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
#if PYTHON_VERSION < 0x360
        PyErr_Format(PyExc_TypeError, "unorderable types: list() <= %s()", type2->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'<=' not supported between instances of 'list' and '%s'", type2->tp_name);
#endif
        return NUITKA_BOOL_EXCEPTION;
    }
#endif
}

/* Code referring to "LIST" corresponds to Python 'list' and "LIST" to Python 'list'. */
nuitka_bool RICH_COMPARE_LE_NBOOL_LIST_LIST(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_NBOOL_LIST_LIST(operand1, operand2);
}

static PyObject *COMPARE_LE_OBJECT_LONG_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));

    PyLongObject *operand1_long_object = (PyLongObject *)operand1;

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
            operand2_digit_count += 1;
            assert(operand2_digit_count <= (Py_ssize_t)(sizeof(operand2_digit_count) / sizeof(digit)));

            operand2_digits[operand2_digit_count] = (digit)(t & PyLong_MASK);
            t >>= PyLong_SHIFT;
        }
    }

    NUITKA_MAY_BE_UNUSED Py_ssize_t operand2_size =
        operand2_is_negative == false ? operand2_digit_count : -operand2_digit_count;

    bool r;

    if (Nuitka_LongGetSignedDigitSize(operand1_long_object) != operand2_size) {
        r = Nuitka_LongGetSignedDigitSize(operand1_long_object) - operand2_size < 0;
    } else {
        Py_ssize_t i = Nuitka_LongGetDigitSize(operand1_long_object);
        r = true;
        while (--i >= 0) {
            if (Nuitka_LongGetDigitPointer(operand1_long_object)[i] != operand2_digits[i]) {
                r = Nuitka_LongGetDigitPointer(operand1_long_object)[i] < operand2_digits[i];
                if (Nuitka_LongIsNegative(operand1_long_object)) {
                    r = !r;
                }
                break;
            }
        }
    }

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
PyObject *RICH_COMPARE_LE_OBJECT_LONG_INT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_OBJECT_LONG_CLONG(operand1, PyInt_AS_LONG(operand1));
}
#endif

static bool COMPARE_LE_CBOOL_LONG_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));

    PyLongObject *operand1_long_object = (PyLongObject *)operand1;

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
            operand2_digit_count += 1;
            assert(operand2_digit_count <= (Py_ssize_t)(sizeof(operand2_digit_count) / sizeof(digit)));

            operand2_digits[operand2_digit_count] = (digit)(t & PyLong_MASK);
            t >>= PyLong_SHIFT;
        }
    }

    NUITKA_MAY_BE_UNUSED Py_ssize_t operand2_size =
        operand2_is_negative == false ? operand2_digit_count : -operand2_digit_count;

    bool r;

    if (Nuitka_LongGetSignedDigitSize(operand1_long_object) != operand2_size) {
        r = Nuitka_LongGetSignedDigitSize(operand1_long_object) - operand2_size < 0;
    } else {
        Py_ssize_t i = Nuitka_LongGetDigitSize(operand1_long_object);
        r = true;
        while (--i >= 0) {
            if (Nuitka_LongGetDigitPointer(operand1_long_object)[i] != operand2_digits[i]) {
                r = Nuitka_LongGetDigitPointer(operand1_long_object)[i] < operand2_digits[i];
                if (Nuitka_LongIsNegative(operand1_long_object)) {
                    r = !r;
                }
                break;
            }
        }
    }

    // Convert to target type.
    bool result = r;

    return result;
}
#if PYTHON_VERSION < 0x300
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "INT" to Python2 'int'. */
bool RICH_COMPARE_LE_CBOOL_LONG_INT(PyObject *operand1, PyObject *operand2) {

    return COMPARE_LE_CBOOL_LONG_CLONG(operand1, PyInt_AS_LONG(operand1));
}
#endif

#if PYTHON_VERSION < 0x300
static PyObject *COMPARE_LE_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));

    const long a = PyInt_AS_LONG(operand1);
    const long b = operand2;

    bool r = a <= b;

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
#endif
#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
PyObject *RICH_COMPARE_LE_OBJECT_INT_CLONG(PyObject *operand1, long operand2) {

    return COMPARE_LE_OBJECT_INT_CLONG(operand1, operand2);
}
#endif

#if PYTHON_VERSION < 0x300
static bool COMPARE_LE_CBOOL_INT_CLONG(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyInt_CheckExact(operand1));

    const long a = PyInt_AS_LONG(operand1);
    const long b = operand2;

    bool r = a <= b;

    // Convert to target type.
    bool result = r;

    return result;
}
#endif
#if PYTHON_VERSION < 0x300
/* Code referring to "INT" corresponds to Python2 'int' and "CLONG" to C platform long value. */
bool RICH_COMPARE_LE_CBOOL_INT_CLONG(PyObject *operand1, long operand2) {

    return COMPARE_LE_CBOOL_INT_CLONG(operand1, operand2);
}
#endif

static PyObject *COMPARE_LE_OBJECT_LONG_DIGIT(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    assert(Py_ABS(operand2) < (1 << PyLong_SHIFT));

    PyLongObject *operand1_long_object = (PyLongObject *)operand1;

    bool r;

    if (Nuitka_LongGetSignedDigitSize(operand1_long_object) !=
        (Py_ssize_t)((operand2 == 0) ? 0 : ((operand2 < 0) ? -1 : 1))) {
        r = Nuitka_LongGetSignedDigitSize(operand1_long_object) -
                (Py_ssize_t)((operand2 == 0) ? 0 : ((operand2 < 0) ? -1 : 1)) <
            0;
    } else {
        Py_ssize_t i = Nuitka_LongGetDigitSize(operand1_long_object);
        r = true;
        while (--i >= 0) {
            if (Nuitka_LongGetDigitPointer(operand1_long_object)[i] != (digit)Py_ABS(operand2)) {
                r = Nuitka_LongGetDigitPointer(operand1_long_object)[i] < (digit)Py_ABS(operand2);
                if (Nuitka_LongIsNegative(operand1_long_object)) {
                    r = !r;
                }
                break;
            }
        }
    }

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "DIGIT" to C platform digit value for long
 * Python objects. */
PyObject *RICH_COMPARE_LE_OBJECT_LONG_DIGIT(PyObject *operand1, long operand2) {

    return COMPARE_LE_OBJECT_LONG_DIGIT(operand1, operand2);
}

static bool COMPARE_LE_CBOOL_LONG_DIGIT(PyObject *operand1, long operand2) {
    CHECK_OBJECT(operand1);
    assert(PyLong_CheckExact(operand1));
    assert(Py_ABS(operand2) < (1 << PyLong_SHIFT));

    PyLongObject *operand1_long_object = (PyLongObject *)operand1;

    bool r;

    if (Nuitka_LongGetSignedDigitSize(operand1_long_object) !=
        (Py_ssize_t)((operand2 == 0) ? 0 : ((operand2 < 0) ? -1 : 1))) {
        r = Nuitka_LongGetSignedDigitSize(operand1_long_object) -
                (Py_ssize_t)((operand2 == 0) ? 0 : ((operand2 < 0) ? -1 : 1)) <
            0;
    } else {
        Py_ssize_t i = Nuitka_LongGetDigitSize(operand1_long_object);
        r = true;
        while (--i >= 0) {
            if (Nuitka_LongGetDigitPointer(operand1_long_object)[i] != (digit)Py_ABS(operand2)) {
                r = Nuitka_LongGetDigitPointer(operand1_long_object)[i] < (digit)Py_ABS(operand2);
                if (Nuitka_LongIsNegative(operand1_long_object)) {
                    r = !r;
                }
                break;
            }
        }
    }

    // Convert to target type.
    bool result = r;

    return result;
}
/* Code referring to "LONG" corresponds to Python2 'long', Python3 'int' and "DIGIT" to C platform digit value for long
 * Python objects. */
bool RICH_COMPARE_LE_CBOOL_LONG_DIGIT(PyObject *operand1, long operand2) {

    return COMPARE_LE_CBOOL_LONG_DIGIT(operand1, operand2);
}

static PyObject *COMPARE_LE_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = operand2;

    bool r = a <= b;

    // Convert to target type.
    PyObject *result = BOOL_FROM(r);
    Py_INCREF_IMMORTAL(result);
    return result;
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "CFLOAT" to C platform float value. */
PyObject *RICH_COMPARE_LE_OBJECT_FLOAT_CFLOAT(PyObject *operand1, double operand2) {

    return COMPARE_LE_OBJECT_FLOAT_CFLOAT(operand1, operand2);
}

static bool COMPARE_LE_CBOOL_FLOAT_CFLOAT(PyObject *operand1, double operand2) {
    CHECK_OBJECT(operand1);
    assert(PyFloat_CheckExact(operand1));

    const double a = PyFloat_AS_DOUBLE(operand1);
    const double b = operand2;

    bool r = a <= b;

    // Convert to target type.
    bool result = r;

    return result;
}
/* Code referring to "FLOAT" corresponds to Python 'float' and "CFLOAT" to C platform float value. */
bool RICH_COMPARE_LE_CBOOL_FLOAT_CFLOAT(PyObject *operand1, double operand2) {

    return COMPARE_LE_CBOOL_FLOAT_CFLOAT(operand1, operand2);
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
