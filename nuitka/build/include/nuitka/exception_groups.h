//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

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

// This is copied directly from CPython
NUITKA_MAY_BE_UNUSED static inline int EXCEPTION_GROUP_MATCH_BOOL(PyThreadState *tstate, PyObject *exc_value,
                                                                  PyObject *match_type, PyObject **match,
                                                                  PyObject **rest) {
    if (Py_IsNone(exc_value)) {
        Py_INCREF_IMMORTAL(Py_None) *match = Py_None;
        Py_INCREF_IMMORTAL(Py_None) *rest = Py_None;
        return 0;
    }
    assert(PyExceptionInstance_Check(exc_value));

    if (PyErr_GivenExceptionMatches(exc_value, match_type)) {
        /* Full match of exc itself */
        bool is_eg = _PyBaseExceptionGroup_Check(exc_value);
        if (is_eg) {
            *match = Py_NewRef(exc_value);
        } else {
            /* naked exception - wrap it */
            PyObject *excs = MAKE_TUPLE1(tstate, exc_value);
            if (excs == NULL) {
                return -1;
            }
            PyObject *wrapped = _PyExc_CreateExceptionGroup("", excs);
            Py_DECREF(excs);
            if (wrapped == NULL) {
                return -1;
            }
            /*
            PyFrameObject *f = _PyFrame_GetFrameObject(frame);
            if (f != NULL) {
                PyObject *tb = _PyTraceBack_FromFrame(NULL, f);
                if (tb == NULL) {
                    return -1;
                }
                PyException_SetTraceback(wrapped, tb);
                Py_DECREF(tb);
            }*/
            *match = wrapped;
        }
        Py_INCREF_IMMORTAL(Py_None) *rest = Py_None;
        return 0;
    }

    /* exc_value does not match match_type.
     * Check for partial match if it's an exception group.
     */
    if (_PyBaseExceptionGroup_Check(exc_value)) {
        PyObject *pair = PyObject_CallMethod(exc_value, "split", "(O)", match_type);
        if (pair == NULL) {
            return -1;
        }

        if (!PyTuple_CheckExact(pair)) {
            SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyExc_TypeError, "%.200s.split must return a tuple, not %.200s",
                                                Py_TYPE(exc_value)->tp_name, Py_TYPE(pair)->tp_name);
            Py_DECREF(pair);
            return -1;
        }

        // allow tuples of length > 2 for backwards compatibility
        if (PyTuple_GET_SIZE(pair) < 2) {
            PyErr_Format(PyExc_TypeError,
                         "%.200s.split must return a 2-tuple, "
                         "got tuple of size %zd",
                         Py_TYPE(exc_value)->tp_name, PyTuple_GET_SIZE(pair));
            Py_DECREF(pair);
            return -1;
        }

        *match = Py_NewRef(PyTuple_GET_ITEM(pair, 0));
        *rest = Py_NewRef(PyTuple_GET_ITEM(pair, 1));
        Py_DECREF(pair);
        return 0;
    }
    /* no match */
    Py_INCREF_IMMORTAL(Py_None) *match = Py_None;
    *rest = Py_NewRef(exc_value);
    return 0;
}

NUITKA_MAY_BE_UNUSED static inline PyObject *EXCEPTION_GROUP_MATCH(PyThreadState *tstate, PyObject *exc_value,
                                                                   PyObject *match_type) {
    CHECK_OBJECT(exc_value);
    CHECK_OBJECT(match_type);
    PyObject *match;
    PyObject *rest;
    if (EXCEPTION_GROUP_MATCH_BOOL(tstate, exc_value, match_type, &match, &rest) < 0) {
        return NULL;
    }

    CHECK_OBJECT(match);
    CHECK_OBJECT(rest);
    return MAKE_TUPLE2_0(tstate, match, rest);
}

#endif

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.gnu.org/licenses/agpl.txt
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
