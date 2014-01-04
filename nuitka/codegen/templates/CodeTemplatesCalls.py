#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Templates for calling functions with positional args only very quickly.

"""

template_call_cpython_function_fast_impl = """\
NUITKA_MAY_BE_UNUSED static PyObject *_fast_function_args( PyObject *func, PyObject **args, int count )
{
    PyCodeObject *co = (PyCodeObject *)PyFunction_GET_CODE( func );
    PyObject *globals = PyFunction_GET_GLOBALS( func );
    PyObject *argdefs = PyFunction_GET_DEFAULTS(func);

#if PYTHON_VERSION >= 300
    PyObject *kwdefs = PyFunction_GET_KW_DEFAULTS(func);

    if ( kwdefs == NULL && argdefs == NULL && co->co_argcount == count &&
        co->co_flags == ( CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE ))
#else
    if ( argdefs == NULL && co->co_argcount == count &&
        co->co_flags == ( CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE ))
#endif
    {
        PyThreadState *tstate = PyThreadState_GET();
        assertObject( globals );

        PyFrameObject *frame = PyFrame_New( tstate, co, globals, NULL );

        if (unlikely( frame == NULL ))
        {
            throw PythonException();
        };

        for ( int i = 0; i < count; i++ )
        {
            frame->f_localsplus[i] = INCREASE_REFCOUNT( args[i] );
        }

        PyObject *result = PyEval_EvalFrameEx( frame, 0 );

        // Frame release protects against recursion as it may lead to variable
        // destruction.
        ++tstate->recursion_depth;
        Py_DECREF( frame );
        --tstate->recursion_depth;

        if ( result == NULL )
        {
            throw PythonException();
        }

        return result;
    }

    PyObject **defaults = NULL;
    int nd = 0;

    if ( argdefs != NULL )
    {
        defaults = &PyTuple_GET_ITEM(argdefs, 0);
        nd = int( Py_SIZE( argdefs ) );
    }

    PyObject *result = PyEval_EvalCodeEx(
#if PYTHON_VERSION >= 300
        (PyObject *)co,
#else
        co,        // code object
#endif
        globals,   // globals
        NULL,      // no locals
        args,      // args
        count,     // argcount
        NULL,      // kwds
        0,         // kwcount
        defaults,  // defaults
        nd,        // defcount
#if PYTHON_VERSION >= 300
        kwdefs,
#endif
        PyFunction_GET_CLOSURE( func )
    );

    if ( result == 0 )
    {
        throw PythonException();
    }

    return result;
}
"""

template_call_function_with_args_decl = """\
extern PyObject *CALL_FUNCTION_WITH_ARGS%(args_count)d( PyObject *called, %(args_decl)s );"""

template_call_function_with_args_impl = """\
PyObject *CALL_FUNCTION_WITH_ARGS%(args_count)d( PyObject *called, %(args_decl)s )
{
    assertObject( called );

    // Check if arguments are valid objects in debug mode.
#ifndef __NUITKA_NO_ASSERT__
    PyObject *args_for_test[] = { %(args_list)s };

    for( size_t i = 0; i < sizeof( args_for_test ) / sizeof( PyObject * ); i++ )
    {
        assertObject( args_for_test[ i ] );
    }
#endif

    if ( Nuitka_Function_Check( called ) )
    {
        if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object" ) ))
        {
            throw PythonException();
        }

        Nuitka_FunctionObject *function = (Nuitka_FunctionObject *)called;
        PyObject *result;

        PyObject *args[] = { %(args_list)s };

        if ( function->m_direct_arg_parser )
        {
            result = function->m_direct_arg_parser(
                function,
                args,
                sizeof( args ) / sizeof( PyObject * )
            );
        }
        else
        {
            result = function->m_code(
                function,
                args,
                sizeof( args ) / sizeof( PyObject * ),
                NULL
            );
        }

        Py_LeaveRecursiveCall();

        if ( result == NULL )
        {
            throw PythonException();
        }

        return result;
    }
    else if ( Nuitka_Method_Check( called ) )
    {
        Nuitka_MethodObject *method = (Nuitka_MethodObject *)called;

        // Unbound method without arguments, let the error path be slow.
        if ( method->m_object != NULL )
        {
            if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object" ) ))
            {
                throw PythonException();
            }

            PyObject *args[] = {
                method->m_object,
                %(args_list)s
            };

            PyObject *result;

            if ( method->m_function->m_direct_arg_parser )
            {
                result = method->m_function->m_direct_arg_parser(
                    method->m_function,
                    args,
                    sizeof( args ) / sizeof( PyObject * )
                );
            }
            else
            {
                result = method->m_function->m_code(
                    method->m_function,
                    args,
                    sizeof( args ) / sizeof( PyObject * ),
                    NULL
                );
            }

            Py_LeaveRecursiveCall();

            if ( result == NULL )
            {
                throw PythonException();
            }

            return result;
        }
    }
    else if ( PyFunction_Check( called ) )
    {
        PyObject *args[] = { %(args_list)s };

        return _fast_function_args(
            called,
            args,
            sizeof( args ) / sizeof( PyObject * )
        );
    }

    return CALL_FUNCTION(
        called,
        PyObjectTemporary( MAKE_TUPLE%(args_count)d( %(args_list)s ) ).asObject0(),
        NULL
    );
}
"""
