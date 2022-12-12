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

python_initproc default_tp_init_wrapper;

#if PYTHON_VERSION < 0x300
static cmpfunc default_tp_compare;
#endif

void _initSlotCompare(void) {
    // Create a class with "__cmp__" attribute, to get a hand at the default
    // implementation of tp_compare. It's not part of the API and with shared
    // libraries it's not accessible. The name does not matter, nor does the
    // actual value used for "__cmp__".

    // Use "int" as the base class.
    PyObject *pos_args = MAKE_TUPLE1((PyObject *)&PyLong_Type);

    // Use "__cmp__" with true value, won't matter.
    // Note: Not using MAKE_DICT_EMPTY on purpose, this is called early on.
    PyObject *kw_args = PyDict_New();
#if PYTHON_VERSION < 0x0300
    PyDict_SetItem(kw_args, const_str_plain___cmp__, Py_True);
#endif
    PyDict_SetItem(kw_args, const_str_plain___init__, (PyObject *)Py_TYPE(Py_None));

    // Create the type.
    PyTypeObject *c = (PyTypeObject *)PyObject_CallFunctionObjArgs((PyObject *)&PyType_Type, const_str_plain___cmp__,
                                                                   pos_args, kw_args, NULL);
    Py_DECREF(pos_args);
    Py_DECREF(kw_args);

    CHECK_OBJECT(c);

#if PYTHON_VERSION < 0x0300
    assert(c->tp_compare);
    default_tp_compare = c->tp_compare;
#endif

    assert(c->tp_init);
    default_tp_init_wrapper = c->tp_init;

    Py_DECREF(c);
}

#if PYTHON_VERSION < 0x300

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
