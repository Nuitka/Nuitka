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
/** Helpers for matching values with 3.10 or higher
 *
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static void FORMAT_MATCH_MISMATCH_ERROR(PyTypeObject *type, Py_ssize_t max_allowed, Py_ssize_t actual) {
    const char *plural_form = (max_allowed == 1) ? "" : "s";

    PyErr_Format(PyExc_TypeError, "%s() accepts %d positional sub-pattern%s (%d given)",
                 ((PyTypeObject *)type)->tp_name, max_allowed, plural_form, actual);
}

PyObject *MATCH_CLASS_ARGS(PyObject *matched, Py_ssize_t max_allowed) {
    PyObject *match_args = NULL;
    PyTypeObject *type = Py_TYPE(matched);

    // First, the positional sub-patterns:
    match_args = LOOKUP_ATTRIBUTE((PyObject *)type, const_str_plain___match_args__);
    Py_ssize_t actual;

    if (match_args) {
        if (unlikely(!PyTuple_CheckExact(match_args))) {
            PyErr_Format(PyExc_TypeError, "%s.__match_args__ must be a tuple (got %s)", type->tp_name,
                         Py_TYPE(match_args)->tp_name);
            Py_DECREF(match_args);
            return NULL;
        }

        actual = PyTuple_GET_SIZE(match_args);
    } else if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED()) {
        if (PyType_HasFeature(type, _Py_TPFLAGS_MATCH_SELF)) {
            if (max_allowed > 1) {
                FORMAT_MATCH_MISMATCH_ERROR(type, max_allowed, 1);
                return NULL;
            }

            // TODO: Specialize for single element maybe, but LTO solves
            // this just fine.
            PyObject *elements[1] = {matched};
            return MAKE_TUPLE(elements, 1);
        }

        actual = 0;
    } else {
        return NULL;
    }

    if (max_allowed > actual) {
        FORMAT_MATCH_MISMATCH_ERROR(type, max_allowed, actual);
        return NULL;
    }

    PyObject *result = MAKE_TUPLE_EMPTY_VAR(actual);

    for (Py_ssize_t i = 0; i < max_allowed; i++) {
        PyObject *arg_name = PyTuple_GET_ITEM(match_args, i);

        if (unlikely(!PyUnicode_CheckExact(arg_name))) {
            PyErr_Format(PyExc_TypeError,
                         "__match_args__ elements must be strings "
                         "(got %s)",
                         Py_TYPE(arg_name)->tp_name);

            Py_DECREF(match_args);
            Py_DECREF(result);

            return NULL;
        }

        PyObject *arg_value = LOOKUP_ATTRIBUTE(matched, arg_name);
        if (unlikely(arg_value == NULL)) {
            Py_DECREF(match_args);
            Py_DECREF(result);

            return NULL;
        }

        PyTuple_SET_ITEM(result, i, arg_value);
    }

    Py_DECREF(match_args);
    return result;
}