//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* This helpers is used to work with lists.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static void FORMAT_TYPE_ERROR1(PyObject **exception_type, PyObject **exception_value, char const *format,
                               char const *arg) {
    *exception_type = PyExc_TypeError;
    Py_INCREF(*exception_type);

    *exception_value = Nuitka_String_FromFormat(format, arg);
    CHECK_OBJECT(*exception_value);
}

#if PYTHON_VERSION >= 0x270
static void FORMAT_TYPE_ERROR2(PyObject **exception_type, PyObject **exception_value, char const *format,
                               char const *arg1, char const *arg2) {
    *exception_type = PyExc_TypeError;
    Py_INCREF(*exception_type);

    *exception_value = Nuitka_String_FromFormat(format, arg1, arg2);
    CHECK_OBJECT(*exception_value);
}
#endif

#if PYTHON_VERSION < 0x266
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must be classes or instances, not %s"
#elif PYTHON_VERSION < 0x300
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must be old-style classes or derived from BaseException, not %s"
#else
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must derive from BaseException"
#endif

void RAISE_EXCEPTION_WITH_TYPE(PyThreadState *tstate, PyObject **exception_type, PyObject **exception_value,
                               PyTracebackObject **exception_tb) {
    *exception_value = NULL;
    *exception_tb = NULL;

#if PYTHON_VERSION < 0x300
    // Next, repeatedly, replace a tuple exception with its first item
    while (PyTuple_Check(*exception_type) && PyTuple_GET_SIZE(*exception_type) > 0) {
        PyObject *tmp = *exception_type;
        *exception_type = PyTuple_GET_ITEM(*exception_type, 0);
        Py_INCREF(*exception_type);
        Py_DECREF(tmp);
    }
#endif

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(tstate, exception_type, exception_value, exception_tb);
#if PYTHON_VERSION >= 0x270
        // TODO: It seems NORMALIZE_EXCEPTION already does this?
        if (unlikely(!PyExceptionInstance_Check(*exception_value))) {
            assert(false);

            PyObject *old_exception_type = *exception_type;
            PyObject *old_exception_value = *exception_value;

            FORMAT_TYPE_ERROR2(exception_type, exception_value,
                               "calling %s() should have returned an instance of BaseException, not '%s'",
                               Py_TYPE(*exception_type)->tp_name, Py_TYPE(*exception_value)->tp_name);

            Py_DECREF(old_exception_type);
            Py_DECREF(old_exception_value);

            return;
        }
#endif

#if PYTHON_VERSION >= 0x300
        CHAIN_EXCEPTION(tstate, *exception_value);
#endif
        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);

#if PYTHON_VERSION >= 0x300
        CHAIN_EXCEPTION(tstate, *exception_value);

        // Note: Cannot be assigned here.
        assert(*exception_tb == NULL);
        *exception_tb = GET_EXCEPTION_TRACEBACK(*exception_value);
        Py_XINCREF(*exception_tb);
#endif

        return;
    } else {
        PyObject *old_exception_type = *exception_type;

        FORMAT_TYPE_ERROR1(exception_type, exception_value, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(*exception_type)->tp_name);

        Py_DECREF(old_exception_type);

        return;
    }
}

#if PYTHON_VERSION >= 0x300
void RAISE_EXCEPTION_WITH_CAUSE(PyThreadState *tstate, PyObject **exception_type, PyObject **exception_value,
                                PyTracebackObject **exception_tb, PyObject *exception_cause) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(exception_cause);
    *exception_tb = NULL;

    // None is not a cause.
    if (exception_cause == Py_None) {
        Py_DECREF_IMMORTAL(exception_cause);
        exception_cause = NULL;
    } else if (PyExceptionClass_Check(exception_cause)) {
        PyObject *old_exception_cause = exception_cause;
        exception_cause = PyObject_CallObject(exception_cause, NULL);
        Py_DECREF(old_exception_cause);

        if (unlikely(exception_cause == NULL)) {
            Py_DECREF(*exception_type);
            Py_XDECREF(*exception_tb);

            struct Nuitka_ExceptionPreservationItem exception_state;
            FETCH_ERROR_OCCURRED_STATE(tstate, &exception_state);

            ASSIGN_ARGS_FROM_EXCEPTION_PRESERVATION_STATE(&exception_state, exception_type, exception_value,
                                                          exception_tb);
            RELEASE_ERROR_OCCURRED_STATE(&exception_state);

            return;
        }
    }

    if (unlikely(exception_cause != NULL && !PyExceptionInstance_Check(exception_cause))) {
        Py_DECREF(*exception_type);
        Py_XDECREF(*exception_tb);

        PyObject *old_exception_cause = exception_cause;

#ifdef _NUITKA_FULL_COMPAT
        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_TypeError, "exception causes must derive from BaseException");
        FETCH_ERROR_OCCURRED(tstate, exception_type, exception_value, exception_tb);
#else
        FORMAT_TYPE_ERROR1(exception_type, exception_value,
                           "exception causes must derive from BaseException (%s does not)",
                           Py_TYPE(exception_cause)->tp_name);
#endif

        Py_XDECREF(old_exception_cause);
        return;
    }

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(tstate, exception_type, exception_value, exception_tb);

        if (unlikely(!PyExceptionInstance_Check(*exception_value))) {
            Py_DECREF(*exception_tb);
            Py_XDECREF(exception_cause);

            PyObject *old_exception_type = *exception_type;
            PyObject *old_exception_value = *exception_value;

            FORMAT_TYPE_ERROR2(exception_type, exception_value,
                               "calling %s() should have returned an instance of BaseException, not '%s'",
                               Py_TYPE(*exception_type)->tp_name, Py_TYPE(*exception_value)->tp_name);

            Py_DECREF(old_exception_type);
            Py_XDECREF(old_exception_value);

            return;
        }

        PyException_SetCause(*exception_value, exception_cause);

        CHAIN_EXCEPTION(tstate, *exception_value);
        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);

        PyException_SetCause(*exception_value, exception_cause);

        CHAIN_EXCEPTION(tstate, *exception_value);
        return;
    } else {
        Py_XDECREF(exception_cause);

        PyObject *old_exception_type = *exception_type;

        FORMAT_TYPE_ERROR1(exception_type, exception_value, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(*exception_type)->tp_name);

        Py_DECREF(old_exception_type);

        return;
    }
}
#endif

void RAISE_EXCEPTION_WITH_VALUE(PyThreadState *tstate, PyObject **exception_type, PyObject **exception_value,
                                PyTracebackObject **exception_tb) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(*exception_value);
    *exception_tb = NULL;

    // Non-empty tuple exceptions are the first element.
    while (unlikely(PyTuple_Check(*exception_type) && PyTuple_GET_SIZE(*exception_type) > 0)) {
        *exception_type = PyTuple_GET_ITEM(*exception_type, 0);
    }

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(tstate, exception_type, exception_value, exception_tb);
#if PYTHON_VERSION >= 0x270
        if (unlikely(!PyExceptionInstance_Check(*exception_value))) {
            PyObject *old_exception_type = *exception_type;
            PyObject *old_exception_value = *exception_type;

            FORMAT_TYPE_ERROR2(exception_type, exception_value,
                               "calling %s() should have returned an instance of BaseException, not '%s'",
                               Py_TYPE(*exception_type)->tp_name, Py_TYPE(*exception_value)->tp_name);

            Py_DECREF(old_exception_type);
            Py_DECREF(old_exception_value);
        }
#endif

        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
        if (unlikely(*exception_value != NULL && *exception_value != Py_None)) {
            Py_DECREF(*exception_type);
            Py_DECREF(*exception_value);

            *exception_type = PyExc_TypeError;
            Py_INCREF(PyExc_TypeError);
            *exception_value = Nuitka_String_FromString("instance exception may not have a separate value");

            return;
        }

        // The type is rather a value, so we are overriding it here.
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);

        return;
    } else {
        PyObject *old_exception_type = *exception_type;

        FORMAT_TYPE_ERROR1(exception_type, exception_value, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(*exception_type)->tp_name);

        Py_DECREF(old_exception_type);

        return;
    }
}

void RAISE_EXCEPTION_IMPLICIT(PyThreadState *tstate, PyObject **exception_type, PyObject **exception_value,
                              PyTracebackObject **exception_tb) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(*exception_value);
    *exception_tb = NULL;

    // Non-empty tuple exceptions are the first element.
    while (unlikely(PyTuple_Check(*exception_type) && PyTuple_GET_SIZE(*exception_type) > 0)) {
        *exception_type = PyTuple_GET_ITEM(*exception_type, 0);
    }

    if (PyExceptionClass_Check(*exception_type)) {
#if PYTHON_VERSION >= 0x340
        NORMALIZE_EXCEPTION(tstate, exception_type, exception_value, exception_tb);
        CHAIN_EXCEPTION(tstate, *exception_value);
#endif

        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
#if PYTHON_VERSION >= 0x340
        CHAIN_EXCEPTION(tstate, *exception_value);
#endif

        // The type is rather a value, so we are overriding it here.
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);

        return;
    } else {
        PyObject *old_exception_type = *exception_type;
        Py_DECREF(*exception_value);

        FORMAT_TYPE_ERROR1(exception_type, exception_value, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(*exception_type)->tp_name);

        Py_DECREF(old_exception_type);

#if PYTHON_VERSION >= 0x340
        CHAIN_EXCEPTION(tstate, *exception_value);
#endif

        return;
    }
}

void RAISE_EXCEPTION_WITH_TRACEBACK(PyThreadState *tstate, PyObject **exception_type, PyObject **exception_value,
                                    PyTracebackObject **exception_tb) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(*exception_value);

    if (*exception_tb == (PyTracebackObject *)Py_None) {
        Py_DECREF_IMMORTAL(*exception_tb);
        *exception_tb = NULL;
    }

    // Non-empty tuple exceptions are the first element.
    while (unlikely(PyTuple_Check(*exception_type) && PyTuple_GET_SIZE(*exception_type) > 0)) {
        *exception_type = PyTuple_GET_ITEM(*exception_type, 0);
    }

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(tstate, exception_type, exception_value, exception_tb);
#if PYTHON_VERSION >= 0x270
        if (unlikely(!PyExceptionInstance_Check(*exception_value))) {
            PyObject *old_exception_type = *exception_type;
            PyObject *old_exception_value = *exception_value;

            FORMAT_TYPE_ERROR2(exception_type, exception_value,
                               "calling %s() should have returned an instance of BaseException, not '%s'",
                               Py_TYPE(*exception_type)->tp_name, Py_TYPE(*exception_value)->tp_name);

            Py_DECREF(old_exception_type);
            Py_DECREF(old_exception_value);
        }
#endif

        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
        if (unlikely(*exception_value != NULL && *exception_value != Py_None)) {
            Py_DECREF(*exception_type);
            Py_XDECREF(*exception_value);
            Py_XDECREF(*exception_tb);

            *exception_type = PyExc_TypeError;
            Py_INCREF(PyExc_TypeError);
            *exception_value = Nuitka_String_FromString("instance exception may not have a separate value");

            return;
        }

        // The type is rather a value, so we are overriding it here.
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);

        return;
    } else {
        PyObject *old_exception_type = *exception_type;

        FORMAT_TYPE_ERROR1(exception_type, exception_value, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(*exception_type)->tp_name);

        Py_DECREF(old_exception_type);

        return;
    }
}

bool RERAISE_EXCEPTION(PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb) {
    PyThreadState *tstate = PyThreadState_GET();
    assert(tstate);

#if PYTHON_VERSION < 0x3b0
    *exception_type = EXC_TYPE(tstate) != NULL ? EXC_TYPE(tstate) : Py_None;
    Py_INCREF(*exception_type);
    *exception_value = EXC_VALUE(tstate);
    Py_XINCREF(*exception_value);
    *exception_tb = (PyTracebackObject *)EXC_TRACEBACK(tstate);
    Py_XINCREF(*exception_tb);

    if (unlikely(*exception_type == Py_None)) {
#if PYTHON_VERSION >= 0x300
        Py_DECREF(*exception_type);

        Py_INCREF(PyExc_RuntimeError);
        *exception_type = PyExc_RuntimeError;
        *exception_value = PyUnicode_FromString("No active exception to reraise");
        *exception_tb = NULL;
#else
        PyObject *old_exception_type = *exception_type;

        FORMAT_TYPE_ERROR1(exception_type, exception_value, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(*exception_type)->tp_name);

        Py_DECREF(old_exception_type);
#endif

        return false;
    }
#else
    *exception_value = EXC_VALUE(tstate);

    if (*exception_value == Py_None || *exception_value == NULL) {
        Py_INCREF(PyExc_RuntimeError);
        *exception_type = PyExc_RuntimeError;
        *exception_value = PyUnicode_FromString("No active exception to reraise");
        *exception_tb = NULL;

        return false;
    } else {
        Py_INCREF(*exception_value);

        *exception_type = PyExceptionInstance_Class(*exception_value);
        Py_INCREF(*exception_type);
        *exception_tb = GET_EXCEPTION_TRACEBACK(*exception_value);
        Py_XINCREF(*exception_tb);
    }
#endif

    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(*exception_value);
    CHECK_OBJECT_X(*exception_tb);

    return true;
}

// Raise NameError for a given variable name.
void RAISE_CURRENT_EXCEPTION_NAME_ERROR(PyThreadState *tstate, PyObject *variable_name, PyObject **exception_type,
                                        PyObject **exception_value) {
#if PYTHON_VERSION < 0x300
    PyObject *exception_value_str =
        Nuitka_String_FromFormat("name '%s' is not defined", Nuitka_String_AsString_Unchecked(variable_name));
#else
    PyObject *exception_value_str = Nuitka_String_FromFormat("name '%U' is not defined", variable_name);
#endif

    *exception_value = MAKE_EXCEPTION_FROM_TYPE_ARG0(tstate, PyExc_NameError, exception_value_str);
    Py_DECREF(exception_value_str);

    *exception_type = PyExc_NameError;
    Py_INCREF(PyExc_NameError);

#if PYTHON_VERSION >= 0x300
    CHAIN_EXCEPTION(tstate, *exception_value);
#endif
}

#if PYTHON_VERSION < 0x340
void RAISE_CURRENT_EXCEPTION_GLOBAL_NAME_ERROR(PyThreadState *tstate, PyObject *variable_name,
                                               PyObject **exception_type, PyObject **exception_value) {
#if PYTHON_VERSION < 0x300
    PyObject *exception_value_str =
        Nuitka_String_FromFormat("global name '%s' is not defined", Nuitka_String_AsString_Unchecked(variable_name));
#else
    PyObject *exception_value_str = Nuitka_String_FromFormat("global name '%U' is not defined", variable_name);
#endif
    *exception_value = MAKE_EXCEPTION_FROM_TYPE_ARG0(tstate, PyExc_NameError, exception_value_str);
    Py_DECREF(exception_value_str);

    *exception_type = PyExc_NameError;
    Py_INCREF(PyExc_NameError);
}
#endif

#if PYTHON_VERSION >= 0x300

void RAISE_EXCEPTION_WITH_CAUSE_STATE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                      PyObject *exception_cause) {
#if PYTHON_VERSION < 0x3c0
    RAISE_EXCEPTION_WITH_CAUSE(tstate, &exception_state->exception_type, &exception_state->exception_value,
                               &exception_state->exception_tb, exception_cause);
#else
    PyObject *exception_type = (PyObject *)PyExceptionInstance_Class(exception_state->exception_value);
    Py_INCREF(exception_type);
    PyTracebackObject *exception_tb = NULL;

    // Python3.12: We are being a bit lazy there, by preparing the 3 things when
    // we shouldn't really need them.
    RAISE_EXCEPTION_WITH_CAUSE(tstate, &exception_type, &exception_state->exception_value, &exception_tb,
                               exception_cause);

    Py_DECREF(exception_type);
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
