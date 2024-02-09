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
/* These helpers are used to work with tuples.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if NUITKA_TUPLE_HAS_FREELIST
static struct _Py_tuple_state *_Nuitka_Py_get_tuple_state(void) {
    PyInterpreterState *interp = _PyInterpreterState_GET();
    return &interp->tuple;
}

PyObject *MAKE_TUPLE_EMPTY(Py_ssize_t size) {
    PyTupleObject *result_tuple;

    // Lets not get called other than this
    assert(size > 0);

    struct _Py_tuple_state *state = _Nuitka_Py_get_tuple_state();

#if PYTHON_VERSION < 0x3b0
    Py_ssize_t index = size;
#else
    Py_ssize_t index = size - 1;
#endif

    if ((size < PyTuple_MAXSAVESIZE) && (result_tuple = state->free_list[index]) != NULL) {
        state->free_list[index] = (PyTupleObject *)result_tuple->ob_item[0];
        state->numfree[index] -= 1;

        assert(Py_SIZE(result_tuple) == size);
        assert(Py_TYPE(result_tuple) == &PyTuple_Type);

        Nuitka_Py_NewReference((PyObject *)result_tuple);
    } else {
        // Check for overflow
        if ((size_t)size >
            ((size_t)PY_SSIZE_T_MAX - (sizeof(PyTupleObject) - sizeof(PyObject *))) / sizeof(PyObject *)) {
            return PyErr_NoMemory();
        }

        result_tuple = (PyTupleObject *)Nuitka_GC_NewVar(&PyTuple_Type, size);
    }

    // TODO: Why not use memset here, and can we rely on memory being cleared
    // by allocator?

    // TODO: When first initializing the tuple, we might skip this and use
    // assignments that ignore this.
    for (Py_ssize_t i = 0; i < size; i++) {
        result_tuple->ob_item[i] = NULL;
    }

    Nuitka_GC_Track(result_tuple);

    assert(PyTuple_CheckExact(result_tuple));
    assert(PyTuple_GET_SIZE(result_tuple) == size);

    return (PyObject *)result_tuple;
}

PyObject *MAKE_TUPLE_EMPTY_VAR(Py_ssize_t size) {
    if (size == 0) {
        PyObject *result = const_tuple_empty;
        Py_INCREF(result);
        return result;
    } else {
        return MAKE_TUPLE_EMPTY(size);
    }
}

#endif

PyObject *TUPLE_CONCAT(PyObject *tuple1, PyObject *tuple2) {
    Py_ssize_t size = Py_SIZE(tuple1) + Py_SIZE(tuple2);

    // Do not ignore MemoryError, may actually happen.
    PyTupleObject *result = (PyTupleObject *)MAKE_TUPLE_EMPTY_VAR(size);
    if (unlikely(result == NULL)) {
        return NULL;
    }

    PyObject **src = ((PyTupleObject *)tuple1)->ob_item;
    PyObject **dest = result->ob_item;

    for (Py_ssize_t i = 0; i < Py_SIZE(tuple1); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }

    src = ((PyTupleObject *)tuple2)->ob_item;
    dest = result->ob_item + Py_SIZE(tuple1);

    for (Py_ssize_t i = 0; i < Py_SIZE(tuple2); i++) {
        PyObject *v = src[i];
        Py_INCREF(v);
        dest[i] = v;
    }

    return (PyObject *)result;
}

PyObject *TUPLE_COPY(PyObject *tuple) {
    CHECK_OBJECT(tuple);
    assert(PyTuple_CheckExact(tuple));

    Py_ssize_t size = PyTuple_GET_SIZE(tuple);
    PyObject *result = MAKE_TUPLE_EMPTY(size);

    if (unlikely(result == NULL)) {
        return NULL;
    }

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *item = PyTuple_GET_ITEM(tuple, i);
        Py_INCREF(item);
        PyList_SET_ITEM(result, i, item);
    }

    return result;
}
