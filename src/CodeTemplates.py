# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 

from templates.CodeTemplatesMain import *

from templates.CodeTemplatesCompiledFunctionType import *

from templates.CodeTemplatesFunction import *
from templates.CodeTemplatesGeneratorExpression import *
from templates.CodeTemplatesGeneratorFunction import *
from templates.CodeTemplatesListContraction import *

from templates.CodeTemplatesParameterParsing import *

from templates.CodeTemplatesExceptions import *
from templates.CodeTemplatesImporting import *
from templates.CodeTemplatesClass import *



global_copyright = """
// Generated code for Python source '%(name)s'

// This code is in part copyright Kay Hayen, license GPLv3. This has the consequence that
// your must either obtain a commercial license or also publish your original source code
// under the same license unless you don't distribute this source or its binary.
"""

# Template for the global stuff that must be had, compiling one or multple modules.
global_prelude = """\

#ifdef __PYDRA_NO_ASSERT__
#define NDEBUG
#endif

// Include the Python C/API header files

#include "Python.h"
#include "methodobject.h"
#include "frameobject.h"
#include <stdio.h>
#include <string>

// An idea I first saw used with Cython, hint the compiler about branches that are more or less likely to
// be taken. And hint the compiler about things that we assume to be normally true. If other compilers
// can do similar, I would be grateful for howtos.

#ifdef __GNUC__
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

PyObject *_expression_temps[100];

// From CPython, to allow us quick access to the dictionary of an module.
typedef struct {
        PyObject_HEAD
        PyObject *md_dict;
} PyModuleObject;

"""

global_helper = """\

template<typename... P>
static void PRINT_ITEMS( bool new_line, PyObject *file, P...eles );
static PyObject *INCREASE_REFCOUNT( PyObject *object );

static int _current_line = -1;
static char *_current_file = NULL;

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

        _PythonException( PyObject *exception, PyObject *value, float unused )
        {
            assert( exception );
            assert( value );
            assert( exception->ob_refcnt > 0 );
            assert( value->ob_refcnt > 0 );

            this->line = _current_line;

            Py_INCREF( exception );
            Py_INCREF( value );

            this->exception_type = exception;
            this->exception_value = value;
            this->exception_tb = NULL;
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

            // PyErr_NormalizeException( &this->exception_type, &this->exception_value, &this->exception_tb );
            PyErr_Clear();
        }

        inline int getLine() const
        {
            return this->line;
        }

        inline bool matches( PyObject *exception ) const
        {
            return PyErr_GivenExceptionMatches( this->exception_type, exception ) || PyErr_GivenExceptionMatches( this->exception_value, exception );;
        }

        inline void toPython()
        {
            PyErr_Restore( this->exception_type, this->exception_value, this->exception_tb );

            PyThreadState *thread_state = PyThreadState_GET();

            assert( this->exception_type == thread_state->curexc_type );
            assert( thread_state->curexc_type );

            this->exception_type  = NULL;
            this->exception_value = NULL;
            this->exception_tb    = NULL;
        }

        inline void toExceptionHandler()
        {
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

            assert( thread_state->exc_traceback );
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

        inline PyObject *setTraceback( PyTracebackObject *traceback )
        {
            assert( traceback );
            assert( traceback->ob_refcnt > 0 );

            // printf( "setTraceback %d\\n", traceback->ob_refcnt );

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


    protected:
        PyObject *exception_type, *exception_value, *exception_tb;
        int line;
};

class _PythonExceptionKeeper
{
    public:
        _PythonExceptionKeeper()
        {
            empty = true;
        }

        ~_PythonExceptionKeeper()
        {
            if ( this->empty == false)
            {
                delete this->saved;
            }
        }

        void save( const _PythonException &e )
        {
            this->saved = new _PythonException( e );

            empty = false;
        }

        void rethrow()
        {
            if (empty == false)
            {
                throw *this->saved;
            }
        }

        bool isEmpty() const
        {
            return this->empty;
        }

    protected:
        bool empty;

        _PythonException *saved;
};

// Helper functions for reference count handling in the fly.
static PyObject *INCREASE_REFCOUNT( PyObject *object )
{
    assert( object->ob_refcnt > 0 );

    Py_INCREF( object );

    return object;
}

static PyObject *DECREASE_REFCOUNT( PyObject *object )
{
    Py_DECREF( object );

    return object;
}


// Helper functions for print. Need to play nice with Python softspace behaviour.


static void PRINT_ITEM_TO( PyObject *file, PyObject *object )
{
    PyObject *str = PyObject_Str( object );
    PyObject *print;
    bool softspace;

    if ( str == NULL )
    {
        PyErr_Clear();

        print = object;
        softspace = false;
    }
    else
    {
        char *buffer;
        Py_ssize_t length;

        int res = PyString_AsStringAndSize( str, &buffer, &length );
        assert( res != -1 );

        softspace = length > 0 && buffer[length - 1 ] == '\t';

        print = str;
    }

    // Check for soft space indicator, need to hold a reference to the file
    // or else __getattr__ may release "file" in the mean time.
    if ( PyFile_SoftSpace( file, !softspace ) )
    {
        if (unlikely( PyFile_WriteString( " ", file ) == -1 ))
        {
            Py_DECREF( file );
            Py_DECREF( str );
            throw _PythonException();
        }
    }

    if ( unlikely( PyFile_WriteObject( print, file, Py_PRINT_RAW ) == -1 ))
    {
        Py_XDECREF( str );
        throw _PythonException();
    }

    Py_XDECREF( str );

    if ( softspace )
    {
        PyFile_SoftSpace( file, !softspace );
    }
}

static void PRINT_NEW_LINE_TO( PyObject *file )
{
    if (unlikely( PyFile_WriteString( "\\n", file ) == -1))
    {
        throw _PythonException();
    }

    PyFile_SoftSpace( file, 0 );
}

template<typename... P>
static void PRINT_ITEMS( bool new_line, PyObject *file, P...eles )
{
    int size = sizeof...(eles);

    if ( file == NULL || file == Py_None )
    {
        file = PySys_GetObject((char *)"stdout");
    }

    // Need to hold a reference for the case that the printing somehow removes
    // the last reference to "file" while printing.
    Py_INCREF( file );

    PyObject *elements[] = {eles...};

    for( int i = 0; i < size; i++ )
    {
        PRINT_ITEM_TO( file, elements[ i ] );
    }

    if ( new_line )
    {
        PRINT_NEW_LINE_TO( file );
    }

    // TODO: Use of PyObjectTemporary should be possible, this won't be
    // exception safe otherwise
    Py_DECREF( file );
}


static void PRINT_NEW_LINE( void )
{
    PyObject *stdout = PySys_GetObject((char *)"stdout");

    if (unlikely( stdout == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "problem with stdout" );
        throw _PythonException();
    }

    PRINT_NEW_LINE_TO( stdout );
}


static void RAISE_EXCEPTION( PyObject *exception, PyTracebackObject *traceback )
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
        throw _PythonException();
    }
}

static void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyTracebackObject *traceback )
{
    // TODO: Check traceback

    if ( PyExceptionClass_Check( exception_type ) )
    {
       PyErr_NormalizeException( &exception_type, &value, (PyObject **)&traceback );
    }

    throw _PythonException( exception_type, value, traceback );
}

static inline void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyObject *traceback )
{
    RAISE_EXCEPTION( exception_type, value, (PyTracebackObject *)traceback );
}


static bool CHECK_IF_TRUE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    int res = PyObject_IsTrue( object );

    if (res == -1)
    {
        throw _PythonException();
    }

    return res == 1;
}

static bool CHECK_IF_FALSE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    int res = PyObject_Not( object );

    if (res == -1)
    {
        throw _PythonException();
    }

    return res == 1;
}

static PyObject *BOOL_FROM( bool value )
{
    return value ? _python_bool_True : _python_bool_False;
}

static PyObject *TO_BOOL( PyObject *object )
{
    return BOOL_FROM( CHECK_IF_TRUE( object ));
}

static PyObject *UNARY_NOT( PyObject *object )
{
    int result = PyObject_Not( object );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 1 );
}

typedef PyObject *(binary_api)( PyObject *, PyObject * );

static PyObject *BINARY_OPERATION( binary_api api, PyObject *operand1, PyObject *operand2 )
{
    int line = _current_line;

    PyObject *result = api( operand1, operand2 );

    if (result == NULL)
    {
        _current_line = line;
        throw _PythonException();
    }

    return result;
}

typedef PyObject *(unary_api)( PyObject * );

static PyObject *UNARY_OPERATION( unary_api api, PyObject *operand )
{
    PyObject *result = api( operand );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *POWER_OPERATION( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_Power( operand1, operand2, Py_None );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *POWER_OPERATION_INPLACE( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_InPlacePower( operand1, operand2, Py_None );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *RICH_COMPARE( int opid, PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, opid );

    if ( result == NULL )
    {
        _current_line = line;
        throw _PythonException();
    }

    return result;
}

static bool RICH_COMPARE_BOOL( int opid, PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    int result = PyObject_RichCompareBool( operand1, operand2, opid );

    if ( result == -1 )
    {
        _current_line = line;
        throw _PythonException();
    }

    return result == 1;
}


static PyObject *SEQUENCE_CONTAINS( PyObject *sequence, PyObject *element)
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 1 );
}

static PyObject *SEQUENCE_CONTAINS_NOT( PyObject *sequence, PyObject *element)
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 0 );
}


// Helper functions to debug the compiler operation.
static void PRINT_REFCOUNT( PyObject *object )
{
   PyObject *stdout = PySys_GetObject((char *)"stdout");

   if (unlikely( stdout == NULL ))
   {
      PyErr_Format( PyExc_RuntimeError, "problem with stdout" );
      throw _PythonException();
   }

   char buffer[1024];
   sprintf( buffer, " refcnt %d ", object->ob_refcnt );

   if (unlikely( PyFile_WriteString(buffer, stdout) == -1 ))
   {
      throw _PythonException();
   }

}

static PyObject *CALL_FUNCTION( PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    assert( function_object != NULL );
    assert( function_object->ob_refcnt > 0 );
    assert( positional_args != NULL );
    assert( positional_args->ob_refcnt > 0 );
    assert( named_args == NULL || named_args->ob_refcnt > 0 );

    int line = _current_line;

    PyObject *result = PyObject_Call( function_object, positional_args, named_args );

    if (result == NULL)
    {
        _current_line = line;
        throw _PythonException();
    }

    return result;
}

static PyObject *TO_TUPLE( PyObject *seq_obj )
{
    PyObject *result = PySequence_Tuple( seq_obj );

    if (result == NULL)
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
            assert (elements[ i ] != NULL);
            assert (elements[ i ]->ob_refcnt > 0);
        }

        PyObject *result = PyTuple_New( size );

        if (result == NULL)
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

    if (result == NULL)
    {
        throw _PythonException();
    }

    for (Py_ssize_t i = 0; i < size; i++ )
    {
        assert (elements[ i ] != NULL);
        assert (elements[ i ]->ob_refcnt > 0);

        PyList_SET_ITEM( result, i, elements[ size - 1 - i ] );
    }

    assert (result->ob_refcnt == 1);

    return result;
}

template<typename... P>
static PyObject *MAKE_DICT( P...eles )
{
    PyObject *elements[] = {eles...};
    int size = sizeof...(eles);

    assert (size % 2 == 0);

    PyObject *result = PyDict_New();

    if (result == NULL)
    {
        throw _PythonException();
    }

    for( int i = 0; i < size; i += 2 )
    {
        int res = PyDict_SetItem( result, elements[i], elements[i+1] );

        if ( res == -1 )
        {
            throw _PythonException();
        }
    }

    return result;
}

static PyObject *MERGE_DICTS( PyObject *dict_a, PyObject *dict_b, bool allow_conflict )
{
    PyObject *result = PyDict_Copy( dict_a );

    if ( result == NULL )
    {
        throw _PythonException();
    }

    int res = PyDict_Merge( result, dict_b, 1 );

    if ( res == -1 )
    {
        throw _PythonException();
    }

    if ( allow_conflict == false && PyDict_Size( dict_a ) + PyDict_Size( dict_b ) != PyDict_Size( result ))
    {
        Py_DECREF( result );

        PyErr_Format( PyExc_TypeError, "got multiple values for keyword argument" );
        throw _PythonException();
    }

    return result;
}

static PyObject *MAKE_STATIC_METHOD( PyObject *method )
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

static PyObject *SEQUENCE_ELEMENT( PyObject *sequence, Py_ssize_t element )
{
    PyObject *result = PySequence_GetItem( sequence, element );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *MAKE_ITERATOR( PyObject *iterated )
{
    PyObject *result = PyObject_GetIter( iterated );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

// Return the next item of an iterator. Avoiding any exception for end of iteration, callers must
// deal with NULL return as end of iteration, but will know it wasn't an Python exception, that will show as a thrown exception.
static PyObject *ITERATOR_NEXT( PyObject *iterator )
{
    assert( iterator != NULL );
    assert( iterator->ob_refcnt > 0 );

    PyObject *result = PyIter_Next( iterator );

    if ( result == NULL )
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

static inline PyObject *UNPACK_NEXT( PyObject *iterator, int seq_size_so_far )
{
    assert( iterator != NULL );
    assert( iterator->ob_refcnt > 0 );

    PyObject *result = PyIter_Next( iterator );

    if ( result == NULL )
    {
        if ( PyErr_Occurred() != NULL )
        {
            throw _PythonException();
        }

        if ( seq_size_so_far == 1 )
        {
            PyErr_Format( PyExc_ValueError, "need more than 1 value to unpack" );
        }
        else
        {
            PyErr_Format( PyExc_ValueError, "need more than %d values to unpack", seq_size_so_far );
        }

        throw _PythonException();
    }

    assert( result->ob_refcnt > 0 );

    return result;
}

static inline void UNPACK_ITERATOR_CHECK( PyObject *iterator )
{
    PyObject *attempt = PyIter_Next( iterator );

    if (likely( attempt == NULL ))
    {
        PyErr_Clear();
    }
    else
    {
        Py_DECREF( attempt );

        PyErr_Format( PyExc_ValueError, "too many values to unpack" );
        throw _PythonException();
    }
}


static PyObject *SELECT_IF_TRUE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    if (CHECK_IF_TRUE( object ))
    {
        return object;
    }
    else
    {
        Py_DECREF( object );

        return NULL;
    }
}

static PyObject *SELECT_IF_FALSE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    if (CHECK_IF_FALSE( object ))
    {
        return object;
    }
    else
    {
        Py_DECREF( object );

        return NULL;
    }
}

static PyObject *LOOKUP_SUBSCRIPT( PyObject *source, PyObject *subscript )
{
    assert (source);
    assert (source->ob_refcnt > 0);
    assert (subscript);
    assert (subscript->ob_refcnt > 0);

    PyObject *result = PyObject_GetItem( source, subscript );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static bool HAS_KEY( PyObject *source, PyObject *key )
{
    assert (source);
    assert (source->ob_refcnt > 0);
    assert (key);
    assert (key->ob_refcnt > 0);

    return PyMapping_HasKey( source, key ) != 0;
}

static PyObject *LOOKUP_VARS( PyObject *source )
{
    assert (source);
    assert (source->ob_refcnt > 0);

    static PyObject *dict_str = PyString_FromString( "__dict__" );

    PyObject *result = PyObject_GetAttr( source, dict_str );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}


static void SET_SUBSCRIPT( PyObject *target, PyObject *subscript, PyObject *value )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (subscript);
    assert (subscript->ob_refcnt > 0);
    assert (value);
    assert (value->ob_refcnt > 0);

    int status = PyObject_SetItem( target, subscript, value );

    if (status == -1)
    {
        throw _PythonException();
    }
}

static void DEL_SUBSCRIPT( PyObject *target, PyObject *subscript )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (subscript);
    assert (subscript->ob_refcnt > 0);

    int status = PyObject_DelItem( target, subscript );

    if (status == -1)
    {
        throw _PythonException();
    }
}


static PyObject *LOOKUP_SLICE( PyObject *source, Py_ssize_t lower, Py_ssize_t upper )
{
    assert (source);
    assert (source->ob_refcnt > 0);

    PyObject *result = PySequence_GetSlice( source, lower, upper);

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static void SET_SLICE( PyObject *target, Py_ssize_t lower, Py_ssize_t upper, PyObject *value )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (value);
    assert (value->ob_refcnt > 0);

    int status = PySequence_SetSlice( target, lower, upper, value );

    if (status == -1)
    {
        throw _PythonException();
    }
}

static Py_ssize_t CONVERT_TO_INDEX( PyObject *value );

static void DEL_SLICE( PyObject *target, PyObject *lower, PyObject *upper )
{
    assert (target);
    assert (target->ob_refcnt > 0);

    if ( target->ob_type->tp_as_sequence && target->ob_type->tp_as_sequence->sq_ass_slice )
    {
        int status = PySequence_DelSlice( target, lower != Py_None ? CONVERT_TO_INDEX( lower ) : 0, upper != Py_None ? CONVERT_TO_INDEX( upper ) : PY_SSIZE_T_MAX );

        if (status == -1)
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

        if (status == -1)
        {
            throw _PythonException();
        }
    }
}

static PyObject *MAKE_SLICEOBJ( PyObject *start, PyObject *stop, PyObject *step )
{
    assert (start);
    assert (start->ob_refcnt > 0);
    assert (stop);
    assert (stop->ob_refcnt > 0);
    assert (step);
    assert (step->ob_refcnt > 0);

    PyObject *result = PySlice_New( start, stop, step );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static Py_ssize_t CONVERT_TO_INDEX( PyObject *value )
{
    assert (value);
    assert (value->ob_refcnt > 0);

    if ( PyInt_Check( value ) )
    {
        return PyInt_AS_LONG( value );
    }
    else if ( PyIndex_Check( value ) )
    {
        Py_ssize_t result = PyNumber_AsSsize_t( value, NULL );

        if ( result == -1 && PyErr_Occurred() )
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

static PyObject *LOOKUP_ATTRIBUTE( PyObject *source, PyObject *attr_name )
{
    assert (source);
    assert (source->ob_refcnt > 0);
    assert (attr_name);
    assert (attr_name->ob_refcnt > 0);

    PyObject *result = PyObject_GetAttr( source, attr_name );

    if (result == NULL)
    {
        throw _PythonException();
    }

    assert( result->ob_refcnt > 0 );

    return result;
}

static void SET_ATTRIBUTE( PyObject *target, PyObject *attr_name, PyObject *value )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (attr_name);
    assert (attr_name->ob_refcnt > 0);
    assert (value);
    assert (value->ob_refcnt > 0);

    int status = PyObject_SetAttr( target, attr_name, value );

    if (status == -1)
    {
        throw _PythonException();
    }
}

static void DEL_ATTRIBUTE( PyObject *target, PyObject *attr_name )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (attr_name);
    assert (attr_name->ob_refcnt > 0);

    int status = PyObject_DelAttr( target, attr_name );

    if (status == -1)
    {
        throw _PythonException();
    }
}


static void APPEND_TO_LIST( PyObject *list, PyObject *item)
{
    int res = PyList_Append( list, item );

    if (res == -1)
    {
        throw _PythonException();
    }
}

static PyObject *SEQUENCE_CONCAT( PyObject *seq1, PyObject *seq2 )
{

    PyObject *result = PySequence_Concat( seq1, seq2 );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

template<typename... P>
static PyObject *NUMBER_AND( P...vars )
{
    PyObject *operands[] = {vars...};

    int size = sizeof...(vars);

    PyObject *result = PyNumber_And( operands[ 0 ], operands[ 1 ] );

    if ( result == NULL )
    {
        throw _PythonException();
    }

    for (int i = 2; i < size; i++ )
    {
        result = PyNumber_And( result, operands[ i ] );

        if ( result == NULL )
        {
            throw _PythonException();
        }
    }

    return result;
}

template<typename... P>
static PyObject *NUMBER_OR( P...vars )
{
    PyObject *operands[] = {vars...};

    int size = sizeof...(vars);

    PyObject *result = PyNumber_Or( operands[ 0 ], operands[ 1 ] );

    if ( result == NULL )
    {
        throw _PythonException();
    }

    for (int i = 2; i < size; i++ )
    {
        result = PyNumber_Or( result, operands[ i ] );

        if ( result == NULL )
        {
            throw _PythonException();
        }
    }

    return result;
}

template<typename... P>
static PyObject *NUMBER_XOR( P...vars )
{
    PyObject *operands[] = {vars...};

    int size = sizeof...(vars);

    PyObject *result = PyNumber_Xor( operands[ 0 ], operands[ 1 ] );

    if ( result == NULL )
    {
        throw _PythonException();
    }

    for (int i = 2; i < size; i++ )
    {
        result = PyNumber_Xor( result, operands[ i ] );

        if ( result == NULL )
        {
            throw _PythonException();
        }
    }

    return result;
}


// This structure is the attachment for all generator functions without context.

struct _context_genexpr_t
{
    _context_genexpr_t( PyObject *iterator )
    {
        assert (iterator);
        assert (iterator->ob_refcnt > 0);

        this->iterator = iterator;
    }

    // Store the iterator provided at creation time here.
    PyObject *iterator;
};

static void _context_genexpr_destructor( void *context_voidptr )
{
    _context_genexpr_t *_python_context = (struct _context_genexpr_t *)context_voidptr;

    delete _python_context;
}


// Helper class to be used when PyObject * are provided as parameters where they
// are not consumed, but not needed anymore after the call and and need a release
// as soon as possible.

class PyObjectTemporary {
    public:
        PyObjectTemporary( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            this->object = object;

#ifdef __PYDRA_REF_DEBUG__
            printf( "Create Temp '" );
            PRINT_ITEM( this->object );
#endif
        }

        ~PyObjectTemporary() {
#ifdef __PYDRA_REF_DEBUG__
            printf( "Delete Temp '" );
            PRINT_ITEM( this->object );
#endif
            Py_DECREF( this->object );
        }

        PyObject *asObject()
        {
            assert( this->object );
            assert( this->object->ob_refcnt > 0 );

            return this->object;
        }
    private:
        PyObject *object;
};

class PyObjectLocalVariable {
    public:
        explicit PyObjectLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = true ) {
            this->var_name   = var_name;
            this->object     = object;
            this->free_value = free_value;
        }

        explicit PyObjectLocalVariable() {
            this->var_name   = NULL;
            this->object     = NULL;
            this->free_value = false;
        }

        ~PyObjectLocalVariable()
        {
            this->del();
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

#ifdef __PYDRA_REF_DEBUG__
            if (this->object)
            {
               printf( "Delete Local:" );
               PRINT_ITEM( this->object );
               PRINT_REFCOUNT( this->object );
               puts( "" );
            }
#endif

            PyObject *old_object = this->free_value ? this->object : NULL;

            this->object = object;
            this->free_value = true;

            // Free old value if any available and owned.
            Py_XDECREF( old_object );
        }

        PyObject *asObject() const
        {
            if ( this->object == NULL && this->var_name != NULL )
            {
                printf( "Using uninialized variable '%s'.\\n", PyString_AsString( this->var_name ) );
            }
            assert( this->object );
            assert( this->object->ob_refcnt > 0 );

            return this->object;
        }

        bool isInitialized() const
        {
            return this->object != NULL;
        }

        void del()
        {
            if ( this->free_value )
            {
#ifdef __PYDRA_REF_DEBUG__
                if (this->object)
                {
                    printf( "Delete Local:" );
                    PRINT_ITEM( this->object );
                    PRINT_REFCOUNT( this->object );
                    puts( "" );
                }
#endif

                Py_XDECREF( this->object );
            }

            this->object = NULL;
            this->free_value = true;
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
                Py_XDECREF( this->object );
            }
        }

        void operator=( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            PyObject *old_object = this->free_value ? this->object : NULL;

            this->object = object;
            this->free_value = true;

            // Free old value if any available and owned.
            Py_XDECREF( old_object );
        }

        PyObject *var_name;
        PyObject *object;
        bool free_value;
        int ref_count;
};

class PyObjectSharedLocalVariable
{
    public:
        explicit PyObjectSharedLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = true )
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
            assert(this->storage == NULL);
            assert(other.storage != NULL);

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
                PyErr_Format( PyExc_NameError, "free variable '%s' referenced before assignment in enclosing scope", PyString_AsString( this->storage->var_name ) );
                throw _PythonException();

            }

            if ( (this->storage->object)->ob_refcnt == 0 )
            {
                PyErr_Format( PyExc_NameError, "free variable '%s' referenced after its finalization in enclosing scope", PyString_AsString( this->storage->var_name ) );
                throw _PythonException();
            }

            return this->storage->object;
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

static PyObject *_module_builtin = NULL;

class PyObjectGlobalVariable
{
    public:
        explicit PyObjectGlobalVariable( PyObject **module_ptr, PyObject **var_name )
        {
            assert( module_ptr );
            assert( var_name );

            this->module_ptr = module_ptr;
            this->var_name   = var_name;
        }

        PyObject *asObject() const
        {
            // Idea similar to LOAD_GLOBAL in CPython. Because the variable name is a string, we can shortcut
            // much of the dictionary code by using its hash and dictionary knowledge here. Only improvement
            // would be to identify how to ensure that the hash is computed already. Calling hash early on
            // could do that potentially.

            long hash = ((PyStringObject *)*this->var_name)->ob_shash;

            if (hash != -1)
            {
                PyDictObject *dict = (PyDictObject *)((PyModuleObject *)*this->module_ptr)->md_dict;
                PyDictEntry *entry = dict->ma_lookup( dict, *this->var_name, hash );

                if (unlikely(entry == NULL))
                {
                    throw _PythonException();
                }

                if (likely( entry->me_value ))
                {
                    return INCREASE_REFCOUNT( entry->me_value );
                }

                dict = (PyDictObject *)((PyModuleObject *)_module_builtin)->md_dict;
                entry = dict->ma_lookup( dict, *this->var_name, hash );

                if (unlikely( entry == NULL ))
                {
                    throw _PythonException();
                }

                if (likely( entry->me_value != NULL ))
                {
                    return INCREASE_REFCOUNT( entry->me_value );
                }

                PyErr_Format( PyExc_NameError, "global name %s is not defined", PyString_AsString( *this->var_name ) );
                throw _PythonException();
            }
            else
            {
                PyObject *result = PyObject_GetAttr( *this->module_ptr, *this->var_name );

                if (unlikely (result == NULL))
                {
                    PyErr_Clear();

                    PyObject *result2 = PyObject_GetAttr( _module_builtin, *this->var_name );

                    if (unlikely (result2 == NULL))
                    {
                        PyErr_Format( PyExc_NameError, "global name %s is not defined", PyString_AsString( *this->var_name ) );
                        throw _PythonException();
                    }

                    return result2;
                }

                return result;
            }
        }

        void assign( PyObject *value ) const
        {
            SET_ATTRIBUTE( *this->module_ptr, *this->var_name, value );
        }

        void del() const
        {
           DEL_ATTRIBUTE(  *this->module_ptr, *this->var_name );
        }

        bool isInitialized() const
        {
            long hash = ((PyStringObject *)*this->var_name)->ob_shash;

            if (hash != -1)
            {
                PyDictObject *dict = (PyDictObject *)((PyModuleObject *)*this->module_ptr)->md_dict;
                PyDictEntry *entry = dict->ma_lookup( dict, *this->var_name, hash );

                if (unlikely(entry == NULL))
                {
                    throw _PythonException();
                }

                return entry->me_value != NULL;
            }
            else
            {
                return PyObject_HasAttr( *this->module_ptr, *this->var_name );
            }
        }

    private:
       PyObject **module_ptr;
       PyObject **var_name;
};

static PyObject *MAKE_LOCALS_DICT( void )
{
    PyObject *result = PyDict_New();

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

template<typename T>
static void FILL_LOCALS_DICT( PyObject *dict, T variable )
{
    if ( variable->isInitialized() )
    {
        int res = PyDict_SetItem( dict, variable->getVariableName(), variable->asObject() );

        if ( res == -1 )
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
        int res = PyDict_SetItem( dict, variable->getVariableName(), variable->asObject() );

        if ( res == -1 )
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

class PythonBuiltin
{
    public:
        explicit PythonBuiltin( char const *name )
        {
            this->name = name;
            this->value = NULL;
        }

        PyObject *asObject()
        {
            if ( this->value == NULL )
            {
                this->value = PyObject_GetAttrString( _module_builtin, this->name );
            }

            assert( this->value != NULL );

            return this->value;
        }

    private:
        char const *name;
        PyObject *value;
};

PythonBuiltin _python_builtin_compile( "compile" );
PythonBuiltin _python_builtin_open( "open" );

static PyCodeObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode )
{
    // May be a source, but also could already be a compiled object, in which case this should
    // just return it.
    if ( PyCode_Check( source_code ) )
    {
        return (PyCodeObject *)source_code;
    }

    static PyObject *strip_str = PyString_FromString( "strip" );

    // Workaround leading whitespace causing a trouble to compile, but not eval builtin
    PyObject *source;

    if ( ( PyString_Check( source_code ) || PyUnicode_Check( source_code ) ) && strcmp( PyString_AsString( mode ), "exec" ) != 0 )
    {
        // TODO: There is an API to call a method, use it.
        source = LOOKUP_ATTRIBUTE( source_code, strip_str );
        source = PyObject_CallFunctionObjArgs( source, NULL );

        assert( source );
    }
    else
    {
        source = source_code;
    }

    PyObject *result = PyObject_CallFunctionObjArgs(
        _python_builtin_compile.asObject(),
        source,
        file_name,
        mode,
        NULL
    );

    if ( result == NULL )
    {
        throw _PythonException();
    }

    return (PyCodeObject *)result;
}

static PyObject *OPEN_FILE( PyObject *file_name, PyObject *mode, PyObject *buffering )
{
    PyObject *result = PyObject_CallFunctionObjArgs(
        _python_builtin_open.asObject(),
        file_name,
        mode,
        buffering,
        NULL
    );

    if (result == NULL)
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *EVAL_CODE( PyCodeObject *code, PyObject *globals, PyObject *locals )
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

    // Set the __builtin__ in globals, it is expected to be present.
    if ( PyMapping_HasKeyString( globals, (char *)"__builtins__" ) == 0 )
    {
        if ( PyMapping_SetItemString( globals, (char *)"__builtins__", _module_builtin ) == -1 )
        {
            throw _PythonException();
        }
    }

    PyObject *result = PyEval_EvalCode( code, globals, locals );

    if ( result == NULL )
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *empty_code = PyBuffer_FromMemory( NULL, 0 );

static PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name, int line )
{
    // TODO: Potentially it is possible to create a line2no table that will
    // allow to use only one code object per function, this could then be
    // cached and presumably be much faster, because it could be reused.

    assert( PyString_Check( filename ));
    assert( PyString_Check( function_name ));

    assert( empty_code );

    // printf( "MAKE_CODEOBJ code object %d\\n", empty_code->ob_refcnt );

    PyCodeObject *result = PyCode_New (
        0, 0, 0, 0, // argcount, locals, stacksize, flags
        empty_code, //
        _python_tuple_empty,
        _python_tuple_empty,
        _python_tuple_empty,
        _python_tuple_empty,
        _python_tuple_empty,
        filename,
        function_name,
        line,
        _python_str_empty
    );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

static PyFrameObject *MAKE_FRAME( PyObject *module, PyObject *filename, PyObject *function_name, int line )
{
    PyCodeObject *code = MAKE_CODEOBJ( filename, function_name, line );

    PyFrameObject *result = PyFrame_New(
        PyThreadState_GET(),
        code,
        ((PyModuleObject *)module)->md_dict,
        NULL // No locals yet
    );

    Py_DECREF( code );

    assert( result );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    result->f_lineno = line;

    return result;
}

static PyTracebackObject *MAKE_TRACEBACK_START( PyFrameObject *frame, int line )
{
    PyTracebackObject *result = PyObject_GC_New( PyTracebackObject, &PyTraceBack_Type );

    result->tb_next = NULL;

    Py_INCREF( frame );
    result->tb_frame  = frame;

    result->tb_lasti  = 0;
    result->tb_lineno = line;

    PyObject_GC_Track( result );

    return result;
}


static void ADD_TRACEBACK( PyObject *module, PyObject *filename, PyObject *function_name, int line )
{
    // TODO: The frame object really might deserve a longer life that this, it is relatively expensive to create.
    PyFrameObject *frame = MAKE_FRAME( module, filename, function_name, line );

    // Inlining PyTraceBack_Here may be faster
    PyTraceBack_Here( frame );

    Py_DECREF( frame );
}


"""


try_finally_template = """
_PythonExceptionKeeper _caught_%(try_count)d;

try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    _caught_%(try_count)d.save( _exception );
}

%(final_code)s

_caught_%(try_count)d.rethrow();

"""

try_except_template = """
try
{
%(tried_code)s
}
catch (_PythonException &_exception)
{
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
    }
    _exception.toExceptionHandler();
    traceback = false;

    %(exception_code)s
}
"""

try_except_else_template = """
bool _caught_%(except_count)d = false;
try
{
%(tried_code)s
}
catch (_PythonException &_exception)
{
    _caught_%(except_count)d = true;

    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
    }
    _exception.toExceptionHandler();
    traceback = false;

    %(exception_code)s
}
if (_caught_%(except_count)d == false)
{
%(else_code)s
}
"""


import_from_template = """
{
    PyObject *_module_temp = PyImport_ImportModuleEx( (char *)"%(module_name)s", NULL, NULL, %(import_list)s );

    if ( unlikely( _module_temp == NULL ) )
    {
        throw _PythonException();
    }

    %(module_imports)s

    Py_DECREF( _module_temp );
}

"""
