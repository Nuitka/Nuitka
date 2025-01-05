//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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

// The full API is available for Python 3.5 only
#if PYTHON_VERSION >= 0x350 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_ALLOCATORS)
extern void *(*python_obj_malloc)(void *ctx, size_t size);
extern void *(*python_mem_malloc)(void *ctx, size_t size);
extern void *(*python_mem_calloc)(void *ctx, size_t nelem, size_t elsize);
#ifndef Py_GIL_DISABLED
extern void *(*python_mem_realloc)(void *ctx, void *ptr, size_t new_size);
#else
extern void (*python_mem_free)(void *ctx, void *ptr);
#endif

#if defined(Py_DEBUG)
extern void *python_obj_ctx;
extern void *python_mem_ctx;
#else
#define python_obj_ctx (NULL)
#define python_mem_ctx (NULL)
#endif

extern void initNuitkaAllocators(void);

// Our version of "PyObject_Malloc".
NUITKA_MAY_BE_UNUSED static void *NuitkaObject_Malloc(size_t size) { return python_obj_malloc(python_obj_ctx, size); }

// Our version of "PyMem_Malloc".
NUITKA_MAY_BE_UNUSED static void *NuitkaMem_Malloc(size_t size) { return python_mem_malloc(python_mem_ctx, size); }

// Our version of "PyMem_Calloc".
NUITKA_MAY_BE_UNUSED static void *NuitkaMem_Calloc(size_t nelem, size_t elsize) {
    return python_mem_calloc(python_mem_ctx, nelem, elsize);
}

#ifndef Py_GIL_DISABLED
// Our version of "PyMem_Realloc".
NUITKA_MAY_BE_UNUSED static void *NuitkaMem_Realloc(void *ptr, size_t new_size) {
    return python_mem_realloc(python_mem_ctx, ptr, new_size);
}
#else
NUITKA_MAY_BE_UNUSED static void NuitkaMem_Free(void *ptr) { python_mem_free(python_mem_ctx, ptr); }
#endif

#else
#define NuitkaObject_Malloc(size) PyObject_MALLOC(size)
#define NuitkaMem_Malloc(size) PyMem_MALLOC(size)
#define NuitkaMem_Calloc(elem, elsize) PyMem_Calloc(elem, elsize)
#ifndef Py_GIL_DISABLED
#if defined(_WIN32)
// On Windows, mixing different runtime DLLs can cause issues at
// release, so we need to go through the API to get the proper
// DLL runtime.
#define NuitkaMem_Realloc(ptr, new_size) PyMem_Realloc(ptr, new_size)
#else
#define NuitkaMem_Realloc(ptr, new_size) PyMem_REALLOC(ptr, new_size)
#endif
#else
#define NuitkaMem_Free(ptr) PyMem_Free(ptr)
#endif
#endif

#if PYTHON_VERSION >= 0x380 && PYTHON_VERSION < 0x3c0
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

#elif PYTHON_VERSION >= 0x3c0 && defined(_WIN32) && !defined(Py_DEBUG) && !defined(Py_TRACE_REFS) &&                   \
    !defined(Py_GIL_DISABLED) && !defined(_NUITKA_EXPERIMENTAL_DISABLE_PY_DECREF_OVERRIDE)

#undef Py_DECREF
#define Py_DECREF(arg)                                                                                                 \
    do {                                                                                                               \
        PyObject *op = _PyObject_CAST(arg);                                                                            \
        if (_Py_IsImmortal(op)) {                                                                                      \
            break;                                                                                                     \
        }                                                                                                              \
        _Py_DECREF_STAT_INC();                                                                                         \
        if (--op->ob_refcnt == 0) {                                                                                    \
            destructor dealloc = Py_TYPE(op)->tp_dealloc;                                                              \
            (*dealloc)(op);                                                                                            \
        }                                                                                                              \
    } while (0)

#undef Py_XDECREF
#define Py_XDECREF(arg)                                                                                                \
    do {                                                                                                               \
        PyObject *xop = _PyObject_CAST(arg);                                                                           \
        if (xop != NULL) {                                                                                             \
            Py_DECREF(xop);                                                                                            \
        }                                                                                                              \
    } while (0)

#undef Py_IS_TYPE
#define Py_IS_TYPE(ob, type) (_PyObject_CAST(ob)->ob_type == (type))

#undef _Py_DECREF_SPECIALIZED
#define _Py_DECREF_SPECIALIZED(arg, dealloc)                                                                           \
    do {                                                                                                               \
        PyObject *op = _PyObject_CAST(arg);                                                                            \
        if (_Py_IsImmortal(op)) {                                                                                      \
            break;                                                                                                     \
        }                                                                                                              \
        _Py_DECREF_STAT_INC();                                                                                         \
        if (--op->ob_refcnt == 0) {                                                                                    \
            destructor d = (destructor)(dealloc);                                                                      \
            d(op);                                                                                                     \
        }                                                                                                              \
    } while (0)
#endif

// For Python3.12, avoid reference management if value is known to be immortal.
#if PYTHON_VERSION < 0x3c0
#define Py_INCREF_IMMORTAL(value) Py_INCREF(value)
#define Py_DECREF_IMMORTAL(value) Py_DECREF(value)
#elif defined(_NUITKA_DEBUG_DEBUG_IMMORTAL)
#define Py_INCREF_IMMORTAL(value) assert(Py_REFCNT(value) == _Py_IMMORTAL_REFCNT)
#define Py_DECREF_IMMORTAL(value) assert(Py_REFCNT(value) == _Py_IMMORTAL_REFCNT)
#else
#define Py_INCREF_IMMORTAL(value)
#define Py_DECREF_IMMORTAL(value)
#endif

// Macro introduced with Python3.9 or higher, make it generally available.
#ifndef Py_SET_TYPE
static inline void _Py_SET_TYPE(PyObject *ob, PyTypeObject *type) { ob->ob_type = type; }
#define Py_SET_TYPE(ob, type) _Py_SET_TYPE((PyObject *)(ob), type)
#endif

// After Python 3.9 this was moved into the DLL potentially, making
// it expensive to call.
#if PYTHON_VERSION >= 0x390
static inline void Nuitka_Py_NewReferenceNoTotal(PyObject *op) { Py_SET_REFCNT(op, 1); }
static inline void Nuitka_Py_NewReference(PyObject *op) {
#ifdef Py_REF_DEBUG
#if PYTHON_VERSION < 0x3c0
    _Py_RefTotal++;
#else
    // Refcounts are now in the interpreter state, spell-checker: ignore reftotal
    _PyInterpreterState_GET()->object_state.reftotal++;
#endif
#endif
#if !defined(Py_GIL_DISABLED)
    op->ob_refcnt = 1;
#else
    op->ob_tid = _Py_ThreadId();
    op->_padding = 0;
    op->ob_mutex = (PyMutex){0};
    op->ob_gc_bits = 0;
    op->ob_ref_local = 1;
    op->ob_ref_shared = 0;
#endif
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

    char *alloc = (char *)NuitkaObject_Malloc(size + pre_size);
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

    char *alloc = (char *)NuitkaObject_Malloc(_PyObject_SIZE(type) + pre_size);
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

static bool inline Nuitka_GC_IS_TRACKED_X(PyObject *object) {
    return object == NULL || _PyObject_GC_IS_TRACKED(object);
}

// To allow us marking some of our own values as immortal.
#if PYTHON_VERSION >= 0x3c0
static void inline Py_SET_REFCNT_IMMORTAL(PyObject *object) {
    assert(object != NULL);

    // Normally done only with 3.13, but it makes sense to do this.
    if (_PyObject_IS_GC(object) && _PyObject_GC_IS_TRACKED(object)) {
        Nuitka_GC_UnTrack(object);
    }

#ifdef Py_GIL_DISABLED
    object->ob_tid = _Py_UNOWNED_TID;
    object->ob_ref_local = _Py_IMMORTAL_REFCNT_LOCAL;
    object->ob_ref_shared = 0;
#else
    object->ob_refcnt = _Py_IMMORTAL_REFCNT;
#endif
}
#else
#define Py_SET_REFCNT_IMMORTAL(object)
#endif

// Have these defines from newer Python for all Python versions available
#ifndef _Py_CAST
#define _Py_CAST(type, expr) ((type)(expr))
#endif

#ifndef _PyObject_CAST
#define _PyObject_CAST(op) _Py_CAST(PyObject *, (op))
#endif

#ifndef Py_SETREF
#ifdef _Py_TYPEOF
#define Py_SETREF(dst, src)                                                                                            \
    do {                                                                                                               \
        _Py_TYPEOF(dst) *_tmp_dst_ptr = &(dst);                                                                        \
        _Py_TYPEOF(dst) _tmp_old_dst = (*_tmp_dst_ptr);                                                                \
        *_tmp_dst_ptr = (src);                                                                                         \
        Py_DECREF(_tmp_old_dst);                                                                                       \
    } while (0)
#else
#define Py_SETREF(dst, src)                                                                                            \
    do {                                                                                                               \
        PyObject **_tmp_dst_ptr = _Py_CAST(PyObject **, &(dst));                                                       \
        PyObject *_tmp_old_dst = (*_tmp_dst_ptr);                                                                      \
        PyObject *_tmp_src = _PyObject_CAST(src);                                                                      \
        memcpy(_tmp_dst_ptr, &_tmp_src, sizeof(PyObject *));                                                           \
        Py_DECREF(_tmp_old_dst);                                                                                       \
    } while (0)
#endif
#endif

#ifndef Py_XSETREF
/* Py_XSETREF() is a variant of Py_SETREF() that uses Py_XDECREF() instead of
 * Py_DECREF().
 */
#ifdef _Py_TYPEOF
#define Py_XSETREF(dst, src)                                                                                           \
    do {                                                                                                               \
        _Py_TYPEOF(dst) *_tmp_dst_ptr = &(dst);                                                                        \
        _Py_TYPEOF(dst) _tmp_old_dst = (*_tmp_dst_ptr);                                                                \
        *_tmp_dst_ptr = (src);                                                                                         \
        Py_XDECREF(_tmp_old_dst);                                                                                      \
    } while (0)
#else
#define Py_XSETREF(dst, src)                                                                                           \
    do {                                                                                                               \
        PyObject **_tmp_dst_ptr = _Py_CAST(PyObject **, &(dst));                                                       \
        PyObject *_tmp_old_dst = (*_tmp_dst_ptr);                                                                      \
        PyObject *_tmp_src = _PyObject_CAST(src);                                                                      \
        memcpy(_tmp_dst_ptr, &_tmp_src, sizeof(PyObject *));                                                           \
        Py_XDECREF(_tmp_old_dst);                                                                                      \
    } while (0)
#endif
#endif

#endif

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
