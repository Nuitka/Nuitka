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
/* This helpers is used to work with lists.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

// #include "richcomparisons.h"

static PyObject *Nuitka_LongFromCLong(long ival);

#if NUITKA_LIST_HAS_FREELIST
static struct _Py_list_state *_Nuitka_Py_get_list_state(void) {
    PyInterpreterState *interp = _PyInterpreterState_GET();
    return &interp->list;
}

PyObject *MAKE_LIST_EMPTY(Py_ssize_t size) {
    assert(size >= 0);

    struct _Py_list_state *state = _Nuitka_Py_get_list_state();
    PyListObject *result_list;

    assert(state->numfree >= 0);

    if (state->numfree) {
        state->numfree -= 1;
        result_list = state->free_list[state->numfree];

        Nuitka_Py_NewReference((PyObject *)result_list);
    } else {
        result_list = (PyListObject *)Nuitka_GC_New(&PyList_Type);
    }

    // Elements are allocated separately.
    if (size > 0) {
        result_list->ob_item = (PyObject **)PyMem_Calloc(size, sizeof(PyObject *));

        if (unlikely(result_list->ob_item == NULL)) {
            Py_DECREF(result_list);
            return PyErr_NoMemory();
        }
    } else {
        result_list->ob_item = NULL;
    }

    Py_SET_SIZE(result_list, size);
    result_list->allocated = size;

    Nuitka_GC_Track(result_list);

    return (PyObject *)result_list;
}
#endif

PyObject *LIST_COPY(PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    Py_ssize_t size = PyList_GET_SIZE(list);
    PyObject *result = MAKE_LIST_EMPTY(size);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = PyList_GET_ITEM(list, i);
        Py_INCREF(item);
        PyList_SET_ITEM(result, i, item);
    }

    return result;
}

static bool LIST_RESIZE(PyListObject *list, Py_ssize_t newsize) {
    Py_ssize_t allocated = list->allocated;

    if (allocated >= newsize && newsize >= (allocated >> 1)) {
        Py_SET_SIZE(list, newsize);

        return true;
    }

    size_t new_allocated;

    if (newsize == 0) {
        new_allocated = 0;
    } else {
        new_allocated = ((size_t)newsize + (newsize >> 3) + 6) & ~(size_t)3;
    }

    size_t num_allocated_bytes = new_allocated * sizeof(PyObject *);

    PyObject **items = (PyObject **)PyMem_Realloc(list->ob_item, num_allocated_bytes);
    if (unlikely(items == NULL)) {
        PyErr_NoMemory();
        return false;
    }

    list->ob_item = items;
    Py_SET_SIZE(list, newsize);
    list->allocated = new_allocated;

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

    size_t n = PyList_GET_SIZE(other);

    if (n == 0) {
        return true;
    }

    size_t m = Py_SIZE(list);

    if (LIST_RESIZE((PyListObject *)list, m + n) == false) {
        return false;
    }

    PyObject **src = &PyList_GET_ITEM(other, 0);
    PyObject **dest = &PyList_GET_ITEM(list, m);

    for (size_t i = 0; i < n; i++) {
        PyObject *o = src[i];
        Py_INCREF(o);

        dest[i] = o;
    }

    return true;
#endif
}

bool LIST_EXTEND(PyObject *target, PyObject *other) {
    CHECK_OBJECT(target);
    assert(PyList_Check(target));

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
    // First attempt those things that occur most often. Keep in mind that
    // other might be the same object as list.
    PyObject **src;
    Py_ssize_t src_size;

    if (PyList_CheckExact(other)) { // this covers list == other too.
        src = _PyList_ITEMS(other);
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
        if (LIST_RESIZE(list, list_size + src_size) == false) {
            return false;
        }

        PyObject **target_items = _PyList_ITEMS(list) + list_size;

        for (Py_ssize_t i = 0; i < src_size; i++) {
            PyObject *value = src[i];
            Py_INCREF(value);
            *target_items++ = value;
        }

        return true;
    }

    // Slow path needs to use iterator. TODO:
    PyObject *iter = MAKE_ITERATOR(other);

    if (iter == NULL) {
        return false;
    }
    PyObject *(*iternext)(PyObject *) = *Py_TYPE(iter)->tp_iternext;

    Py_ssize_t cur_size = PyList_GET_SIZE(list);

#if PYTHON_VERSION >= 0x340
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
        if (LIST_RESIZE(list, list_size + src_size) == false) {
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
            bool stop_iteration_error = CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED();

            Py_DECREF(iter);

            if (unlikely(stop_iteration_error == false)) {
                if (cur_size < list->allocated) {
                    if (LIST_RESIZE(list, cur_size) == false) {
                        return false;
                    }
                }

                return false;
            }

            break;
        }

        CHECK_OBJECT(item);

        if (cur_size < list->allocated) {
            // Already allocated, so we can just set it.
            PyList_SET_ITEM(list, cur_size, item);
            Py_SET_SIZE(list, cur_size + 1);
        } else {
            assert(cur_size != PY_SSIZE_T_MAX);

            if (LIST_RESIZE(list, cur_size + 1) == false) {
                return false;
            }

            PyList_SET_ITEM(list, cur_size, item);
        }
        cur_size += 1;
    }

    /* Cut back result list if initial guess was too large. */
    assert(cur_size == PyList_GET_SIZE(list));

    if (cur_size < list->allocated) {
        if (LIST_RESIZE(list, cur_size) == false) {
            return false;
        }
    }

    return true;
#endif
}

#if PYTHON_VERSION >= 0x390
bool LIST_EXTEND_FOR_UNPACK(PyObject *list, PyObject *other) {
    // TODO: For improved performance, inline this, but we probably wait
    // until code generation for this kind of helpers is there.
    bool result = LIST_EXTEND(list, other);

    if (likely(result)) {
        return true;
    }

    PyObject *error = GET_ERROR_OCCURRED();

    if (EXCEPTION_MATCH_BOOL_SINGLE(error, PyExc_TypeError) &&
        (Py_TYPE(other)->tp_iter == NULL && !PySequence_Check(other))) {
        CLEAR_ERROR_OCCURRED();
        PyErr_Format(PyExc_TypeError, "Value after * must be an iterable, not %s", Py_TYPE(other)->tp_name);
    }

    return false;
}
#endif

bool LIST_APPEND1(PyObject *target, PyObject *item) {
#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT
    int res == PyList_Append(target, item);
    Py_DECREF(item);
    return res == 0;
#else
    CHECK_OBJECT(target);
    assert(PyList_Check(target));

    CHECK_OBJECT(item);

    PyListObject *list = (PyListObject *)target;

    Py_ssize_t cur_size = PyList_GET_SIZE(list);

    // Overflow is not really realistic, so we only assert against it.
    assert(cur_size <= PY_SSIZE_T_MAX);

    if (LIST_RESIZE(list, cur_size + 1) == false) {
        return false;
    }

    PyList_SET_ITEM(list, cur_size, item);

    return true;
#endif
}

bool LIST_APPEND0(PyObject *target, PyObject *item) {
#if _NUITKA_EXPERIMENTAL_DISABLE_LIST_OPT
    int res == PyList_Append(target, item);
    return res == 0;
#else
    CHECK_OBJECT(target);
    assert(PyList_Check(target));

    CHECK_OBJECT(item);

    PyListObject *list = (PyListObject *)target;

    Py_ssize_t cur_size = PyList_GET_SIZE(list);

    // Overflow is not really realistic, so we only assert against it.
    assert(cur_size <= PY_SSIZE_T_MAX);

    if (LIST_RESIZE(list, cur_size + 1) == false) {
        return false;
    }

    PyList_SET_ITEM0(list, cur_size, item);

    return true;
#endif
}

void LIST_CLEAR(PyObject *target) {
    CHECK_OBJECT(target);
    assert(PyList_Check(target));

    PyListObject *list = (PyListObject *)target;

    PyObject **items = list->ob_item;

    if (items != NULL) {
        // Make the list empty first, so the data we release is not accessible.
        Py_ssize_t i = Py_SIZE(list);
        Py_SET_SIZE(list, 0);
        list->ob_item = NULL;
        list->allocated = 0;

        while (--i >= 0) {
            Py_XDECREF(items[i]);
        }

        PyMem_Free(items);
    }
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

PyObject *LIST_COUNT(PyObject *list, PyObject *item) {
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

static PyObject *_LIST_INDEX_COMMON(PyListObject *list, PyObject *item, Py_ssize_t start, Py_ssize_t stop) {
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

#if PYTHON_VERSION < 0x300
    PyObject *err_format = PyString_FromString("%r is not in list");
    PyObject *format_tuple = MAKE_TUPLE1_0(item);
    PyObject *err_string = PyString_Format(err_format, format_tuple);
    Py_DECREF(format_tuple);

    if (err_string == NULL) {
        return NULL;
    }

    SET_CURRENT_EXCEPTION_TYPE0_VALUE1(PyExc_ValueError, err_string);
    return NULL;
#else
    PyErr_Format(PyExc_ValueError, "%R is not in list", item);
    return NULL;
#endif
}

PyObject *LIST_INDEX2(PyObject *list, PyObject *item) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    return _LIST_INDEX_COMMON((PyListObject *)list, item, 0, Py_SIZE(list));
}

PyObject *LIST_INDEX3(PyObject *list, PyObject *item, PyObject *start) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    PyObject *start_index = Nuitka_Number_IndexAsLong(start);

    if (unlikely(start_index == NULL)) {
        DROP_ERROR_OCCURRED();

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "slice indices must be integers or have an __index__ method");
        return NULL;
    }

    Py_ssize_t start_ssize = PyLong_AsSsize_t(start_index);

    return _LIST_INDEX_COMMON((PyListObject *)list, item, start_ssize, Py_SIZE(list));
}

PyObject *LIST_INDEX4(PyObject *list, PyObject *item, PyObject *start, PyObject *stop) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    PyObject *start_index = Nuitka_Number_IndexAsLong(start);

    if (unlikely(start_index == NULL)) {
        DROP_ERROR_OCCURRED();

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "slice indices must be integers or have an __index__ method");
        return NULL;
    }

    Py_ssize_t start_ssize = PyLong_AsSsize_t(start_index);

    PyObject *stop_index = Nuitka_Number_IndexAsLong(stop);

    if (unlikely(stop_index == NULL)) {
        DROP_ERROR_OCCURRED();

        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "slice indices must be integers or have an __index__ method");
        return NULL;
    }

    Py_ssize_t stop_ssize = PyLong_AsSsize_t(stop_index);

    return _LIST_INDEX_COMMON((PyListObject *)list, item, start_ssize, stop_ssize);
}

bool LIST_INSERT(PyObject *list, PyObject *index, PyObject *item) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    CHECK_OBJECT(item);

    PyObject *index_long = Nuitka_Number_IndexAsLong(index);

    if (unlikely(index_long == NULL)) {
        DROP_ERROR_OCCURRED();

        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' cannot be interpreted as an integer", index);
        return false;
    }

    Py_ssize_t index_ssize = PyLong_AsSsize_t(index_long);

    LIST_INSERT_CONST(list, index_ssize, item);
    return true;
}

void LIST_INSERT_CONST(PyObject *list, Py_ssize_t index, PyObject *item) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    CHECK_OBJECT(item);

    PyListObject *list_object = (PyListObject *)list;

    Py_ssize_t n = Py_SIZE(list_object);

    // Expand the list by needed space.
    if (LIST_RESIZE(list_object, n + 1) == false) {
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
        items[i + 1] = items[i];
    }

    Py_INCREF(item);
    items[index] = item;
}

static void _Nuitka_ReverseObjectsSlice(PyObject **lo, PyObject **hi) {
    assert(lo != NULL && hi != NULL);

    hi -= 1;

    while (lo < hi) {
        {
            PyObject *t = *lo;
            *lo = *hi;
            *hi = t;
        }

        lo += 1;
        hi -= 1;
    }
}

void LIST_REVERSE(PyObject *list) {
    PyListObject *list_object = (PyListObject *)list;

    if (Py_SIZE(list_object) > 1) {
        _Nuitka_ReverseObjectsSlice(list_object->ob_item, list_object->ob_item + Py_SIZE(list_object));
    }
}

#if PYTHON_VERSION >= 0x340
static bool allocateListItems(PyListObject *list, Py_ssize_t size) {
    PyObject **items = PyMem_New(PyObject *, size);

    if (unlikely(items == NULL)) {
        PyErr_NoMemory();
        return false;
    }

    list->ob_item = items;
    list->allocated = size;

    return true;
}
#endif

PyObject *MAKE_LIST(PyObject *iterable) {
    // TODO: Could create the list with length on 3.4 hint already, however the memory
    // is not allocated for a 0 sized list yet, so it probably doesn't matter much.
    PyObject *list = MAKE_LIST_EMPTY(0);

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
#if PYTHON_VERSION >= 0x340
    if (_PyObject_HasLen(iterable)) {
        Py_ssize_t iter_len = Nuitka_PyObject_Size(iterable);

        if (unlikely(iter_len == -1)) {
            if (!PyErr_ExceptionMatches(PyExc_TypeError)) {
                return NULL;
            }

            CLEAR_ERROR_OCCURRED();
        }

        if (iter_len > 0) {
            if (allocateListItems((PyListObject *)list, iter_len) == false) {
                return NULL;
            }
        }
    }
#endif

    bool res = LIST_EXTEND(list, iterable);

    if (unlikely(res == false)) {
        Py_DECREF(list);
        return NULL;
    }

    return list;
#endif
}
