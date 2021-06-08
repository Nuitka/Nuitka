//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_TUPLES_H__
#define __NUITKA_HELPER_TUPLES_H__

NUITKA_MAY_BE_UNUSED static PyObject *TUPLE_CONCAT(PyObject *t1, PyObject *t2) {
    Py_ssize_t size = Py_SIZE(t1) + Py_SIZE(t2);

    // Ignore MemoryError.
    if (unlikely(size < 0)) {
        return PyErr_NoMemory();
    }

    PyTupleObject *result = (PyTupleObject *)PyTuple_New(size);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    PyObject **src = ((PyTupleObject *)t1)->ob_item;
    PyObject **dest = result->ob_item;

    for (Py_ssize_t i = 0; i < Py_SIZE(t1); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }

    src = ((PyTupleObject *)t2)->ob_item;
    dest = result->ob_item + Py_SIZE(t1);
    for (Py_ssize_t i = 0; i < Py_SIZE(t2); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }

    return (PyObject *)result;
}

// Like PyTuple_SET_ITEM but takes a reference to the item.
#define PyTuple_SET_ITEM0(tuple, index, value)                                                                         \
    {                                                                                                                  \
        PyObject *tmp = value;                                                                                         \
        Py_INCREF(tmp);                                                                                                \
        PyTuple_SET_ITEM(tuple, index, tmp);                                                                           \
    }

#endif