//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
/** For making rich comparisons work.
 *
 * Helpers that implement the details of comparisons for both Python2 and
 * Python3 individually, mostly because of the many changes.
 *
 **/

#if PYTHON_VERSION < 300

extern PyObject *const_str_plain___cmp__;
static cmpfunc default_tp_compare;

void _initSlotCompare() {
    // Create a class with "__cmp__" attribute, to get a hand at the default
    // implementation of tp_compare. It's not part of the API and with shared
    // libraries it's not accessible. The name does not matter, nor does the
    // actual value used for "__cmp__".

    // Use "int" as the base class.
    PyObject *pos_args = PyTuple_New(1);
    PyTuple_SET_ITEM(pos_args, 0, (PyObject *)&PyInt_Type);
    Py_INCREF(&PyInt_Type);

    // Use "__cmp__" with true value, won't matter.
    PyObject *kw_args = PyDict_New();
    PyDict_SetItem(kw_args, const_str_plain___cmp__, Py_True);

    // Create the type.
    PyObject *c =
        PyObject_CallFunctionObjArgs((PyObject *)&PyType_Type, const_str_plain___cmp__, pos_args, kw_args, NULL);
    Py_DECREF(pos_args);
    Py_DECREF(kw_args);

    PyObject *r = PyObject_CallFunctionObjArgs(c, NULL);
    Py_DECREF(c);

    CHECK_OBJECT(r);
    assert(Py_TYPE(r)->tp_compare);

    default_tp_compare = Py_TYPE(r)->tp_compare;

    Py_DECREF(r);
}

#define RICHCOMPARE(t) (PyType_HasFeature((t), Py_TPFLAGS_HAVE_RICHCOMPARE) ? (t)->tp_richcompare : NULL)

static inline int adjust_tp_compare(int c) {
    if (PyErr_Occurred()) {
        return -2;
    } else if (c < -1 || c > 1) {
        return c < -1 ? -1 : 1;
    } else {
        return c;
    }
}

static inline int coerce_objects(PyObject **pa, PyObject **pb) {
    PyObject *a = *pa;
    PyObject *b = *pb;

    // Shortcut only for old-style types
    if (a->ob_type == b->ob_type && !PyType_HasFeature(a->ob_type, Py_TPFLAGS_CHECKTYPES)) {
        Py_INCREF(a);
        Py_INCREF(b);

        return 0;
    }
    if (a->ob_type->tp_as_number && a->ob_type->tp_as_number->nb_coerce) {
        int res = (*a->ob_type->tp_as_number->nb_coerce)(pa, pb);

        if (res <= 0) {
            return res;
        }
    }
    if (b->ob_type->tp_as_number && b->ob_type->tp_as_number->nb_coerce) {
        int res = (*b->ob_type->tp_as_number->nb_coerce)(pb, pa);

        if (res <= 0) {
            return res;
        }
    }

    return 1;
}

static int try_3way_compare(PyObject *a, PyObject *b) {
    cmpfunc f1 = a->ob_type->tp_compare;
    cmpfunc f2 = b->ob_type->tp_compare;
    int c;

    // Same compares, just use it.
    if (f1 != NULL && f1 == f2) {
        c = (*f1)(a, b);
        return adjust_tp_compare(c);
    }

    // If one slot is _PyObject_SlotCompare (which we got our hands on under a
    // different name in case it's a shared library), prefer it.
    if (f1 == default_tp_compare || f2 == default_tp_compare) {
        return default_tp_compare(a, b);
    }

    // Try coercion.
    c = coerce_objects(&a, &b);

    if (c < 0) {
        return -2;
    }
    if (c > 0) {
        return 2;
    }

    f1 = a->ob_type->tp_compare;
    if (f1 != NULL && f1 == b->ob_type->tp_compare) {
        c = (*f1)(a, b);
        Py_DECREF(a);
        Py_DECREF(b);

        return adjust_tp_compare(c);
    }

    // No comparison defined.
    Py_DECREF(a);
    Py_DECREF(b);
    return 2;
}

static PyObject *MY_RICHCOMPARE(PyObject *a, PyObject *b, int op) {
    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

    PyObject *result;

    // TODO: Type a-ware rich comparison would be really nice, but this is what
    // CPython does, and should be even in "richcomparisons.h" as the first
    // thing, so it's even cheaper.
    if (PyInt_CheckExact(a) && PyInt_CheckExact(b)) {
        long aa, bb;
#ifdef __NUITKA_NO_ASSERT__
        bool res;
#else
        bool res = false;
#endif

        aa = PyInt_AS_LONG(a);
        bb = PyInt_AS_LONG(b);

        switch (op) {
        case Py_LT:
            res = aa < bb;
            break;
        case Py_LE:
            res = aa <= bb;
            break;
        case Py_EQ:
            res = aa == bb;
            break;
        case Py_NE:
            res = aa != bb;
            break;
        case Py_GT:
            res = aa > bb;
            break;
        case Py_GE:
            res = aa >= bb;
            break;
        default:
            assert(false);
        }

        result = BOOL_FROM(res);
        Py_INCREF(result);
        return result;
    }

    // TODO: Get hint from recursion control if that's needed.
    if (unlikely(Py_EnterRecursiveCall((char *)" in cmp"))) {
        return NULL;
    }

    // If the types are equal, we may get away immediately.
    if (a->ob_type == b->ob_type && !PyInstance_Check(a)) {
        richcmpfunc frich = RICHCOMPARE(a->ob_type);

        if (frich != NULL) {
            result = (*frich)(a, b, op);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();
                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison, but maybe compare works.
        cmpfunc fcmp = a->ob_type->tp_compare;
        if (fcmp != NULL) {
            int c = (*fcmp)(a, b);
            c = adjust_tp_compare(c);

            Py_LeaveRecursiveCall();

            if (c == -2) {
                return NULL;
            }

            switch (op) {
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

            result = BOOL_FROM(c != 0);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (a->ob_type != b->ob_type && PyType_IsSubtype(b->ob_type, a->ob_type)) {
        f = RICHCOMPARE(b->ob_type);

        if (f != NULL) {
            result = (*f)(b, a, swapped_op[op]);

            if (result != Py_NotImplemented) {
                Py_LeaveRecursiveCall();
                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(a->ob_type);
    if (f != NULL) {
        result = (*f)(a, b, op);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();
            return result;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(b->ob_type);
    if (f != NULL) {
        result = (*f)(b, a, swapped_op[op]);

        if (result != Py_NotImplemented) {
            Py_LeaveRecursiveCall();
            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(a)) {
        c = (*a->ob_type->tp_compare)(a, b);
    } else if (PyInstance_Check(b)) {
        c = (*b->ob_type->tp_compare)(a, b);
    } else {
        c = try_3way_compare(a, b);
    }

    if (c >= 2) {
        if (a->ob_type == b->ob_type) {
            Py_uintptr_t aa = (Py_uintptr_t)a;
            Py_uintptr_t bb = (Py_uintptr_t)b;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (a == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (b == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(a)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(b)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)Py_TYPE(a);
                Py_uintptr_t bb = (Py_uintptr_t)Py_TYPE(b);

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(b)) {
            c = 1;
        } else {
            int s = strcmp(a->ob_type->tp_name, b->ob_type->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)Py_TYPE(a);
                Py_uintptr_t bb = (Py_uintptr_t)Py_TYPE(b);

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (op) {
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

    result = BOOL_FROM(c != 0);
    Py_INCREF(result);
    return result;
}

static PyObject *MY_RICHCOMPARE_NORECURSE(PyObject *a, PyObject *b, int op) {
    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

    // TODO: Type a-ware rich comparison would be really nice, but this is what
    // CPython does, and should be even in "richcomparisons.h" as the first
    // thing, so it's even cheaper.
    if (PyInt_CheckExact(a) && PyInt_CheckExact(b)) {
        long aa, bb;
#ifdef __NUITKA_NO_ASSERT__
        bool res;
#else
        bool res = false;
#endif

        aa = PyInt_AS_LONG(a);
        bb = PyInt_AS_LONG(b);

        switch (op) {
        case Py_LT:
            res = aa < bb;
            break;
        case Py_LE:
            res = aa <= bb;
            break;
        case Py_EQ:
            res = aa == bb;
            break;
        case Py_NE:
            res = aa != bb;
            break;
        case Py_GT:
            res = aa > bb;
            break;
        case Py_GE:
            res = aa >= bb;
            break;
        default:
            assert(false);
        }

        PyObject *result = BOOL_FROM(res);
        Py_INCREF(result);
        return result;
    }

    PyObject *result;

    // If the types are equal, we may get away immediately.
    if (a->ob_type == b->ob_type && !PyInstance_Check(a)) {
        richcmpfunc frich = RICHCOMPARE(a->ob_type);

        if (frich != NULL) {
            result = (*frich)(a, b, op);

            if (result != Py_NotImplemented) {
                return result;
            }

            Py_DECREF(result);
        }

        // No rich comparison, but maybe compare works.
        cmpfunc fcmp = a->ob_type->tp_compare;
        if (fcmp != NULL) {
            int c = (*fcmp)(a, b);
            c = adjust_tp_compare(c);

            if (c == -2) {
                return NULL;
            }

            switch (op) {
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

            result = BOOL_FROM(c != 0);
            Py_INCREF(result);
            return result;
        }
    }

    // Fast path was not successful or not taken
    richcmpfunc f;

    if (a->ob_type != b->ob_type && PyType_IsSubtype(b->ob_type, a->ob_type)) {
        f = RICHCOMPARE(b->ob_type);

        if (f != NULL) {
            result = (*f)(b, a, swapped_op[op]);

            if (result != Py_NotImplemented) {
                return result;
            }

            Py_DECREF(result);
        }
    }

    f = RICHCOMPARE(a->ob_type);
    if (f != NULL) {
        result = (*f)(a, b, op);

        if (result != Py_NotImplemented) {
            return result;
        }

        Py_DECREF(result);
    }

    f = RICHCOMPARE(b->ob_type);
    if (f != NULL) {
        result = (*f)(b, a, swapped_op[op]);

        if (result != Py_NotImplemented) {
            return result;
        }

        Py_DECREF(result);
    }

    int c;

    if (PyInstance_Check(a)) {
        c = (*a->ob_type->tp_compare)(a, b);
    } else if (PyInstance_Check(b)) {
        c = (*b->ob_type->tp_compare)(a, b);
    } else {
        c = try_3way_compare(a, b);
    }

    if (c >= 2) {
        if (a->ob_type == b->ob_type) {
            Py_uintptr_t aa = (Py_uintptr_t)a;
            Py_uintptr_t bb = (Py_uintptr_t)b;

            c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
        } else if (a == Py_None) {
            // None is smaller than everything else
            c = -1;
        } else if (b == Py_None) {
            // None is smaller than everything else
            c = 1;
        } else if (PyNumber_Check(a)) {
            // different type: compare type names but numbers are smaller than
            // others.
            if (PyNumber_Check(b)) {
                // Both numbers, need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)Py_TYPE(a);
                Py_uintptr_t bb = (Py_uintptr_t)Py_TYPE(b);

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            } else {
                c = -1;
            }
        } else if (PyNumber_Check(b)) {
            c = 1;
        } else {
            int s = strcmp(a->ob_type->tp_name, b->ob_type->tp_name);

            if (s < 0) {
                c = -1;
            } else if (s > 0) {
                c = 1;
            } else {
                // Same type name need to make a decision based on types.
                Py_uintptr_t aa = (Py_uintptr_t)Py_TYPE(a);
                Py_uintptr_t bb = (Py_uintptr_t)Py_TYPE(b);

                c = (aa < bb) ? -1 : (aa > bb) ? 1 : 0;
            }
        }
    }

    if (unlikely(c <= -2)) {
        return NULL;
    }

    switch (op) {
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

    result = BOOL_FROM(c != 0);
    Py_INCREF(result);
    return result;
}

#else

// Table for operation names as strings.
static char const *op_strings[] = {"<", "<=", "==", "!=", ">", ">="};

PyObject *MY_RICHCOMPARE(PyObject *a, PyObject *b, int op) {
    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

    if (unlikely(Py_EnterRecursiveCall((char *)" in comparison"))) {
        return NULL;
    }

    bool checked_reverse_op = false;
    PyObject *result = NULL;
    richcmpfunc f;

    if (a->ob_type != b->ob_type && PyType_IsSubtype(b->ob_type, a->ob_type)) {
        f = b->ob_type->tp_richcompare;
        if (f != NULL) {
            checked_reverse_op = true;

            result = (*f)(b, a, swapped_op[op]);

            if (unlikely(result == NULL)) {
                Py_LeaveRecursiveCall();
                return NULL;
            }

            if (result == Py_NotImplemented) {
                Py_DECREF(result);
                result = NULL;
            }
        }
    }

    if (result == NULL) {
        f = a->ob_type->tp_richcompare;

        if (f != NULL) {
            result = (*f)(a, b, op);

            if (unlikely(result == NULL)) {
                Py_LeaveRecursiveCall();
                return NULL;
            }

            if (result == Py_NotImplemented) {
                Py_DECREF(result);
                result = NULL;
            }
        }
    }

    if (result == NULL && checked_reverse_op == false) {
        f = b->ob_type->tp_richcompare;

        if (f != NULL) {
            result = (*f)(b, a, swapped_op[op]);

            if (unlikely(result == NULL)) {
                Py_LeaveRecursiveCall();
                return NULL;
            }

            if (result == Py_NotImplemented) {
                Py_DECREF(result);
                result = NULL;
            }
        }
    }

    Py_LeaveRecursiveCall();

    if (result != NULL) {
        return result;
    }

    // If it is not implemented, do identify checks as "==" and "!=" and
    // otherwise give an error
    if (op == Py_EQ) {
        result = BOOL_FROM(a == b);
        Py_INCREF(result);
        return result;
    } else if (op == Py_NE) {
        result = BOOL_FROM(a != b);
        Py_INCREF(result);
        return result;
    } else {
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() %s %s()", a->ob_type->tp_name, op_strings[op],
                     b->ob_type->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'%s' not supported between instances of '%s' and '%s'", op_strings[op],
                     a->ob_type->tp_name, b->ob_type->tp_name);
#endif
        return NULL;
    }
}

PyObject *MY_RICHCOMPARE_NORECURSE(PyObject *a, PyObject *b, int op) {
    CHECK_OBJECT(a);
    CHECK_OBJECT(b);

    bool checked_reverse_op = false;
    PyObject *result = NULL;
    richcmpfunc f;

    if (a->ob_type != b->ob_type && PyType_IsSubtype(b->ob_type, a->ob_type)) {
        f = b->ob_type->tp_richcompare;
        if (f != NULL) {
            checked_reverse_op = true;

            result = (*f)(b, a, swapped_op[op]);

            if (unlikely(result == NULL)) {
                return NULL;
            }

            if (result == Py_NotImplemented) {
                Py_DECREF(result);
                result = NULL;
            }
        }
    }

    if (result == NULL) {
        f = a->ob_type->tp_richcompare;

        if (f != NULL) {
            result = (*f)(a, b, op);

            if (unlikely(result == NULL)) {
                return NULL;
            }

            if (result == Py_NotImplemented) {
                Py_DECREF(result);
                result = NULL;
            }
        }
    }

    if (result == NULL && checked_reverse_op == false) {
        f = b->ob_type->tp_richcompare;

        if (f != NULL) {
            result = (*f)(b, a, swapped_op[op]);

            if (unlikely(result == NULL)) {
                return NULL;
            }

            if (result == Py_NotImplemented) {
                Py_DECREF(result);
                result = NULL;
            }
        }
    }

    if (result != NULL) {
        return result;
    }

    // If it is not implemented, do identify checks as "==" and "!=" and
    // otherwise give an error
    if (op == Py_EQ) {
        result = BOOL_FROM(a == b);
        Py_INCREF(result);
        return result;
    } else if (op == Py_NE) {
        result = BOOL_FROM(a != b);
        Py_INCREF(result);
        return result;
    } else {
#if PYTHON_VERSION < 360
        PyErr_Format(PyExc_TypeError, "unorderable types: %s() %s %s()", a->ob_type->tp_name, op_strings[op],
                     b->ob_type->tp_name);
#else
        PyErr_Format(PyExc_TypeError, "'%s' not supported between instances of '%s' and '%s'", op_strings[op],
                     a->ob_type->tp_name, b->ob_type->tp_name);
#endif

        return NULL;
    }
}

#endif

static inline bool IS_SANE_TYPE(PyTypeObject *type) {
    return
#if PYTHON_VERSION < 300
        type == &PyString_Type || type == &PyInt_Type ||
#endif
        type == &PyLong_Type || type == &PyList_Type || type == &PyTuple_Type;
}

#if PYTHON_VERSION < 300
PyObject *RICH_COMPARE_LT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_LT);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_LTE_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_LE);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_EQ_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_EQ);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_NOTEQ_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        Py_INCREF(Py_False);
        return Py_False;
    }

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_NE);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_GT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_GT);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_GTE_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    return MY_RICHCOMPARE(operand1, operand2, Py_GE);
}

PyObject *RICH_COMPARE_LT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand2));

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_LT);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_LTE_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand2));

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_LE);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_EQ_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand2));

    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_EQ);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_LTE_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    PyObject *result = BOOL_FROM(aa <= bb);
    Py_INCREF(result);
    return result;
}

PyObject *RICH_COMPARE_EQ_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    PyObject *result = BOOL_FROM(aa == bb);
    Py_INCREF(result);
    return result;
}

PyObject *RICH_COMPARE_NOTEQ_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    PyObject *result = BOOL_FROM(aa != bb);
    Py_INCREF(result);
    return result;
}

PyObject *RICH_COMPARE_GT_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    PyObject *result = BOOL_FROM(aa > bb);
    Py_INCREF(result);
    return result;
}

PyObject *RICH_COMPARE_GTE_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    PyObject *result = BOOL_FROM(aa >= bb);
    Py_INCREF(result);
    return result;
}

#endif

PyObject *RICH_COMPARE_LT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_LT);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_LTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    PyObject *result = MY_RICHCOMPARE(operand1, operand2, Py_LE);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    return result;
}

PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    return MY_RICHCOMPARE(operand1, operand2, Py_EQ);
}

PyObject *RICH_COMPARE_EQ_OBJECT_OBJECT_NORECURSE(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    return MY_RICHCOMPARE_NORECURSE(operand1, operand2, Py_EQ);
}

PyObject *RICH_COMPARE_NOTEQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        Py_INCREF(Py_False);
        return Py_False;
    }

    return MY_RICHCOMPARE(operand1, operand2, Py_NE);
}

PyObject *RICH_COMPARE_GT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return MY_RICHCOMPARE(operand1, operand2, Py_GT);
}

PyObject *RICH_COMPARE_GTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    return MY_RICHCOMPARE(operand1, operand2, Py_GE);
}

// C bool result type variants
static int MY_RICHCOMPARE_BOOL(PyObject *a, PyObject *b, int op) {
    PyObject *rich_result = MY_RICHCOMPARE(a, b, op);

    if (unlikely(rich_result == NULL)) {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if (rich_result == Py_True) {
        result = 1;
    } else if (rich_result == Py_False || rich_result == Py_None) {
        result = 0;
    } else {
        result = CHECK_IF_TRUE(rich_result);
    }

    Py_DECREF(rich_result);

    return result;
}

static int MY_RICHCOMPARE_BOOL_NORECURSE(PyObject *a, PyObject *b, int op) {
    PyObject *rich_result = MY_RICHCOMPARE_NORECURSE(a, b, op);

    if (unlikely(rich_result == NULL)) {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if (rich_result == Py_True) {
        result = 1;
    } else if (rich_result == Py_False || rich_result == Py_None) {
        result = 0;
    } else {
        result = CHECK_IF_TRUE(rich_result);
    }

    Py_DECREF(rich_result);

    return result;
}

#if PYTHON_VERSION < 300

int RICH_COMPARE_BOOL_LT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_LT);
}

int RICH_COMPARE_BOOL_LTE_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_LE);
}

int RICH_COMPARE_BOOL_EQ_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_EQ);
}

int RICH_COMPARE_BOOL_EQ_INT_OBJECT_NORECURSE(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL_NORECURSE(operand1, operand2, Py_EQ);
}

int RICH_COMPARE_BOOL_NOTEQ_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 0;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_NE);
}

int RICH_COMPARE_BOOL_GT_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_GT);
}

int RICH_COMPARE_BOOL_GTE_INT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_GE);
}

int RICH_COMPARE_BOOL_LT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_LT);
}

int RICH_COMPARE_BOOL_LTE_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_LE);
}

int RICH_COMPARE_BOOL_EQ_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_EQ);
}

int RICH_COMPARE_BOOL_EQ_OBJECT_INT_NORECURSE(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL_NORECURSE(operand1, operand2, Py_EQ);
}

int RICH_COMPARE_BOOL_NOTEQ_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 0;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_NE);
}

int RICH_COMPARE_BOOL_GT_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_GT);
}

int RICH_COMPARE_BOOL_GTE_OBJECT_INT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_GE);
}

int RICH_COMPARE_BOOL_LT_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    return aa < bb;
}

int RICH_COMPARE_BOOL_LTE_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    return aa <= bb;
}

int RICH_COMPARE_BOOL_EQ_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    return aa == bb;
}

int RICH_COMPARE_BOOL_NOTEQ_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    return aa != bb;
}

int RICH_COMPARE_BOOL_GT_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    return aa > bb;
}

int RICH_COMPARE_BOOL_GTE_INT_INT(PyObject *operand1, PyObject *operand2) {
    assert(PyInt_CheckExact(operand1));
    assert(PyInt_CheckExact(operand2));

    long aa = PyInt_AS_LONG(operand1);
    long bb = PyInt_AS_LONG(operand2);

    return aa >= bb;
}

#endif

int RICH_COMPARE_BOOL_LT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_LT);
}

int RICH_COMPARE_BOOL_LTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_LE);
}

int RICH_COMPARE_BOOL_EQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_EQ);
}

int RICH_COMPARE_BOOL_EQ_OBJECT_OBJECT_NORECURSE(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL_NORECURSE(operand1, operand2, Py_EQ);
}

int RICH_COMPARE_BOOL_NOTEQ_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        return 0;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_NE);
}

int RICH_COMPARE_BOOL_GT_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_GT);
}

int RICH_COMPARE_BOOL_GTE_OBJECT_OBJECT(PyObject *operand1, PyObject *operand2) {
    // Quick path for avoidable checks, compatible with CPython.
    if (operand1 == operand2 && IS_SANE_TYPE(Py_TYPE(operand1))) {
        return 1;
    }

    return MY_RICHCOMPARE_BOOL(operand1, operand2, Py_GE);
}
