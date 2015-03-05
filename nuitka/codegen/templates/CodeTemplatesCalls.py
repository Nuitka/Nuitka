#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

template_call_function_with_args_decl = """\
extern PyObject *CALL_FUNCTION_WITH_ARGS%(args_count)d( PyObject *called, %(args_decl)s );"""

template_call_function_with_args_impl = """\
PyObject *CALL_FUNCTION_WITH_ARGS%(args_count)d( PyObject *called, %(args_decl)s )
{
    CHECK_OBJECT( called );

    // Check if arguments are valid objects in debug mode.
#ifndef __NUITKA_NO_ASSERT__
    PyObject *args_for_test[] = { %(args_list)s };

    for( size_t i = 0; i < sizeof( args_for_test ) / sizeof( PyObject * ); i++ )
    {
        CHECK_OBJECT( args_for_test[ i ] );
    }
#endif

    if ( Nuitka_Function_Check( called ) )
    {
        if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object" ) ))
        {
            return NULL;
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
                return NULL;
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

            return result;
        }
    }
    else if ( PyCFunction_Check( called ) )
    {
        // Try to be fast about wrapping the arguments.
        int flags = PyCFunction_GET_FLAGS( called );

        if ( flags & METH_NOARGS )
        {
#if %(args_count)d == 0
            PyCFunction method = PyCFunction_GET_FUNCTION( called );
            PyObject *self = PyCFunction_GET_SELF( called );

            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object" ) ))
            {
                return NULL;
            }
#endif

            PyObject *result = (*method)( self, NULL );

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            // Some buggy C functions do this, and Nuitka inner workings can get
            // upset from it.
            if (unlikely( result != NULL )) DROP_ERROR_OCCURRED();

            return result;
#else
            PyErr_Format(
                PyExc_TypeError,
                "%%s() takes no arguments (%(args_count)d given)",
                ((PyCFunctionObject *)called)->m_ml->ml_name
            );
            return NULL;
#endif
        }
        else if ( flags & METH_O )
        {
#if %(args_count)d == 1
            PyCFunction method = PyCFunction_GET_FUNCTION( called );
            PyObject *self = PyCFunction_GET_SELF( called );

            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object" ) ))
            {
                return NULL;
            }
#endif

            PyObject *result = (*method)( self, %(args_list)s );

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            // Some buggy C functions do this, and Nuitka inner workings can get
            // upset from it.
            if (unlikely( result != NULL )) DROP_ERROR_OCCURRED();

            return result;
#else
            PyErr_Format(PyExc_TypeError,
                "%%s() takes exactly one argument (%(args_count)d given)",
                 ((PyCFunctionObject *)called)->m_ml->ml_name
            );
            return NULL;
#endif
        }
        else
        {
            PyCFunction method = PyCFunction_GET_FUNCTION( called );
            PyObject *self = PyCFunction_GET_SELF( called );

            PyObject *args[] = { %(args_list)s };
            PyObject *pos_args = MAKE_TUPLE( args, sizeof( args ) / sizeof( PyObject * ) );

            PyObject *result;

            assert( flags && METH_VARARGS );

            // Recursion guard is not strictly necessary, as we already have
            // one on our way to here.
#ifdef _NUITKA_FULL_COMPAT
            if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object" ) ))
            {
                return NULL;
            }
#endif

            if ( flags && METH_KEYWORDS )
            {
                result = (*(PyCFunctionWithKeywords)method)( self, pos_args, NULL );
            }
            else
            {
                result = (*method)( self, pos_args );
            }

#ifdef _NUITKA_FULL_COMPAT
            Py_LeaveRecursiveCall();
#endif

            // Some buggy C functions do this, and Nuitka inner workings can get
            // upset from it.
            if ( result != NULL ) DROP_ERROR_OCCURRED();

            Py_DECREF( pos_args );

            return result;
        }
    }
    else if ( PyFunction_Check( called ) )
    {
        PyObject *args[] = { %(args_list)s };

        return callPythonFunction(
            called,
            args,
            sizeof( args ) / sizeof( PyObject * )
        );
    }

    PyObject *args[] = { %(args_list)s };
    PyObject *pos_args = MAKE_TUPLE( args, sizeof( args ) / sizeof( PyObject * ) );

    PyObject *result = CALL_FUNCTION(
        called,
        pos_args,
        NULL
    );

    Py_DECREF( pos_args );

    return result;
}
"""
