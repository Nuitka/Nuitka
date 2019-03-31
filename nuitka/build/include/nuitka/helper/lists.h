//     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_LISTS_H__
#define __NUITKA_HELPER_LISTS_H__

NUITKA_MAY_BE_UNUSED static PyObject *LIST_COPY(PyObject *list) {
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

NUITKA_MAY_BE_UNUSED static bool LIST_RESIZE(PyListObject *list, Py_ssize_t newsize) {
    Py_ssize_t allocated = list->allocated;

    if (allocated >= newsize && newsize >= (allocated >> 1)) {
        Py_SIZE(list) = newsize;

        return true;
    }

    size_t new_allocated;

    if (newsize == 0) {
        new_allocated = 0;
    } else {
        new_allocated = (size_t)newsize + (newsize >> 3) + (newsize < 9 ? 3 : 6);
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

NUITKA_MAY_BE_UNUSED static bool LIST_EXTEND_FROM_LIST(PyObject *list, PyObject *other) {
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
}

NUITKA_MAY_BE_UNUSED static PyObject *LIST_CONCAT(PyObject *l1, PyObject *l2) {
    Py_ssize_t size = Py_SIZE(l1) + Py_SIZE(l2);

    // Ignore MemoryError.
    if (unlikely(size < 0)) {
        return PyErr_NoMemory();
    }

    PyListObject *result = (PyListObject *)PyList_New(size);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    PyObject **src = ((PyListObject *)l1)->ob_item;
    PyObject **dest = result->ob_item;

    for (Py_ssize_t i = 0; i < Py_SIZE(l1); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    src = ((PyListObject *)l2)->ob_item;
    dest = result->ob_item + Py_SIZE(l1);
    for (Py_ssize_t i = 0; i < Py_SIZE(l2); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }
    return (PyObject *)result;
}

#endif
