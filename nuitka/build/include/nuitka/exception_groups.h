//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

#ifndef __NUITKA_EXCEPTION_GROUPS_H__
#define __NUITKA_EXCEPTION_GROUPS_H__

// Exception group helpers for generated code and compiled code helpers.

#if PYTHON_VERSION >= 0x3b0

NUITKA_MAY_BE_UNUSED static void FORMAT_CLASS_CATCH_ERROR(PyThreadState *tstate) {
    SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                    "catching classes that do not inherit from BaseException is not allowed");
}

NUITKA_MAY_BE_UNUSED static int CHECK_EXCEPTION_TYPE_VALID(PyThreadState *tstate, PyObject *right) {
    if (PyTuple_Check(right)) {
        Py_ssize_t length = PyTuple_GET_SIZE(right);

        for (Py_ssize_t i = 0; i < length; i++) {
            PyObject *exc = PyTuple_GET_ITEM(right, i);

            if (!PyExceptionClass_Check(exc)) {
                FORMAT_CLASS_CATCH_ERROR(tstate);
                return -1;
            }
        }
    } else {
        if (!PyExceptionClass_Check(right)) {
            FORMAT_CLASS_CATCH_ERROR(tstate);
            return -1;
        }
    }
    return 0;
}

NUITKA_MAY_BE_UNUSED static int CHECK_EXCEPTION_STAR_VALID(PyThreadState *tstate, PyObject *right) {
    if (CHECK_EXCEPTION_TYPE_VALID(tstate, right) < 0) {
        return -1;
    }

    // TODO: Wants to reject except *ExceptionGroup, but we would be able to
    // statically tell that often, and then this wouldn't have to be done,
    // but it might be code.
    int is_subclass = 0;

    if (PyTuple_Check(right)) {
        Py_ssize_t length = PyTuple_GET_SIZE(right);

        for (Py_ssize_t i = 0; i < length; i++) {
            PyObject *exc = PyTuple_GET_ITEM(right, i);
            is_subclass = PyObject_IsSubclass(exc, PyExc_BaseExceptionGroup);

            if (is_subclass < 0) {
                return -1;
            }

            if (is_subclass) {
                break;
            }
        }
    } else {
        is_subclass = PyObject_IsSubclass(right, PyExc_BaseExceptionGroup);

        if (is_subclass < 0) {
            return -1;
        }
    }

    if (is_subclass) {
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError,
                                        "catching ExceptionGroup with except* is not allowed. Use except instead.");
        return -1;
    }

    return 0;
}

NUITKA_MAY_BE_UNUSED static int EXCEPTION_GROUP_MATCH(PyThreadState *tstate, PyObject *exc_value, PyObject *match_type,
                                                      PyObject **match, PyObject **rest) {
    // TODO: Avoid this from happening, we should not call it then.
    if (exc_value == Py_None) {
        *match = Py_None;
        Py_INCREF_IMMORTAL(*match);
        *rest = Py_None;
        Py_INCREF_IMMORTAL(*rest);

        return 0;
    }

    // If not none, must be an instance at this point.
    assert(PyExceptionInstance_Check(exc_value));

    if (PyErr_GivenExceptionMatches(exc_value, match_type)) {
        bool is_exception_group = _PyBaseExceptionGroup_Check(exc_value);

        if (is_exception_group) {
            *match = exc_value;
            Py_INCREF(*match);
        } else {
            // Old style plain exception, put it into an exception group.
            PyObject *exception_tuple = MAKE_TUPLE1_0(tstate, exc_value);
            PyObject *wrapped = _PyExc_CreateExceptionGroup("", exception_tuple);
            Py_DECREF(exception_tuple);

            if (unlikely(wrapped == NULL)) {
                return -1;
            }

            *match = wrapped;
        }

        *rest = Py_None;
        Py_INCREF_IMMORTAL(*rest);

        return 0;
    }

    // exc_value does not match match_type completely, need to check for partial
    // match if it's an exception group.
    if (_PyBaseExceptionGroup_Check(exc_value)) {
        PyObject *pair = CALL_METHOD_WITH_SINGLE_ARG(tstate, exc_value, const_str_plain_split, match_type);

        if (pair == NULL) {
            return -1;
        }

        // TODO: What is that split method going to be, can we then inline it. CPython
        // asserts these, so maybe it's not free to do what it wants.
        assert(PyTuple_CheckExact(pair));
        assert(PyTuple_GET_SIZE(pair) == 2);

        *match = PyTuple_GET_ITEM(pair, 0);
        Py_INCREF(*match);

        *rest = PyTuple_GET_ITEM(pair, 1);
        Py_INCREF(*rest);

        Py_DECREF(pair);
        return 0;
    }

    *match = Py_None;
    Py_INCREF_IMMORTAL(*match);

    *rest = Py_None;
    Py_INCREF_IMMORTAL(*rest);

    return 0;
}

#endif

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
