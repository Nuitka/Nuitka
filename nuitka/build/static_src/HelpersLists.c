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

// TODO: Move these into prelude maybe
#ifndef _PyTuple_ITEMS
#define _PyTuple_ITEMS(op) (((PyTupleObject *)(op))->ob_item)
#endif

#ifndef _PyList_ITEMS
#define _PyList_ITEMS(op) (((PyListObject *)(op))->ob_item)
#endif

#ifndef Py_SET_SIZE
#define Py_SET_SIZE(op, size) ((PyVarObject *)(op))->ob_size = size
#endif

PyObject *LIST_COPY(PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));

    Py_ssize_t size = PyList_GET_SIZE(list);
    PyObject *result = PyList_New(size);

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
        Py_SIZE(list) = newsize;

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
    Py_SIZE(list) = newsize;
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
    PyObject *list = PyList_New(0);

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
        Py_ssize_t iter_len = PyObject_Size(iterable);

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
