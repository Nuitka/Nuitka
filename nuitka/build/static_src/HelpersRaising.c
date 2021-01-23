//     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

void RAISE_EXCEPTION_WITH_TYPE(PyObject **exception_type, PyObject **exception_value,
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
        NORMALIZE_EXCEPTION(exception_type, exception_value, exception_tb);
#if PYTHON_VERSION >= 0x270
        if (unlikely(!PyExceptionInstance_Check(*exception_value))) {
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
        CHAIN_EXCEPTION(*exception_value);
#endif
        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);

#if PYTHON_VERSION >= 0x300
        CHAIN_EXCEPTION(*exception_value);

        // Note: Cannot be assigned here.
        assert(*exception_tb == NULL);
        *exception_tb = (PyTracebackObject *)PyException_GetTraceback(*exception_value);
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
void RAISE_EXCEPTION_WITH_CAUSE(PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb,
                                PyObject *exception_cause) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(exception_cause);
    *exception_tb = NULL;

    // None is not a cause.
    if (exception_cause == Py_None) {
        Py_DECREF(exception_cause);
        exception_cause = NULL;
    } else if (PyExceptionClass_Check(exception_cause)) {
        PyObject *old_exception_cause = exception_cause;
        exception_cause = PyObject_CallObject(exception_cause, NULL);
        Py_DECREF(old_exception_cause);

        if (unlikely(exception_cause == NULL)) {
            Py_DECREF(*exception_type);
            Py_XDECREF(*exception_tb);

            FETCH_ERROR_OCCURRED(exception_type, exception_value, exception_tb);

            return;
        }
    }

    if (unlikely(exception_cause != NULL && !PyExceptionInstance_Check(exception_cause))) {
        Py_DECREF(*exception_type);
        Py_XDECREF(*exception_tb);

        PyObject *old_exception_cause = exception_cause;

#ifdef _NUITKA_FULL_COMPAT
        SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_TypeError, "exception causes must derive from BaseException");
        FETCH_ERROR_OCCURRED(exception_type, exception_value, exception_tb);
#else
        FORMAT_TYPE_ERROR1(exception_type, exception_value,
                           "exception causes must derive from BaseException (%s does not)",
                           Py_TYPE(exception_cause)->tp_name);
#endif

        Py_XDECREF(old_exception_cause);
        return;
    }

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(exception_type, exception_value, exception_tb);

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

        CHAIN_EXCEPTION(*exception_value);
        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class(*exception_type);
        Py_INCREF(*exception_type);

        PyException_SetCause(*exception_value, exception_cause);

        CHAIN_EXCEPTION(*exception_value);
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

void RAISE_EXCEPTION_WITH_VALUE(PyObject **exception_type, PyObject **exception_value,
                                PyTracebackObject **exception_tb) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(*exception_value);
    *exception_tb = NULL;

    // Non-empty tuple exceptions are the first element.
    while (unlikely(PyTuple_Check(*exception_type) && PyTuple_GET_SIZE(*exception_type) > 0)) {
        *exception_type = PyTuple_GET_ITEM(*exception_type, 0);
    }

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(exception_type, exception_value, exception_tb);
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

void RAISE_EXCEPTION_IMPLICIT(PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(*exception_value);
    *exception_tb = NULL;

    // Non-empty tuple exceptions are the first element.
    while (unlikely(PyTuple_Check(*exception_type) && PyTuple_GET_SIZE(*exception_type) > 0)) {
        *exception_type = PyTuple_GET_ITEM(*exception_type, 0);
    }

    if (PyExceptionClass_Check(*exception_type)) {
#if PYTHON_VERSION >= 0x340
        NORMALIZE_EXCEPTION(exception_type, exception_value, exception_tb);
        CHAIN_EXCEPTION(*exception_value);
#endif

        return;
    } else if (PyExceptionInstance_Check(*exception_type)) {
#if PYTHON_VERSION >= 0x340
        CHAIN_EXCEPTION(*exception_value);
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
        CHAIN_EXCEPTION(*exception_value);
#endif

        return;
    }
}

void RAISE_EXCEPTION_WITH_TRACEBACK(PyObject **exception_type, PyObject **exception_value,
                                    PyTracebackObject **exception_tb) {
    CHECK_OBJECT(*exception_type);
    CHECK_OBJECT(*exception_value);

    if (*exception_tb == (PyTracebackObject *)Py_None) {
        Py_DECREF(*exception_tb);
        *exception_tb = NULL;
    }

    // Non-empty tuple exceptions are the first element.
    while (unlikely(PyTuple_Check(*exception_type) && PyTuple_GET_SIZE(*exception_type) > 0)) {
        *exception_type = PyTuple_GET_ITEM(*exception_type, 0);
    }

    if (PyExceptionClass_Check(*exception_type)) {
        NORMALIZE_EXCEPTION(exception_type, exception_value, exception_tb);
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

    *exception_type = EXC_TYPE(tstate) != NULL ? EXC_TYPE(tstate) : Py_None;
    Py_INCREF(*exception_type);
    *exception_value = EXC_VALUE(tstate);
    Py_XINCREF(*exception_value);
    *exception_tb = (PyTracebackObject *)EXC_TRACEBACK(tstate);
    Py_XINCREF(*exception_tb);

    CHECK_OBJECT(*exception_type);

    if (*exception_type == Py_None) {
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

    return true;
}
