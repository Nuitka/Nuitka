//     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

#include "__helpers.hpp"

// Note: We do the reversal for function call arguments completely ourselves and here, so
// we don't have to do it in generated code. For each CALL_FUNCTION variant there is a
// define that includes a use of EVAL_ORDERED_x and a _CALL_FUNCTION implementation that
// does the actual work.

extern PyObject *_python_tuple_empty;

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION( PyObject *function_object, PyObject *positional_args, PyObject *named_args )
{
    assertObject( function_object );
    assertObject( positional_args );
    assert( named_args == NULL || Py_REFCNT( named_args ) > 0 );

    ternaryfunc call_slot = function_object->ob_type->tp_call;

    if (unlikely( call_slot == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object is not callable",
            function_object->ob_type->tp_name
        );

        throw PythonException();
    }

    if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object") ))
    {
        throw PythonException();
    }

    PyObject *result = (*call_slot)( function_object, positional_args, named_args );

    Py_LeaveRecursiveCall();

    if ( result == NULL )
    {
        if (unlikely( !ERROR_OCCURED() ))
        {
            PyErr_Format(
                PyExc_SystemError,
                "NULL result without error in PyObject_Call"
            );
        }

        throw PythonException();
    }
    else
    {
        return result;
    }
}

// Function call variant with no arguments provided at all.

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_NO_ARGS( PyObject *function_object )
{
    return CALL_FUNCTION(
        function_object,
        _python_tuple_empty,
        NULL
    );
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_WITH_POSARGS( PyObject *function_object, PyObject *positional_args )
{
    return CALL_FUNCTION(
        function_object,
        positional_args,
        NULL
    );
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_WITH_KEYARGS( PyObject *function_object, PyObject *named_args )
{
    return CALL_FUNCTION(
        function_object,
        _python_tuple_empty,
        named_args
    );
}


#endif
