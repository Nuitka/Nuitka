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

        PyObject *o = old_exc_value, *context;
        while (( context = PyException_GetContext(o) ))
        {
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

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_TYPE( PyObject *exception_type, PyObject *exception_tb )
{
    PyTracebackObject *traceback = (PyTracebackObject *)exception_tb;
    assertObject( traceback );
    assert( PyTraceBack_Check( traceback ) );
    assertObject( exception_type );

    if ( PyExceptionClass_Check( exception_type ) )
    {
        PyObject *value = NULL;

        Py_INCREF( exception_type );
        Py_XINCREF( traceback );

        NORMALIZE_EXCEPTION( &exception_type, &value, &traceback );
#if PYTHON_VERSION >= 270
        if (unlikely( !PyExceptionInstance_Check( value ) ))
        {
            Py_DECREF( exception_type );
            Py_DECREF( value );
            Py_XDECREF( traceback );

            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)exception_type)->tp_name,
                Py_TYPE( value )->tp_name
            );

            throw PythonException();
        }
#endif

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( exception_type, value );
#endif
        throw PythonException(
            exception_type,
            value,
            traceback
        );
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        PyObject *value = exception_type;
        exception_type = PyExceptionInstance_Class( exception_type );

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( exception_type, value );

        PyTracebackObject *prev = (PyTracebackObject *)PyException_GetTraceback( value );

        if ( prev != NULL )
        {
            assert( traceback->tb_next == NULL );
            traceback->tb_next = prev;
        }

        PyException_SetTraceback( value, (PyObject *)traceback );
#endif

        throw PythonException(
            INCREASE_REFCOUNT( exception_type ),
            INCREASE_REFCOUNT( value ),
            INCREASE_REFCOUNT( traceback )
        );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        PythonException to_throw;
        to_throw.setTraceback( INCREASE_REFCOUNT( traceback ) );

        throw to_throw;
    }
}

#if PYTHON_VERSION >= 300
NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_CAUSE( PyObject *exception_type, PyObject *exception_cause, PyObject *exception_tb )
{
    PyTracebackObject *traceback = (PyTracebackObject *)exception_tb;

    assertObject( exception_type );
    assertObject( exception_cause );

#if PYTHON_VERSION >= 330
    // None is not a cause.
    if ( exception_cause == Py_None )
    {
        exception_cause = NULL;
    }
    else
#endif
    if ( PyExceptionClass_Check( exception_cause ) )
    {
        exception_cause = PyObject_CallObject( exception_cause, NULL );

        if (unlikely( exception_cause == NULL ))
        {
            throw PythonException();
        }
    }
    else
    {
        Py_INCREF( exception_cause );
    }

#if PYTHON_VERSION >= 330
    if (unlikely( exception_cause != NULL && !PyExceptionInstance_Check( exception_cause ) ))
#else
    if (unlikely( !PyExceptionInstance_Check( exception_cause ) ))
#endif
    {
        Py_XDECREF( exception_cause );

        PyErr_Format( PyExc_TypeError, "exception causes must derive from BaseException" );
        throw PythonException();
    }


    if ( PyExceptionClass_Check( exception_type ) )
    {
        PyObject *value = NULL;

        Py_INCREF( exception_type );
        Py_INCREF( traceback );

        NORMALIZE_EXCEPTION( &exception_type, &value, &traceback );
        if (unlikely( !PyExceptionInstance_Check( value ) ))
        {
            Py_DECREF( exception_type );
            Py_XDECREF( value );
            Py_DECREF( traceback );
            Py_XDECREF( exception_cause );

            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)exception_type)->tp_name,
                Py_TYPE( value )->tp_name
            );

            throw PythonException();
        }

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( exception_type, value );
#endif

        PythonException to_throw( exception_type, value, traceback );
        to_throw.setCause( exception_cause );
        throw to_throw;
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        PyObject *value = exception_type;
        exception_type = PyExceptionInstance_Class( value );

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( exception_type, value );
#endif

        PythonException to_throw(
            INCREASE_REFCOUNT( exception_type ),
            INCREASE_REFCOUNT( value ),
            INCREASE_REFCOUNT( traceback )
        );
        to_throw.setCause( exception_cause );
        throw to_throw;
    }
    else
    {
        Py_XDECREF( exception_cause );

        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        PythonException to_throw;
        to_throw.setTraceback( INCREASE_REFCOUNT( traceback ) );

        throw to_throw;
    }
}
#endif

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_VALUE( PyObject *exception_type, PyObject *value, PyObject *exception_tb )
{
    assertObject( exception_type );
    PyTracebackObject *traceback = (PyTracebackObject *)exception_tb;

    // Non-empty tuple exceptions are the first element.
    while (unlikely( PyTuple_Check( exception_type ) && PyTuple_Size( exception_type ) > 0 ))
    {
        exception_type = PyTuple_GET_ITEM( exception_type, 0 );
    }

    if ( PyExceptionClass_Check( exception_type ) )
    {
        Py_INCREF( exception_type );
        Py_XINCREF( value );
        Py_XINCREF( traceback );

        NORMALIZE_EXCEPTION( &exception_type, &value, &traceback );
#if PYTHON_VERSION >= 270
        if (unlikely( !PyExceptionInstance_Check( value ) ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)exception_type)->tp_name,
                Py_TYPE( value )->tp_name
            );

            Py_DECREF( exception_type );
            Py_XDECREF( value );
            Py_XDECREF( traceback );

            throw PythonException();
        }
#endif

        throw PythonException(
            exception_type,
            value,
            traceback
        );
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        if (unlikely( value != NULL && value != Py_None ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "instance exception may not have a separate value"
            );

            throw PythonException();
        }

        // The type is rather a value, so we are overriding it here.
        value = exception_type;
        exception_type = PyExceptionInstance_Class( exception_type );

        throw PythonException(
            INCREASE_REFCOUNT( exception_type ),
            INCREASE_REFCOUNT( value ),
            INCREASE_REFCOUNT_X( traceback )
        );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        throw PythonException();
    }
}

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_VALUE_NO_NORMALIZE( PyObject *exception_type, PyObject *value, PyObject *tb )
{
    PyTracebackObject *traceback = (PyTracebackObject *)tb;

    assertObject( exception_type );
    assert( !PyTuple_Check( exception_type ) );

    if ( PyExceptionClass_Check( exception_type ) )
    {
        throw PythonException(
            INCREASE_REFCOUNT( exception_type ),
            INCREASE_REFCOUNT( value ),
            INCREASE_REFCOUNT_X( traceback )
        );
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        assert ( value == NULL || value == Py_None );

        // The type is rather a value, so we are overriding it here.
        value = exception_type;
        exception_type = PyExceptionInstance_Class( exception_type );

        throw PythonException(
            INCREASE_REFCOUNT( exception_type ),
            INCREASE_REFCOUNT( value ),
            INCREASE_REFCOUNT_X( traceback )
        );
    }
    else
    {
        assert( false );

        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        throw PythonException();
    }
}


NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static inline void RAISE_EXCEPTION_WITH_TRACEBACK( PyObject *exception_type, PyObject *value, PyObject *traceback )
{
    if ( traceback == Py_None )
    {
        traceback = NULL;
    }

    // Check traceback
    if( traceback != NULL && !PyTraceBack_Check( traceback ) )
    {
        PyErr_Format( PyExc_TypeError, "raise: arg 3 must be a traceback or None" );
        throw PythonException();
    }

    RAISE_EXCEPTION_WITH_VALUE( exception_type, value, traceback );
}

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RERAISE_EXCEPTION( void )
{
    PyThreadState *tstate = PyThreadState_GET();
    assert( tstate );

    PyObject *type = tstate->exc_type != NULL ? tstate->exc_type : Py_None;
    PyObject *value = tstate->exc_value;
    PyObject *tb = tstate->exc_traceback;

    assertObject( type );

#if PYTHON_VERSION >= 300
    if ( type == Py_None )
    {
        PyErr_Format( PyExc_RuntimeError, "No active exception to reraise" );
        throw PythonException();
    }
#endif

    RAISE_EXCEPTION_WITH_TRACEBACK( type, value, tb );
}

// Throw an exception from within an expression, this is without normalization. Note:
// There is also a form for use as a statement, and also doesn't do it, seeing this used
// normally means, the implicit exception was not propagated.
NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static PyObject *THROW_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyObject *traceback )
{
    RAISE_EXCEPTION_WITH_VALUE_NO_NORMALIZE(
        exception_type,
        exception_value,
        traceback
    );
}



NUITKA_MAY_BE_UNUSED static void THROW_IF_ERROR_OCCURED( void )
{
    if ( ERROR_OCCURED() )
    {
        throw PythonException();
    }
}

NUITKA_MAY_BE_UNUSED static void THROW_IF_ERROR_OCCURED_NOT( PyObject *ignored )
{
    if ( ERROR_OCCURED() )
    {
        if ( PyErr_ExceptionMatches( ignored ))
        {
            PyErr_Clear();
        }
        else
        {
            throw PythonException();
        }
    }
}

#endif
