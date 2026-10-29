//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* This helpers is used to work with lists.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/freelists.h"
#include "nuitka/prelude.h"
#endif

#include "nuitka/helper/long_helpers.h"

// #include "richcomparisons.h"

#ifdef Py_GIL_DISABLED
#define NUITKA_LIST_BEGIN(list) Py_BEGIN_CRITICAL_SECTION(list)
#define NUITKA_LIST_END() Py_END_CRITICAL_SECTION()
#define NUITKA_LIST_STORE_PTR(ptr, value) FT_ATOMIC_STORE_PTR_RELEASE(*(ptr), (value))
#else
#define NUITKA_LIST_BEGIN(list)
#define NUITKA_LIST_END()
#define NUITKA_LIST_STORE_PTR(ptr, value) (*(ptr) = (value))
#endif

#ifdef Py_GIL_DISABLED
typedef struct {
    Py_ssize_t allocated;
    PyObject *ob_item[];
} _PyListArray;

static _PyListArray *Nuitka_AllocateListArray(size_t capacity) {
    if (unlikely(capacity > PY_SSIZE_T_MAX / sizeof(PyObject *) - 1)) {
        return NULL;
    }

    _PyListArray *list_array = NuitkaMem_Malloc(sizeof(_PyListArray) + capacity * sizeof(PyObject *));

    if (unlikely(list_array == NULL)) {
        return NULL;
    }

    list_array->allocated = capacity;
    return list_array;
}

// spell-checker: ignore use_qsbr
static void Nuitka_FreeListArray(PyObject **items, bool use_qsbr) {
    _PyListArray *array = _Py_CONTAINER_OF(items, _PyListArray, ob_item);

    if (use_qsbr) {
        NuitkaMem_FreeDelayed(array);
    } else {
        NuitkaMem_Free(array);
    }
}

static void Nuitka_List_EnsureSharedOnResize(PyListObject *list) {
    assert(Py_REFCNT(list) == 1 || PyMutex_IsLocked(&((PyObject *)list)->ob_mutex));

    if (!_Py_IsOwnedByCurrentThread((PyObject *)list) && !_PyObject_GC_IS_SHARED(list)) {
        _PyObject_GC_SET_SHARED(list);
    }
}

#endif

#if NUITKA_LIST_HAS_FREELIST

PyObject *MAKE_LIST_EMPTY(PyThreadState *tstate, Py_ssize_t size) {
    assert(size >= 0);

#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT
    return PyList_New(size);
#else
#if PYTHON_VERSION >= 0x3e0
    PyListObject *result_list = (PyListObject *)Nuitka_PyFreeList_Pop(&Nuitka_Py_freelists_GET(tstate)->lists);

    if (result_list == NULL) {
        result_list = (PyListObject *)Nuitka_GC_New(&PyList_Type);
    } else {
        Nuitka_Py_NewReference((PyObject *)result_list);
    }
#else
    // This is the CPython name, spell-checker: ignore numfree
#if PYTHON_VERSION < 0x3d0
    PyListObject **items = tstate->interp->list.free_list;
    int *numfree = &tstate->interp->list.numfree;
#else
    struct _Py_object_freelists *freelists = _Nuitka_object_freelists_GET(tstate);
    struct _Py_list_freelist *state = &freelists->lists;
    PyListObject **items = state->items;
    int *numfree = &state->numfree;
#endif
    assert(*numfree >= 0);
    PyListObject *result_list;

    if (*numfree) {
        (*numfree) -= 1;
        result_list = items[*numfree];

        Nuitka_Py_NewReference((PyObject *)result_list);
    } else {
        result_list = (PyListObject *)Nuitka_GC_New(&PyList_Type);
    }
#endif
    assert(result_list != NULL);
    assert(PyList_CheckExact(result_list));

    // Elements are allocated separately.
    if (size > 0) {
#ifdef Py_GIL_DISABLED
        _PyListArray *list_array = Nuitka_AllocateListArray(size);

        if (unlikely(list_array == NULL)) {
            Py_DECREF(result_list);
            return PyErr_NoMemory();
        }

        memset(list_array->ob_item, 0, size * sizeof(PyObject *));
        result_list->ob_item = list_array->ob_item;
#else
        result_list->ob_item = (PyObject **)NuitkaMem_Calloc(size, sizeof(PyObject *));

        if (unlikely(result_list->ob_item == NULL)) {
            Py_DECREF(result_list);
            return PyErr_NoMemory();
        }
#endif
    } else {
        result_list->ob_item = NULL;
    }

    Py_SET_SIZE(result_list, size);
    result_list->allocated = size;

    Nuitka_GC_Track(result_list);

    return (PyObject *)result_list;
#endif
}
#endif

PyObject *LIST_COPY(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    PyObject *result;

#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION(list);
#endif

    Py_ssize_t size = PyList_GET_SIZE(list);

    result = MAKE_LIST_EMPTY(tstate, size);
    assert(result != NULL);

    PyObject **src = ((PyListObject *)list)->ob_item;
    PyObject **dest = ((PyListObject *)result)->ob_item;

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = src[i];
        Py_INCREF(item);
        NUITKA_LIST_STORE_PTR(&dest[i], item);
    }

#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION();
#endif

    return result;
}

PyObject *LIST_CONCAT(PyThreadState *tstate, PyObject *operand1, PyObject *operand2) {
    CHECK_OBJECT(operand1);
    assert(PyList_CheckExact(operand1));
    CHECK_OBJECT(operand2);
    assert(PyList_CheckExact(operand2));

    PyObject *result;

#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION2(operand1, operand2);
#endif

    Py_ssize_t size1 = Py_SIZE(operand1);
    Py_ssize_t size2 = Py_SIZE(operand2);

    assert((size_t)size1 + (size_t)size2 < PY_SSIZE_T_MAX);

    result = MAKE_LIST_EMPTY(tstate, size1 + size2);
    assert(result != NULL);

    PyObject **src = ((PyListObject *)operand1)->ob_item;
    PyObject **dest = ((PyListObject *)result)->ob_item;

    for (Py_ssize_t i = 0; i < size1; i++) {
        PyObject *value = src[i];
        Py_INCREF(value);
        NUITKA_LIST_STORE_PTR(&dest[i], value);
    }

    src = ((PyListObject *)operand2)->ob_item;
    dest = ((PyListObject *)result)->ob_item + size1;

    for (Py_ssize_t i = 0; i < size2; i++) {
        PyObject *value = src[i];
        Py_INCREF(value);
        NUITKA_LIST_STORE_PTR(&dest[i], value);
    }

#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION2();
#endif

    return result;
}

static bool _LIST_RESIZE(PyListObject *list, Py_ssize_t new_size) {
    CHECK_OBJECT(list);
    assert(new_size >= 0);

    Py_ssize_t allocated = list->allocated;

    if (allocated >= new_size && new_size >= (allocated >> 1)) {
        Py_SET_SIZE(list, new_size);

        return true;
    }

    size_t new_allocated;

    if (new_size == 0) {
        new_allocated = 0;
    } else {
        new_allocated = ((size_t)new_size + (new_size >> 3) + 6) & ~(size_t)3;
        assert(new_allocated >= (size_t)new_size);
    }

#ifdef Py_GIL_DISABLED
    Nuitka_List_EnsureSharedOnResize(list);

    _PyListArray *array = Nuitka_AllocateListArray(new_allocated);

    if (array == NULL) {
#if PYTHON_VERSION >= 0x3f0
        // Python 3.15 does not fail when shrinking an allocation.
        if (new_size < allocated) {
            Py_SET_SIZE(list, new_size);
            return true;
        }
#endif
        PyErr_NoMemory();
        return false;
    }
    PyObject **old_items = list->ob_item;
    if (list->ob_item != NULL) {
        size_t num_allocated_bytes;
        if (new_allocated < (size_t)allocated) {
            num_allocated_bytes = new_allocated * sizeof(PyObject *);
        } else {
            num_allocated_bytes = allocated * sizeof(PyObject *);
        }
        memcpy(array->ob_item, list->ob_item, num_allocated_bytes);
    }
    if (new_allocated > (size_t)allocated) {
        memset(array->ob_item + allocated, 0, sizeof(PyObject *) * (new_allocated - allocated));
    }
    _Py_atomic_store_ptr_release(&list->ob_item, &array->ob_item);
    list->allocated = new_allocated;
    Py_SET_SIZE(list, new_size);
    if (old_items != NULL) {
        Nuitka_FreeListArray(old_items, _PyObject_GC_IS_SHARED(list));
    }
#else
    size_t num_allocated_bytes = new_allocated * sizeof(PyObject *);

    // TODO: For Python3.13 No-GIL this is different code
    PyObject **items = (PyObject **)NuitkaMem_Realloc(list->ob_item, num_allocated_bytes);
    if (unlikely(items == NULL)) {
        PyErr_NoMemory();
        return false;
    }

    list->ob_item = items;
    Py_SET_SIZE(list, new_size);
    list->allocated = new_allocated;
#endif

    return true;
}

static bool _LIST_EXTEND_SELF(PyListObject *list) {
    Py_ssize_t n = Py_SIZE(list);

    if (n == 0) {
        return true;
    }

    if (n > PY_SSIZE_T_MAX / 2) {
        PyErr_NoMemory();
        return false;
    }

    NUITKA_MAY_BE_UNUSED bool resize_result = _LIST_RESIZE(list, n * 2);
    assert(resize_result);

    PyObject **items = list->ob_item;

    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *item = items[i];
        Py_INCREF(item);
        NUITKA_LIST_STORE_PTR(&items[n + i], item);
    }

    return true;
}

static bool _LIST_EXTEND_FROM_LIST_LOCK_HELD(PyListObject *list, PyListObject *other) {
    size_t n = Py_SIZE(other);

    if (n == 0) {
        return true;
    }

    size_t m = Py_SIZE(list);

    NUITKA_MAY_BE_UNUSED bool resize_result = _LIST_RESIZE(list, m + n);
    assert(resize_result);

    PyObject **src = other->ob_item;
    PyObject **dest = list->ob_item + m;

    for (size_t i = 0; i < n; i++) {
        PyObject *o = src[i];
        Py_INCREF(o);

        NUITKA_LIST_STORE_PTR(&dest[i], o);
    }

    return true;
}

bool LIST_EXTEND_FROM_LIST(PyObject *list, PyObject *other) {
#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT
    PyObject *result = _PyList_Extend((PyListObject *)list, other);
    if (result != NULL) {
        Py_DECREF(result);
        return true;
    } else {
        return false;
    }
#else
    assert(PyList_CheckExact(list));
    assert(PyList_CheckExact(other));

#ifdef Py_GIL_DISABLED
    bool result;

    if (list == other) {
        Py_BEGIN_CRITICAL_SECTION(list);
        result = _LIST_EXTEND_SELF((PyListObject *)list);
        Py_END_CRITICAL_SECTION();
    } else {
        Py_BEGIN_CRITICAL_SECTION2(list, other);
        result = _LIST_EXTEND_FROM_LIST_LOCK_HELD((PyListObject *)list, (PyListObject *)other);
        Py_END_CRITICAL_SECTION2();
    }

    return result;
#else
    if (list == other) {
        return _LIST_EXTEND_SELF((PyListObject *)list);
    }

    return _LIST_EXTEND_FROM_LIST_LOCK_HELD((PyListObject *)list, (PyListObject *)other);
#endif
#endif
}

static bool _LIST_EXTEND_FROM_ITERABLE_LOCK_HELD(PyThreadState *tstate, PyListObject *list, PyObject *other) {
    assert((PyObject *)list != other);

    // First attempt those things that occur most often.
    PyObject **src;
    Py_ssize_t src_size;

    if (PyList_CheckExact(other)) {
        src = NUITKA_LIST_ITEMS(other);
        src_size = PyList_GET_SIZE(other);
    } else if (PyTuple_CheckExact(other)) {
        src = _PyTuple_ITEMS(other);
        src_size = PyTuple_GET_SIZE(other);
    } else {
        src = NULL;
#ifndef __NUITKA_NO_ASSERT__
        src_size = 0;
#endif
    }

    if (src != NULL) {
        if (src_size == 0) {
            return true;
        }

        Py_ssize_t list_size = PyList_GET_SIZE(list);

        // Overflow is not really realistic, so we only assert against it.
        assert(list_size <= PY_SSIZE_T_MAX - src_size);
        NUITKA_MAY_BE_UNUSED bool resize_result = _LIST_RESIZE(list, list_size + src_size);
        assert(resize_result);

        PyObject **target_items = NUITKA_LIST_ITEMS(list) + list_size;

        for (Py_ssize_t i = 0; i < src_size; i++) {
            PyObject *value = src[i];
            Py_INCREF(value);
            NUITKA_LIST_STORE_PTR(target_items, value);
            target_items += 1;
        }

        return true;
    }

    // Slow path needs to use iterator.
    PyObject *iter = MAKE_ITERATOR(tstate, other);

    if (iter == NULL) {
        return false;
    }
    PyObject *(*iternext)(PyObject *) = *Py_TYPE(iter)->tp_iternext;

#if PYTHON_VERSION >= 0x300
    // Guess a iterator size if possible
    src_size = PyObject_LengthHint(other, 8);

    if (src_size < 0) {
        Py_DECREF(iter);
        return false;
    }

    Py_ssize_t list_size = PyList_GET_SIZE(list);

    if (list_size > PY_SSIZE_T_MAX - src_size) {
        // Overflow is not really realistic, hope is, it will not come true.
    } else {
        // Allocate the space in one go.
        if (_LIST_RESIZE(list, list_size + src_size) == false) {
            Py_DECREF(iter);
            return false;
        }

        // Restore validity of the object for the time being.
        Py_SET_SIZE(list, list_size);
    }
#endif

    for (;;) {
        PyObject *item = iternext(iter);

        if (item == NULL) {
            bool stop_iteration_error = CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED(tstate);

            Py_DECREF(iter);

            if (unlikely(stop_iteration_error == false)) {
                Py_ssize_t cur_size = PyList_GET_SIZE(list);

                if (cur_size < list->allocated) {
                    if (_LIST_RESIZE(list, cur_size) == false) {
                        return false;
                    }
                }

                return false;
            }

            break;
        }

        CHECK_OBJECT(item);

        Py_ssize_t cur_size = PyList_GET_SIZE(list);

        if (cur_size < list->allocated) {
            // Already allocated, so we can just set it.
            NUITKA_LIST_STORE_PTR(&list->ob_item[cur_size], item);
            Py_SET_SIZE(list, cur_size + 1);
        } else {
            assert(cur_size != PY_SSIZE_T_MAX);

            if (_LIST_RESIZE(list, cur_size + 1) == false) {
                Py_DECREF(item);
                return false;
            }

            NUITKA_LIST_STORE_PTR(&list->ob_item[cur_size], item);
        }
    }

    /* Cut back result list if initial guess was too large. */
    Py_ssize_t cur_size = PyList_GET_SIZE(list);

    if (cur_size < list->allocated) {
        if (_LIST_RESIZE(list, cur_size) == false) {
            return false;
        }
    }

    return true;
}

bool LIST_EXTEND_FROM_ITERABLE(PyThreadState *tstate, PyObject *target, PyObject *other) {
    CHECK_OBJECT(target);
    assert(PyList_CheckExact(target));

    CHECK_OBJECT(other);

    PyListObject *list = (PyListObject *)target;

#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT
    PyObject *result = _PyList_Extend(list, other);
    if (result != NULL) {
        Py_DECREF(result);
        return true;
    } else {
        return false;
    }
#else
    if ((PyObject *)list == other) {
#ifdef Py_GIL_DISABLED
        bool result;
        Py_BEGIN_CRITICAL_SECTION(list);
        result = _LIST_EXTEND_SELF(list);
        Py_END_CRITICAL_SECTION();

        return result;
#else
        return _LIST_EXTEND_SELF(list);
#endif
    }

#ifdef Py_GIL_DISABLED
    bool result;

    if (PyList_CheckExact(other)) {
        Py_BEGIN_CRITICAL_SECTION2(list, other);
        result = _LIST_EXTEND_FROM_ITERABLE_LOCK_HELD(tstate, list, other);
        Py_END_CRITICAL_SECTION2();
    } else {
        Py_BEGIN_CRITICAL_SECTION(list);
        result = _LIST_EXTEND_FROM_ITERABLE_LOCK_HELD(tstate, list, other);
        Py_END_CRITICAL_SECTION();
    }

    return result;
#else
    return _LIST_EXTEND_FROM_ITERABLE_LOCK_HELD(tstate, list, other);
#endif
#endif
}

#if PYTHON_VERSION >= 0x390
bool LIST_EXTEND_FOR_UNPACK(PyThreadState *tstate, PyObject *list, PyObject *other) {
    // TODO: For improved performance, inline this, but we probably wait
    // until code generation for this kind of helpers is there.
    bool result = LIST_EXTEND_FROM_ITERABLE(tstate, list, other);

    if (likely(result)) {
        return true;
    }

    PyObject *error = GET_ERROR_OCCURRED(tstate);

    assert(error != NULL);

    if (EXCEPTION_MATCH_BOOL_SINGLE(tstate, error, PyExc_TypeError) &&
        (Py_TYPE(other)->tp_iter == NULL && !PySequence_Check(other))) {
        CLEAR_ERROR_OCCURRED(tstate);
        PyErr_Format(PyExc_TypeError, "Value after * must be an iterable, not %s", Py_TYPE(other)->tp_name);
    }

    return false;
}
#endif

static bool _LIST_APPEND1_LOCK_HELD(PyObject *target, PyObject *item) {
    PyListObject *list = (PyListObject *)target;

    Py_ssize_t cur_size = PyList_GET_SIZE(list);

    // Overflow is not really realistic, so we only assert against it.
    assert(cur_size <= PY_SSIZE_T_MAX);

    if (_LIST_RESIZE(list, cur_size + 1) == false) {
        return false;
    }

    NUITKA_LIST_STORE_PTR(&list->ob_item[cur_size], item);

    return true;
}

bool LIST_APPEND1(PyObject *target, PyObject *item) {
    CHECK_OBJECT(target);
    assert(PyList_CheckExact(target));

    CHECK_OBJECT(item);

#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT && !defined(Py_GIL_DISABLED)
    int res = PyList_Append(target, item);
    Py_DECREF(item);
    return res == 0;
#else
    bool result;
    NUITKA_LIST_BEGIN(target);
    result = _LIST_APPEND1_LOCK_HELD(target, item);
    NUITKA_LIST_END();

    return result;
#endif
}

static bool _LIST_APPEND0_LOCK_HELD(PyObject *target, PyObject *item) {
    PyListObject *list = (PyListObject *)target;

    Py_ssize_t cur_size = PyList_GET_SIZE(list);

    // Overflow is not really realistic, so we only assert against it.
    assert(cur_size <= PY_SSIZE_T_MAX);

    if (_LIST_RESIZE(list, cur_size + 1) == false) {
        return false;
    }

    Py_INCREF(item);
    NUITKA_LIST_STORE_PTR(&list->ob_item[cur_size], item);

    return true;
}

bool LIST_APPEND0(PyObject *target, PyObject *item) {
    CHECK_OBJECT(target);
    assert(PyList_CheckExact(target));

    CHECK_OBJECT(item);

#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT && !defined(Py_GIL_DISABLED)
    int res = PyList_Append(target, item);
    return res == 0;
#else
    bool result;
    NUITKA_LIST_BEGIN(target);
    result = _LIST_APPEND0_LOCK_HELD(target, item);
    NUITKA_LIST_END();

    return result;
#endif
}

static bool _LIST_REMOVE_LOCK_HELD(PyObject *target, PyObject *item) {
    PyListObject *list = (PyListObject *)target;

    for (Py_ssize_t i = 0; i < Py_SIZE(list); i++) {
        PyObject *element = list->ob_item[i];

        Py_INCREF(element);
        nuitka_bool cmp = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(element, item);
        Py_DECREF(element);

        if (cmp == NUITKA_BOOL_TRUE) {
            // The comparison may run arbitrary code that mutates the list.
            Py_ssize_t cur_size = Py_SIZE(list);

            if (i >= cur_size) {
                // The item was already removed by the comparison code.
                return true;
            }

            PyObject *removed = list->ob_item[i];

            Py_SET_SIZE(list, cur_size - 1);

#ifdef Py_GIL_DISABLED
            for (Py_ssize_t j = i; j + 1 < cur_size; j++) {
                NUITKA_LIST_STORE_PTR(&list->ob_item[j], list->ob_item[j + 1]);
            }
#else
            memmove(list->ob_item + i, list->ob_item + i + 1, sizeof(PyObject *) * (cur_size - i - 1));
#endif

            // Only release the removed item once the list is canonical again,
            // as its deallocator may mutate the list.
            Py_DECREF(removed);

            return true;
        } else if (unlikely(cmp == NUITKA_BOOL_EXCEPTION)) {
            return false;
        }
    }

    PyThreadState *tstate = PyThreadState_GET();

    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "list.remove(x): x not in list");
    return false;
}

bool LIST_REMOVE(PyObject *target, PyObject *item) {
    CHECK_OBJECT(target);
    assert(PyList_CheckExact(target));

    CHECK_OBJECT(item);

#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT && 0
    // TODO: This is not exposed, would need to delete as slice instead.
    int res = PyList_Remove(target, item);
    return res == 0;
#else
    bool result;
    NUITKA_LIST_BEGIN(target);
    result = _LIST_REMOVE_LOCK_HELD(target, item);
    NUITKA_LIST_END();

    return result;
#endif
}

static void _LIST_CLEAR_LOCK_HELD(PyObject *target) {
    CHECK_OBJECT(target);
    assert(PyList_CheckExact(target));

    PyListObject *list = (PyListObject *)target;

    PyObject **items = list->ob_item;

    if (items != NULL) {
        // Make the list empty first, so the data we release is not accessible.
        Py_ssize_t i = Py_SIZE(list);
        Py_SET_SIZE(list, 0);
#ifdef Py_GIL_DISABLED
        _Py_atomic_store_ptr_release(&list->ob_item, NULL);
#else
        list->ob_item = NULL;
#endif
        list->allocated = 0;

        while (--i >= 0) {
            Py_XDECREF(items[i]);
        }

#ifdef Py_GIL_DISABLED
        Nuitka_List_EnsureSharedOnResize(list);
        Nuitka_FreeListArray(items, _PyObject_GC_IS_SHARED(list));
#else
        PyMem_Free(items);
#endif
    }
}

void LIST_CLEAR(PyObject *target) {
    NUITKA_LIST_BEGIN(target);
    _LIST_CLEAR_LOCK_HELD(target);
    NUITKA_LIST_END();
}

PyObject *getListIndexObject(Py_ssize_t value) {
#if PYTHON_VERSION < 0x300
    return PyInt_FromSsize_t(value);
#else
    // TODO: Actually to be fully correct, we will need a "Nuitka_LongFromCSsize_t" which
    // we do not have yet.
    return Nuitka_LongFromCLong((long)value);
#endif
}

static PyObject *_LIST_COUNT_LOCK_HELD(PyObject *list, PyObject *item) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    Py_ssize_t count = 0;

    for (Py_ssize_t i = 0; i < Py_SIZE(list); i++) {
        PyObject *element = PyList_GET_ITEM(list, i);

        // Fast path, is identical
        if (element == item) {
            count++;
            continue;
        }

        // Rich compare element while holding a reference. TODO: If we knew the type
        // of "item" we could be faster by picking variants that know stuff, but
        // maybe it is not as important.
        Py_INCREF(element);
        nuitka_bool nbool_res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(element, item);
        Py_DECREF(element);

        if (nbool_res == NUITKA_BOOL_TRUE) {
            count++;
            continue;
        }

        // Pass on exceptions from comparisons.
        if (unlikely(nbool_res == NUITKA_BOOL_EXCEPTION)) {
            return NULL;
        }
    }

    return getListIndexObject(count);
}

PyObject *LIST_COUNT(PyObject *list, PyObject *item) {
    PyObject *result;
    NUITKA_LIST_BEGIN(list);
    result = _LIST_COUNT_LOCK_HELD(list, item);
    NUITKA_LIST_END();

    return result;
}

static PyObject *_LIST_INDEX_COMMON(PyThreadState *tstate, PyListObject *list, PyObject *item, Py_ssize_t start,
                                    Py_ssize_t stop) {
    // Negative values for start/stop are handled here.
    if (start < 0) {
        start += Py_SIZE(list);

        if (start < 0) {
            start = 0;
        }
    }

    if (stop < 0) {
        stop += Py_SIZE(list);

        if (stop < 0) {
            stop = 0;
        }
    }

    for (Py_ssize_t i = start; i < stop && i < Py_SIZE(list); i++) {
        PyObject *element = list->ob_item[i];

        Py_INCREF(element);
        nuitka_bool nbool_res = RICH_COMPARE_EQ_NBOOL_OBJECT_OBJECT(element, item);
        Py_DECREF(element);

        if (nbool_res == NUITKA_BOOL_TRUE) {
            return getListIndexObject(i);
        }

        // Pass on exceptions from comparisons.
        if (unlikely(nbool_res == NUITKA_BOOL_EXCEPTION)) {
            return NULL;
        }
    }

#if PYTHON_VERSION < 0x270
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "list.index(x): x not in list");
    return NULL;
#elif PYTHON_VERSION < 0x300
    PyObject *err_format = PyString_FromString("%r is not in list");
    PyObject *format_tuple = MAKE_TUPLE1_0(tstate, item);
    PyObject *err_string = PyString_Format(err_format, format_tuple);
    Py_DECREF(format_tuple);

    if (err_string == NULL) {
        return NULL;
    }

    SET_CURRENT_EXCEPTION_TYPE0_VALUE1(tstate, PyExc_ValueError, err_string);
    return NULL;
#elif PYTHON_VERSION < 0x3e0
    PyErr_Format(PyExc_ValueError, "%R is not in list", item);
    return NULL;
#else
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_ValueError, "list.index(x): x not in list");
    return NULL;
#endif
}

PyObject *LIST_INDEX2(PyThreadState *tstate, PyObject *list, PyObject *item) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    PyObject *result;
    NUITKA_LIST_BEGIN(list);
    result = _LIST_INDEX_COMMON(tstate, (PyListObject *)list, item, 0, Py_SIZE(list));
    NUITKA_LIST_END();

    return result;
}

static void SET_SLICE_INDICES_ERROR(PyThreadState *tstate) {
    // The message changed in CPython 2.7.14, 3.5.4, and 3.6.2, when 'list.index' switched to
    // '_PyEval_SliceIndexNotNone'.
#if PYTHON_VERSION < 0x27e || (PYTHON_VERSION >= 0x300 && PYTHON_VERSION < 0x354) ||                                   \
    (PYTHON_VERSION >= 0x360 && PYTHON_VERSION < 0x362)
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                    "slice indices must be integers or None or have an __index__ method");
#else
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                    "slice indices must be integers or have an __index__ method");
#endif
}

PyObject *LIST_INDEX3(PyThreadState *tstate, PyObject *list, PyObject *item, PyObject *start) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    if (unlikely(!Nuitka_Index_Check(start))) {
        SET_SLICE_INDICES_ERROR(tstate);
        return NULL;
    }

    Py_ssize_t start_ssize = Nuitka_Number_AsSsize_t(start, NULL);

    if (unlikely(start_ssize == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    PyObject *result;
    NUITKA_LIST_BEGIN(list);
    result = _LIST_INDEX_COMMON(tstate, (PyListObject *)list, item, start_ssize, Py_SIZE(list));
    NUITKA_LIST_END();

    return result;
}

PyObject *LIST_INDEX4(PyThreadState *tstate, PyObject *list, PyObject *item, PyObject *start, PyObject *stop) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    if (unlikely(!Nuitka_Index_Check(start))) {
        SET_SLICE_INDICES_ERROR(tstate);
        return NULL;
    }

    Py_ssize_t start_ssize = Nuitka_Number_AsSsize_t(start, NULL);

    if (unlikely(start_ssize == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    if (unlikely(!Nuitka_Index_Check(stop))) {
        SET_SLICE_INDICES_ERROR(tstate);
        return NULL;
    }

    Py_ssize_t stop_ssize = Nuitka_Number_AsSsize_t(stop, NULL);

    if (unlikely(stop_ssize == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return NULL;
    }

    PyObject *result;
    NUITKA_LIST_BEGIN(list);
    result = _LIST_INDEX_COMMON(tstate, (PyListObject *)list, item, start_ssize, stop_ssize);
    NUITKA_LIST_END();

    return result;
}

static void _LIST_INSERT_CONST_LOCK_HELD(PyObject *list, Py_ssize_t index, PyObject *item);

bool LIST_INSERT(PyThreadState *tstate, PyObject *list, PyObject *index, PyObject *item) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    CHECK_OBJECT(index);
    CHECK_OBJECT(item);

    Py_ssize_t index_ssize;

#if PYTHON_VERSION < 0x300
    // CPython2 list.insert uses its integer argument parsing, which does not
    // use "__index__". Python2.6 only warns about float values, while Python2.7
    // rejects them.
#if PYTHON_VERSION < 0x270
    if (unlikely(PyFloat_Check(index))) {
        if (unlikely(PyErr_WarnEx(PyExc_DeprecationWarning, "integer argument expected, got float", 1) < 0)) {
            return false;
        }
    }
#else
    if (unlikely(PyFloat_Check(index))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");
        return false;
    }
#endif

#if SIZEOF_SIZE_T == SIZEOF_LONG
    // Where "Py_ssize_t" and "long" have the same size, the CPython "n"
    // argument conversion falls through to the "l" one, which uses
    // "PyInt_AsLong" and reports overflow with a different message.
    index_ssize = (Py_ssize_t)PyInt_AsLong(index);
#else
    index_ssize = PyInt_AsSsize_t(index);
#endif

    if (unlikely(index_ssize == -1 && HAS_ERROR_OCCURRED(tstate))) {
        return false;
    }
#else
#if PYTHON_VERSION < 0x3a0
    // Older CPython argument parsing rejects float values before converting.
    if (unlikely(PyFloat_Check(index))) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "integer argument expected, got float");
        return false;
    }
#endif

    PyObject *index_long = Nuitka_Number_Index(index);

    if (unlikely(index_long == NULL)) {
        return false;
    }

    index_ssize = Nuitka_PyLong_AsSsize_t(tstate, index_long);

    // Values that do not fit raise "OverflowError", unlike for slice indexes.
    if (unlikely(index_ssize == -1 && HAS_ERROR_OCCURRED(tstate))) {
        Py_DECREF(index_long);
        return false;
    }

    Py_DECREF(index_long);
#endif

    NUITKA_LIST_BEGIN(list);
    _LIST_INSERT_CONST_LOCK_HELD(list, index_ssize, item);
    NUITKA_LIST_END();

    return true;
}

static void _LIST_INSERT_CONST_LOCK_HELD(PyObject *list, Py_ssize_t index, PyObject *item) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    CHECK_OBJECT(item);

    PyListObject *list_object = (PyListObject *)list;

    Py_ssize_t n = Py_SIZE(list_object);

    // Expand the list by needed space.
    if (_LIST_RESIZE(list_object, n + 1) == false) {
        abort();
    }

    // Negative values and overflow for for index are handled here.
    if (index < 0) {
        index += n;
        if (index < 0) {
            index = 0;
        }
    }
    if (index > n) {
        index = n;
    }

    // Shift the items behind the insert index.
    PyObject **items = list_object->ob_item;

    for (Py_ssize_t i = n; --i >= index;) {
        NUITKA_LIST_STORE_PTR(&items[i + 1], items[i]);
    }

    Py_INCREF(item);
    NUITKA_LIST_STORE_PTR(&items[index], item);
}

void LIST_INSERT_CONST(PyObject *list, Py_ssize_t index, PyObject *item) {
    NUITKA_LIST_BEGIN(list);
    _LIST_INSERT_CONST_LOCK_HELD(list, index, item);
    NUITKA_LIST_END();
}

static void _Nuitka_ReverseObjectsSlice(PyObject **lo, PyObject **hi) {
    assert(lo != NULL && hi != NULL);

    hi -= 1;

    while (lo < hi) {
        {
            PyObject *t = *lo;
            NUITKA_LIST_STORE_PTR(lo, *hi);
            NUITKA_LIST_STORE_PTR(hi, t);
        }

        lo += 1;
        hi -= 1;
    }
}

static void _LIST_REVERSE_LOCK_HELD(PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    PyListObject *list_object = (PyListObject *)list;

    if (Py_SIZE(list_object) > 1) {
        _Nuitka_ReverseObjectsSlice(list_object->ob_item, list_object->ob_item + Py_SIZE(list_object));
    }
}

void LIST_REVERSE(PyObject *list) {
    NUITKA_LIST_BEGIN(list);
    _LIST_REVERSE_LOCK_HELD(list);
    NUITKA_LIST_END();
}

#if PYTHON_VERSION >= 0x300 && !defined(_NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT)
static bool allocateListItems(PyListObject *list, Py_ssize_t size) {
#ifdef Py_GIL_DISABLED
    _PyListArray *array = Nuitka_AllocateListArray(size);

    if (unlikely(array == NULL)) {
        return false;
    }

    PyObject **items = array->ob_item;
    memset(items, 0, size * sizeof(PyObject *));
    FT_ATOMIC_STORE_PTR_RELEASE(list->ob_item, items);
#else
    PyObject **items = PyMem_New(PyObject *, size);

    if (unlikely(items == NULL)) {
        return false;
    }

    list->ob_item = items;
#endif
    list->allocated = size;

    return true;
}

#endif

PyObject *MAKE_LIST(PyThreadState *tstate, PyObject *iterable) {
    // Can leave the size hinting to later functions, because the list is allocated empty without
    // items, and when then extending, etc. length hints can be used.
    PyObject *list = MAKE_LIST_EMPTY(tstate, 0);

#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT
    PyObject *result = _PyList_Extend((PyListObject *)list, iterable);
    if (result == NULL) {
        Py_DECREF(list);
        return NULL;
    } else {
        Py_DECREF(result);
        return list;
    }
#else
    Py_INCREF(iterable);

#if PYTHON_VERSION >= 0x300
    if (Nuitka_PyObject_HasLen(iterable)) {
        Py_ssize_t iter_len = Nuitka_PyObject_Size(iterable);

        if (unlikely(iter_len == -1)) {
            if (!CHECK_AND_CLEAR_TYPE_ERROR_OCCURRED(tstate)) {
                Py_DECREF(iterable);
                Py_DECREF(list);
                return NULL;
            }
        }

        if (iter_len > 0) {
            if (allocateListItems((PyListObject *)list, iter_len) == false) {
                Py_DECREF(iterable);
                Py_DECREF(list);

                PyErr_NoMemory();
                return NULL;
            }
        }
    }
#endif

    bool res = LIST_EXTEND_FROM_ITERABLE(tstate, list, iterable);

    Py_DECREF(iterable);

    if (unlikely(res == false)) {
        Py_DECREF(list);
        return NULL;
    }

    return list;
#endif
}

#include "HelpersListsGenerated.c"

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
