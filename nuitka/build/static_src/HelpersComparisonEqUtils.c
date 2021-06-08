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
/** For making rich comparisons work.
 *
 * Helpers that implement the details of comparisons for both Python2 and
 * Python3 individually, mostly because of the many changes.
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if PYTHON_VERSION < 0x300

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

static inline int adjust_tp_compare(int c) {
    if (ERROR_OCCURRED()) {
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

#endif

static inline bool IS_SANE_TYPE(PyTypeObject *type) {
    return
#if PYTHON_VERSION < 0x300
        type == &PyString_Type || type == &PyInt_Type ||
#endif
        type == &PyLong_Type || type == &PyList_Type || type == &PyTuple_Type;
}
