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
#ifndef __NUITKA_ALLOCATOR_H__
#define __NUITKA_ALLOCATOR_H__

#if PYTHON_VERSION >= 0x3b0

#include <internal/pycore_gc.h>
typedef struct _gc_runtime_state GCState;

#define AS_GC(o) ((PyGC_Head *)(((char *)(o)) - sizeof(PyGC_Head)))

static void Nuitka_PyObject_GC_Link(PyObject *op) {
    PyGC_Head *g = AS_GC(op);
    assert(((uintptr_t)g & (sizeof(uintptr_t) - 1)) == 0); // g must be correctly aligned

    PyThreadState *tstate = _PyThreadState_GET();
    GCState *gcstate = &tstate->interp->gc;
    g->_gc_next = 0;
    g->_gc_prev = 0;
    gcstate->generations[0].count++;
    if (gcstate->generations[0].count > gcstate->generations[0].threshold && gcstate->enabled &&
        gcstate->generations[0].threshold && !gcstate->collecting && !HAS_ERROR_OCCURRED(tstate)) {
        PyGC_Collect();
    }
}

static inline int _PyType_HasFeature(PyTypeObject *type, unsigned long feature) {
    return ((type->tp_flags & feature) != 0);
}

#define _PyType_IS_GC(t) _PyType_HasFeature((t), Py_TPFLAGS_HAVE_GC)

static inline size_t Nuitka_PyType_PreHeaderSize(PyTypeObject *tp) {
    return _PyType_IS_GC(tp) * sizeof(PyGC_Head) +
           _PyType_HasFeature(tp, Py_TPFLAGS_MANAGED_DICT) * 2 * sizeof(PyObject *);
}

static PyObject *Nuitka_PyType_AllocNoTrackVar(PyTypeObject *type, Py_ssize_t nitems) {
    // There is always a sentinel now, therefore add one
    const size_t size = _PyObject_VAR_SIZE(type, nitems + 1);

    // TODO: This ought to be static for all our types, so remove it.
    const size_t presize = Nuitka_PyType_PreHeaderSize(type);

    char *alloc = (char *)PyObject_Malloc(size + presize);
    assert(alloc);
    PyObject *obj = (PyObject *)(alloc + presize);

    if (presize) {
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
    Py_INCREF(type);

    _Py_NewReference(obj);

    return obj;
}
#endif

NUITKA_MAY_BE_UNUSED static void *Nuitka_GC_NewVar(PyTypeObject *type, Py_ssize_t nitems) {
    assert(nitems >= 0);

#if PYTHON_VERSION < 0x3b0
    size_t size = _PyObject_VAR_SIZE(type, nitems);
    PyVarObject *op = (PyVarObject *)_PyObject_GC_Malloc(size);
    assert(op != NULL);

    Py_TYPE(op) = type;
    Py_SIZE(op) = size;
    Py_SET_REFCNT(op, 1);

    // TODO: Above assignments might replace this actually.
    op = PyObject_INIT_VAR(op, type, nitems);

    return op;
#else
    // TODO: We ought to inline this probably too, and statically consider
    // _PyType_PreHeaderSize result, which often will be 0.
    return Nuitka_PyType_AllocNoTrackVar(type, nitems);
#endif
}

#endif
