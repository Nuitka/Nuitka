//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/** For setting exceptions.
 *
 * These are non-inline variants for exception raises, done so to avoid the code bloat.
 *
 **/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

void SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyObject *exception_type, char const *format, char const *value) {
    PyErr_Format(exception_type, format, value);
}

void SET_CURRENT_EXCEPTION_TYPE0_FORMAT2(PyObject *exception_type, char const *format, char const *value1,
                                         char const *value2) {
    PyErr_Format(exception_type, format, value1, value2);
}

void SET_CURRENT_EXCEPTION_TYPE0_FORMAT3(PyObject *exception_type, char const *format, char const *value1,
                                         char const *value2, char const *value3) {
    PyErr_Format(exception_type, format, value1, value2, value3);
}

void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT(char const *format, PyObject *mistyped) {
    SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, format, Py_TYPE(mistyped)->tp_name);
}

static char const *TYPE_NAME_DESC(PyObject *type) {
    if (type == Py_None) {
        return "None";
    } else {
        return Py_TYPE(type)->tp_name;
    }
}

void SET_CURRENT_EXCEPTION_TYPE_COMPLAINT_NICE(char const *format, PyObject *mistyped) {
    SET_CURRENT_EXCEPTION_TYPE0_FORMAT1(PyExc_TypeError, format, TYPE_NAME_DESC(mistyped));
}

void FORMAT_UNBOUND_LOCAL_ERROR(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                PyObject *variable_name) {
#if PYTHON_VERSION < 0x300
    char const *message = "local variable '%s' referenced before assignment";
    PyObject *exception_value = Nuitka_String_FromFormat(message, Nuitka_String_AsString_Unchecked(variable_name));
#elif PYTHON_VERSION < 0x3b0
    char const *message = "local variable '%U' referenced before assignment";
    PyObject *exception_value = Nuitka_String_FromFormat(message, variable_name);
#else
    char const *message = "cannot access local variable '%U' where it is not associated with a value";
    PyObject *exception_value = Nuitka_String_FromFormat(message, variable_name);
#endif

    CHECK_OBJECT(exception_value);
    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, PyExc_UnboundLocalError,
                                                       exception_value);
}

void FORMAT_UNBOUND_CLOSURE_ERROR(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                  PyObject *variable_name) {
#if PYTHON_VERSION < 0x3b0
    char const *message = "free variable '%s' referenced before assignment in enclosing scope";
#else
    char const *message = "cannot access free variable '%s' where it is not associated with a value in enclosing scope";
#endif

    PyObject *exception_value = Nuitka_String_FromFormat(message, Nuitka_String_AsString_Unchecked(variable_name));
    CHECK_OBJECT(exception_value);

    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, PyExc_NameError, exception_value);
}

static PyObject *_Nuitka_Err_CreateException(PyThreadState *tstate, PyObject *exception_type, PyObject *value) {
    PyObject *exc;

    if (value == NULL || value == Py_None) {
        exc = CALL_FUNCTION_NO_ARGS(tstate, exception_type);
    } else if (PyTuple_Check(value)) {
        exc = CALL_FUNCTION_WITH_POS_ARGS(tstate, exception_type, value);
    } else {
        exc = CALL_FUNCTION_WITH_SINGLE_ARG(tstate, exception_type, value);
    }

    if (exc != NULL && !PyExceptionInstance_Check(exc)) {
        PyErr_Format(PyExc_TypeError,
                     "calling %s should have returned an instance of "
                     "BaseException, not %s",
                     GET_CALLABLE_NAME(exception_type), Py_TYPE(exc)->tp_name);
        Py_DECREF(exc);

        return NULL;
    }

    return exc;
}

PyObject *MAKE_EXCEPTION_WITH_VALUE(PyThreadState *tstate, PyObject *exception_type, PyObject *value) {
    return _Nuitka_Err_CreateException(tstate, exception_type, value);
}

// Our replacement for PyErr_NormalizeException, that however does not attempt
// to deal with recursion, i.e. exception during normalization, we just avoid
// the API call overhead in the normal case.

#if PYTHON_VERSION >= 0x3d0
// TODO: Merge with old branch for enhancements.
void Nuitka_Err_NormalizeException(PyThreadState *tstate, PyObject **exc, PyObject **val, PyTracebackObject **tb) {
    int recursion_depth = 0;
    tstate->recursion_headroom++;

    PyObject *type, *value;
    PyTracebackObject *initial_tb;

restart:
    type = *exc;

    if (type == NULL) {
        tstate->recursion_headroom--;
        return;
    }

    value = *val;

    if (!value) {
        Py_INCREF_IMMORTAL(Py_None);
        value = Py_None;
    }

    if (PyExceptionClass_Check(type)) {
        PyObject *instance_class = NULL;

        int is_subclass = 0;

        if (PyExceptionInstance_Check(value)) {
            instance_class = PyExceptionInstance_Class(value);

            is_subclass = PyObject_IsSubclass(instance_class, type);
            if (is_subclass < 0) {
                goto error;
            }
        }

        if (!is_subclass) {
            PyObject *fixed_value = _Nuitka_Err_CreateException(tstate, type, value);

            if (fixed_value == NULL) {
                goto error;
            }

            Py_SETREF(value, fixed_value);
        } else if (instance_class != type) {
            Py_SETREF(type, Py_NewRef(instance_class));
        }
    }
    *exc = type;
    *val = value;
    tstate->recursion_headroom--;
    return;

error:
    Py_DECREF(type);
    Py_DECREF(value);
    recursion_depth++;
    if (recursion_depth == 32) {
        _PyErr_SetString(tstate, PyExc_RecursionError,
                         "maximum recursion depth exceeded "
                         "while normalizing an exception");
    }

    initial_tb = *tb;

    struct Nuitka_ExceptionPreservationItem exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &exception_state);

    ASSIGN_ARGS_FROM_EXCEPTION_PRESERVATION_STATE(&exception_state, exc, val, tb);
    RELEASE_ERROR_OCCURRED_STATE(&exception_state);

    assert(*exc != NULL);
    if (initial_tb != NULL) {
        if (*tb == NULL)
            *tb = initial_tb;
        else
            Py_DECREF(initial_tb);
    }
    if (recursion_depth >= 32 + 2) {
        if (PyErr_GivenExceptionMatches(*exc, PyExc_MemoryError)) {
            Py_FatalError("Cannot recover from MemoryErrors "
                          "while normalizing exceptions.");
        } else {
            Py_FatalError("Cannot recover from the recursive normalization "
                          "of an exception.");
        }
    }
    goto restart;
}
#else
void Nuitka_Err_NormalizeException(PyThreadState *tstate, PyObject **exc, PyObject **val, PyTracebackObject **tb) {
    PyObject *type = *exc;

    // Dealt with in NORMALIZE_EXCEPTION
    assert(type != NULL && type != Py_None);

    PyObject *value = *val;

    // Allow setting the value to NULL for time savings with quick type only errors
    if (value == NULL) {
        value = Py_None;
        Py_INCREF_IMMORTAL(value);
    }

    // Normalize the exception from class to instance
    if (PyExceptionClass_Check(type)) {
        PyObject *instance_class = NULL;

        int is_subclass = 0;

        if (PyExceptionInstance_Check(value)) {
            instance_class = PyExceptionInstance_Class(value);

            is_subclass = PyObject_IsSubclass(instance_class, type);

            if (is_subclass < 0) {
                goto error;
            }
        }

        // If the value was not an instance, or is not an instance of derived
        // type, then call it
        if (!is_subclass) {
            PyObject *fixed_value = _Nuitka_Err_CreateException(tstate, type, value);

            if (unlikely(fixed_value == NULL)) {
                goto error;
            }

            Py_DECREF(value);
            value = fixed_value;
        } else if (instance_class != type) {
            // Switch to given type then
            Py_INCREF(instance_class);
            Py_DECREF(type);

            type = instance_class;
        }
    }

    *exc = type;
    *val = value;

    return;

error:

    Py_DECREF(type);
    Py_DECREF(value);
    PyTracebackObject *initial_tb = *tb;

    struct Nuitka_ExceptionPreservationItem exception_state;
    FETCH_ERROR_OCCURRED_STATE(tstate, &exception_state);

    ASSIGN_ARGS_FROM_EXCEPTION_PRESERVATION_STATE(&exception_state, exc, val, tb);
    RELEASE_ERROR_OCCURRED_STATE(&exception_state);

    if (initial_tb != NULL) {
        if (*tb == NULL) {
            *tb = initial_tb;
        } else {
            Py_DECREF(initial_tb);
        }
    }

#if PYTHON_VERSION >= 0x380
    _PyErr_NormalizeException(tstate, exc, val, (PyObject **)tb);
#else
    PyErr_NormalizeException(exc, val, (PyObject **)tb);
#endif
}

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
