//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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

PyObject *MATCH_CLASS_ARGS(PyThreadState *tstate, PyObject *matched, PyObject *matched_type,
                           Py_ssize_t positional_count, PyObject **keywords, Py_ssize_t keywords_count) {
    PyObject *match_args = NULL;
    PyTypeObject *type = (PyTypeObject *)matched_type;

    PyObject *seen = NULL;
    bool needs_check = positional_count + keywords_count > 1;
    if (needs_check) {
        seen = PySet_New(NULL);
    }

    assert(positional_count + keywords_count > 0);

    // First, the positional sub-patterns if any.
    if (positional_count > 0) {
        match_args = LOOKUP_ATTRIBUTE(tstate, (PyObject *)type, const_str_plain___match_args__);
        Py_ssize_t actual;

        if (match_args) {
            if (unlikely(!PyTuple_CheckExact(match_args))) {
                PyErr_Format(PyExc_TypeError, "%s.__match_args__ must be a tuple (got %s)", type->tp_name,
                             Py_TYPE(match_args)->tp_name);
                Py_DECREF(match_args);
                return NULL;
            }

            actual = PyTuple_GET_SIZE(match_args);
        } else if (CHECK_AND_CLEAR_ATTRIBUTE_ERROR_OCCURRED(tstate)) {
            if (PyType_HasFeature(type, _Py_TPFLAGS_MATCH_SELF)) {
                if (positional_count > 1) {
                    FORMAT_MATCH_MISMATCH_ERROR(type, positional_count, 1);
                    return NULL;
                }

                assert(keywords_count == 0);

                return MAKE_TUPLE1(tstate, matched);
            }

            actual = 0;
        } else {
            return NULL;
        }

        if (positional_count > actual) {
            FORMAT_MATCH_MISMATCH_ERROR(type, positional_count, actual);
            return NULL;
        }
    }

    PyObject *result = MAKE_TUPLE_EMPTY_VAR(tstate, positional_count + keywords_count);

    for (Py_ssize_t i = 0; i < positional_count; i++) {
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

        if (needs_check) {
            if (i != 0 && PySet_Contains(seen, arg_name)) {
                _PyErr_Format(tstate, PyExc_TypeError, "%s() got multiple sub-patterns for attribute %R",
                              ((PyTypeObject *)type)->tp_name, arg_name);

                return NULL;
            }

            PySet_Add(seen, arg_name);
        }

        PyObject *arg_value = LOOKUP_ATTRIBUTE(tstate, matched, arg_name);
        if (unlikely(arg_value == NULL)) {
            DROP_ERROR_OCCURRED(tstate);

            Py_DECREF(match_args);
            Py_DECREF(result);

            Py_INCREF_IMMORTAL(Py_None);
            return Py_None;
        }

        PyTuple_SET_ITEM(result, i, arg_value);
    }

    for (Py_ssize_t i = 0; i < keywords_count; i++) {
        PyObject *arg_name = keywords[i];
        CHECK_OBJECT(arg_name);
        assert(PyUnicode_CheckExact(arg_name));

        if (needs_check) {
            if (PySet_Contains(seen, arg_name)) {
                _PyErr_Format(tstate, PyExc_TypeError, "%s() got multiple sub-patterns for attribute %R",
                              ((PyTypeObject *)type)->tp_name, arg_name);

                return NULL;
            }

            PySet_Add(seen, arg_name);
        }

        PyObject *arg_value = LOOKUP_ATTRIBUTE(tstate, matched, arg_name);
        if (unlikely(arg_value == NULL)) {
            DROP_ERROR_OCCURRED(tstate);

            Py_XDECREF(match_args);
            Py_DECREF(result);

            Py_INCREF_IMMORTAL(Py_None);
            return Py_None;
        }

        PyTuple_SET_ITEM(result, positional_count + i, arg_value);
    }

    Py_XDECREF(match_args);
    return result;
}

bool MATCH_MAPPING_KEY(PyThreadState *tstate, PyObject *map, PyObject *key) {
    // Need to use get_method with default value, so "defaultdict" do not
    // mutate. TODO: Use a cached value across the "match".
    // spell-checker: ignore defaultdict
    PyObject *get_method = LOOKUP_ATTRIBUTE(tstate, map, const_str_plain_get);
    if (unlikely(get_method == NULL)) {
        // TODO: Maybe only drop AttributeError?
        DROP_ERROR_OCCURRED(tstate);
        return false;
    }

    PyObject *args[] = {key, Nuitka_sentinel_value};

    PyObject *value = CALL_FUNCTION_WITH_ARGS2(tstate, get_method, args);

    Py_XDECREF(get_method);

    if (unlikely(value == NULL)) {
        return false;
    }

    if (value == Nuitka_sentinel_value) {
        Py_DECREF_IMMORTAL(value);

        return false;
    }

    Py_DECREF(value);

    return true;
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
