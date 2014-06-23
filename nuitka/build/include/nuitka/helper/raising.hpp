//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_RAISING_H__
#define __NUITKA_HELPER_RAISING_H__

#if PYTHON_VERSION < 300
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must be old-style classes or derived from BaseException, not %s"
#else
#define WRONG_EXCEPTION_TYPE_ERROR_MESSAGE "exceptions must derive from BaseException"
#endif

#if PYTHON_VERSION >= 300
static void CHAIN_EXCEPTION( PyObject *exception_type, PyObject *exception_value )
{
    // Implicit chain of exception already existing.
    PyThreadState *thread_state = PyThreadState_GET();

    // Normalize existing exception first.
    PyErr_NormalizeException( &thread_state->exc_type, &thread_state->exc_value, &thread_state->exc_traceback );

    PyObject *old_exc_value = thread_state->exc_value;

    if ( old_exc_value != NULL && old_exc_value != Py_None && old_exc_value != exception_value )
    {
        Py_INCREF( old_exc_value );

        PyObject *o = old_exc_value;
        while(true)
        {
            PyObject *context = PyException_GetContext(o);
            if (!context) break;

            Py_DECREF( context );

            if ( context == exception_value )
            {
                PyException_SetContext( o, NULL );
                break;
            }

            o = context;
        }

        PyException_SetContext( exception_value, old_exc_value );
        PyException_SetTraceback( old_exc_value, thread_state->exc_traceback );
    }
}
#endif

NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_TYPE( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    *exception_value = NULL;
    *exception_tb = NULL;

    if ( PyExceptionClass_Check( *exception_type ) )
    {
        NORMALIZE_EXCEPTION( exception_type, exception_value, exception_tb );
#if PYTHON_VERSION >= 270
        if (unlikely( !PyExceptionInstance_Check( *exception_value ) ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)*exception_type)->tp_name,
                Py_TYPE( *exception_value )->tp_name
            );

            Py_DECREF( *exception_type );
            Py_DECREF( *exception_value );

            PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
            return;
        }
#endif

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( *exception_type, *exception_value );
#endif
        return;
    }
    else if ( PyExceptionInstance_Check( *exception_type ) )
    {
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class( *exception_type );
        Py_INCREF( *exception_type );

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( *exception_type, *exception_value );

        // TODO: Ever true?
        if ( *exception_tb )
        {
            PyTracebackObject *prev = (PyTracebackObject *)PyException_GetTraceback( *exception_value );

            if ( prev != NULL )
            {
                assert( (*exception_tb)->tb_next == NULL );
                (*exception_tb)->tb_next = prev;
            }

            PyException_SetTraceback( *exception_value, (PyObject *)(*exception_tb ? *exception_tb : (PyTracebackObject *)Py_None ) );
        }
#endif

        return;
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( *exception_type )->tp_name );
        PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );

        return;
    }
}

#if PYTHON_VERSION >= 300
NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_CAUSE( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb, PyObject *exception_cause  )
{
    assertObject( *exception_type );
    assertObject( exception_cause );
    *exception_value = NULL;
    *exception_tb = NULL;

#if PYTHON_VERSION >= 330
    // None is not a cause.
    if ( exception_cause == Py_None )
    {
        Py_DECREF( exception_cause );
        exception_cause = NULL;
    }
    else
#endif
    if ( PyExceptionClass_Check( exception_cause ) )
    {
        PyObject *old_exception_cause = exception_cause;
        exception_cause = PyObject_CallObject( exception_cause, NULL );
        Py_DECREF( old_exception_cause );

        if (unlikely( exception_cause == NULL ))
        {
            Py_DECREF( *exception_type );
            Py_XDECREF( *exception_tb );

            PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );

            return;
        }
    }

#if PYTHON_VERSION >= 330
    if (unlikely( exception_cause != NULL && !PyExceptionInstance_Check( exception_cause ) ))
#else
    if (unlikely( !PyExceptionInstance_Check( exception_cause ) ))
#endif
    {
        Py_DECREF( *exception_type );
        Py_XDECREF( *exception_tb );
        Py_XDECREF( exception_cause );

        PyErr_Format( PyExc_TypeError, "exception causes must derive from BaseException" );

        PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
        return;
    }

    if ( PyExceptionClass_Check( *exception_type ) )
    {
        NORMALIZE_EXCEPTION( exception_type, exception_value, exception_tb );

        if (unlikely( !PyExceptionInstance_Check( *exception_value ) ))
        {
            Py_DECREF( *exception_type );
            Py_XDECREF( *exception_value );
            Py_DECREF( *exception_tb );
            Py_XDECREF( exception_cause );

            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)exception_type)->tp_name,
                Py_TYPE( *exception_value )->tp_name
            );

            PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
            return;
        }

        PyException_SetCause( *exception_value, exception_cause );

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( *exception_type, *exception_value );
#endif
        return;
    }
    else if ( PyExceptionInstance_Check( *exception_type ) )
    {
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class( *exception_type );

        PyException_SetCause( *exception_value, exception_cause );

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( *exception_type, *exception_value );
#endif

        return;
    }
    else
    {
        Py_DECREF( *exception_type );
        Py_XDECREF( exception_cause );

        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
        return;
    }
}
#endif

NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_VALUE( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    assertObject( *exception_type );
    assertObject( *exception_value );
    *exception_tb = NULL;

    // Non-empty tuple exceptions are the first element.
    while (unlikely( PyTuple_Check( *exception_type ) && PyTuple_Size( *exception_type ) > 0 ))
    {
        *exception_type = PyTuple_GET_ITEM( *exception_type, 0 );
    }

    if ( PyExceptionClass_Check( *exception_type ) )
    {
        NORMALIZE_EXCEPTION( exception_type, exception_value, exception_tb );
#if PYTHON_VERSION >= 270
        if (unlikely( !PyExceptionInstance_Check( *exception_value ) ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)*exception_type)->tp_name,
                Py_TYPE( *exception_value )->tp_name
            );

            Py_DECREF( *exception_type );
            Py_XDECREF( *exception_value );
            Py_XDECREF( *exception_tb );

            PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
        }
#endif

        return;
    }
    else if ( PyExceptionInstance_Check( *exception_type ) )
    {
        if (unlikely( *exception_value != NULL && *exception_value != Py_None ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "instance exception may not have a separate value"
            );

            Py_DECREF( *exception_type );
            Py_XDECREF( *exception_value );
            Py_XDECREF( *exception_tb );

            PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );

            return;
        }

        // The type is rather a value, so we are overriding it here.
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class( *exception_type );
        Py_INCREF( *exception_type );

        return;
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );
        PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
        return;
    }
}

NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_IMPLICIT( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    assertObject( *exception_type );
    assertObject( *exception_value );
    *exception_tb = NULL;

    // Non-empty tuple exceptions are the first element.
    while (unlikely( PyTuple_Check( *exception_type ) && PyTuple_Size( *exception_type ) > 0 ))
    {
        *exception_type = PyTuple_GET_ITEM( *exception_type, 0 );
    }

    if ( PyExceptionClass_Check( *exception_type ) )
    {
        return;
    }
    else if ( PyExceptionInstance_Check( *exception_type ) )
    {
        // The type is rather a value, so we are overriding it here.
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class( *exception_type );
        Py_INCREF( *exception_type );

        return;
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );
        PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
        return;
    }
}

NUITKA_MAY_BE_UNUSED static inline void RAISE_EXCEPTION_WITH_TRACEBACK( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    assertObject( *exception_type );
    assertObject( *exception_value );

    if ( *exception_tb == (PyTracebackObject *)Py_None )
    {
        Py_DECREF( *exception_tb );
        *exception_tb = NULL;
    }

    // Non-empty tuple exceptions are the first element.
    while (unlikely( PyTuple_Check( *exception_type ) && PyTuple_Size( *exception_type ) > 0 ))
    {
        *exception_type = PyTuple_GET_ITEM( *exception_type, 0 );
    }

    if ( PyExceptionClass_Check( *exception_type ) )
    {
        NORMALIZE_EXCEPTION( exception_type, exception_value, exception_tb );
#if PYTHON_VERSION >= 270
        if (unlikely( !PyExceptionInstance_Check( *exception_value ) ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)*exception_type)->tp_name,
                Py_TYPE( *exception_value )->tp_name
            );

            Py_DECREF( *exception_type );
            Py_XDECREF( *exception_value );
            Py_XDECREF( *exception_tb );

            PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
        }
#endif

        return;
    }
    else if ( PyExceptionInstance_Check( *exception_type ) )
    {
        if (unlikely( *exception_value != NULL && *exception_value != Py_None ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "instance exception may not have a separate value"
            );

            Py_DECREF( *exception_type );
            Py_XDECREF( *exception_value );
            Py_XDECREF( *exception_tb );

            PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );

            return;
        }

        // The type is rather a value, so we are overriding it here.
        *exception_value = *exception_type;
        *exception_type = PyExceptionInstance_Class( *exception_type );
        Py_INCREF( *exception_type );

        return;
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );
        PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
        return;
    }
}

NUITKA_MAY_BE_UNUSED static void RERAISE_EXCEPTION( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    PyThreadState *tstate = PyThreadState_GET();
    assert( tstate );

    *exception_type = INCREASE_REFCOUNT( tstate->exc_type != NULL ? tstate->exc_type : Py_None );
    *exception_value = INCREASE_REFCOUNT_X( tstate->exc_value );
    *exception_tb = (PyTracebackObject *)INCREASE_REFCOUNT_X( tstate->exc_traceback );

    assertObject( *exception_type );

    if ( *exception_type == Py_None )
    {
#if PYTHON_VERSION >= 300
        Py_DECREF( *exception_type );

        *exception_type = INCREASE_REFCOUNT( PyExc_RuntimeError );
        *exception_value = PyUnicode_FromString( "No active exception to reraise" );
        *exception_tb = NULL;
#else
        PyErr_Format(
            PyExc_TypeError,
            "exceptions must be old-style classes or derived from BaseException, not %s",
            Py_TYPE( *exception_type )->tp_name
        );
        PyErr_Fetch( exception_type, exception_value, (PyObject **)exception_tb );
#endif
    }
}


#endif
