//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// For interacting with the Python GC unexposed details

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// spell-checker: ignore PYMEM_DOMAIN,Nuitka_gc_decref,gcstate,uncollectable,sisnsn,QSBR,wrasgc
// spell-checker: ignore Nuitka_visit_decref,finalizers,wrcb,wrlist,_PyObject_GET_WEAKREFS_LISTPTR
// spell-checker: ignore objmalloc,qbsr,stoptheworld

void *(*python_obj_malloc)(void *ctx, size_t size) = NULL;
void *(*python_mem_malloc)(void *ctx, size_t size) = NULL;
void *(*python_mem_calloc)(void *ctx, size_t nelem, size_t elsize) = NULL;
#ifndef Py_GIL_DISABLED
void *(*python_mem_realloc)(void *ctx, void *ptr, size_t new_size) = NULL;
#else
void (*python_mem_free)(void *ctx, void *ptr) = NULL;
#endif

#if defined(Py_DEBUG)
void *python_obj_ctx = NULL;
void *python_mem_ctx = NULL;
#endif

void initNuitkaAllocators(void) {
    PyMemAllocatorEx allocators;

    PyMem_GetAllocator(PYMEM_DOMAIN_OBJ, &allocators);

#if defined(Py_DEBUG)
    python_obj_ctx = allocators.ctx;
#endif

    python_obj_malloc = allocators.malloc;

    PyMem_GetAllocator(PYMEM_DOMAIN_MEM, &allocators);

#if defined(Py_DEBUG)
    python_mem_ctx = allocators.ctx;
#endif

    python_mem_malloc = allocators.malloc;
    python_mem_calloc = allocators.calloc;
#ifndef Py_GIL_DISABLED
    python_mem_realloc = allocators.realloc;
#else
    python_mem_free = allocators.free;
#endif
}

#if PYTHON_VERSION >= 0x3b0

typedef struct _gc_runtime_state GCState;

#if PYTHON_VERSION < 0x3d0

#define AS_GC(o) ((PyGC_Head *)(((char *)(o)) - sizeof(PyGC_Head)))
#define FROM_GC(g) ((PyObject *)(((char *)(g)) + sizeof(PyGC_Head)))

static inline bool Nuitka_gc_is_collecting(PyGC_Head *g) { return (g->_gc_prev & _PyGC_PREV_MASK_COLLECTING) != 0; }

static inline void Nuitka_gc_clear_collecting(PyGC_Head *g) { g->_gc_prev &= ~_PyGC_PREV_MASK_COLLECTING; }

static inline Py_ssize_t Nuitka_gc_get_refs(PyGC_Head *g) { return (Py_ssize_t)(g->_gc_prev >> _PyGC_PREV_SHIFT); }

static inline void Nuitka_gc_set_refs(PyGC_Head *g, Py_ssize_t refs) {
    g->_gc_prev = (g->_gc_prev & ~_PyGC_PREV_MASK) | ((uintptr_t)(refs) << _PyGC_PREV_SHIFT);
}

static inline void Nuitka_gc_reset_refs(PyGC_Head *g, Py_ssize_t refs) {
    g->_gc_prev = (g->_gc_prev & _PyGC_PREV_MASK_FINALIZED) | _PyGC_PREV_MASK_COLLECTING |
                  ((uintptr_t)(refs) << _PyGC_PREV_SHIFT);
}

static inline void Nuitka_gc_decref(PyGC_Head *g) { g->_gc_prev -= 1 << _PyGC_PREV_SHIFT; }

#define GEN_HEAD(gcstate, n) (&(gcstate)->generations[n].head)
#define GC_NEXT _PyGCHead_NEXT
#define GC_PREV _PyGCHead_PREV

static void Nuitka_invoke_gc_callback(PyThreadState *tstate, const char *phase, int generation, Py_ssize_t collected,
                                      Py_ssize_t uncollectable) {
    assert(!HAS_ERROR_OCCURRED(tstate));

    GCState *gcstate = &tstate->interp->gc;
    if (gcstate->callbacks == NULL) {
        return;
    }

    PyObject *info = NULL;

    if (PyList_GET_SIZE(gcstate->callbacks) != 0) {
        info =
            Py_BuildValue("{sisnsn}", "generation", generation, "collected", collected, "uncollectable", uncollectable);

        if (info == NULL) {
            PyErr_WriteUnraisable(NULL);
            return;
        }
    }

    for (Py_ssize_t i = 0; i < PyList_GET_SIZE(gcstate->callbacks); i++) {
        PyObject *r, *cb = PyList_GET_ITEM(gcstate->callbacks, i);
        Py_INCREF(cb);

        r = PyObject_CallFunction(cb, "sO", phase, info);

        if (r == NULL) {
            PyErr_WriteUnraisable(cb);
        } else {
            Py_DECREF(r);
        }

        Py_DECREF(cb);
    }

    Py_XDECREF(info);

    assert(!HAS_ERROR_OCCURRED(tstate));
}

static inline bool Nuitka_gc_list_is_empty(PyGC_Head *list) { return (list->_gc_next == (uintptr_t)list); }

static inline void Nuitka_gc_list_init(PyGC_Head *list) {
    list->_gc_prev = (uintptr_t)list;
    list->_gc_next = (uintptr_t)list;
}

static void Nuitka_gc_list_merge(PyGC_Head *from, PyGC_Head *to) {
    if (Nuitka_gc_list_is_empty(from) == false) {
        PyGC_Head *to_tail = GC_PREV(to);
        PyGC_Head *from_head = GC_NEXT(from);
        PyGC_Head *from_tail = GC_PREV(from);

        assert(from_head != from);
        assert(from_tail != from);

        _PyGCHead_SET_NEXT(to_tail, from_head);
        _PyGCHead_SET_PREV(from_head, to_tail);

        _PyGCHead_SET_NEXT(from_tail, to);
        _PyGCHead_SET_PREV(to, from_tail);
    }

    Nuitka_gc_list_init(from);
}

static void Nuitka_update_refs(PyGC_Head *containers) {
    for (PyGC_Head *gc = GC_NEXT(containers); gc != containers; gc = GC_NEXT(gc)) {
        Nuitka_gc_reset_refs(gc, Py_REFCNT(FROM_GC(gc)));
    }
}

static int Nuitka_visit_decref(PyObject *op, void *parent) {
    if (_PyObject_IS_GC(op)) {
        PyGC_Head *gc = AS_GC(op);

        if (Nuitka_gc_is_collecting(gc)) {
            Nuitka_gc_decref(gc);
        }
    }

    return 0;
}

static void Nuitka_subtract_refs(PyGC_Head *containers) {
    for (PyGC_Head *gc = GC_NEXT(containers); gc != containers; gc = GC_NEXT(gc)) {
        PyObject *op = FROM_GC(gc);
        traverseproc traverse = Py_TYPE(op)->tp_traverse;
        (void)traverse(op, (visitproc)Nuitka_visit_decref, op);
    }
}

#define NEXT_MASK_UNREACHABLE 1

static inline void Nuitka_gc_list_append(PyGC_Head *node, PyGC_Head *list) {
    PyGC_Head *last = (PyGC_Head *)list->_gc_prev;

    _PyGCHead_SET_PREV(node, last);
    _PyGCHead_SET_NEXT(last, node);

    _PyGCHead_SET_NEXT(node, list);
    list->_gc_prev = (uintptr_t)node;
}

static inline void Nuitka_gc_list_remove(PyGC_Head *node) {
    PyGC_Head *prev = GC_PREV(node);
    PyGC_Head *next = GC_NEXT(node);

    _PyGCHead_SET_NEXT(prev, next);
    _PyGCHead_SET_PREV(next, prev);

    node->_gc_next = 0;
}

static int Nuitka_visit_reachable(PyObject *op, PyGC_Head *reachable) {
    if (!_PyObject_IS_GC(op)) {
        return 0;
    }

    PyGC_Head *gc = AS_GC(op);
    const Py_ssize_t gc_refs = Nuitka_gc_get_refs(gc);

    if (Nuitka_gc_is_collecting(gc) == false) {
        return 0;
    }

    assert(gc->_gc_next != 0);

    if (gc->_gc_next & NEXT_MASK_UNREACHABLE) {
        PyGC_Head *prev = GC_PREV(gc);
        PyGC_Head *next = (PyGC_Head *)(gc->_gc_next & ~NEXT_MASK_UNREACHABLE);
        prev->_gc_next = gc->_gc_next;
        _PyGCHead_SET_PREV(next, prev);

        Nuitka_gc_list_append(gc, reachable);
        Nuitka_gc_set_refs(gc, 1);
    } else if (gc_refs == 0) {
        Nuitka_gc_set_refs(gc, 1);
    }

    return 0;
}

static void Nuitka_move_unreachable(PyGC_Head *young, PyGC_Head *unreachable) {
    PyGC_Head *prev = young;
    PyGC_Head *gc = GC_NEXT(young);

    while (gc != young) {
        if (Nuitka_gc_get_refs(gc)) {
            PyObject *op = FROM_GC(gc);
            traverseproc traverse = Py_TYPE(op)->tp_traverse;

            (void)traverse(op, (visitproc)Nuitka_visit_reachable, (void *)young);
            _PyGCHead_SET_PREV(gc, prev);

            Nuitka_gc_clear_collecting(gc);
            prev = gc;
        } else {
            prev->_gc_next = gc->_gc_next;

            PyGC_Head *last = GC_PREV(unreachable);
            last->_gc_next = (NEXT_MASK_UNREACHABLE | (uintptr_t)gc);
            _PyGCHead_SET_PREV(gc, last);
            gc->_gc_next = (NEXT_MASK_UNREACHABLE | (uintptr_t)unreachable);
            unreachable->_gc_prev = (uintptr_t)gc;
        }
        gc = (PyGC_Head *)prev->_gc_next;
    }

    young->_gc_prev = (uintptr_t)prev;
    unreachable->_gc_next &= ~NEXT_MASK_UNREACHABLE;
}

static inline void Nuitka_deduce_unreachable(PyGC_Head *base, PyGC_Head *unreachable) {
    Nuitka_update_refs(base);
    Nuitka_subtract_refs(base);

    Nuitka_gc_list_init(unreachable);
    Nuitka_move_unreachable(base, unreachable);
}

static void Nuitka_untrack_tuples(PyGC_Head *head) {
    PyGC_Head *gc = GC_NEXT(head);

    while (gc != head) {
        PyObject *op = FROM_GC(gc);
        PyGC_Head *next = GC_NEXT(gc);

        if (PyTuple_CheckExact(op)) {
            // TODO: API function
            _PyTuple_MaybeUntrack(op);
        }

        gc = next;
    }
}

static Py_ssize_t Nuitka_gc_list_size(PyGC_Head *list) {
    Py_ssize_t n = 0;

    for (PyGC_Head *gc = GC_NEXT(list); gc != list; gc = GC_NEXT(gc)) {
        n += 1;
    }

    return n;
}

static void Nuitka_untrack_dicts(PyGC_Head *head) {
    PyGC_Head *next, *gc = GC_NEXT(head);
    while (gc != head) {
        PyObject *op = FROM_GC(gc);
        next = GC_NEXT(gc);
        if (PyDict_CheckExact(op)) {
            // TODO: API function
            _PyDict_MaybeUntrack(op);
        }
        gc = next;
    }
}

static bool Nuitka_has_legacy_finalizer(PyObject *op) { return Py_TYPE(op)->tp_del != NULL; }

static void Nuitka_gc_list_move(PyGC_Head *node, PyGC_Head *list) {
    PyGC_Head *from_prev = GC_PREV(node);
    PyGC_Head *from_next = GC_NEXT(node);
    _PyGCHead_SET_NEXT(from_prev, from_next);
    _PyGCHead_SET_PREV(from_next, from_prev);

    PyGC_Head *to_prev = (PyGC_Head *)list->_gc_prev;
    _PyGCHead_SET_PREV(node, to_prev);
    _PyGCHead_SET_NEXT(to_prev, node);
    list->_gc_prev = (uintptr_t)node;
    _PyGCHead_SET_NEXT(node, list);
}

static void _Nuitka_move_legacy_finalizers(PyGC_Head *unreachable, PyGC_Head *finalizers) {
    PyGC_Head *next;
    for (PyGC_Head *gc = GC_NEXT(unreachable); gc != unreachable; gc = next) {
        PyObject *op = FROM_GC(gc);

        _PyObject_ASSERT(op, gc->_gc_next & NEXT_MASK_UNREACHABLE);
        gc->_gc_next &= ~NEXT_MASK_UNREACHABLE;
        next = (PyGC_Head *)gc->_gc_next;

        if (Nuitka_has_legacy_finalizer(op)) {
            Nuitka_gc_clear_collecting(gc);
            Nuitka_gc_list_move(gc, finalizers);
        }
    }
}

static int _Nuitka_visit_move(PyObject *op, PyGC_Head *to_list) {
    if (_PyObject_IS_GC(op)) {
        PyGC_Head *gc = AS_GC(op);
        if (Nuitka_gc_is_collecting(gc)) {
            Nuitka_gc_list_move(gc, to_list);
            Nuitka_gc_clear_collecting(gc);
        }
    }

    // Required for traverseproc
    return 0;
}

static void Nuitka_move_legacy_finalizer_reachable(PyGC_Head *finalizers) {
    for (PyGC_Head *gc = GC_NEXT(finalizers); gc != finalizers; gc = GC_NEXT(gc)) {
        traverseproc traverse = Py_TYPE(FROM_GC(gc))->tp_traverse;
        (void)traverse(FROM_GC(gc), (visitproc)_Nuitka_visit_move, (void *)finalizers);
    }
}

static void Nuitka_finalize_garbage(PyThreadState *tstate, PyGC_Head *collectable) {
    destructor finalize;
    PyGC_Head seen;

    Nuitka_gc_list_init(&seen);

    while (Nuitka_gc_list_is_empty(collectable) == false) {
        PyGC_Head *gc = GC_NEXT(collectable);
        PyObject *object = FROM_GC(gc);
        Nuitka_gc_list_move(gc, &seen);

        if (!_PyGCHead_FINALIZED(gc) && (finalize = Py_TYPE(object)->tp_finalize) != NULL) {
            _PyGCHead_SET_FINALIZED(gc);
            Py_INCREF(object);
            finalize(object);
            assert(!HAS_ERROR_OCCURRED(tstate));
            Py_DECREF(object);
        }
    }
    Nuitka_gc_list_merge(&seen, collectable);
}

static int Nuitka_handle_weakrefs(PyThreadState *tstate, PyGC_Head *unreachable, PyGC_Head *old) {
    PyGC_Head *gc;
    PyObject *object;
    PyWeakReference *wr;
    PyGC_Head wrcb_to_call;
    PyGC_Head *next;
    int num_freed = 0;

    Nuitka_gc_list_init(&wrcb_to_call);

    for (gc = GC_NEXT(unreachable); gc != unreachable; gc = next) {
        PyWeakReference **wrlist;

        object = FROM_GC(gc);
        next = GC_NEXT(gc);

        if (PyWeakref_Check(object)) {
            _PyWeakref_ClearRef((PyWeakReference *)object);
        }

        if (!_PyType_SUPPORTS_WEAKREFS(Py_TYPE(object)))
            continue;

        wrlist = (PyWeakReference **)_PyObject_GET_WEAKREFS_LISTPTR(object);

        for (wr = *wrlist; wr != NULL; wr = *wrlist) {
            PyGC_Head *wrasgc;

            _PyWeakref_ClearRef(wr);

            if (wr->wr_callback == NULL) {
                continue;
            }

            if (Nuitka_gc_is_collecting(AS_GC(wr))) {
                continue;
            }

            Py_INCREF(wr);

            wrasgc = AS_GC(wr);
            Nuitka_gc_list_move(wrasgc, &wrcb_to_call);
        }
    }

    while (Nuitka_gc_list_is_empty(&wrcb_to_call) == false) {
        PyObject *temp;
        PyObject *callback;

        gc = (PyGC_Head *)wrcb_to_call._gc_next;
        object = FROM_GC(gc);
        wr = (PyWeakReference *)object;
        callback = wr->wr_callback;

        temp = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, callback, (PyObject *)wr);
        if (temp == NULL)
            PyErr_WriteUnraisable(callback);
        else
            Py_DECREF(temp);

        Py_DECREF(object);
        if (wrcb_to_call._gc_next == (uintptr_t)gc) {
            Nuitka_gc_list_move(gc, old);
        } else {
            ++num_freed;
        }
    }

    return num_freed;
}

static inline void Nuitka_gc_list_clear_collecting(PyGC_Head *collectable) {
    for (PyGC_Head *gc = GC_NEXT(collectable); gc != collectable; gc = GC_NEXT(gc)) {
        Nuitka_gc_clear_collecting(gc);
    }
}

static inline void Nuitka_clear_unreachable_mask(PyGC_Head *unreachable) {
    PyGC_Head *next;

    for (PyGC_Head *gc = GC_NEXT(unreachable); gc != unreachable; gc = next) {
        gc->_gc_next &= ~NEXT_MASK_UNREACHABLE;
        next = (PyGC_Head *)gc->_gc_next;
    }
}

static inline void handle_resurrected_objects(PyGC_Head *unreachable, PyGC_Head *still_unreachable,
                                              PyGC_Head *old_generation) {
    Nuitka_gc_list_clear_collecting(unreachable);

    PyGC_Head *resurrected = unreachable;
    Nuitka_deduce_unreachable(resurrected, still_unreachable);
    Nuitka_clear_unreachable_mask(still_unreachable);

    Nuitka_gc_list_merge(resurrected, old_generation);
}

static void Nuitka_delete_garbage(PyThreadState *tstate, GCState *gcstate, PyGC_Head *collectable, PyGC_Head *old) {
    assert(!HAS_ERROR_OCCURRED(tstate));

    while (Nuitka_gc_list_is_empty(collectable) == false) {
        PyGC_Head *gc = GC_NEXT(collectable);
        PyObject *object = FROM_GC(gc);

        _PyObject_ASSERT_WITH_MSG(object, Py_REFCNT(object) > 0, "refcount is too small");

        {
            inquiry clear;
            if ((clear = Py_TYPE(object)->tp_clear) != NULL) {
                Py_INCREF(object);
                (void)clear(object);
                if (HAS_ERROR_OCCURRED(tstate)) {
                    _PyErr_WriteUnraisableMsg("in tp_clear of", (PyObject *)Py_TYPE(object));
                }
                Py_DECREF(object);
            }
        }
        if (GC_NEXT(collectable) == gc) {
            Nuitka_gc_clear_collecting(gc);
            Nuitka_gc_list_move(gc, old);
        }
    }
}

static void Nuitka_handle_legacy_finalizers(PyThreadState *tstate, GCState *gcstate, PyGC_Head *finalizers,
                                            PyGC_Head *old) {
    assert(!HAS_ERROR_OCCURRED(tstate));

    for (PyGC_Head *gc = GC_NEXT(finalizers); gc != finalizers; gc = GC_NEXT(gc)) {
        PyObject *op = FROM_GC(gc);

        if (Nuitka_has_legacy_finalizer(op)) {
            if (PyList_Append(gcstate->garbage, op) < 0) {
                CLEAR_ERROR_OCCURRED(tstate);
                break;
            }
        }
    }

    Nuitka_gc_list_merge(finalizers, old);
}

static Py_ssize_t Nuitka_gc_collect_main(PyThreadState *tstate, int generation, Py_ssize_t *n_collected,
                                         Py_ssize_t *n_uncollectable) {
    int i;
    Py_ssize_t m = 0;
    Py_ssize_t n = 0;
    PyGC_Head *young;
    PyGC_Head *old;
    PyGC_Head unreachable;
    PyGC_Head finalizers;
    PyGC_Head *gc;

    GCState *gcstate = &tstate->interp->gc;

    assert(gcstate->garbage != NULL);
    assert(!HAS_ERROR_OCCURRED(tstate));

    if (generation + 1 < NUM_GENERATIONS) {
        gcstate->generations[generation + 1].count += 1;
    }

    for (i = 0; i <= generation; i++) {
        gcstate->generations[i].count = 0;
    }

    for (i = 0; i < generation; i++) {
        Nuitka_gc_list_merge(GEN_HEAD(gcstate, i), GEN_HEAD(gcstate, generation));
    }

    young = GEN_HEAD(gcstate, generation);
    if (generation < NUM_GENERATIONS - 1) {
        old = GEN_HEAD(gcstate, generation + 1);
    } else {
        old = young;
    }

    Nuitka_deduce_unreachable(young, &unreachable);

    Nuitka_untrack_tuples(young);

    if (young != old) {
        if (generation == NUM_GENERATIONS - 2) {
            gcstate->long_lived_pending += Nuitka_gc_list_size(young);
        }

        Nuitka_gc_list_merge(young, old);
    } else {
        Nuitka_untrack_dicts(young);

        gcstate->long_lived_pending = 0;
        gcstate->long_lived_total = Nuitka_gc_list_size(young);
    }

    Nuitka_gc_list_init(&finalizers);

    _Nuitka_move_legacy_finalizers(&unreachable, &finalizers);

    Nuitka_move_legacy_finalizer_reachable(&finalizers);

    m += Nuitka_handle_weakrefs(tstate, &unreachable, old);

    Nuitka_finalize_garbage(tstate, &unreachable);

    PyGC_Head final_unreachable;
    handle_resurrected_objects(&unreachable, &final_unreachable, old);

    m += Nuitka_gc_list_size(&final_unreachable);
    Nuitka_delete_garbage(tstate, gcstate, &final_unreachable, old);

    for (gc = GC_NEXT(&finalizers); gc != &finalizers; gc = GC_NEXT(gc)) {
        n++;
    }

    Nuitka_handle_legacy_finalizers(tstate, gcstate, &finalizers, old);

    if (HAS_ERROR_OCCURRED(tstate)) {
        _PyErr_WriteUnraisableMsg("in garbage collection", NULL);
    }

    if (n_collected) {
        *n_collected = m;
    }
    if (n_uncollectable) {
        *n_uncollectable = n;
    }

    struct gc_generation_stats *stats = &gcstate->generation_stats[generation];
    stats->collections++;
    stats->collected += m;
    stats->uncollectable += n;

    assert(!HAS_ERROR_OCCURRED(tstate));
    return n + m;
}

static Py_ssize_t Nuitka_gc_collect_with_callback(PyThreadState *tstate, int generation) {
    assert(!HAS_ERROR_OCCURRED(tstate));

    Nuitka_invoke_gc_callback(tstate, "start", generation, 0, 0);
    Py_ssize_t collected, uncollectable;
    Py_ssize_t result = Nuitka_gc_collect_main(tstate, generation, &collected, &uncollectable);
    Nuitka_invoke_gc_callback(tstate, "stop", generation, collected, uncollectable);

    assert(!HAS_ERROR_OCCURRED(tstate));
    return result;
}

static Py_ssize_t Nuitka_gc_collect_generations(PyThreadState *tstate) {
    GCState *gcstate = &tstate->interp->gc;

    Py_ssize_t n = 0;

    for (int i = NUM_GENERATIONS - 1; i >= 0; i--) {
        if (gcstate->generations[i].count > gcstate->generations[i].threshold) {
            if (i == NUM_GENERATIONS - 1 && gcstate->long_lived_pending < gcstate->long_lived_total / 4)
                continue;

            n = Nuitka_gc_collect_with_callback(tstate, i);
            break;
        }
    }

    return n;
}

#else

static void Nuitka_Py_ScheduleGC(PyThreadState *tstate) {
    if (!_Py_eval_breaker_bit_is_set(tstate, _PY_GC_SCHEDULED_BIT)) {
        _Py_set_eval_breaker_bit(tstate, _PY_GC_SCHEDULED_BIT);
    }
}

#endif

// This is called during object creation and might trigger garbage collection
void Nuitka_PyObject_GC_Link(PyObject *op) {
#if PYTHON_VERSION < 0x3d0
    PyGC_Head *g = AS_GC(op);

    PyThreadState *tstate = _PyThreadState_GET();
    GCState *gcstate = &tstate->interp->gc;

    g->_gc_next = 0;
    g->_gc_prev = 0;
    gcstate->generations[0].count++;

    if (gcstate->generations[0].count > gcstate->generations[0].threshold && gcstate->enabled &&
        gcstate->generations[0].threshold && !gcstate->collecting && !HAS_ERROR_OCCURRED(tstate)) {

        gcstate->collecting = 1;
        Nuitka_gc_collect_generations(tstate);
        gcstate->collecting = 0;
    }
#else
    PyGC_Head *gc = _Py_AS_GC(op);

    // gc must be correctly aligned
    _PyObject_ASSERT(op, ((uintptr_t)gc & (sizeof(uintptr_t) - 1)) == 0);

    // TODO: Have this passed.

    PyThreadState *tstate = _PyThreadState_GET();
    GCState *gcstate = &tstate->interp->gc;

    gc->_gc_next = 0;
    gc->_gc_prev = 0;

    gcstate->generations[0].count++;

    if (gcstate->generations[0].count > gcstate->generations[0].threshold && gcstate->enabled &&
        gcstate->generations[0].threshold && !_Py_atomic_load_int_relaxed(&gcstate->collecting) &&
        !_PyErr_Occurred(tstate)) {
        Nuitka_Py_ScheduleGC(tstate);
    }
#endif
}

#endif

#ifdef Py_GIL_DISABLED

// Needs to align with CPython "objmalloc.c"
#define WORK_ITEMS_PER_CHUNK 254
struct _mem_work_item {
    uintptr_t ptr; // lowest bit tagged 1 for objects freed with PyObject_Free
    uint64_t qsbr_goal;
};

struct _mem_work_chunk {
    struct llist_node node;

    Py_ssize_t rd_idx; // index of next item to read
    Py_ssize_t wr_idx; // index of next item to write
    struct _mem_work_item array[WORK_ITEMS_PER_CHUNK];
};

// Aligns with CPython "qsbr.c"
#define QSBR_DEFERRED_LIMIT 10

static uint64_t Nuitka_qsbr_advance(struct _qsbr_shared *shared) {
    return _Py_atomic_add_uint64(&shared->wr_seq, QSBR_INCR) + QSBR_INCR;
}

static uint64_t Nuitka_qsbr_deferred_advance(struct _qsbr_thread_state *qsbr) {
    if (++qsbr->deferrals < QSBR_DEFERRED_LIMIT) {
        return _Py_qsbr_shared_current(qsbr->shared) + QSBR_INCR;
    }
    qsbr->deferrals = 0;
    return Nuitka_qsbr_advance(qsbr->shared);
}

static uint64_t _Nuitka_qsbr_poll_scan(struct _qsbr_shared *shared) {
    _Py_atomic_fence_seq_cst();

    uint64_t min_seq = _Py_atomic_load_uint64(&shared->wr_seq);
    struct _qsbr_pad *array = shared->array;
    for (Py_ssize_t i = 0, size = shared->size; i != size; i++) {
        struct _qsbr_thread_state *qsbr = &array[i].qsbr;

        uint64_t seq = _Py_atomic_load_uint64(&qsbr->seq);
        if (seq != QSBR_OFFLINE && QSBR_LT(seq, min_seq)) {
            min_seq = seq;
        }
    }

    uint64_t rd_seq = _Py_atomic_load_uint64(&shared->rd_seq);
    if (QSBR_LT(rd_seq, min_seq)) {
        (void)_Py_atomic_compare_exchange_uint64(&shared->rd_seq, &rd_seq, min_seq);
        rd_seq = min_seq;
    }

    return rd_seq;
}

static bool _Nuitka_qsbr_poll(struct _qsbr_thread_state *qsbr, uint64_t goal) {
    assert(_Py_atomic_load_int_relaxed(&_PyThreadState_GET()->state) == _Py_THREAD_ATTACHED);

    if (_Py_qbsr_goal_reached(qsbr, goal)) {
        return true;
    }

    uint64_t rd_seq = _Nuitka_qsbr_poll_scan(qsbr->shared);
    return QSBR_LEQ(goal, rd_seq);
}

static void _NuitkaMem_free_work_item(uintptr_t ptr) {
    if (ptr & 0x01) {
        PyObject_Free((char *)(ptr - 1));
    } else {
        NuitkaMem_Free((void *)ptr);
    }
}

static struct _mem_work_chunk *work_queue_first(struct llist_node *head) {
    return llist_data(head->next, struct _mem_work_chunk, node);
}

static void _Nuitka_process_queue(struct llist_node *head, struct _qsbr_thread_state *qsbr, bool keep_empty) {
    while (!llist_empty(head)) {
        struct _mem_work_chunk *buf = work_queue_first(head);

        while (buf->rd_idx < buf->wr_idx) {
            struct _mem_work_item *item = &buf->array[buf->rd_idx];
            if (!_Nuitka_qsbr_poll(qsbr, item->qsbr_goal)) {
                return;
            }

            _NuitkaMem_free_work_item(item->ptr);
            buf->rd_idx++;
        }

        assert(buf->rd_idx == buf->wr_idx);

        if (keep_empty && buf->node.next == head) {
            // Keeping the last buffer as a free-list entry.
            buf->rd_idx = buf->wr_idx = 0;
            return;
        }

        llist_remove(&buf->node);
        NuitkaMem_Free(buf);
    }
}

struct mutex_entry {
    // The time after which the unlocking thread should hand off lock ownership
    // directly to the waiting thread. Written by the waiting thread.
    PyTime_t time_to_be_fair;

    // Set to 1 if the lock was handed off. Written by the unlocking thread.
    int handed_off;
};

static const PyTime_t TIME_TO_BE_FAIR_NS = 1000 * 1000;
static const int MAX_SPIN_COUNT = 40;

static void _Nuitka_yield(void) {
#ifdef _WIN32
    SwitchToThread();
#else
    sched_yield();
#endif
}

PyLockStatus _NuitkaMutex_LockTimed(PyMutex *m) {
    uint8_t v = _Py_atomic_load_uint8_relaxed(&m->_bits);
    if ((v & _Py_LOCKED) == 0) {
        if (_Py_atomic_compare_exchange_uint8(&m->_bits, &v, v | _Py_LOCKED)) {
            return PY_LOCK_ACQUIRED;
        }
    } else {
        return PY_LOCK_FAILURE;
    }

    Py_ssize_t spin_count = 0;

    for (;;) {
        if ((v & _Py_LOCKED) == 0) {
            if (_Py_atomic_compare_exchange_uint8(&m->_bits, &v, v | _Py_LOCKED)) {
                return PY_LOCK_ACQUIRED;
            }
            continue;
        }

        if (!(v & _Py_HAS_PARKED) && spin_count < MAX_SPIN_COUNT) {
            // Spin for a bit.
            _Nuitka_yield();

            spin_count++;
            continue;
        }

        return PY_LOCK_FAILURE;
    }
}

static void _Nuitka_process_interp_queue(struct _Py_mem_interp_free_queue *queue, struct _qsbr_thread_state *qsbr) {
    if (!_Py_atomic_load_int_relaxed(&queue->has_work)) {
        return;
    }

    // Try to acquire the lock, but don't block if it's already held.
    if (_NuitkaMutex_LockTimed(&queue->mutex) == PY_LOCK_ACQUIRED) {
        _Nuitka_process_queue(&queue->head, qsbr, false);

        int more_work = !llist_empty(&queue->head);
        _Py_atomic_store_int_relaxed(&queue->has_work, more_work);

        PyMutex_Unlock(&queue->mutex);
    }
}

void _NuitkaMem_ProcessDelayed(PyThreadState *tstate) {
    PyInterpreterState *interp = tstate->interp;
    _PyThreadStateImpl *tstate_impl = (_PyThreadStateImpl *)tstate;

    // Release thread-local queue
    _Nuitka_process_queue(&tstate_impl->mem_free_queue, tstate_impl->qsbr, true);

    // Release interpreter queue
    _Nuitka_process_interp_queue(&interp->mem_free_queue, tstate_impl->qsbr);
}

static void _NuitkaMem_FreeDelayed2(uintptr_t ptr) {
    // Free immediately if possible.
    if (_PyRuntime.stoptheworld.world_stopped) {
        _NuitkaMem_free_work_item(ptr);
        return;
    }

    // Allocate an entry for later processing.
    _PyThreadStateImpl *tstate = (_PyThreadStateImpl *)_PyThreadState_GET();
    struct llist_node *head = &tstate->mem_free_queue;

    struct _mem_work_chunk *buf = NULL;
    if (!llist_empty(head)) {
        // Try to reuse the last buffer
        buf = llist_data(head->prev, struct _mem_work_chunk, node);
        if (buf->wr_idx == WORK_ITEMS_PER_CHUNK) {
            // already full
            buf = NULL;
        }
    }

    if (buf == NULL) {
        buf = NuitkaMem_Calloc(1, sizeof(*buf));
    }

    assert(buf != NULL && buf->wr_idx < WORK_ITEMS_PER_CHUNK);
    uint64_t seq = Nuitka_qsbr_deferred_advance(tstate->qsbr);
    buf->array[buf->wr_idx].ptr = ptr;
    buf->array[buf->wr_idx].qsbr_goal = seq;
    buf->wr_idx++;

    if (buf->wr_idx == WORK_ITEMS_PER_CHUNK) {
        _NuitkaMem_ProcessDelayed((PyThreadState *)tstate);
    }
}

void NuitkaMem_FreeDelayed(void *ptr) {
    assert(!((uintptr_t)ptr & 0x01));
    _NuitkaMem_FreeDelayed2((uintptr_t)ptr);
}

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
