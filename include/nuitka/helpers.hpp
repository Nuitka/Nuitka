//
//     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an attempt of building an optimizing Python compiler
//     that is compatible and integrates with CPython, but also works on its
//     own.
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
#ifndef __NUITKA_HELPERS_H__
#define __NUITKA_HELPERS_H__

#include "__constants.hpp"

// From CPython, to allow us quick access to the dictionary of an module, the structure is
// normally private, but we need it for quick access to the module dictionary.
typedef struct {
    PyObject_HEAD
    PyObject *md_dict;
} PyModuleObject;

template<typename... P>
static void PRINT_ITEMS( bool new_line, PyObject *file, P...eles );
static PyObject *INCREASE_REFCOUNT( PyObject *object );

extern int _current_line;

// Wraps a PyObject * you received or acquired from another container to
// simplify refcount handling when you're not going to use the object
// beyond the local scope. It will hold a reference to the wrapped object
// as long as the PyObjectTemporary is alive, and will release the reference
// when the wrapper is destroyed: this eliminates the need for manual DECREF
// calls on Python objects before returning from a method call.
//
// In effect, wrapping an object inside a PyObjectTemporary is equivalent to
// a deferred Py_DECREF() call on the wrapped object.

class PyObjectTemporary {
    public:
        explicit PyObjectTemporary( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            this->object = object;
        }

        PyObjectTemporary( const PyObjectTemporary &object ) = delete;

        ~PyObjectTemporary()
        {
            Py_DECREF( this->object );
        }

        PyObject *asObject()
        {
            assert( this->object->ob_refcnt > 0 );

            return this->object;
        }

        void assign( PyObject *object )
        {
            Py_DECREF( this->object );

            assert( object );
            assert( object->ob_refcnt > 0 );

            this->object = object;
        }

        void checkSanity( char const *message ) const
        {
            if ( this->object->ob_refcnt <= 0 )
            {
                puts( message );
                assert( false );
            }
        }

    private:

        PyObject *object;
};

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
            assert( exception );
            assert( exception->ob_refcnt > 0 );

            this->line = _current_line;

            Py_INCREF( exception );

            this->exception_type = exception;
            this->exception_value = NULL;
            this->exception_tb = NULL;
        }

        _PythonException( PyObject *exception, PyTracebackObject *traceback )
        {
            assert( exception );
            assert( exception->ob_refcnt > 0 );

            assert( traceback );
            assert( traceback->ob_refcnt > 0 );

            this->line = _current_line;

            this->exception_type = exception;
            this->exception_value = NULL;
            this->exception_tb = (PyObject *)traceback;
        }

        _PythonException( PyObject *exception, PyObject *value, PyTracebackObject *traceback )
        {
            assert( exception );
            assert( value );
            assert( traceback );
            assert( exception->ob_refcnt > 0 );
            assert( value->ob_refcnt > 0 );
            assert( traceback->ob_refcnt > 0 );

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
            assert( this->exception_type );
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

            // Restore only sets the current exception to the interpreter.
            PyThreadState *thread_state = PyThreadState_GET();

            PyObject *old_type  = thread_state->exc_type;
            PyObject *old_value = thread_state->exc_value;
            PyObject *old_tb    = thread_state->exc_traceback;

            thread_state->exc_type = this->exception_type;
            thread_state->exc_value = this->exception_value;
            thread_state->exc_traceback = this->exception_tb;

            Py_INCREF(  thread_state->exc_type );
            Py_XINCREF( thread_state->exc_value );
            Py_XINCREF(  thread_state->exc_traceback );

            Py_XDECREF( old_type );
            Py_XDECREF( old_value );
            Py_XDECREF( old_tb );

            PySys_SetObject( (char *)"exc_type", thread_state->exc_type );
            PySys_SetObject( (char *)"exc_value", thread_state->exc_value );
            PySys_SetObject( (char *)"exc_traceback", thread_state->exc_traceback );
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

        inline void setTraceback( PyTracebackObject *traceback )
        {
            assert( traceback );
            assert( traceback->ob_refcnt > 0 );

            // printf( "setTraceback %d\n", traceback->ob_refcnt );

            // Py_INCREF( traceback );
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

        PyObject *exception_type, *exception_value, *exception_tb;
        int line;
};

class _PythonExceptionKeeper
{
    public:
        _PythonExceptionKeeper()
        {
            saved = NULL;
        }

        ~_PythonExceptionKeeper()
        {
            if ( this->saved )
            {
                delete this->saved;
            }
        }

        void save( const _PythonException &e )
        {
            this->saved = new _PythonException( e );
        }

        void rethrow()
        {
            if ( this->saved )
            {
                throw *this->saved;
            }
        }

        bool isEmpty() const
        {
            return this->saved == NULL;
        }

    private:
        bool empty;

        _PythonException *saved;
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

// Helper functions for reference count handling in the fly.
NUITKA_MAY_BE_UNUSED static PyObject *INCREASE_REFCOUNT( PyObject *object )
{
    assert( object->ob_refcnt > 0 );

    Py_INCREF( object );

    return object;
}

NUITKA_MAY_BE_UNUSED static PyObject *DECREASE_REFCOUNT( PyObject *object )
{
    assert( object->ob_refcnt > 0 );

    Py_DECREF( object );

    return object;
}

#include "printing.hpp"

NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( PyObject *exception, PyTracebackObject *traceback )
{
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

NUITKA_MAY_BE_UNUSED static void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyTracebackObject *traceback )
{
    // TODO: Check traceback

    if ( PyExceptionClass_Check( exception_type ) )
    {
       PyErr_NormalizeException( &exception_type, &value, (PyObject **)&traceback );
    }

    throw _PythonException( exception_type, value, traceback );
}

NUITKA_MAY_BE_UNUSED static inline void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyObject *traceback )
{
    RAISE_EXCEPTION( exception_type, value, (PyTracebackObject *)traceback );
}

NUITKA_MAY_BE_UNUSED static void RERAISE_EXCEPTION( void )
{
    PyThreadState *tstate = PyThreadState_GET();

    PyObject *type = tstate->exc_type != NULL ? tstate->exc_type : Py_None;
    PyObject *value = tstate->exc_value;
    PyObject *tb = tstate->exc_traceback;

    // TODO: Clarify if these are necessary.
    Py_XINCREF( type );
    Py_XINCREF( value );
    Py_XINCREF( tb );

    RAISE_EXCEPTION( type, value, tb );
}


NUITKA_MAY_BE_UNUSED static bool CHECK_IF_TRUE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    int status = PyObject_IsTrue( object );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    return status == 1;
}

NUITKA_MAY_BE_UNUSED static bool CHECK_IF_FALSE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    int status = PyObject_Not( object );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    return status == 1;
}

NUITKA_MAY_BE_UNUSED static PyObject *BOOL_FROM( bool value )
{
    return value ? _python_bool_True : _python_bool_False;
}

NUITKA_MAY_BE_UNUSED static PyObject *UNARY_NOT( PyObject *object )
{
    int result = PyObject_Not( object );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 1 );
}

typedef PyObject *(binary_api)( PyObject *, PyObject * );

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION( binary_api api, PyObject *operand1, PyObject *operand2 )
{
    int line = _current_line;
    PyObject *result = api( operand1, operand2 );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

typedef PyObject *(unary_api)( PyObject * );

NUITKA_MAY_BE_UNUSED static PyObject *UNARY_OPERATION( unary_api api, PyObject *operand )
{
    PyObject *result = api( operand );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *POWER_OPERATION( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_Power( operand1, operand2, Py_None );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *POWER_OPERATION_INPLACE( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_InPlacePower( operand1, operand2, Py_None );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE( int opid, PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, opid );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL( int opid, PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    int result = PyObject_RichCompareBool( operand1, operand2, opid );
    _current_line = line;

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return result == 1;
}


NUITKA_MAY_BE_UNUSED static PyObject *SEQUENCE_CONTAINS( PyObject *sequence, PyObject *element )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 1 );
}

NUITKA_MAY_BE_UNUSED static PyObject *SEQUENCE_CONTAINS_NOT( PyObject *sequence, PyObject *element )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 0 );
}

NUITKA_MAY_BE_UNUSED static bool SEQUENCE_CONTAINS_BOOL( PyObject *sequence, PyObject *element )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return result == 1;
}

NUITKA_MAY_BE_UNUSED static bool SEQUENCE_CONTAINS_NOT_BOOL( PyObject *sequence, PyObject *element )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return result == 0;
}

// Helper functions to debug the compiler operation.
NUITKA_MAY_BE_UNUSED static void PRINT_REFCOUNT( PyObject *object )
{
   PyObject *stdout = PySys_GetObject((char *)"stdout");

   if (unlikely( stdout == NULL ))
   {
      PyErr_Format( PyExc_RuntimeError, "problem with stdout" );
      throw _PythonException();
   }

   char buffer[1024];
   sprintf( buffer, " refcnt %zd ", object->ob_refcnt );

   if (unlikely( PyFile_WriteString(buffer, stdout) == -1 ))
   {
      throw _PythonException();
   }

}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION( PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    assert( function_object != NULL );
    assert( function_object->ob_refcnt > 0 );
    assert( positional_args != NULL );
    assert( positional_args->ob_refcnt > 0 );
    assert( named_args == NULL || named_args->ob_refcnt > 0 );

    int line = _current_line;
    PyObject *result = PyObject_Call( function_object, positional_args, named_args );
    _current_line = line;

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static inline bool Nuitka_Function_Check( PyObject *object );
static inline PyObject *Nuitka_Function_GetName( PyObject *object );

static inline bool Nuitka_Generator_Check( PyObject *object );
static inline PyObject *Nuitka_Generator_GetName( PyObject *object );

#if PY_MAJOR_VERSION < 3
#define Nuitka_String_AsString PyString_AsString
#else
#define Nuitka_String_AsString _PyUnicode_AsString
#endif

static char const *GET_CALLABLE_NAME( PyObject *object )
{
    if ( Nuitka_Function_Check( object ) )
    {
        return Nuitka_String_AsString( Nuitka_Function_GetName( object ) );
    }
    else if ( Nuitka_Generator_Check( object ) )
    {
        return Nuitka_String_AsString( Nuitka_Generator_GetName( object ) );
    }
    else if ( PyMethod_Check( object ) )
    {
        return PyEval_GetFuncName( PyMethod_GET_FUNCTION( object ) );
    }
    else if ( PyFunction_Check( object ) )
    {
        return Nuitka_String_AsString( ((PyFunctionObject*)object)->func_name );
    }
#if PY_MAJOR_VERSION < 3
    else if ( PyInstance_Check( object ) )
    {
        return Nuitka_String_AsString( ((PyInstanceObject*)object)->in_class->cl_name );
    }
    else if ( PyClass_Check( object ) )
    {
        return Nuitka_String_AsString(((PyClassObject*)object)->cl_name );
    }
#endif
    else if ( PyCFunction_Check( object ) )
    {
        return ((PyCFunctionObject*)object)->m_ml->ml_name;
    }
    else
    {
        return object->ob_type->tp_name;
    }
}

static const char *GET_CALLABLE_DESC( PyObject *object )
{
    if ( Nuitka_Function_Check( object ) || Nuitka_Generator_Check( object ) || PyMethod_Check( object ) || PyFunction_Check( object ) || PyCFunction_Check( object ) )
    {
        return "()";
    }
#if PY_MAJOR_VERSION < 3
    else if ( PyClass_Check( object ) )
    {
        return " constructor";
    }
    else if ( PyInstance_Check( object ))
    {
        return " instance";
    }
#endif
    else
    {
        return " object";
    }
}


NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_DICT( PyObject *dict_star_arg, PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), dict_star_arg->ob_type->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_Copy( named_args ) );

    int status = PyDict_Merge( result.asObject(), dict_star_arg, 1 );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    if (unlikely( PyMapping_Size( dict_star_arg ) + PyDict_Size( named_args ) != PyDict_Size( result.asObject() )))
    {
        PyObject *key, *value;
        Py_ssize_t pos = 0;

        while ( PyDict_Next( named_args, &pos, &key, &value ) )
        {
            if ( PyMapping_HasKey( dict_star_arg, key ))
            {
                PyErr_Format( PyExc_TypeError, "%s%s got multiple values for keyword argument '%s'", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Nuitka_String_AsString( key ) );
                throw _PythonException();
            }
        }

        PyErr_Format( PyExc_RuntimeError, "%s%s got multiple values for keyword argument", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ) );
        throw _PythonException();
    }

    // TODO: This is likely only useful for a paranoid mode and can be done faster for a
    // dict by checking if a member has a specific value, because of a optimization

    PyObject *key, *value;
    Py_ssize_t pos = 0;

    while ( PyDict_Next( result.asObject(), &pos, &key, &value ) )
    {
#if PY_MAJOR_VERSION < 3
        if (unlikely( PyString_Check( key ) == 0 && PyUnicode_Check( key ) == 0 ))
#else
        if (unlikely( PyUnicode_Check( key ) == 0 ))
#endif
        {
            PyErr_Format( PyExc_TypeError, "%s%s keywords must be strings", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ) );
            throw _PythonException();
        }
    }

    return CALL_FUNCTION( result.asObject(), positional_args, function_object );
}

NUITKA_MAY_BE_UNUSED static PyObject *MERGE_STAR_LIST_ARGS( PyObject *list_star_arg, PyObject *positional_args, PyObject *function_object )
{
    PyObject *list_star_arg_tuple;

    if ( PyTuple_Check( list_star_arg ) == 0 )
    {
        list_star_arg_tuple = PySequence_Tuple( list_star_arg );

        if (unlikely( list_star_arg_tuple == NULL ))
        {
            if ( PyErr_ExceptionMatches( PyExc_TypeError ) )
            {
                PyErr_Format( PyExc_TypeError, "%s%s argument after * must be a sequence, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), list_star_arg->ob_type->tp_name );
            }

            throw _PythonException();
        }
    }
    else
    {
        list_star_arg_tuple = list_star_arg;
    }

    // TODO: This is actually only a TUPLE_CONCAT from here on.

    int positional_args_size = PyTuple_Size( positional_args );
    int list_star_arg_size = PyTuple_Size( list_star_arg_tuple );

    PyObject *result = PyTuple_New( positional_args_size  + list_star_arg_size );

    for ( int i = 0; i < positional_args_size; i++ )
    {
        PyTuple_SET_ITEM( result, i, INCREASE_REFCOUNT( PyTuple_GET_ITEM( positional_args, i ) ) );
    }

    for ( int i = 0; i < list_star_arg_size; i++ )
    {
        PyTuple_SET_ITEM( result, positional_args_size + i, INCREASE_REFCOUNT( PyTuple_GET_ITEM( list_star_arg_tuple, i ) ) );
    }

    if ( list_star_arg_tuple != list_star_arg )
    {
        Py_DECREF( list_star_arg_tuple );
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_LIST( PyObject *list_star_arg, PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    return CALL_FUNCTION( named_args, PyObjectTemporary( MERGE_STAR_LIST_ARGS( list_star_arg, positional_args, function_object ) ).asObject(), function_object );
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_BOTH( PyObject *dict_star_arg, PyObject *list_star_arg, PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    return CALL_FUNCTION_STAR_DICT( dict_star_arg, named_args, PyObjectTemporary( MERGE_STAR_LIST_ARGS( list_star_arg, positional_args, function_object ) ).asObject(), function_object );
}

NUITKA_MAY_BE_UNUSED static long TO_LONG( PyObject *value )
{
    long result = PyInt_AsLong( value );

    if (unlikely( result == -1 && PyErr_Occurred() ))
    {
        throw _PythonException();
    }

    return result;
}



NUITKA_MAY_BE_UNUSED static PyObject *TO_TUPLE( PyObject *seq_obj )
{
    PyObject *result = PySequence_Tuple( seq_obj );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

template<typename... P>
static PyObject *MAKE_TUPLE( P...eles )
{
    int size = sizeof...(eles);

    if ( size > 0 )
    {
        PyObject *elements[] = {eles...};

        for ( Py_ssize_t i = 0; i < size; i++ )
        {
            assert( elements[ i ] != NULL );
            assert( elements[ i ]->ob_refcnt > 0 );
        }

        PyObject *result = PyTuple_New( size );

        if (unlikely( result == NULL ))
        {
            throw _PythonException();
        }

        for ( Py_ssize_t i = 0; i < size; i++ )
        {
            PyTuple_SET_ITEM( result, i, INCREASE_REFCOUNT( elements[ size - 1 - i ] ));
        }

        assert( result->ob_refcnt == 1 );

        return result;
    }
    else
    {
        return INCREASE_REFCOUNT( _python_tuple_empty );
    }
}

template<typename... P>
static PyObject *MAKE_LIST( P...eles )
{
    PyObject *elements[] = {eles...};

    int size = sizeof...(eles);

    PyObject *result = PyList_New( size );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    for (Py_ssize_t i = 0; i < size; i++ )
    {
        assert( elements[ i ] != NULL );
        assert( elements[ i ]->ob_refcnt > 0 );

        PyList_SET_ITEM( result, i, elements[ size - 1 - i ] );
    }

    assert( result->ob_refcnt == 1 );

    return result;
}

template<typename... P>
static PyObject *MAKE_DICT( P...eles )
{
    PyObject *elements[] = {eles...};
    int size = sizeof...(eles);

    assert( size % 2 == 0 );

    PyObject *result = PyDict_New();

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    for( int i = 0; i < size; i += 2 )
    {
        int status = PyDict_SetItem( result, elements[i], elements[i+1] );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static void DICT_SET_ITEM( PyObject *dict, PyObject *key, PyObject *value )
{
    int status = PyDict_SetItem( dict, key, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

#if PY_MAJOR_VERSION < 3
static PyDictEntry *GET_PYDICT_ENTRY( PyDictObject *dict, PyStringObject *key )
#else
static PyDictEntry *GET_PYDICT_ENTRY( PyDictObject *dict, PyUnicodeObject *key )
#endif
{
    assert( PyDict_CheckExact( dict ) );

    // Only improvement would be to identify how to ensure that the hash is computed
    // already. Calling hash early on could do that potentially.
#if PY_MAJOR_VERSION < 3
    long hash = key->ob_shash;
#else
    long hash = key->hash;
#endif

    if ( hash == -1 )
    {
#if PY_MAJOR_VERSION < 3
        hash = PyString_Type.tp_hash( (PyObject *)key );
        key->ob_shash = hash;
#else
        hash = PyUnicode_Type.tp_hash( (PyObject *)key );
        key->hash = hash;
#endif
    }

    PyDictEntry *entry = dict->ma_lookup( dict, (PyObject *)key, hash );

    // The "entry" cannot be NULL, it can only be empty for a string dict lookup, but at
    // least assert it.
    assert( entry != NULL );

    return entry;
}

#if PY_MAJOR_VERSION < 3
static PyDictEntry *GET_PYDICT_ENTRY( PyModuleObject *module, PyStringObject *key )
#else
static PyDictEntry *GET_PYDICT_ENTRY( PyModuleObject *module, PyUnicodeObject *key )
#endif
{
    // Idea similar to LOAD_GLOBAL in CPython. Because the variable name is a string, we
    // can shortcut much of the dictionary code by using its hash and dictionary knowledge
    // here.

    PyDictObject *dict = (PyDictObject *)(module->md_dict);

    return GET_PYDICT_ENTRY( dict, key );
}

template<typename... P>
static PyObject *MAKE_SET( P...eles )
{
    PyObject *tuple = MAKE_TUPLE( eles... );

    PyObject *result = PySet_New( tuple );

    Py_DECREF( tuple );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_STATIC_METHOD( PyObject *method )
{
    PyObject *attempt = PyStaticMethod_New( method );

    if ( attempt )
    {
        return attempt;
    }
    else
    {
        PyErr_Clear();

        return method;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *SEQUENCE_ELEMENT( PyObject *sequence, Py_ssize_t element )
{
    PyObject *result = PySequence_GetItem( sequence, element );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_ITERATOR( PyObject *iterated )
{
    PyObject *result = PyObject_GetIter( iterated );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

// Return the next item of an iterator. Avoiding any exception for end of iteration,
// callers must deal with NULL return as end of iteration, but will know it wasn't an
// Python exception, that will show as a thrown exception.
NUITKA_MAY_BE_UNUSED static PyObject *ITERATOR_NEXT( PyObject *iterator )
{
    assert( iterator != NULL );
    assert( iterator->ob_refcnt > 0 );

    int line = _current_line;
    PyObject *result = PyIter_Next( iterator );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        if ( PyErr_Occurred() != NULL )
        {
            throw _PythonException();
        }
    }
    else
    {
        assert( result->ob_refcnt > 0 );
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static inline PyObject *UNPACK_NEXT( PyObject *iterator, int seq_size_so_far )
{
    assert( iterator != NULL );
    assert( iterator->ob_refcnt > 0 );

    PyObject *result = PyIter_Next( iterator );

    if (unlikely( result == NULL ))
    {
        if ( !PyErr_Occurred() )
        {
            if ( seq_size_so_far == 1 )
            {
                PyErr_Format( PyExc_ValueError, "need more than 1 value to unpack" );
            }
            else
            {
                PyErr_Format( PyExc_ValueError, "need more than %d values to unpack", seq_size_so_far );
            }
        }

        throw _PythonException();
    }

    assert( result->ob_refcnt > 0 );

    return result;
}

NUITKA_MAY_BE_UNUSED static inline void UNPACK_ITERATOR_CHECK( PyObject *iterator )
{
    PyObject *attempt = PyIter_Next( iterator );

    if (likely( attempt == NULL ))
    {
        if (unlikely( PyErr_Occurred() ))
        {
            throw _PythonException();
        }
    }
    else
    {
        Py_DECREF( attempt );

        PyErr_Format( PyExc_ValueError, "too many values to unpack" );
        throw _PythonException();
    }
}


NUITKA_MAY_BE_UNUSED static PyObject *SELECT_IF_TRUE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    if ( CHECK_IF_TRUE( object ) )
    {
        return object;
    }
    else
    {
        Py_DECREF( object );

        return NULL;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *SELECT_IF_FALSE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    if ( CHECK_IF_FALSE( object ) )
    {
        return object;
    }
    else
    {
        Py_DECREF( object );

        return NULL;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SUBSCRIPT( PyObject *source, PyObject *subscript )
{
    assert( source );
    assert( source->ob_refcnt > 0 );
    assert( subscript );
    assert( subscript->ob_refcnt > 0 );

    PyObject *result = PyObject_GetItem( source, subscript );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static bool HAS_KEY( PyObject *source, PyObject *key )
{
    assert( source );
    assert( source->ob_refcnt > 0 );
    assert( key );
    assert( key->ob_refcnt > 0 );

    return PyMapping_HasKey( source, key ) != 0;
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_VARS( PyObject *source )
{
    assert( source );
    assert( source->ob_refcnt > 0 );

    PyObject *result = PyObject_GetAttr( source, _python_str_plain___dict__ );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}


NUITKA_MAY_BE_UNUSED static void SET_SUBSCRIPT( PyObject *target, PyObject *subscript, PyObject *value )
{
    assert( target );
    assert( target->ob_refcnt > 0 );
    assert( subscript );
    assert( subscript->ob_refcnt > 0 );
    assert( value );
    assert( value->ob_refcnt > 0 );

    int status = PyObject_SetItem( target, subscript, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

NUITKA_MAY_BE_UNUSED static void DEL_SUBSCRIPT( PyObject *target, PyObject *subscript )
{
    assert( target );
    assert( target->ob_refcnt > 0 );
    assert( subscript );
    assert( subscript->ob_refcnt > 0 );

    int status = PyObject_DelItem( target, subscript );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}


NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SLICE( PyObject *source, Py_ssize_t lower, Py_ssize_t upper )
{
    assert( source );
    assert( source->ob_refcnt > 0 );

    PyObject *result = PySequence_GetSlice( source, lower, upper);

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static void SET_SLICE( PyObject *target, Py_ssize_t lower, Py_ssize_t upper, PyObject *value )
{
    assert( target );
    assert( target->ob_refcnt > 0 );
    assert( value );
    assert( value->ob_refcnt > 0 );

    int status = PySequence_SetSlice( target, lower, upper, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

static Py_ssize_t CONVERT_TO_INDEX( PyObject *value );

NUITKA_MAY_BE_UNUSED static void DEL_SLICE( PyObject *target, PyObject *lower, PyObject *upper )
{
    assert( target );
    assert( target->ob_refcnt > 0 );

    if ( target->ob_type->tp_as_sequence && target->ob_type->tp_as_sequence->sq_ass_slice )
    {
        int status = PySequence_DelSlice( target, lower != Py_None ? CONVERT_TO_INDEX( lower ) : 0, upper != Py_None ? CONVERT_TO_INDEX( upper ) : PY_SSIZE_T_MAX );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
    else
    {
        PyObject *slice = PySlice_New( lower, upper, NULL );

        if (slice == NULL)
        {
            throw _PythonException();
        }

        int status = PyObject_DelItem( target, slice );

        Py_DECREF( slice );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_SLICEOBJ( PyObject *start, PyObject *stop, PyObject *step )
{
    assert( start );
    assert( start->ob_refcnt > 0 );
    assert( stop );
    assert( stop->ob_refcnt > 0 );
    assert( step );
    assert( step->ob_refcnt > 0 );

    PyObject *result = PySlice_New( start, stop, step );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static Py_ssize_t CONVERT_TO_INDEX( PyObject *value )
{
    assert( value );
    assert( value->ob_refcnt > 0 );

#if PY_MAJOR_VERSION < 3
    if ( PyInt_Check( value ) )
    {
        return PyInt_AS_LONG( value );
    }
    else
#endif
    if ( PyIndex_Check( value ) )
    {
        Py_ssize_t result = PyNumber_AsSsize_t( value, NULL );

        if (unlikely( result == -1 && PyErr_Occurred() ))
        {
            throw _PythonException();
        }

        return result;
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "slice indices must be integers or None or have an __index__ method" );
        throw _PythonException();
    }
}

#if PY_MAJOR_VERSION < 3
NUITKA_MAY_BE_UNUSED static PyObject *FIND_ATTRIBUTE_IN_CLASS( PyClassObject *klass, PyObject *attr_name )
{
    PyObject *result = GET_PYDICT_ENTRY( (PyDictObject *)klass->cl_dict, (PyStringObject *)attr_name )->me_value;

    if ( result == NULL )
    {
        Py_ssize_t base_count = PyTuple_Size( klass->cl_bases );

        for( Py_ssize_t i = 0; i < base_count; i++ )
        {
            result = FIND_ATTRIBUTE_IN_CLASS( (PyClassObject *)PyTuple_GetItem( klass->cl_bases, i ), attr_name );

            if ( result )
            {
                break;
            }
        }
    }

    return result;
}
#endif

#if PY_MAJOR_VERSION < 3
NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_INSTANCE( PyObject *source, PyObject *attr_name )
{
    assert( PyInstance_Check( source ) );
    assert( PyString_Check( attr_name ) );

    PyInstanceObject *source_instance = (PyInstanceObject *)source;

    // TODO: The special cases should get their own SET_ATTRIBUTE variant on the code
    // generation level as SET_ATTRIBUTE is called with constants only.
    if (unlikely( attr_name == _python_str_plain___dict__ ))
    {
        return INCREASE_REFCOUNT( source_instance->in_dict );
    }
    else if (unlikely( attr_name == _python_str_plain___class__ ))
    {
        return INCREASE_REFCOUNT( (PyObject *)source_instance->in_class );
    }
    else
    {
        // Try the instance dict first.
        PyObject *result = GET_PYDICT_ENTRY( (PyDictObject *)source_instance->in_dict, (PyStringObject *)attr_name )->me_value;

        if ( result )
        {
            return INCREASE_REFCOUNT( result );
        }

        // Next see if a class has it
        result = FIND_ATTRIBUTE_IN_CLASS( source_instance->in_class, attr_name );

        int line = _current_line;

        if ( result )
        {
            descrgetfunc func = Py_TYPE( result )->tp_descr_get;

            if ( func )
            {
                result = func( result, source, (PyObject *)source_instance->in_class );

                if (unlikely( result == NULL ))
                {
                    throw _PythonException();
                }

                return result;
            }
            else
            {
                return INCREASE_REFCOUNT( result );
            }
        }

        if (unlikely( PyErr_Occurred() && !PyErr_ExceptionMatches( PyExc_AttributeError ) ))
        {
            _current_line = line;
            throw _PythonException();
        }

        // Finally allow a __getattr__ to handle it or else it's an error.
        if ( source_instance->in_class->cl_getattr == NULL )
        {
            PyErr_Format( PyExc_AttributeError, "%s instance has no attribute '%s'", PyString_AS_STRING( source_instance->in_class->cl_name ), PyString_AS_STRING( attr_name ) );

            _current_line = line;
            throw _PythonException();
        }
        else
        {
            PyErr_Clear();

            PyObjectTemporary args( MAKE_TUPLE( attr_name, source ) );

            PyObject *result = PyObject_Call( source_instance->in_class->cl_getattr, args.asObject(), NULL );

            if (unlikely( result == NULL ))
            {
                _current_line = line;
                throw _PythonException();
            }

            return result;
        }
    }
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_ATTRIBUTE( PyObject *source, PyObject *attr_name )
{
    assert( source );
    assert( source->ob_refcnt > 0 );
    assert( attr_name );
    assert( attr_name->ob_refcnt > 0 );

#if PY_MAJOR_VERSION < 3
    if ( PyInstance_Check( source ) )
    {
        return LOOKUP_INSTANCE( source, attr_name );
    }
    else
#endif
    {
        int line = _current_line;
        PyObject *result = PyObject_GetAttr( source, attr_name );
        _current_line = line;

        if (unlikely( result == NULL ))
        {
            throw _PythonException();
        }

        assert( result->ob_refcnt > 0 );

        return result;
    }
}

NUITKA_MAY_BE_UNUSED static void SET_ATTRIBUTE( PyObject *target, PyObject *attr_name, PyObject *value )
{
    assert( target );
    assert( target->ob_refcnt > 0 );
    assert( attr_name );
    assert( attr_name->ob_refcnt > 0 );
    assert( value );
    assert( value->ob_refcnt > 0 );

#if PY_MAJOR_VERSION < 3
    if ( PyInstance_Check( target ) )
    {
        PyInstanceObject *target_instance = (PyInstanceObject *)target;

        // TODO: The special cases should get their own SET_ATTRIBUTE variant on the code
        // generation level as SET_ATTRIBUTE is called with constants only.
        if (unlikely( attr_name == _python_str_plain___dict__ ))
        {
            if (unlikely( !PyDict_Check( value ) ))
            {
                PyErr_SetString( PyExc_TypeError, "__dict__ must be set to a dictionary" );
                throw _PythonException();
            }

            PyObjectTemporary old_dict( target_instance->in_dict );

            target_instance->in_dict = INCREASE_REFCOUNT( value );
        }
        else if (unlikely( attr_name == _python_str_plain___class__ ))
        {
            if (unlikely( !PyClass_Check( value ) ))
            {
                PyErr_SetString( PyExc_TypeError, "__class__ must be set to a class" );
                throw _PythonException();
            }

            PyObjectTemporary old_class( (PyObject *)target_instance->in_class );

            target_instance->in_class = (PyClassObject *)INCREASE_REFCOUNT( value );
        }
        else
        {
            if ( target_instance->in_class->cl_setattr != NULL )
            {
                PyObjectTemporary args( MAKE_TUPLE( value, attr_name, target ) );

                PyObject *result = PyObject_Call( target_instance->in_class->cl_setattr, args.asObject(), NULL );

                if (unlikely( result == NULL ))
                {
                    throw _PythonException();
                }

                Py_DECREF( result );
            }
            else
            {
                int status = PyDict_SetItem( target_instance->in_dict, attr_name, value );

                if (unlikely( status == -1 ))
                {
                    throw _PythonException();
                }
            }
        }
    }
    else
#endif
    {
        int status = PyObject_SetAttr( target, attr_name, value );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

NUITKA_MAY_BE_UNUSED static void DEL_ATTRIBUTE( PyObject *target, PyObject *attr_name )
{
    assert( target );
    assert( target->ob_refcnt > 0 );
    assert( attr_name );
    assert( attr_name->ob_refcnt > 0 );

    int status = PyObject_DelAttr( target, attr_name );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *LOOKUP_SPECIAL( PyObject *source, PyObject *attr_name )
{
#if PY_MAJOR_VERSION < 3
    if ( PyInstance_Check( source ) )
    {
        return LOOKUP_INSTANCE( source, attr_name );
    }
#endif

    // TODO: There is heavy optimization in CPython to avoid it. Potentially that's worth
    // it to imitate that.

    PyObject *result = _PyType_Lookup( Py_TYPE( source ), attr_name );

    if (likely( result ))
    {
        descrgetfunc func = Py_TYPE( result )->tp_descr_get;

        if ( func == NULL )
        {
            return INCREASE_REFCOUNT( result );
        }
        else
        {
            PyObject *func_result = func( result, source, (PyObject *)( Py_TYPE( source ) ) );

            if (unlikely( func_result == NULL ))
            {
                throw _PythonException();
            }

            return func_result;
        }
    }

    PyErr_SetObject( PyExc_AttributeError, attr_name );
    throw _PythonException();
}

// Necessary to abstract the with statement lookup difference between pre-Python2.7 and
// others. Since Python 2.7 the code does no full attribute lookup anymore, but instead
// treats enter and exit as specials.
NUITKA_MAY_BE_UNUSED static inline PyObject *LOOKUP_WITH_ENTER( PyObject *source )
{
#if PY_MAJOR_VERSION < 3 && PY_MINOR_VERSION < 7
    return LOOKUP_ATTRIBUTE( source, _python_str_plain___enter__ );
#else
    return LOOKUP_SPECIAL( source, _python_str_plain___enter__ );
#endif
}

NUITKA_MAY_BE_UNUSED static inline PyObject *LOOKUP_WITH_EXIT( PyObject *source )
{
#if PY_MAJOR_VERSION < 3 && PY_MINOR_VERSION < 7
    return LOOKUP_ATTRIBUTE( source, _python_str_plain___exit__ );
#else
    return LOOKUP_SPECIAL( source, _python_str_plain___exit__ );
#endif
}

NUITKA_MAY_BE_UNUSED static void APPEND_TO_LIST( PyObject *list, PyObject *item )
{
    int status = PyList_Append( list, item );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

NUITKA_MAY_BE_UNUSED static void ADD_TO_SET( PyObject *set, PyObject *item )
{
    int status = PySet_Add( set, item );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}



NUITKA_MAY_BE_UNUSED static PyObject *SEQUENCE_CONCAT( PyObject *seq1, PyObject *seq2 )
{
    PyObject *result = PySequence_Concat( seq1, seq2 );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}


class PyObjectLocalDictVariable {
    public:
        explicit PyObjectLocalDictVariable( PyObject *storage, PyObject *var_name, PyObject *object = NULL )
        {
            this->storage    = (PyDictObject *) storage;
            this->var_name   = (PyStringObject *)var_name;

            if ( object != NULL )
            {
#ifndef __NUITKA_NO_ASSERT__
                int status =
#endif
                    PyDict_SetItem( storage, var_name, object );

                assert( status == 0 );
            }
        }

        PyObject *asObject() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY(
                this->storage,
                this->var_name
            );
            PyObject *result = entry->me_value;

            if (unlikely( result == NULL ))
            {
                PyErr_Format(
                    PyExc_UnboundLocalError,
                    "local variable '%s' referenced before assignment",
                    Nuitka_String_AsString( (PyObject *)this->var_name )
                );
                throw _PythonException();
            }

            assert( result->ob_refcnt > 0 );

            return result;
        }

        PyObject *asObject1() const
        {
            return INCREASE_REFCOUNT( this->asObject() );
        }

        void operator=( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

#ifndef __NUITKA_NO_ASSERT__
            int status =
#endif
                PyDict_SetItem(
                    (PyObject *)this->storage,
                    (PyObject *)this->var_name,
                    object
                );
            assert( status == 0 );
        }

        bool isInitialized() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY(
                this->storage,
                this->var_name
            );

            return entry->me_value != NULL;
        }

        void del()
        {
            int status = PyDict_DelItem(
                (PyObject *)this->storage,
                (PyObject *)this->var_name
            );

            if (unlikely( status == -1 ))
            {
                // TODO: Probably an error should be raised?
                PyErr_Clear();
            }
        }


        PyObject *getVariableName() const
        {
            return (PyObject *)this->var_name;
        }

    private:
        PyDictObject *storage;
        PyStringObject *var_name;
};

class PyObjectLocalVariable {
    public:
        explicit PyObjectLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = false )
        {
            this->var_name   = var_name;
            this->object     = object;
            this->free_value = free_value;
        }

        explicit PyObjectLocalVariable()
        {
            this->var_name   = NULL;
            this->object     = NULL;
            this->free_value = false;
        }

        ~PyObjectLocalVariable()
        {
            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }
        }

        void setVariableName( PyObject *var_name )
        {
            assert( var_name );
            assert( var_name->ob_refcnt > 0 );

            assert( this->var_name == NULL);

            this->var_name = var_name;
        }

        void operator=( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            if ( this->free_value )
            {
                PyObject *old_object = this->object;

                this->object = object;

                // Free old value if any available and owned.
                Py_DECREF( old_object );
            }
            else
            {
                this->object = object;
                this->free_value = true;
            }
        }

        PyObject *asObject() const
        {
            if ( this->object == NULL && this->var_name != NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", Nuitka_String_AsString( this->var_name ) );
                throw _PythonException();
            }

            assert( this->object );
            assert( this->object->ob_refcnt > 0 );

            return this->object;
        }

        PyObject *asObject1() const
        {
            return INCREASE_REFCOUNT( this->asObject() );
        }

        bool isInitialized() const
        {
            return this->object != NULL;
        }

        void del()
        {
            if ( this->object == NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", Nuitka_String_AsString( this->var_name ) );
                throw _PythonException();
            }

            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }

            this->object = NULL;
            this->free_value = false;
        }

        PyObject *getVariableName() const
        {
            return this->var_name;
        }

    private:

        PyObject *var_name;
        PyObject *object;
        bool free_value;
};

class PyObjectSharedStorage
{
    public:
        explicit PyObjectSharedStorage( PyObject *var_name, PyObject *object, bool free_value )
        {
            assert( object == NULL || object->ob_refcnt > 0 );

            this->var_name   = var_name;
            this->object     = object;
            this->free_value = free_value;
            this->ref_count  = 1;
        }

        ~PyObjectSharedStorage()
        {
            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }
        }

        void operator=( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            if ( this->free_value )
            {
                PyObject *old_object = this->object;

                this->object = object;

                // Free old value if any available and owned.
                Py_DECREF( old_object );
            }
            else
            {
                this->object = object;
                this->free_value = true;
            }
        }

        inline PyObject *getVarName() const
        {
            return this->var_name;
        }

        PyObject *var_name;
        PyObject *object;
        bool free_value;
        int ref_count;
};

class PyObjectSharedLocalVariable
{
    public:
        explicit PyObjectSharedLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = false )
        {
            this->storage = new PyObjectSharedStorage( var_name, object, free_value );
        }

        explicit PyObjectSharedLocalVariable()
        {
            this->storage = NULL;
        }

        ~PyObjectSharedLocalVariable()
        {
            if ( this->storage )
            {
                assert( this->storage->ref_count > 0 );
                this->storage->ref_count -= 1;

                if (this->storage->ref_count == 0)
                {
                    delete this->storage;
                }
            }
        }

        void setVariableName( PyObject *var_name )
        {
            assert( this->storage == NULL );

            this->storage = new PyObjectSharedStorage( var_name, NULL, false );
        }

        void shareWith( const PyObjectSharedLocalVariable &other )
        {
            assert( this->storage == NULL );
            assert( other.storage != NULL );

            this->storage = other.storage;
            this->storage->ref_count += 1;
        }

        void operator=( PyObject *object )
        {
            this->storage->operator=( object );
        }

        PyObject *asObject() const
        {
            assert( this->storage );

            if ( this->storage->object == NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "free variable '%s' referenced before assignment in enclosing scope", Nuitka_String_AsString( this->storage->getVarName() ) );
                throw _PythonException();

            }

            if ( (this->storage->object)->ob_refcnt == 0 )
            {
                PyErr_Format( PyExc_UnboundLocalError, "free variable '%s' referenced after its finalization in enclosing scope", Nuitka_String_AsString( this->storage->getVarName() ) );
                throw _PythonException();
            }

            return this->storage->object;
        }

        PyObject *asObject1() const
        {
            return INCREASE_REFCOUNT( this->asObject() );
        }

        bool isInitialized() const
        {
            return this->storage->object != NULL;
        }

        PyObject *getVariableName() const
        {
            return this->storage->var_name;
        }

    private:
        PyObjectSharedLocalVariable( PyObjectSharedLocalVariable & );

        PyObjectSharedStorage *storage;
};

extern PyModuleObject *_module_builtin;

class PyObjectGlobalVariable
{
    public:
        explicit PyObjectGlobalVariable( PyObject **module_ptr, PyObject **var_name )
        {
            assert( module_ptr );
            assert( var_name );

            this->module_ptr = (PyModuleObject **)module_ptr;
            this->var_name   = (PyStringObject **)var_name;
        }

        PyObject *asObject0() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assert( entry->me_value->ob_refcnt > 0 );

                return entry->me_value;
            }

            entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assert( entry->me_value->ob_refcnt > 0 );

                return entry->me_value;
            }

            PyErr_Format( PyExc_NameError, "global name '%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
            throw _PythonException();
        }

        PyObject *asObject() const
        {
            return INCREASE_REFCOUNT( this->asObject0() );
        }

        PyObject *asObject( PyObject *dict ) const
        {
            if ( PyDict_Contains( dict, (PyObject *)*this->var_name ) )
            {
                return PyDict_GetItem( dict, (PyObject *)*this->var_name );
            }
            else
            {
                return this->asObject();
            }
        }

        void assign( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = value;

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name, value );

                Py_DECREF( value );
            }
        }

        void assign0( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = INCREASE_REFCOUNT( value );

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name, value );
            }
        }

        void del() const
        {
            int status = PyDict_DelItem( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name );

            if (unlikely( status == -1 ))
            {
                PyErr_Format( PyExc_NameError, "name '%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
                throw _PythonException();
            }
        }

        bool isInitialized() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                return true;
            }

            entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

            return entry->me_value != NULL;
        }

    private:
       PyModuleObject **module_ptr;
       PyStringObject **var_name;
};

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_LOCALS_DICT( void )
{
    return MAKE_DICT();
}

template<typename T>
static void FILL_LOCALS_DICT( PyObject *dict, T variable )
{
    if ( variable->isInitialized() )
    {
        int status = PyDict_SetItem( dict, variable->getVariableName(), variable->asObject() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

template<typename T, typename... P>
static void FILL_LOCALS_DICT( PyObject *dict, T variable, P... variables )
{
    if ( variable->isInitialized() )
    {
        int status = PyDict_SetItem( dict, variable->getVariableName(), variable->asObject() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }

    FILL_LOCALS_DICT( dict, variables... );
}

template<typename... P>
static PyObject *MAKE_LOCALS_DICT( P...variables )
{
    PyObject *result = MAKE_LOCALS_DICT();

    FILL_LOCALS_DICT( result, variables... );

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_LOCALS_DIR( void )
{
    return MAKE_LIST();
}

template<typename T>
static void FILL_LOCALS_DIR( PyObject *list, T variable )
{
    if ( variable->isInitialized() )
    {
        int status = PyList_Append( list, variable->getVariableName() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

template<typename T, typename... P>
static void FILL_LOCALS_DIR( PyObject *list, T variable, P... variables )
{
    if ( variable->isInitialized() )
    {
        int status = PyList_Append( list, variable->getVariableName() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }

    FILL_LOCALS_DIR( list, variables... );
}

template<typename... P>
static PyObject *MAKE_LOCALS_DIR( P...variables )
{
    PyObject *result = MAKE_LOCALS_DIR();

    FILL_LOCALS_DIR( result, variables... );

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *TUPLE_COPY( PyObject *tuple )
{
    assert( tuple != NULL );
    assert( tuple->ob_refcnt > 0 );

    assert( PyTuple_CheckExact( tuple ) );

    Py_ssize_t size = PyTuple_GET_SIZE( tuple );

    PyObject *result = PyTuple_New( size );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        PyTuple_SET_ITEM( result, i, INCREASE_REFCOUNT( PyTuple_GET_ITEM( tuple, i ) ) );
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *LIST_COPY( PyObject *list )
{
    assert( list != NULL );
    assert( list->ob_refcnt > 0 );

    assert( PyList_CheckExact( list ) );

    Py_ssize_t size = PyList_GET_SIZE( list );

    PyObject *result = PyList_New( size );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        PyList_SET_ITEM( result, i, INCREASE_REFCOUNT( PyList_GET_ITEM( list, i ) ) );
    }

    return result;
}

class PythonBuiltin
{
    public:
        explicit PythonBuiltin( char const *name )
        {
            this->name = (PyStringObject *)PyString_FromString( name );
            this->value = NULL;
        }

        PyObject *asObject()
        {
            if ( this->value == NULL )
            {
                PyDictEntry *entry = GET_PYDICT_ENTRY(
                    _module_builtin,
                    this->name
                );
                this->value = entry->me_value;
            }

            assert( this->value != NULL );

            return this->value;
        }

        template<typename... P>
        PyObject *call( P...eles )
        {
            return CALL_FUNCTION( NULL, MAKE_TUPLE( eles... ), this->asObject() );
        }

    private:
        PythonBuiltin( PythonBuiltin const &  ) = delete;

        PyStringObject *name;
        PyObject *value;
};

// Compile source code given, pretending the file name was given.
extern PyObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode, int flags );

// For quicker builtin open() functionality.
extern PyObject *OPEN_FILE( PyObject *file_name, PyObject *mode, PyObject *buffering );

// For quicker builtin chr() functionality.
extern PyObject *CHR( PyObject *value );
// For quicker builtin ord() functionality.
extern PyObject *ORD( PyObject *value );

// For quicker type() functionality if 1 argument is given.
extern PyObject *BUILTIN_TYPE1( PyObject *arg );

// For quicker type() functionality if 3 arguments are given (to build a new type).
extern PyObject *BUILTIN_TYPE3( PyObject *module_name, PyObject *name, PyObject *bases, PyObject *dict );

// For quicker builtin range() functionality.
extern PyObject *BUILTIN_RANGE( PyObject *low, PyObject *high, PyObject *step );
extern PyObject *BUILTIN_RANGE( PyObject *low, PyObject *high );
extern PyObject *BUILTIN_RANGE( PyObject *boundary );

// For quicker builtin len() functionality.
extern PyObject *BUILTIN_LEN( PyObject *boundary );

NUITKA_MAY_BE_UNUSED static PyObject *EVAL_CODE( PyObject *code, PyObject *globals, PyObject *locals )
{
    if ( PyDict_Check( globals ) == 0 )
    {
        PyErr_Format( PyExc_TypeError, "exec: arg 2 must be a dictionary or None" );
        throw _PythonException();
    }

    if ( locals == NULL || locals == Py_None )
    {
        locals = globals;
    }

    if ( PyMapping_Check( locals ) == 0 )
    {
        PyErr_Format( PyExc_TypeError, "exec: arg 3 must be a mapping or None" );
        throw _PythonException();
    }

    // Set the __builtins__ in globals, it is expected to be present.
    if ( PyDict_GetItemString( globals, (char *)"__builtins__" ) == NULL )
    {
        if ( PyDict_SetItemString( globals, (char *)"__builtins__", (PyObject *)_module_builtin ) == -1 )
        {
            throw _PythonException();
        }
    }

    PyObject *result = PyEval_EvalCode( (PyCodeObject *)code, globals, locals );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

// Create a frame for the given code location.
PyObject *MAKE_FRAME( PyObject *module, PyObject *filename, PyObject *function_name, int line );

NUITKA_MAY_BE_UNUSED static PyTracebackObject *MAKE_TRACEBACK( PyObject *frame, int line )
{
    PyTracebackObject *result = PyObject_GC_New( PyTracebackObject, &PyTraceBack_Type );

    result->tb_next = NULL;
    result->tb_frame = (PyFrameObject *)INCREASE_REFCOUNT( frame );

    result->tb_lasti = 0;
    result->tb_lineno = line;

    PyObject_GC_Track( result );

    return result;
}

NUITKA_MAY_BE_UNUSED static void ADD_TRACEBACK( PyObject *module, PyObject *filename, PyObject *function_name, int line )
{
    // TODO: The frame object really might deserve a longer life that this, it is
    // relatively expensive to create.
    PyFrameObject *frame = (PyFrameObject *)MAKE_FRAME( module, filename, function_name, line );

    // Inlining PyTraceBack_Here may be faster
    PyTraceBack_Here( frame );

    Py_DECREF( frame );
}

extern PyObject *IMPORT_MODULE( PyObject *module_name, PyObject *import_name, PyObject *import_list );

extern void IMPORT_MODULE_STAR( PyObject *target, bool is_module, PyObject *module_name );

// For the constant loading:
extern void UNSTREAM_INIT( void );
extern PyObject *UNSTREAM_CONSTANT( char const *buffer, int size );

#endif
