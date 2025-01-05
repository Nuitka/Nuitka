//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* WARNING, this code is GENERATED. Modify the template CodeTemplateMakeListSmall.c.j2 instead! */

/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

PyObject *MAKE_LIST1(PyThreadState *tstate, PyObject *arg0) {

    PyObject *result = MAKE_LIST_EMPTY(tstate, 1);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(arg0);
    Py_INCREF(arg0);
    PyList_SET_ITEM(result, 0, arg0);

    return result;
}
PyObject *MAKE_LIST2(PyThreadState *tstate, PyObject *arg0, PyObject *arg1) {

    PyObject *result = MAKE_LIST_EMPTY(tstate, 2);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(arg0);
    Py_INCREF(arg0);
    PyList_SET_ITEM(result, 0, arg0);

    CHECK_OBJECT(arg1);
    Py_INCREF(arg1);
    PyList_SET_ITEM(result, 1, arg1);

    return result;
}
PyObject *MAKE_LIST3(PyThreadState *tstate, PyObject *arg0, PyObject *arg1, PyObject *arg2) {

    PyObject *result = MAKE_LIST_EMPTY(tstate, 3);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    CHECK_OBJECT(arg0);
    Py_INCREF(arg0);
    PyList_SET_ITEM(result, 0, arg0);

    CHECK_OBJECT(arg1);
    Py_INCREF(arg1);
    PyList_SET_ITEM(result, 1, arg1);

    CHECK_OBJECT(arg2);
    Py_INCREF(arg2);
    PyList_SET_ITEM(result, 2, arg2);

    return result;
}
PyObject *MAKE_LIST4(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 4);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 4);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }

    return result;
}
PyObject *MAKE_LIST5(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 5);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 5);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }

    return result;
}
PyObject *MAKE_LIST6(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 6);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 6);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 5);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 5, item);
    }

    return result;
}
PyObject *MAKE_LIST7(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 7);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 7);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 5);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 5, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 6);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 6, item);
    }

    return result;
}
PyObject *MAKE_LIST8(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 8);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 8);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 5);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 5, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 6);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 6, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 7);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 7, item);
    }

    return result;
}
PyObject *MAKE_LIST9(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 9);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 9);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 5);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 5, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 6);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 6, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 7);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 7, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 8);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 8, item);
    }

    return result;
}
PyObject *MAKE_LIST10(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 10);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 10);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 5);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 5, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 6);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 6, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 7);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 7, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 8);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 8, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 9);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 9, item);
    }

    return result;
}
PyObject *MAKE_LIST11(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 11);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 11);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 5);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 5, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 6);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 6, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 7);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 7, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 8);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 8, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 9);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 9, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 10);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 10, item);
    }

    return result;
}
PyObject *MAKE_LIST12(PyThreadState *tstate, PyObject *list) {
    CHECK_OBJECT(list);
    assert(PyList_CheckExact(list));
    assert(PyList_GET_SIZE(list) == 12);

    PyObject *result = MAKE_LIST_EMPTY(tstate, 12);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    {
        PyObject *item = PyList_GET_ITEM(list, 0);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 0, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 1);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 1, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 2);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 2, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 3);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 3, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 4);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 4, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 5);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 5, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 6);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 6, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 7);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 7, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 8);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 8, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 9);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 9, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 10);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 10, item);
    }
    {
        PyObject *item = PyList_GET_ITEM(list, 11);
        Py_INCREF(item);
        PyList_SET_ITEM(result, 11, item);
    }

    return result;
}

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
