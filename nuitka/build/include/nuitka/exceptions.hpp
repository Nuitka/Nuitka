//
//     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//
#ifndef __NUITKA_EXCEPTIONS_H__
#define __NUITKA_EXCEPTIONS_H__

NUITKA_MAY_BE_UNUSED static PyTracebackObject *MAKE_TRACEBACK( PyFrameObject *frame, int line )
{
    // assertFrameObject( frame );

    PyTracebackObject *result = PyObject_GC_New( PyTracebackObject, &PyTraceBack_Type );

    result->tb_next = NULL;
    result->tb_frame = frame;

    result->tb_lasti = 0;
    result->tb_lineno = line;

    Nuitka_GC_Track( result );

    return result;
}

// Helper that sets the current thread exception, releasing the current one, for use in this
// file only.
inline void _SET_CURRENT_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyObject * exception_tb )
{
    PyThreadState *thread_state = PyThreadState_GET();

    PyObject *old_type  = thread_state->exc_type;
    PyObject *old_value = thread_state->exc_value;
    PyObject *old_tb    = thread_state->exc_traceback;

    thread_state->exc_type = INCREASE_REFCOUNT( exception_type );
    thread_state->exc_value = INCREASE_REFCOUNT_X( exception_value );
    thread_state->exc_traceback = INCREASE_REFCOUNT_X( exception_tb );

    Py_XDECREF( old_type );
    Py_XDECREF( old_value );
    Py_XDECREF( old_tb );

    PySys_SetObject( (char *)"exc_type", exception_type );
    PySys_SetObject( (char *)"exc_value", exception_value );
    PySys_SetObject( (char *)"exc_traceback", exception_tb );
}

class _PythonException
{
public:
    _PythonException()
    {
        this->line = _current_line;

        this->_importFromPython();
    }

    _PythonException( PyObject *exception )
    {
        assertObject( exception );

        this->line = _current_line;

        Py_INCREF( exception );

        this->exception_type = exception;
        this->exception_value = NULL;
        this->exception_tb = NULL;
    }

    _PythonException( PyObject *exception, PyTracebackObject *traceback )
    {
        assertObject( exception );
        assertObject( traceback );

        this->line = _current_line;

        this->exception_type = exception;
        this->exception_value = NULL;
        this->exception_tb = (PyObject *)traceback;
    }

    _PythonException( PyObject *exception, PyObject *value, PyTracebackObject *traceback )
    {
        assertObject( exception );
        assertObject( value );
        assertObject( traceback );

        this->line = _current_line;

        this->exception_type = exception;
        this->exception_value = value;
        this->exception_tb = (PyObject *)traceback;
    }

    _PythonException( const _PythonException &other )
    {
        this->line            = other.line;

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

        this->line            = other.line;

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
        PyErr_Fetch( &this->exception_type, &this->exception_value, &this->exception_tb );

        assertObject( this->exception_type );
    }

    inline int getLine() const
    {
        return this->line;
    }

    inline void normalize()
    {
        PyErr_NormalizeException( &this->exception_type, &this->exception_value, &this->exception_tb );
    }

    inline bool matches( PyObject *exception ) const
    {
        return PyErr_GivenExceptionMatches( this->exception_type, exception ) || PyErr_GivenExceptionMatches( this->exception_value, exception );;
    }

    inline void toPython()
    {
        PyErr_Restore( this->exception_type, this->exception_value, this->exception_tb );

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
            PyErr_NormalizeException( &this->exception_type, &this->exception_value, &this->exception_tb );
        }

        return this->exception_type;
    }

    inline PyObject *getTraceback() const
    {
        return this->exception_tb;
    }

    inline void addTraceback( PyFrameObject *frame )
    {
        PyTracebackObject *traceback_new = MAKE_TRACEBACK( frame, this->line );

        traceback_new->tb_next = (PyTracebackObject *)this->exception_tb;
        this->exception_tb = (PyObject *)traceback_new;
    }

    inline void setTraceback( PyTracebackObject *traceback )
    {
        assertObject( traceback );

        // printf( "setTraceback %d\n", traceback->ob_refcnt );

        this->exception_tb = (PyObject *)traceback;
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

    inline PyObject *getObject()
    {
        PyErr_NormalizeException( &this->exception_type, &this->exception_value, &this->exception_tb );

        return this->exception_value;
    }

    void dump() const
    {
        PRINT_ITEMS( true, NULL, this->exception_type );
    }

private:
    friend class _PythonExceptionKeeper;

    // For the restore of saved ones.
    _PythonException( int line, PyObject *exception, PyObject *value, PyObject *traceback )
    {
        this->line = line;

        this->exception_type = exception;
        this->exception_value = value;
        this->exception_tb = traceback;
    }


    PyObject *exception_type, *exception_value, *exception_tb;
    int line;
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
        this->line = -1;
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
        this->line            = e.line;

        this->exception_type  = e.exception_type;
        this->exception_value = e.exception_value;
        this->exception_tb    = e.exception_tb;

        Py_XINCREF( this->exception_type );
        Py_XINCREF( this->exception_value );
        Py_XINCREF( this->exception_tb );

        this->keeping = true;
    }

    void rethrow()
    {
        if ( this->keeping )
        {
            Py_XINCREF( this->exception_type );
            Py_XINCREF( this->exception_value );
            Py_XINCREF( this->exception_tb );

            throw _PythonException( line, this->exception_type, this->exception_value, this->exception_tb );
        }
    }

    bool isEmpty() const
    {
        return !this->keeping;
    }

private:
    bool keeping;

    PyObject *exception_type, *exception_value, *exception_tb;
    int line;
};

class FrameExceptionKeeper
{
public:

    FrameExceptionKeeper()
    {
        this->frame_exc_type = NULL;
    }

    ~FrameExceptionKeeper()
    {
        if ( this->frame_exc_type != NULL )
        {
            _SET_CURRENT_EXCEPTION( this->frame_exc_type, this->frame_exc_value, this->frame_exc_traceback );
        }
    }

    // Preserve the exception early before the exception handler is set up, so that it can later
    // at function exit be restored.
    void preserveExistingException()
    {
        if ( this->frame_exc_type == NULL )
        {
            PyThreadState *thread_state = PyThreadState_GET();

            if ( this->frame_exc_type != NULL )
            {
                this->frame_exc_type = INCREASE_REFCOUNT( thread_state->exc_type );
                this->frame_exc_value = INCREASE_REFCOUNT_X( thread_state->exc_value );
                this->frame_exc_traceback = INCREASE_REFCOUNT_X( thread_state->exc_traceback );
            }
            else
            {
                this->frame_exc_type = Py_None;
                this->frame_exc_value = NULL;
                this->frame_exc_traceback = NULL;
            }
        }
    }

private:
    PyObject *frame_exc_type, *frame_exc_value, *frame_exc_traceback;

};

class ReturnException
{
};

class ContinueException
{
};

class BreakException
{
};

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( bool *traceback_indicator, PyObject *exception, PyTracebackObject *traceback )
{
    *traceback_indicator = true;

    if ( PyExceptionClass_Check( exception ) )
    {
        throw _PythonException( exception, traceback );
    }
    else if ( PyExceptionInstance_Check( exception ) )
    {
        throw _PythonException( INCREASE_REFCOUNT( PyExceptionInstance_Class( exception ) ), exception, traceback );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "exceptions must be old-style classes or derived from BaseException, not %s", exception->ob_type->tp_name );

        _PythonException to_throw;
        to_throw.setTraceback( traceback );

        throw to_throw;
    }
}

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyTracebackObject *traceback )
{
    if ( PyExceptionClass_Check( exception_type ) )
    {
        PyErr_NormalizeException( &exception_type, &value, (PyObject **)&traceback );
    }

    throw _PythonException( exception_type, value, traceback );
}

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( bool *traceback_indicator, PyObject *exception_type, PyObject *value, PyTracebackObject *traceback )
{
    *traceback_indicator = true;

    RAISE_EXCEPTION( exception_type, value, traceback );
}


NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static inline void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyObject *traceback )
{
    // Check traceback
    assert( PyTraceBack_Check( traceback ) );

    RAISE_EXCEPTION( exception_type, value, (PyTracebackObject *)traceback );
}

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( bool *traceback_indicator, PyObject *exception_type, PyObject *value, PyObject *traceback )
{
    *traceback_indicator = true;

    RAISE_EXCEPTION( exception_type, value, traceback );
}


NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static void RERAISE_EXCEPTION( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *type = tstate->exc_type != NULL ? tstate->exc_type : Py_None;
    PyObject *value = tstate->exc_value;
    PyObject *tb = tstate->exc_traceback;

    Py_INCREF( type );
    Py_XINCREF( value );
    Py_XINCREF( tb );

    RAISE_EXCEPTION( type, value, tb );
}

NUITKA_NO_RETURN NUITKA_MAY_BE_UNUSED static PyObject *THROW_EXCEPTION( PyObject *exception_type, PyObject *exception_value, PyTracebackObject *traceback, bool *traceback_flag )
{
    *traceback_flag = true;

    RAISE_EXCEPTION( exception_type, exception_value, traceback );
}

#endif
