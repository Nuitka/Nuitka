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
// For interacting with the Python GC unexposed details

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

typedef struct _gc_runtime_state GCState;

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
        assert(false);

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

static void Nuitka_move_legacy_finalizers(PyGC_Head *unreachable, PyGC_Head *finalizers) {
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

static int Nuitka_visit_move(PyObject *op, PyGC_Head *tolist) {
    if (_PyObject_IS_GC(op)) {
        PyGC_Head *gc = AS_GC(op);
        if (Nuitka_gc_is_collecting(gc)) {
            Nuitka_gc_list_move(gc, tolist);
            Nuitka_gc_clear_collecting(gc);
        }
    }

    // Required for traverseproc
    return 0;
}

static void Nuitka_move_legacy_finalizer_reachable(PyGC_Head *finalizers) {
    for (PyGC_Head *gc = GC_NEXT(finalizers); gc != finalizers; gc = GC_NEXT(gc)) {
        traverseproc traverse = Py_TYPE(FROM_GC(gc))->tp_traverse;
        (void)traverse(FROM_GC(gc), (visitproc)Nuitka_visit_move, (void *)finalizers);
    }
}

static void Nuitka_finalize_garbage(PyThreadState *tstate, PyGC_Head *collectable) {
    destructor finalize;
    PyGC_Head seen;

    Nuitka_gc_list_init(&seen);

    while (Nuitka_gc_list_is_empty(collectable) == false) {
        PyGC_Head *gc = GC_NEXT(collectable);
        PyObject *op = FROM_GC(gc);
        Nuitka_gc_list_move(gc, &seen);

        if (!_PyGCHead_FINALIZED(gc) && (finalize = Py_TYPE(op)->tp_finalize) != NULL) {
            _PyGCHead_SET_FINALIZED(gc);
            Py_INCREF(op);
            finalize(op);
            assert(!HAS_ERROR_OCCURRED(tstate));
            Py_DECREF(op);
        }
    }
    Nuitka_gc_list_merge(&seen, collectable);
}

static int Nuitka_handle_weakrefs(PyGC_Head *unreachable, PyGC_Head *old) {
    PyGC_Head *gc;
    PyObject *op;
    PyWeakReference *wr;
    PyGC_Head wrcb_to_call;
    PyGC_Head *next;
    int num_freed = 0;

    Nuitka_gc_list_init(&wrcb_to_call);

    for (gc = GC_NEXT(unreachable); gc != unreachable; gc = next) {
        PyWeakReference **wrlist;

        op = FROM_GC(gc);
        next = GC_NEXT(gc);

        if (PyWeakref_Check(op)) {
            _PyWeakref_ClearRef((PyWeakReference *)op);
        }

        if (!_PyType_SUPPORTS_WEAKREFS(Py_TYPE(op)))
            continue;

        wrlist = (PyWeakReference **)_PyObject_GET_WEAKREFS_LISTPTR(op);

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
        op = FROM_GC(gc);
        wr = (PyWeakReference *)op;
        callback = wr->wr_callback;

        temp = CALL_FUNCTION_WITH_SINGLE_ARG(callback, (PyObject *)wr);
        if (temp == NULL)
            PyErr_WriteUnraisable(callback);
        else
            Py_DECREF(temp);

        Py_DECREF(op);
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
        PyObject *op = FROM_GC(gc);

        _PyObject_ASSERT_WITH_MSG(op, Py_REFCNT(op) > 0, "refcount is too small");

        {
            inquiry clear;
            if ((clear = Py_TYPE(op)->tp_clear) != NULL) {
                Py_INCREF(op);
                (void)clear(op);
                if (HAS_ERROR_OCCURRED(tstate)) {
                    _PyErr_WriteUnraisableMsg("in tp_clear of", (PyObject *)Py_TYPE(op));
                }
                Py_DECREF(op);
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
                CLEAR_ERROR_OCCURRED_TSTATE(tstate);
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

    Nuitka_move_legacy_finalizers(&unreachable, &finalizers);

    Nuitka_move_legacy_finalizer_reachable(&finalizers);

    m += Nuitka_handle_weakrefs(&unreachable, old);

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

// This is called during object creation and might trigger garbage collection
void Nuitka_PyObject_GC_Link(PyObject *op) {
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
}
