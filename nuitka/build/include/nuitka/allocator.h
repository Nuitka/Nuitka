//     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_ALLOCATOR_H__
#define __NUITKA_ALLOCATOR_H__

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// For Python2.6, these assertions cannot be done easily, just disable them with dummy code.
#if PYTHON_VERSION < 0x270 && !defined(__NUITKA_NO_ASSERT__)
#define _PyObject_GC_IS_TRACKED(obj) (1)
#endif

#if PYTHON_VERSION >= 0x380
// Need to make Py_DECREF a macro again that doesn't call an API
static inline void _Nuitka_Py_DECREF(PyObject *ob) {
    assert(ob != NULL && ob->ob_refcnt >= 0);

    // Non-limited C API and limited C API for Python 3.9 and older access
    // directly PyObject.ob_refcnt.
#ifdef Py_REF_DEBUG
    _Py_RefTotal--;
#endif
    if (--ob->ob_refcnt == 0) {
        destructor dealloc = Py_TYPE(ob)->tp_dealloc;
#ifdef Py_TRACE_REFS
        _Py_ForgetReference(ob);
#endif
        (*dealloc)(ob);
    }
}

#undef Py_DECREF
#define Py_DECREF(ob) _Nuitka_Py_DECREF((PyObject *)(ob))

// Need to make Py_XDECREF a macro again that doesn't call an API
static inline void _Nuitka_Py_XDECREF(PyObject *ob) {
    if (ob != NULL) {
        assert(ob->ob_refcnt >= 0);

        // Non-limited C API and limited C API for Python 3.9 and older access
        // directly PyObject.ob_refcnt.
#ifdef Py_REF_DEBUG
        _Py_RefTotal--;
#endif
        if (--ob->ob_refcnt == 0) {
            destructor dealloc = Py_TYPE(ob)->tp_dealloc;
#ifdef Py_TRACE_REFS
            _Py_ForgetReference(ob);
#endif
            (*dealloc)(ob);
        }
    }
}

#undef Py_XDECREF
#define Py_XDECREF(ob) _Nuitka_Py_XDECREF((PyObject *)(ob))

// Need to make Py_XDECREF a macro again that uses our Py_DECREF
#undef Py_CLEAR
#define Py_CLEAR(op)                                                                                                   \
    do {                                                                                                               \
        PyObject *_py_tmp = (PyObject *)(op);                                                                          \
        if (_py_tmp != NULL) {                                                                                         \
            (op) = NULL;                                                                                               \
            Py_DECREF(_py_tmp);                                                                                        \
        }                                                                                                              \
    } while (0)

#endif

// Macro introduced with Python3.9 or higher, make it generally available.
#ifndef Py_SET_TYPE
static inline void _Py_SET_TYPE(PyObject *ob, PyTypeObject *type) { ob->ob_type = type; }
#define Py_SET_TYPE(ob, type) _Py_SET_TYPE((PyObject *)(ob), type)
#endif

// After Python 3.9 this was moved into the DLL potentially, making
// it expensive to call.
#if PYTHON_VERSION >= 0x390
static void Nuitka_Py_NewReference(PyObject *op) {
#ifdef Py_REF_DEBUG
    _Py_RefTotal++;
#endif
    Py_SET_REFCNT(op, 1);
}
#else
#define Nuitka_Py_NewReference(op) _Py_NewReference(op)
#endif

static inline int Nuitka_PyType_HasFeature(PyTypeObject *type, unsigned long feature) {
    return ((type->tp_flags & feature) != 0);
}

#if PYTHON_VERSION >= 0x3b0

static inline size_t Nuitka_PyType_PreHeaderSize(PyTypeObject *tp) {
    return _PyType_IS_GC(tp) * sizeof(PyGC_Head) +
           Nuitka_PyType_HasFeature(tp, Py_TPFLAGS_MANAGED_DICT) * 2 * sizeof(PyObject *);
}

extern void Nuitka_PyObject_GC_Link(PyObject *op);

static PyObject *Nuitka_PyType_AllocNoTrackVar(PyTypeObject *type, Py_ssize_t nitems) {
    // There is always a sentinel now, therefore add one
    const size_t size = _PyObject_VAR_SIZE(type, nitems + 1);

    // TODO: This ought to be static for all our types, so remove it as a call.
    const size_t pre_size = Nuitka_PyType_PreHeaderSize(type);
    assert(pre_size == sizeof(PyGC_Head));

    char *alloc = (char *)PyObject_Malloc(size + pre_size);
    assert(alloc);
    PyObject *obj = (PyObject *)(alloc + pre_size);

    assert(pre_size);
    if (pre_size) {
        ((PyObject **)alloc)[0] = NULL;
        ((PyObject **)alloc)[1] = NULL;

        Nuitka_PyObject_GC_Link(obj);
    }

    // We might be able to avoid this, but it's unclear what e.g. the sentinel
    // is supposed to be.
    memset(obj, 0, size);

    // This is the "var" branch, we already know we are variable size here.
    assert(type->tp_itemsize != 0);
    Py_SET_SIZE((PyVarObject *)obj, nitems);

    // Initialize the object references.
    Py_SET_TYPE(obj, type);
    if (Nuitka_PyType_HasFeature(type, Py_TPFLAGS_HEAPTYPE)) {
        Py_INCREF(type);
    }

    Nuitka_Py_NewReference(obj);

    return obj;
}

static PyObject *Nuitka_PyType_AllocNoTrack(PyTypeObject *type) {
    // TODO: This ought to be static for all our types, so remove it as a call.
    const size_t pre_size = Nuitka_PyType_PreHeaderSize(type);

    char *alloc = (char *)PyObject_Malloc(_PyObject_SIZE(type) + pre_size);
    assert(alloc);
    PyObject *obj = (PyObject *)(alloc + pre_size);

    assert(pre_size);
    ((PyObject **)alloc)[0] = NULL;
    ((PyObject **)alloc)[1] = NULL;

    Nuitka_PyObject_GC_Link(obj);

    // Initialize the object references.
    Py_SET_TYPE(obj, type);

    if (Nuitka_PyType_HasFeature(type, Py_TPFLAGS_HEAPTYPE)) {
        Py_INCREF(type);
    }

    Nuitka_Py_NewReference(obj);

    return obj;
}
#endif

NUITKA_MAY_BE_UNUSED static void *Nuitka_GC_NewVar(PyTypeObject *type, Py_ssize_t nitems) {
    assert(nitems >= 0);

#if PYTHON_VERSION < 0x3b0
    size_t size = _PyObject_VAR_SIZE(type, nitems);
    PyVarObject *op = (PyVarObject *)_PyObject_GC_Malloc(size);
    assert(op != NULL);

    Py_SIZE(op) = nitems;
    Py_SET_TYPE(op, type);

#if PYTHON_VERSION >= 0x380
    // TODO: Might have two variants, or more sure this is also false for all of our types,
    // we are just wasting time for compiled times here.
    if (Nuitka_PyType_HasFeature(type, Py_TPFLAGS_HEAPTYPE)) {
        Py_INCREF(type);
    }
#endif

    Nuitka_Py_NewReference((PyObject *)op);

    return op;
#else
    // TODO: We ought to inline this probably too, no point as a separate function.
    PyObject *op = Nuitka_PyType_AllocNoTrackVar(type, nitems);
#endif
    assert(Py_SIZE(op) == nitems);
    return op;
}

NUITKA_MAY_BE_UNUSED static void *Nuitka_GC_New(PyTypeObject *type) {
#if PYTHON_VERSION < 0x3b0
    size_t size = _PyObject_SIZE(type);

    PyVarObject *op = (PyVarObject *)_PyObject_GC_Malloc(size);
    assert(op != NULL);

    Py_SET_TYPE(op, type);

#if PYTHON_VERSION >= 0x380
    // TODO: Might have two variants, or more sure this is also false for all of our types,
    // we are just wasting time for compiled times here.
    if (Nuitka_PyType_HasFeature(type, Py_TPFLAGS_HEAPTYPE)) {
        Py_INCREF(type);
    }
#endif

    Nuitka_Py_NewReference((PyObject *)op);
#else
    // TODO: We ought to inline this probably too, no point as a separate function.
    PyObject *op = Nuitka_PyType_AllocNoTrack(type);
#endif
    return op;
}

#endif
