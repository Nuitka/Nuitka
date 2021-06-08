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
#ifndef __NUITKA_CALLING_H__
#define __NUITKA_CALLING_H__

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION(PyObject *function_object, PyObject *positional_args,
                                                    PyObject *named_args) {
    // Not allowed to enter with an error set. This often catches leaked errors from
    // elsewhere.
    assert(!ERROR_OCCURRED());

    CHECK_OBJECT(function_object);
    CHECK_OBJECT(positional_args);
    assert(named_args == NULL || Py_REFCNT(named_args) > 0);

    ternaryfunc call_slot = Py_TYPE(function_object)->tp_call;

    if (unlikely(call_slot == NULL)) {
        SET_CURRENT_EXCEPTION_TYPE_COMPLAINT("'%s' object is not callable", function_object);

        return NULL;
    }

    if (unlikely(Py_EnterRecursiveCall((char *)" while calling a Python object"))) {
        return NULL;
    }

    PyObject *result = (*call_slot)(function_object, positional_args, named_args);

    Py_LeaveRecursiveCall();

    if (result == NULL) {
        if (unlikely(!ERROR_OCCURRED())) {
            SET_CURRENT_EXCEPTION_TYPE0_STR(PyExc_SystemError, "NULL result without error in CALL_FUNCTION");
        }

        return NULL;
    } else {
        // Some buggy C functions do this, and Nuitka inner workings can get
        // upset from it.
        DROP_ERROR_OCCURRED();

        return result;
    }
}

// Function call variant with no arguments provided at all.
extern PyObject *CALL_FUNCTION_NO_ARGS(PyObject *called);

// Function call variants with positional arguments tuple.
NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_WITH_POSARGS(PyObject *function_object, PyObject *positional_args) {
    return CALL_FUNCTION(function_object, positional_args, NULL);
}

// Method call variants with positional arguments tuple.
extern PyObject *CALL_METHOD_WITH_POSARGS(PyObject *source, PyObject *attr_name, PyObject *positional_args);

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_WITH_KEYARGS(PyObject *function_object, PyObject *named_args) {
    return CALL_FUNCTION(function_object, const_tuple_empty, named_args);
}

// Method call variant with no arguments provided at all.
extern PyObject *CALL_METHOD_NO_ARGS(PyObject *source, PyObject *attribute);

// Forms for single argument calls to not require an array of args from the user side.
extern PyObject *CALL_FUNCTION_WITH_SINGLE_ARG(PyObject *called, PyObject *arg);
extern PyObject *CALL_METHOD_WITH_SINGLE_ARG(PyObject *source, PyObject *attr_name, PyObject *arg);

#endif
