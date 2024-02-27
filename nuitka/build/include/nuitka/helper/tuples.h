//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_HELPER_TUPLES_H__
#define __NUITKA_HELPER_TUPLES_H__

// Like PyTuple_SET_ITEM but takes a reference to the item.
#define PyTuple_SET_ITEM0(tuple, index, value)                                                                         \
    {                                                                                                                  \
        PyObject *tmp = value;                                                                                         \
        Py_INCREF(tmp);                                                                                                \
        PyTuple_SET_ITEM(tuple, index, tmp);                                                                           \
    }

#if PYTHON_VERSION >= 0x3a0
#define NUITKA_TUPLE_HAS_FREELIST 1
extern PyObject *MAKE_TUPLE_EMPTY(Py_ssize_t size);
extern PyObject *MAKE_TUPLE_EMPTY_VAR(Py_ssize_t size);
#else
#define NUITKA_TUPLE_HAS_FREELIST 0

#define MAKE_TUPLE_EMPTY(size) PyTuple_New(size)
#define MAKE_TUPLE_EMPTY_VAR(size) PyTuple_New(size)
#endif

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE(PyObject *const *elements, Py_ssize_t size) {
    PyObject *result = MAKE_TUPLE_EMPTY(size);

    for (Py_ssize_t i = 0; i < size; i++) {
        PyTuple_SET_ITEM0(result, i, elements[i]);
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE1(PyObject *element1) {
    PyObject *result = MAKE_TUPLE_EMPTY(1);

    PyTuple_SET_ITEM0(result, 0, element1);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE1_0(PyObject *element1) {
    PyObject *result = MAKE_TUPLE_EMPTY(1);

    PyTuple_SET_ITEM(result, 0, element1);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE2(PyObject *element1, PyObject *element2) {
    PyObject *result = MAKE_TUPLE_EMPTY(2);

    PyTuple_SET_ITEM0(result, 0, element1);
    PyTuple_SET_ITEM0(result, 1, element2);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE2_0(PyObject *element1, PyObject *element2) {
    PyObject *result = MAKE_TUPLE_EMPTY(2);

    PyTuple_SET_ITEM(result, 0, element1);
    PyTuple_SET_ITEM(result, 1, element2);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE3(PyObject *element1, PyObject *element2, PyObject *element3) {
    PyObject *result = MAKE_TUPLE_EMPTY(3);

    PyTuple_SET_ITEM0(result, 0, element1);
    PyTuple_SET_ITEM0(result, 1, element2);
    PyTuple_SET_ITEM0(result, 2, element3);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE3_0(PyObject *element1, PyObject *element2, PyObject *element3) {
    PyObject *result = MAKE_TUPLE_EMPTY(3);

    PyTuple_SET_ITEM(result, 0, element1);
    PyTuple_SET_ITEM(result, 1, element2);
    PyTuple_SET_ITEM(result, 2, element3);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE4(PyObject *element1, PyObject *element2, PyObject *element3,
                                                  PyObject *element4) {
    PyObject *result = MAKE_TUPLE_EMPTY(4);

    PyTuple_SET_ITEM0(result, 0, element1);
    PyTuple_SET_ITEM0(result, 1, element2);
    PyTuple_SET_ITEM0(result, 2, element3);
    PyTuple_SET_ITEM0(result, 3, element4);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE4_0(PyObject *element1, PyObject *element2, PyObject *element3,
                                                    PyObject *element4) {
    PyObject *result = MAKE_TUPLE_EMPTY(4);

    PyTuple_SET_ITEM(result, 0, element1);
    PyTuple_SET_ITEM(result, 1, element2);
    PyTuple_SET_ITEM(result, 2, element3);
    PyTuple_SET_ITEM(result, 3, element4);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE5(PyObject *element1, PyObject *element2, PyObject *element3,
                                                  PyObject *element4, PyObject *element5) {
    PyObject *result = MAKE_TUPLE_EMPTY(5);

    PyTuple_SET_ITEM0(result, 0, element1);
    PyTuple_SET_ITEM0(result, 1, element2);
    PyTuple_SET_ITEM0(result, 2, element3);
    PyTuple_SET_ITEM0(result, 3, element4);
    PyTuple_SET_ITEM0(result, 4, element5);

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_TUPLE5_0(PyObject *element1, PyObject *element2, PyObject *element3,
                                                    PyObject *element4, PyObject *element5) {
    PyObject *result = MAKE_TUPLE_EMPTY(5);

    PyTuple_SET_ITEM(result, 0, element1);
    PyTuple_SET_ITEM(result, 1, element2);
    PyTuple_SET_ITEM(result, 2, element3);
    PyTuple_SET_ITEM(result, 3, element4);
    PyTuple_SET_ITEM(result, 4, element5);

    return result;
}

// Make this new macro available for older Python too.
#ifndef _PyTuple_ITEMS
#define _PyTuple_ITEMS(op) (((PyTupleObject *)(op))->ob_item)
#endif

extern PyObject *TUPLE_CONCAT(PyObject *tuple1, PyObject *tuple2);

extern PyObject *TUPLE_COPY(PyObject *tuple);

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
