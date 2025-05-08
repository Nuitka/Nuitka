//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

/* This helpers is used to work with lists.

*/

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

static void FORMAT_TYPE_ERROR1(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                               char const *format, char const *arg) {
    PyObject *exception_value = Nuitka_String_FromFormat(format, arg);
    CHECK_OBJECT(exception_value);

    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, PyExc_TypeError, exception_value);
}

static void FORMAT_TYPE_ERROR2(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                               char const *format, char const *arg1, char const *arg2) {
    PyObject *exception_value = Nuitka_String_FromFormat(format, arg1, arg2);
    CHECK_OBJECT(exception_value);

    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1(tstate, exception_state, PyExc_TypeError, exception_value);
}

#if PYTHON_VERSION < 0x266
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must be classes or instances, not %s"
#elif PYTHON_VERSION < 0x300
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must be old-style classes or derived from BaseException, not %s"
#else
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must derive from BaseException"
#endif

// Next, replace a tuple in exception type creation with its first item
#if PYTHON_VERSION < 0x3c0
static void UNPACK_TUPLE_EXCEPTION_TYPE(struct Nuitka_ExceptionPreservationItem *exception_state) {
    while (unlikely(PyTuple_Check(exception_state->exception_type)) &&
           PyTuple_GET_SIZE(exception_state->exception_type) > 0) {
        PyObject *tmp = exception_state->exception_type;
        exception_state->exception_type = PyTuple_GET_ITEM(exception_state->exception_type, 0);
        Py_INCREF(exception_state->exception_type);
        Py_DECREF(tmp);
    }
}
#endif

#if PYTHON_VERSION < 0x3c0
void RAISE_EXCEPTION_WITH_TYPE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    exception_state->exception_value = NULL;
    exception_state->exception_tb = NULL;

#if PYTHON_VERSION < 0x300
    // Next, repeatedly, replace a tuple exception with its first item
    UNPACK_TUPLE_EXCEPTION_TYPE(exception_state);
#endif

    if (PyExceptionClass_Check(exception_state->exception_type)) {
        NORMALIZE_EXCEPTION(tstate, &exception_state->exception_type, &exception_state->exception_value,
                            &exception_state->exception_tb);

#if PYTHON_VERSION >= 0x300
        CHAIN_EXCEPTION(tstate, exception_state->exception_value);
#endif
        return;
    } else if (PyExceptionInstance_Check(exception_state->exception_type)) {
        exception_state->exception_value = exception_state->exception_type;
        exception_state->exception_type = PyExceptionInstance_Class(exception_state->exception_type);
        Py_INCREF(exception_state->exception_type);

#if PYTHON_VERSION >= 0x300
        CHAIN_EXCEPTION(tstate, exception_state->exception_value);

        // Note: Cannot be assigned here.
        assert(exception_state->exception_tb == NULL);
        exception_state->exception_tb = GET_EXCEPTION_TRACEBACK(exception_state->exception_value);
        Py_XINCREF(exception_state->exception_tb);
#endif

        return;
    } else {
        PyObject *old_exception_type = exception_state->exception_type;

        FORMAT_TYPE_ERROR1(tstate, exception_state, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(exception_state->exception_type)->tp_name);

        Py_DECREF(old_exception_type);

        return;
    }
}

void RAISE_EXCEPTION_WITH_TYPE_AND_VALUE(PyThreadState *tstate,
                                         struct Nuitka_ExceptionPreservationItem *exception_state) {
    CHECK_EXCEPTION_STATE(exception_state);

    exception_state->exception_tb = NULL;

    // Non-empty tuple exceptions are the first element.
    UNPACK_TUPLE_EXCEPTION_TYPE(exception_state);

    if (PyExceptionClass_Check(exception_state->exception_type)) {
        NORMALIZE_EXCEPTION_STATE(tstate, exception_state);
#if PYTHON_VERSION >= 0x270
        if (unlikely(!PyExceptionInstance_Check(exception_state->exception_value))) {
            char const *exception_type_type = Py_TYPE(exception_state->exception_type)->tp_name;
            char const *exception_value_type = Py_TYPE(exception_state->exception_value)->tp_name;

            RELEASE_ERROR_OCCURRED_STATE(exception_state);

            FORMAT_TYPE_ERROR2(tstate, exception_state,
                               "calling %s() should have returned an instance of BaseException, not '%s'",
                               exception_type_type, exception_value_type);
        }
#endif

        return;
    } else if (PyExceptionInstance_Check(exception_state->exception_type)) {
        if (unlikely(exception_state->exception_value != NULL && exception_state->exception_value != Py_None)) {
            RELEASE_ERROR_OCCURRED_STATE(exception_state);
            SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, exception_state, PyExc_TypeError,
                                                            "instance exception may not have a separate value");

            return;
        }

        // The type is rather a value, so we are overriding it here.
        exception_state->exception_value = exception_state->exception_type;
        exception_state->exception_type = PyExceptionInstance_Class(exception_state->exception_type);
        Py_INCREF(exception_state->exception_type);

        return;
    } else {
        char const *exception_type_type = Py_TYPE(exception_state->exception_type)->tp_name;

        RELEASE_ERROR_OCCURRED_STATE(exception_state);

        FORMAT_TYPE_ERROR1(tstate, exception_state, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, exception_type_type);

        return;
    }
}

#else

void RAISE_EXCEPTION_WITH_VALUE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    ASSERT_NORMALIZED_EXCEPTION_VALUE(exception_state->exception_value);

    CHAIN_EXCEPTION(tstate, exception_state->exception_value);
}
#endif

#if PYTHON_VERSION >= 0x300
void RAISE_EXCEPTION_WITH_CAUSE(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                PyObject *exception_cause) {
    CHECK_EXCEPTION_STATE(exception_state);
    CHECK_OBJECT(exception_cause);

#if PYTHON_VERSION < 0x3c0
    exception_state->exception_tb = NULL;
#endif

    // None is not a cause.
    if (exception_cause == Py_None) {
        Py_DECREF_IMMORTAL(exception_cause);
        exception_cause = NULL;
    } else if (PyExceptionClass_Check(exception_cause)) {
        PyObject *old_exception_cause = exception_cause;
        exception_cause = CALL_FUNCTION_NO_ARGS(tstate, exception_cause);
        Py_DECREF(old_exception_cause);

        if (unlikely(exception_cause == NULL)) {
            RELEASE_ERROR_OCCURRED_STATE(exception_state);
            FETCH_ERROR_OCCURRED_STATE(tstate, exception_state);

            return;
        }
    }

    if (unlikely(exception_cause != NULL && !PyExceptionInstance_Check(exception_cause))) {
        RELEASE_ERROR_OCCURRED_STATE(exception_state);

#ifdef _NUITKA_FULL_COMPAT
        SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, exception_state, PyExc_TypeError,
                                                        "exception causes must derive from BaseException");
#else
        FORMAT_TYPE_ERROR1(tstate, exception_state, "exception causes must derive from BaseException (%s does not)",
                           Py_TYPE(exception_cause)->tp_name);
#endif

        return;
    }

#if PYTHON_VERSION < 0x3c0
    if (PyExceptionClass_Check(exception_state->exception_type)) {
        char const *exception_type_type = Py_TYPE(exception_state->exception_type)->tp_name;

        NORMALIZE_EXCEPTION_STATE(tstate, exception_state);

        if (unlikely(!PyExceptionInstance_Check(exception_state->exception_value))) {
            Py_XDECREF(exception_cause);

            char const *exception_value_type = Py_TYPE(exception_state->exception_value)->tp_name;

            RELEASE_ERROR_OCCURRED_STATE(exception_state);

            FORMAT_TYPE_ERROR2(tstate, exception_state,
                               "calling %s() should have returned an instance of BaseException, not '%s'",
                               exception_type_type, exception_value_type);

            return;
        }

        Nuitka_Exception_SetCause(exception_state->exception_value, exception_cause);
        CHAIN_EXCEPTION(tstate, exception_state->exception_value);
    } else if (PyExceptionInstance_Check(exception_state->exception_type)) {
        exception_state->exception_value = exception_state->exception_type;
        exception_state->exception_type = PyExceptionInstance_Class(exception_state->exception_type);
        Py_INCREF(exception_state->exception_type);

        Nuitka_Exception_SetCause(exception_state->exception_value, exception_cause);
        CHAIN_EXCEPTION(tstate, exception_state->exception_value);
    } else {
        Py_XDECREF(exception_cause);

        char const *exception_type_type = Py_TYPE(exception_state->exception_type)->tp_name;

        RELEASE_ERROR_OCCURRED_STATE(exception_state);

        FORMAT_TYPE_ERROR1(tstate, exception_state, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, exception_type_type);
    }
#else
    ASSERT_NORMALIZED_EXCEPTION_VALUE(exception_state->exception_value);

    Nuitka_Exception_SetCause(exception_state->exception_value, exception_cause);
    CHAIN_EXCEPTION(tstate, exception_state->exception_value);
#endif
}
#endif

#if PYTHON_VERSION < 0x300
void RAISE_EXCEPTION_WITH_TRACEBACK(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
    if (exception_state->exception_tb == (PyTracebackObject *)Py_None) {
        Py_DECREF_IMMORTAL(exception_state->exception_tb);
        exception_state->exception_tb = NULL;
    }

    // Non-empty tuple exceptions are the first element.
    UNPACK_TUPLE_EXCEPTION_TYPE(exception_state);

    if (PyExceptionClass_Check(exception_state->exception_type)) {
        NORMALIZE_EXCEPTION_STATE(tstate, exception_state);
#if PYTHON_VERSION >= 0x270
        if (unlikely(!PyExceptionInstance_Check(exception_state->exception_value))) {
            char const *exception_type_type = Py_TYPE(exception_state->exception_type)->tp_name;
            char const *exception_value_type = Py_TYPE(exception_state->exception_value)->tp_name;

            RELEASE_ERROR_OCCURRED_STATE(exception_state);

            // TODO: It would be even more safe to create the format value
            // before releasing the value.
            FORMAT_TYPE_ERROR2(tstate, exception_state,
                               "calling %s() should have returned an instance of BaseException, not '%s'",
                               exception_type_type, exception_value_type);
        }
#endif

        return;
    } else if (PyExceptionInstance_Check(exception_state->exception_type)) {
        if (unlikely(exception_state->exception_value != NULL && exception_state->exception_value != Py_None)) {
            RELEASE_ERROR_OCCURRED_STATE(exception_state);
            SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, exception_state, PyExc_TypeError,
                                                            "instance exception may not have a separate value");

            return;
        }

        // The type is rather a value, so we are overriding it here.
        exception_state->exception_value = exception_state->exception_type;
        exception_state->exception_type = PyExceptionInstance_Class(exception_state->exception_type);
        Py_INCREF(exception_state->exception_type);

        return;
    } else {
        FORMAT_TYPE_ERROR1(tstate, exception_state, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                           Py_TYPE(exception_state->exception_type)->tp_name);

        return;
    }
}
#endif

bool RERAISE_EXCEPTION(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state) {
#if PYTHON_VERSION < 0x3b0
    exception_state->exception_type = EXC_TYPE(tstate) != NULL ? EXC_TYPE(tstate) : Py_None;
    Py_INCREF(exception_state->exception_type);
    exception_state->exception_value = EXC_VALUE(tstate);
    Py_XINCREF(exception_state->exception_value);
    exception_state->exception_tb = (PyTracebackObject *)EXC_TRACEBACK(tstate);
    Py_XINCREF(exception_state->exception_tb);

    if (unlikely(exception_state->exception_type == Py_None)) {
#if PYTHON_VERSION >= 0x300
        RELEASE_ERROR_OCCURRED_STATE(exception_state);

        SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, exception_state, PyExc_RuntimeError,
                                                        "No active exception to reraise");
#else
        char const *exception_type_type = Py_TYPE(exception_state->exception_type)->tp_name;

        RELEASE_ERROR_OCCURRED_STATE(exception_state);

        FORMAT_TYPE_ERROR1(tstate, exception_state, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, exception_type_type);

#endif

        return false;
    }
#else
    exception_state->exception_value = EXC_VALUE(tstate);

    if (exception_state->exception_value == Py_None || exception_state->exception_value == NULL) {
        SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_STR(tstate, exception_state, PyExc_RuntimeError,
                                                        "No active exception to reraise");

        return false;
    } else {
        Py_INCREF(exception_state->exception_value);

#if PYTHON_VERSION < 0x3c0
        exception_state->exception_type = PyExceptionInstance_Class(exception_state->exception_value);
        Py_INCREF(exception_state->exception_type);
        exception_state->exception_tb = GET_EXCEPTION_TRACEBACK(exception_state->exception_value);
        Py_XINCREF(exception_state->exception_tb);
#endif
    }
#endif

    // Check for value to be present as well.
    CHECK_EXCEPTION_STATE(exception_state);
    CHECK_OBJECT(exception_state->exception_value);

    return true;
}

// Raise NameError for a given variable name.
void RAISE_CURRENT_EXCEPTION_NAME_ERROR(PyThreadState *tstate, struct Nuitka_ExceptionPreservationItem *exception_state,
                                        PyObject *variable_name) {
#if PYTHON_VERSION < 0x300
    PyObject *exception_value_str =
        Nuitka_String_FromFormat("name '%s' is not defined", Nuitka_String_AsString_Unchecked(variable_name));
#else
    PyObject *exception_value_str = Nuitka_String_FromFormat("name '%U' is not defined", variable_name);
#endif

    PyObject *exception_value = MAKE_EXCEPTION_FROM_TYPE_ARG0(tstate, PyExc_NameError, exception_value_str);
    Py_DECREF(exception_value_str);

#if PYTHON_VERSION >= 0x300
    CHAIN_EXCEPTION(tstate, exception_value);
#endif

    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1_NORMALIZED(tstate, exception_state, PyExc_NameError,
                                                                  exception_value);
}

#if PYTHON_VERSION < 0x300
void RAISE_CURRENT_EXCEPTION_GLOBAL_NAME_ERROR(PyThreadState *tstate,
                                               struct Nuitka_ExceptionPreservationItem *exception_state,
                                               PyObject *variable_name) {
    PyObject *exception_value_str =
        Nuitka_String_FromFormat("global name '%s' is not defined", Nuitka_String_AsString_Unchecked(variable_name));
    PyObject *exception_value = MAKE_EXCEPTION_FROM_TYPE_ARG0(tstate, PyExc_NameError, exception_value_str);
    Py_DECREF(exception_value_str);

    SET_EXCEPTION_PRESERVATION_STATE_FROM_TYPE0_VALUE1_NORMALIZED(tstate, exception_state, PyExc_NameError,
                                                                  exception_value);
}
#endif

PyObject *NORMALIZE_EXCEPTION_VALUE_FOR_RAISE(PyThreadState *tstate, PyObject *exception_type) {
    // Allow setting the value to NULL for time savings with quick type only errors
    CHECK_OBJECT(exception_type);

    if (PyExceptionInstance_Check(exception_type)) {
        return Py_NewRef(exception_type);
    } else {
        if (unlikely(!PyExceptionClass_Check(exception_type))) {
            struct Nuitka_ExceptionPreservationItem exception_state;
            FORMAT_TYPE_ERROR1(tstate, &exception_state, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE,
                               Py_TYPE(exception_type)->tp_name);
            RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);
            return NULL;
        }

        PyObject *exception_value = CALL_FUNCTION_NO_ARGS(tstate, exception_type);

        if (unlikely(exception_value == NULL)) {
            return NULL;
        }

        if (unlikely(!PyExceptionInstance_Check(exception_value))) {
            struct Nuitka_ExceptionPreservationItem exception_state;
            FORMAT_TYPE_ERROR2(tstate, &exception_state,
                               "calling %R should have returned an instance of BaseException, not %R",
                               (char const *)exception_type, (char const *)Py_TYPE(exception_value));
            RESTORE_ERROR_OCCURRED_STATE(tstate, &exception_state);

            Py_DECREF(exception_value);
            return NULL;
        }

        return exception_value;
    }
}

#if PYTHON_VERSION >= 0x300
PyObject *MAKE_STOP_ITERATION_EMPTY(void) {
    // Fake tstate object is OK, no tuple will be needed.
    return Nuitka_CreateStopIteration(NULL, NULL);
}

PyObject *MAKE_BASE_EXCEPTION_DERIVED_EMPTY(PyObject *exception_type) {
    // Note: Fake tstate object is OK, no tuple will be needed to store anything
    // in args.
    PyBaseExceptionObject *result = Nuitka_BaseExceptionSingleArg_new(NULL, (PyTypeObject *)exception_type, NULL);

    return (PyObject *)result;
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
