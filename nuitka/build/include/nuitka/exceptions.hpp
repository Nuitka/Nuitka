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
#ifndef __NUITKA_EXCEPTIONS_H__
#define __NUITKA_EXCEPTIONS_H__

static bool ERROR_OCCURED( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type != NULL;
}


#if PYTHON_VERSION < 300
NUITKA_MAY_BE_UNUSED static void dumpTraceback( PyTracebackObject *traceback )
{
    puts( "Dumping traceback:" );

    if ( traceback == NULL ) puts( "<NULL traceback?!>" );

    while( traceback )
    {
        puts( " Frame object chain:" );

        PyFrameObject *frame = traceback->tb_frame;

        while ( frame )
        {
            printf( "  Frame at %s\n", PyString_AsString( PyObject_Str( (PyObject *)frame->f_code )));

            frame = frame->f_back;
        }

        traceback = traceback->tb_next;
    }

    puts( "End of Dump." );
}
#endif

NUITKA_MAY_BE_UNUSED static PyTracebackObject *INCREASE_REFCOUNT( PyTracebackObject *traceback_object )
{
    Py_INCREF( traceback_object );
    return traceback_object;
}

NUITKA_MAY_BE_UNUSED static PyTracebackObject *INCREASE_REFCOUNT_X( PyTracebackObject *traceback_object )
{
    Py_XINCREF( traceback_object );
    return traceback_object;
}

NUITKA_MAY_BE_UNUSED static PyTracebackObject *MAKE_TRACEBACK( PyFrameObject *frame )
{
    // assertFrameObject( frame );

    PyTracebackObject *result = PyObject_GC_New( PyTracebackObject, &PyTraceBack_Type );

    result->tb_next = NULL;
    result->tb_frame = frame;

    result->tb_lasti = 0;
    result->tb_lineno = frame->f_lineno;

    Nuitka_GC_Track( result );

    return result;
}

extern PyObject *_python_str_plain_exc_type, *_python_str_plain_exc_value, *_python_str_plain_exc_traceback;

// Helper that sets the current thread exception, releasing the current one, for use in this
// file only.
inline void _SET_CURRENT_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyTracebackObject *exception_tb )
{
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *old_type  = thread_state->exc_type;
    PyObject *old_value = thread_state->exc_value;
    PyObject *old_tb    = thread_state->exc_traceback;

    thread_state->exc_type = INCREASE_REFCOUNT_X( exception_type );
    thread_state->exc_value = INCREASE_REFCOUNT_X( exception_value );
    thread_state->exc_traceback = (PyObject *)INCREASE_REFCOUNT_X( exception_tb );

    Py_XDECREF( old_type );
    Py_XDECREF( old_value );
    Py_XDECREF( old_tb );

    // Set sys attributes in the fastest possible way.
    PyObject *sys_dict = thread_state->interp->sysdict;
    assertObject( sys_dict );

    PyDict_SetItem( sys_dict, _python_str_plain_exc_type, exception_type ? exception_type : Py_None );
    PyDict_SetItem( sys_dict, _python_str_plain_exc_value, exception_value ? exception_value : Py_None );
    PyDict_SetItem( sys_dict, _python_str_plain_exc_traceback, exception_tb ? (PyObject *)exception_tb : Py_None );
}

inline void NORMALIZE_EXCEPTION( PyObject **exception_type, PyObject **exception_value, PyTracebackObject **exception_tb )
{
    PyErr_NormalizeException( exception_type, exception_value, (PyObject **)exception_tb );
}


class _PythonException
{
public:
    _PythonException()
    {
        this->_importFromPython();
    }

    _PythonException( PyObject *exception )
    {
        assertObject( exception );

        Py_INCREF( exception );

        this->exception_type = exception;
        this->exception_value = NULL;
        this->exception_tb = NULL;
    }

    _PythonException( PyObject *exception, PyTracebackObject *traceback )
    {
        assertObject( exception );
        assertObject( traceback );

        this->exception_type = exception;
        this->exception_value = NULL;
        this->exception_tb = traceback;
    }

    _PythonException( PyObject *exception, PyObject *value, PyTracebackObject *traceback )
    {
        assertObject( exception );
        assert( value == NULL || Py_REFCNT( value ) > 0 );
        assertObject( traceback );

        this->exception_type = exception;
        this->exception_value = value;
        this->exception_tb = traceback;
    }

    _PythonException( const _PythonException &other )
    {
        this->exception_type  = other.exception_type;
        this->exception_value = other.exception_value;
        this->exception_tb    = other.exception_tb;

        Py_XINCREF( this->exception_type );
        Py_XINCREF( this->exception_value );
        Py_XINCREF( this->exception_tb );
    }

    void operator=( const _PythonException &other )
    {
        Py_XINCREF( other.exception_type );
        Py_XINCREF( other.exception_value );
        Py_XINCREF( other.exception_tb );

        Py_XDECREF( this->exception_type );
        Py_XDECREF( this->exception_value );
        Py_XDECREF( this->exception_tb );

        this->exception_type  = other.exception_type;
        this->exception_value = other.exception_value;
        this->exception_tb    = other.exception_tb;
    }

    ~_PythonException()
    {
        Py_XDECREF( this->exception_type );
        Py_XDECREF( this->exception_value );
        Py_XDECREF( this->exception_tb );
    }

    inline void _importFromPython()
    {
        PyErr_Fetch( &this->exception_type, &this->exception_value, (PyObject **)&this->exception_tb );

        assertObject( this->exception_type );
    }

    inline void normalize()
    {
        NORMALIZE_EXCEPTION( &this->exception_type, &this->exception_value, &this->exception_tb );

#if PYTHON_VERSION >= 300
        PyException_SetTraceback( this->exception_value, (PyObject *)this->exception_tb );
#endif
    }

    inline bool matches( PyObject *exception ) const
    {
#if PYTHON_VERSION >= 300
        if ( PyTuple_Check( exception ))
        {
            Py_ssize_t length = PyTuple_Size( exception );

            for ( Py_ssize_t i = 0; i < length; i += 1 )
            {
                PyObject *element = PyTuple_GET_ITEM( exception, i );

                if (unlikely( !PyExceptionClass_Check( element ) ))
                {
                    PyErr_Format( PyExc_TypeError, "catching classes that do not inherit from BaseException is not allowed" );
                    throw _PythonException();
                }
            }
        }
        else if (unlikely( !PyExceptionClass_Check( exception ) ))
        {
            PyErr_Format( PyExc_TypeError, "catching classes that do not inherit from BaseException is not allowed" );
            throw _PythonException();
        }
#endif

        return
            PyErr_GivenExceptionMatches( this->exception_type, exception ) ||
            PyErr_GivenExceptionMatches( this->exception_value, exception );
    }

    inline void toPython()
    {
        PyErr_Restore( this->exception_type, this->exception_value, (PyObject *)this->exception_tb );

        assert( this->exception_type );

#ifndef __NUITKA_NO_ASSERT__
        PyThreadState *thread_state = PyThreadState_GET();
#endif

        assert( this->exception_type == thread_state->curexc_type );
        assert( thread_state->curexc_type );

        this->exception_type  = NULL;
        this->exception_value = NULL;
        this->exception_tb    = NULL;
    }

    inline void toExceptionHandler()
    {
        this->normalize();

        _SET_CURRENT_EXCEPTION( this->exception_type, this->exception_value, this->exception_tb );
    }

    inline PyObject *getType()
    {
        if ( this->exception_value == NULL )
        {
            this->normalize();
        }

        return this->exception_type;
    }

    inline PyObject *getValue()
    {
        if ( this->exception_value == NULL )
        {
            this->normalize();
        }

        return this->exception_value;
    }


    inline PyTracebackObject *getTraceback() const
    {
        return (PyTracebackObject *)this->exception_tb;
    }

    inline void addTraceback( PyFrameObject *frame )
    {
        assert( this->exception_tb );

#if 0
        printf( "addTraceback %p %s %p %s %d %d\n", exception_tb->tb_frame, PyString_AsString( exception_tb->tb_frame->f_code->co_name ), frame, PyString_AsString( frame->f_code->co_name ), this->exception_tb->tb_lineno, frame->f_lineno );
#endif

        if ( this->exception_tb->tb_frame != frame || this->exception_tb->tb_lineno != frame->f_lineno )
        {
            Py_INCREF( frame );
            PyTracebackObject *traceback_new = MAKE_TRACEBACK( frame );

            traceback_new->tb_next = this->exception_tb;
            this->exception_tb = traceback_new;
        }
    }

    inline void setTraceback( PyTracebackObject *traceback )
    {
        assert( traceback == NULL || Py_REFCNT( traceback ) > 0 );

        PyTracebackObject *old = this->exception_tb;

        this->exception_tb = traceback;

        Py_XDECREF( old );
    }

    inline bool hasTraceback() const
    {
        return this->exception_tb != NULL;
    }

    void setType( PyObject *exception_type )
    {
        Py_XDECREF( this->exception_type );
        this->exception_type = exception_type;
    }

#if PYTHON_VERSION >= 300
    void setCause( PyObject *exception_cause )
    {
        PyException_SetCause( this->exception_value, exception_cause );
    }
#endif

    void dump() const
    {
        PRINT_ITEM_TO( NULL, this->exception_type );
    }

private:

    friend class _PythonExceptionKeeper;

    // For the restore of saved ones.
    _PythonException( PyObject *exception, PyObject *value, PyObject *traceback )
    {
        this->exception_type = exception;
        this->exception_value = value;
        this->exception_tb = (PyTracebackObject *)traceback;
    }


    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;
};


class _PythonExceptionKeeper
{
public:
    _PythonExceptionKeeper()
    {
        this->keeping = false;

#ifndef __NUITKA_NO_ASSERT__
        this->exception_type = NULL;
        this->exception_value = NULL;
        this->exception_tb = NULL;
#endif
    }

    ~_PythonExceptionKeeper()
    {
        if ( this->keeping )
        {
            Py_XDECREF( this->exception_type );
            Py_XDECREF( this->exception_value );
            Py_XDECREF( this->exception_tb );
        }
    }

    void save( const _PythonException &e )
    {
        this->exception_type  = INCREASE_REFCOUNT_X( e.exception_type );
        this->exception_value = INCREASE_REFCOUNT_X( e.exception_value );
        this->exception_tb    = INCREASE_REFCOUNT_X( e.exception_tb );

        this->keeping = true;
    }

    void rethrow()
    {
        if ( this->keeping )
        {
            Py_XINCREF( this->exception_type );
            Py_XINCREF( this->exception_value );
            Py_XINCREF( this->exception_tb );

            // Restore the frame line number from the traceback, if present. Otherwise it
            // will changed already.
            if ( this->exception_tb )
            {
                this->exception_tb->tb_frame->f_lineno = this->exception_tb->tb_lineno;
            }

            throw _PythonException( this->exception_type, this->exception_value, this->exception_tb );
        }
    }

    bool isEmpty() const
    {
        return !this->keeping;
    }

private:

    bool keeping;

    PyObject *exception_type, *exception_value;
    PyTracebackObject *exception_tb;
};

class ContinueException
{
};

class BreakException
{
};

class ReturnValueException
{
public:
    explicit ReturnValueException( PyObject *value )
    {
        assertObject( value );

        this->value = value;
    }

    ~ReturnValueException()
    {
        assertObject( value );

        Py_DECREF( this->value );
    }

    PyObject *getValue() const
    {
        return INCREASE_REFCOUNT( this->value );
    }

private:
    PyObject *value;

};

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


NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( PyObject *exception_type, PyTracebackObject *traceback )
{
    assertObject( exception_type );
    assertObject( traceback );

    if ( PyExceptionClass_Check( exception_type ) )
    {
        PyObject *value = NULL;

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

            throw _PythonException();
        }
#endif

#if PYTHON_VERSION >= 300
        CHAIN_EXCEPTION( exception_type, value );
#endif

        throw _PythonException( exception_type, value, traceback );
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        PyObject *value = exception_type;
        exception_type = INCREASE_REFCOUNT( PyExceptionInstance_Class( exception_type ) );

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

        throw _PythonException( exception_type, value, traceback );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        _PythonException to_throw;
        to_throw.setTraceback( traceback );

        throw to_throw;
    }
}

#if PYTHON_VERSION >= 300
NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION_WITH_CAUSE( PyObject *exception_type, PyObject *exception_cause, PyTracebackObject *traceback )
{
    assertObject( exception_type );
    assertObject( exception_cause );

    if ( PyExceptionClass_Check( exception_cause ) )
    {
        exception_cause = PyObject_CallObject( exception_cause, NULL );

        if (unlikely( exception_cause == NULL ))
        {
            throw _PythonException();
        }
    }

    if (unlikely( !PyExceptionInstance_Check( exception_cause ) ))
    {
        PyErr_Format( PyExc_TypeError, "exception causes must derive from BaseException" );
        throw _PythonException();
    }

    if ( PyExceptionClass_Check( exception_type ) )
    {
        PyObject *value = NULL;

        NORMALIZE_EXCEPTION( &exception_type, &value, &traceback );
        if (unlikely( !PyExceptionInstance_Check( value ) ))
        {
            PyErr_Format(
                PyExc_TypeError,
                "calling %s() should have returned an instance of BaseException, not '%s'",
                ((PyTypeObject *)exception_type)->tp_name,
                Py_TYPE( value )->tp_name
            );

            throw _PythonException();
        }

        _PythonException to_throw( exception_type, value, traceback );
        to_throw.setCause( exception_cause );
        throw to_throw;
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        throw _PythonException( INCREASE_REFCOUNT( PyExceptionInstance_Class( exception_type ) ), exception_type, traceback );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        _PythonException to_throw;
        to_throw.setTraceback( traceback );

        throw to_throw;
    }
}
#endif

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyTracebackObject *traceback )
{
    assertObject( exception_type );

    // Non-empty tuple exceptions are the first element.
    while (unlikely( PyTuple_Check( exception_type ) && PyTuple_Size( exception_type ) > 0 ))
    {
        PyObjectTemporary old( exception_type );
        exception_type = INCREASE_REFCOUNT( PyTuple_GET_ITEM( exception_type, 0 ) );
    }

    if ( PyExceptionClass_Check( exception_type ) )
    {
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

            throw _PythonException();
        }
#endif

        throw _PythonException( exception_type, value, traceback );
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        // The type is rather a value, so we are overriding it here.
        Py_XDECREF( value );

        value = exception_type;
        exception_type = INCREASE_REFCOUNT( PyExceptionInstance_Class( exception_type ) );

        throw _PythonException( exception_type, value, traceback );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        throw _PythonException();
    }
}

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static inline void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyObject *traceback )
{
    // Check traceback
    assert( traceback == NULL || PyTraceBack_Check( traceback ) );

    RAISE_EXCEPTION( exception_type, value, (PyTracebackObject *)traceback );
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
        throw _PythonException();
    }
#endif

    Py_INCREF( type );
    Py_XINCREF( value );
    Py_XINCREF( tb );

    RAISE_EXCEPTION( type, value, tb );
}

// Throw an exception from within an expression, this is without normalization. TODO: There needs
// to be a form that is like a statement, and doesn't do it, so it won't impact "raise", but can
// be used in optimization.
NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static PyObject *THROW_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyTracebackObject *traceback )
{
    assertObject( exception_type );

    if ( PyExceptionClass_Check( exception_type ) )
    {
        throw _PythonException( exception_type, exception_value, traceback );
    }
    else if ( PyExceptionInstance_Check( exception_type ) )
    {
        Py_DECREF( exception_value );

        exception_value = exception_type;
        exception_type = INCREASE_REFCOUNT( PyExceptionInstance_Class( exception_type ) );

        throw _PythonException( exception_type, exception_value, traceback );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, WRONG_EXCEPTION_TYPE_ERROR_MESSAGE, Py_TYPE( exception_type )->tp_name );

        throw _PythonException();
    }
}



static void THROW_IF_ERROR_OCCURED( void )
{
    if ( ERROR_OCCURED() )
    {
        throw _PythonException();
    }
}

static void THROW_IF_ERROR_OCCURED_NOT( PyObject *ignored )
{
    if ( ERROR_OCCURED() )
    {
        if ( PyErr_ExceptionMatches( ignored ))
        {
            PyErr_Clear();
        }
        else
        {
            throw _PythonException();
        }
    }
}

#endif
