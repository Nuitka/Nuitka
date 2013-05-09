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

#include "nuitka/prelude.hpp"

extern PyObject *_python_str_plain_compile;
extern PyObject *_python_str_plain_strip;
extern PyObject *_python_str_plain_read;

static PythonBuiltin _python_builtin_compile( &_python_str_plain_compile );

PyObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode, int flags )
{
    // May be a source, but also could already be a compiled object, in which case this
    // should just return it.
    if ( PyCode_Check( source_code ) )
    {
        return INCREASE_REFCOUNT( source_code );
    }

    // Workaround leading whitespace causing a trouble to compile builtin, but not eval builtin
    PyObject *source;

    if (
        (
#if PYTHON_VERSION < 300
            PyString_Check( source_code ) ||
#endif
            PyUnicode_Check( source_code )
        ) &&
        strcmp( Nuitka_String_AsString( mode ), "exec" ) != 0
       )
    {
        source = PyObject_CallMethodObjArgs( source_code, _python_str_plain_strip, NULL );

        if (unlikely( source == NULL ))
        {
            throw PythonException();
        }
    }
#if PYTHON_VERSION < 300
    // Note: Python3 does not support "exec" with file handles.
    else if ( PyFile_Check( source_code ) && strcmp( Nuitka_String_AsString( mode ), "exec" ) == 0 )
    {
        source = PyObject_CallMethodObjArgs( source_code, _python_str_plain_read, NULL );

        if (unlikely( source == NULL ))
        {
            throw PythonException();
        }
    }
#endif
    else
    {
        source = source_code;
    }

    PyObjectTemporary future_flags( PyInt_FromLong( flags ) );

    return _python_builtin_compile.call_args(
        MAKE_TUPLE5(
            source,
            file_name,
            mode,
            future_flags.asObject(), // flags
            Py_True                  // dont_inherit
        )
    );
}

extern PyObject *_python_str_plain_open;

static PythonBuiltin _python_builtin_open( &_python_str_plain_open );

PyObject *OPEN_FILE( PyObject *file_name, PyObject *mode, PyObject *buffering )
{
    if ( file_name == NULL )
    {
        return _python_builtin_open.call();

    }
    else if ( mode == NULL )
    {
        return _python_builtin_open.call1(
            file_name
        );

    }
    else if ( buffering == NULL )
    {
        return _python_builtin_open.call_args(
            MAKE_TUPLE2(
               file_name,
               mode
            )
        );
    }
    else
    {
        return _python_builtin_open.call_args(
            MAKE_TUPLE3(
                file_name,
                mode,
                buffering
            )
        );
    }
}

PyObject *BUILTIN_CHR( unsigned char c )
{
    // TODO: A switch statement might be faster, because no object needs to be created at
    // all, this here is how CPython does it.
    char s[1];
    s[0] = (char)c;

#if PYTHON_VERSION < 300
    return PyString_FromStringAndSize( s, 1 );
#else
    return PyUnicode_FromStringAndSize( s, 1 );
#endif
}

PyObject *BUILTIN_CHR( PyObject *value )
{
    long x = PyInt_AsLong( value );

#if PYTHON_VERSION < 300
    if ( x < 0 || x >= 256 )
    {
        PyErr_Format( PyExc_ValueError, "chr() arg not in range(256)" );
        throw PythonException();
    }

    // TODO: A switch statement might be faster, because no object needs to be created at
    // all, this is how CPython does it.
    char s[1];
    s[0] = (char)x;

    return PyString_FromStringAndSize( s, 1 );
#else
    PyObject *result = PyUnicode_FromOrdinal( x );

    if (unlikely( result == NULL ))
    {
        throw PythonException();
    }

    assert( PyUnicode_Check( result ));

    return result;
#endif
}

PyObject *BUILTIN_ORD( PyObject *value )
{
    long result;

    if (likely( PyBytes_Check( value ) ))
    {
        Py_ssize_t size = PyBytes_GET_SIZE( value );

        if (likely( size == 1 ))
        {
            result = long( ((unsigned char *)PyBytes_AS_STRING( value ))[0] );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but string of length %zd found", size );
            throw PythonException();
        }
    }
    else if ( PyByteArray_Check( value ) )
    {
        Py_ssize_t size = PyByteArray_GET_SIZE( value );

        if (likely( size == 1 ))
        {
            result = long( ((unsigned char *)PyByteArray_AS_STRING( value ))[0] );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but byte array of length %zd found", size );
            throw PythonException();
        }
    }
    else if ( PyUnicode_Check( value ) )
    {
        Py_ssize_t size = PyUnicode_GET_SIZE( value );

        if (likely( size == 1 ))
        {
            result = long( *PyUnicode_AS_UNICODE( value ) );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but unicode string of length %zd found", size );
            throw PythonException();
        }
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "ord() expected string of length 1, but %s found", Py_TYPE( value )->tp_name );
        throw PythonException();
    }

    return PyInt_FromLong( result );
}

PyObject *BUILTIN_BIN( PyObject *value )
{
    // Note: I don't really know why ord and hex don't use this as well.
    PyObject *result = PyNumber_ToBase( value, 2 );

    if ( unlikely( result == NULL ))
    {
        throw PythonException();
    }

    return result;
}

PyObject *BUILTIN_OCT( PyObject *value )
{
#if PYTHON_VERSION >= 300
    PyObject *result = PyNumber_ToBase( value, 8 );

    if ( unlikely( result == NULL ))
    {
        throw PythonException();
    }

    return result;
#else
    if (unlikely( value == NULL ))
    {
        PyErr_Format( PyExc_TypeError, "oct() argument can't be converted to oct" );
        return NULL;
    }

    PyNumberMethods *nb = Py_TYPE( value )->tp_as_number;

    if (unlikely( nb == NULL || nb->nb_oct == NULL ))
    {
        PyErr_Format( PyExc_TypeError, "oct() argument can't be converted to oct" );
        return NULL;
    }

    PyObject *result = (*nb->nb_oct)( value );

    if ( result )
    {
        if (unlikely( !PyString_Check( result ) ))
        {
            PyErr_Format( PyExc_TypeError, "__oct__ returned non-string (type %s)", Py_TYPE( result )->tp_name );

            Py_DECREF( result );
            return NULL;
        }
    }

    return result;
#endif
}

PyObject *BUILTIN_HEX( PyObject *value )
{
#if PYTHON_VERSION >= 300
    PyObject *result = PyNumber_ToBase( value, 16 );

    if ( unlikely( result == NULL ))
    {
        throw PythonException();
    }

    return result;
#else
    if (unlikely( value == NULL ))
    {
        PyErr_Format( PyExc_TypeError, "hex() argument can't be converted to hex" );
        return NULL;
    }

    PyNumberMethods *nb = Py_TYPE( value )->tp_as_number;

    if (unlikely( nb == NULL || nb->nb_hex == NULL ))
    {
        PyErr_Format( PyExc_TypeError, "hex() argument can't be converted to hex" );
        return NULL;
    }

    PyObject *result = (*nb->nb_hex)( value );

    if ( result )
    {
        if (unlikely( !PyString_Check( result ) ))
        {
            PyErr_Format( PyExc_TypeError, "__hex__ returned non-string (type %s)", Py_TYPE( result )->tp_name );

            Py_DECREF( result );
            return NULL;
        }
    }

    return result;
#endif
}

// From CPython:
typedef struct {
    PyObject_HEAD
    PyObject *it_callable;
    PyObject *it_sentinel;
} calliterobject;

PyObject *BUILTIN_ITER2( PyObject *callable, PyObject *sentinel )
{
    calliterobject *result = PyObject_GC_New( calliterobject, &PyCallIter_Type );

    if (unlikely( result == NULL ))
    {
        throw PythonException();
    }

    // Note: References were taken at call site already.
    result->it_callable = INCREASE_REFCOUNT( callable );
    result->it_sentinel = INCREASE_REFCOUNT( sentinel );

    Nuitka_GC_Track( result );

    return (PyObject *)result;
}

PyObject *BUILTIN_TYPE1( PyObject *arg )
{
    return INCREASE_REFCOUNT( (PyObject *)Py_TYPE( arg ) );
}

extern PyObject *_python_str_plain___module__;

PyObject *BUILTIN_TYPE3( PyObject *module_name, PyObject *name, PyObject *bases, PyObject *dict )
{
    PyObject *result = PyType_Type.tp_new(
        &PyType_Type,
        PyObjectTemporary( MAKE_TUPLE3( name, bases, dict ) ).asObject(),
        NULL
    );

    if (unlikely( result == NULL ))
    {
        throw PythonException();
    }

    PyTypeObject *type = Py_TYPE( result );

    if (likely( PyType_IsSubtype( type, &PyType_Type ) ))
    {
        if (
#if PYTHON_VERSION < 300
            PyType_HasFeature( type, Py_TPFLAGS_HAVE_CLASS ) &&
#endif
            type->tp_init != NULL
           )
        {
            int res = type->tp_init( result, MAKE_TUPLE3( name, bases, dict ), NULL );

            if (unlikely( res < 0 ))
            {
                Py_DECREF( result );
                throw PythonException();
            }
        }
    }

    int res = PyObject_SetAttr( result, _python_str_plain___module__, module_name );

    if ( res == -1 )
    {
        throw PythonException();
    }

    return result;
}

Py_ssize_t ESTIMATE_RANGE( long low, long high, long step )
{
    if ( low >= high )
    {
        return 0;
    }
    else
    {
        return ( high - low - 1 ) / step + 1;
    }
}

#if PYTHON_VERSION < 300
static PyObject *_BUILTIN_RANGE_INT3( long low, long high, long step )
{
    assert( step != 0 );

    Py_ssize_t size;

    if ( step > 0 )
    {
        size = ESTIMATE_RANGE( low, high, step );
    }
    else
    {
        size = ESTIMATE_RANGE( high, low, -step );
    }

    PyObject *result = PyList_New( size );

    long current = low;

    for ( int i = 0; i < size; i++ )
    {
        PyList_SET_ITEM( result, i, PyInt_FromLong( current ) );
        current += step;
    }

    return result;
}

static PyObject *_BUILTIN_RANGE_INT2( long low, long high )
{
    return _BUILTIN_RANGE_INT3( low, high, 1 );
}

static PyObject *_BUILTIN_RANGE_INT( long boundary )
{
    return _BUILTIN_RANGE_INT2( 0, boundary );
}

static PyObject *TO_RANGE_ARG( PyObject *value, char const *name )
{
    if (likely( PyInt_Check( value ) || PyLong_Check( value ) ))
    {
        return INCREASE_REFCOUNT( value );
    }

    PyTypeObject *type = Py_TYPE( value );
    PyNumberMethods *tp_as_number = type->tp_as_number;

    // Everything that casts to int is allowed.
    if (
#if PYTHON_VERSION >= 270
        PyFloat_Check( value ) ||
#endif
        tp_as_number == NULL ||
        tp_as_number->nb_int == NULL
       )
    {
        PyErr_Format( PyExc_TypeError, "range() integer %s argument expected, got %s.", name, type->tp_name );
        throw PythonException();
    }

    PyObject *result = tp_as_number->nb_int( value );

    if (unlikely( result == NULL ))
    {
        throw PythonException();
    }

    return result;
}
#endif

extern PyObject *_python_str_plain_range;

static PythonBuiltin _python_builtin_range( &_python_str_plain_range );

PyObject *BUILTIN_RANGE( PyObject *boundary )
{
#if PYTHON_VERSION < 300
    PyObjectTemporary boundary_temp( TO_RANGE_ARG( boundary, "end" ) );

    long start = PyInt_AsLong( boundary_temp.asObject() );

    if ( start == -1 && ERROR_OCCURED() )
    {
        PyErr_Clear();

        return _python_builtin_range.call1( boundary_temp.asObject() );
    }

    return _BUILTIN_RANGE_INT( start );
#else
    return _python_builtin_range.call1( boundary );
#endif
}

PyObject *BUILTIN_RANGE2( PyObject *low, PyObject *high )
{
#if PYTHON_VERSION < 300
    PyObjectTemporary low_temp( TO_RANGE_ARG( low, "start" ) );
    PyObjectTemporary high_temp( TO_RANGE_ARG( high, "end" ) );

    bool fallback = false;

    long start = PyInt_AsLong( low_temp.asObject() );

    if (unlikely( start == -1 && ERROR_OCCURED() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    long end = PyInt_AsLong( high_temp.asObject() );

    if (unlikely( end == -1 && ERROR_OCCURED() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    if ( fallback )
    {
        return _python_builtin_range.call_args(
            MAKE_TUPLE2(
                low_temp.asObject(),
                high_temp.asObject()
            )
        );
    }
    else
    {
        return _BUILTIN_RANGE_INT2( start, end );
    }
#else
    return _python_builtin_range.call_args(
        MAKE_TUPLE2( low, high )
    );
#endif
}

PyObject *BUILTIN_RANGE3( PyObject *low, PyObject *high, PyObject *step )
{
#if PYTHON_VERSION < 300
    PyObjectTemporary low_temp( TO_RANGE_ARG( low, "start" ) );
    PyObjectTemporary high_temp( TO_RANGE_ARG( high, "end" ) );
    PyObjectTemporary step_temp( TO_RANGE_ARG( step, "step" ) );

    bool fallback = false;

    long start = PyInt_AsLong( low_temp.asObject() );

    if (unlikely( start == -1 && ERROR_OCCURED() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    long end = PyInt_AsLong( high_temp.asObject() );

    if (unlikely( end == -1 && ERROR_OCCURED() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    long step_long = PyInt_AsLong( step_temp.asObject() );

    if (unlikely( step_long == -1 && ERROR_OCCURED() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    if ( fallback )
    {
        return _python_builtin_range.call_args(
            MAKE_TUPLE3(
                low_temp.asObject(),
                high_temp.asObject(),
                step_temp.asObject()
            )
       );
    }
    else
    {
        if (unlikely( step_long == 0 ))
        {
            PyErr_Format( PyExc_ValueError, "range() step argument must not be zero" );
            throw PythonException();
        }

        return _BUILTIN_RANGE_INT3( start, end, step_long );
    }
#else
    return _python_builtin_range.call_args(
        MAKE_TUPLE3( low, high, step )
    );
#endif
}

PyObject *BUILTIN_LEN( PyObject *value )
{
    assertObject( value );

    Py_ssize_t res = PyObject_Size( value );

    if (unlikely( res < 0 && ERROR_OCCURED() ))
    {
        throw PythonException();
    }

    return PyInt_FromSsize_t( res );
}

PyObject *BUILTIN_DIR1( PyObject *arg )
{
    assertObject( arg );

    PyObject *result = PyObject_Dir( arg );

    if (unlikely( result == NULL ))
    {
        throw PythonException();
    }

    return result;
}

extern PyObject *_python_str_plain___import__;

static PythonBuiltin _python_builtin_import( &_python_str_plain___import__ );

PyObject *IMPORT_MODULE( PyObject *module_name, PyObject *globals, PyObject *locals, PyObject *import_items, PyObject *level )
{
    assertObject( module_name );
    assertObject( globals );
    assertObject( locals );
    assertObject( import_items );

    PyObject *import_result;

    import_result = _python_builtin_import.call_args(
        MAKE_TUPLE5(
            module_name,
            globals,
            locals,
            import_items,
            level
        )
    );

    return import_result;
}

extern PyObject *_python_str_plain___all__;

void IMPORT_MODULE_STAR( PyObject *target, bool is_module, PyObject *module )
{
    // Check parameters.
    assertObject( module );
    assertObject( target );

    PyObject *iter;
    bool all_case;

    if ( PyObject *all = PyObject_GetAttr( module, _python_str_plain___all__ ) )
    {
        iter = MAKE_ITERATOR( all );
        all_case = true;
    }
    else if ( PyErr_ExceptionMatches( PyExc_AttributeError ) )
    {
        PyErr_Clear();

        iter = MAKE_ITERATOR( PyModule_GetDict( module ) );
        all_case = false;
    }
    else
    {
        throw PythonException();
    }

    while ( PyObject *item = ITERATOR_NEXT( iter ) )
    {
        assert( Nuitka_String_Check( item ) );

        // TODO: Not yet clear, what happens with __all__ and "_" of its contents.
        if ( all_case == false )
        {
            if ( Nuitka_String_AsString_Unchecked( item )[0] == '_' )
            {
                continue;
            }
        }

        // TODO: Check if the reference is handled correctly
        if ( is_module )
        {
            SET_ATTRIBUTE( LOOKUP_ATTRIBUTE( module, item ), target, item );
        }
        else
        {
            SET_SUBSCRIPT( LOOKUP_ATTRIBUTE( module, item ), target, item );
        }

        Py_DECREF( item );
    }
}

// Helper functions for print. Need to play nice with Python softspace behaviour.

#if PYTHON_VERSION >= 300
extern PyObject *_python_str_plain_print;
extern PyObject *_python_str_plain_end;
extern PyObject *_python_str_plain_file;
extern PyObject *_python_str_empty;

static PythonBuiltin _python_builtin_print( &_python_str_plain_print );
#endif

void PRINT_ITEM_TO( PyObject *file, PyObject *object )
{
// The print builtin function cannot replace "softspace" behaviour of CPython
// print statement, so this code is really necessary.
#if PYTHON_VERSION < 300
    if ( file == NULL || file == Py_None )
    {
        file = GET_STDOUT();
    }

    assertObject( file );
    assertObject( object );

    // need to hold a reference to the file or else __getattr__ may release "file" in the
    // mean time.
    Py_INCREF( file );

    bool softspace;

    if ( PyString_Check( object ) )
    {
        char *buffer;
        Py_ssize_t length;

#ifndef __NUITKA_NO_ASSERT__
        int status =
#endif
            PyString_AsStringAndSize( object, &buffer, &length );
        assert( status != -1 );

        softspace = length > 0 && buffer[ length - 1 ] == '\t';
    }
    else
    {
        softspace = false;
    }

    // Check for soft space indicator
    if ( PyFile_SoftSpace( file, !softspace ) )
    {
        if (unlikely( PyFile_WriteString( " ", file ) == -1 ))
        {
            Py_DECREF( file );
            throw PythonException();
        }
    }

    if ( unlikely( PyFile_WriteObject( object, file, Py_PRINT_RAW ) == -1 ))
    {
        Py_DECREF( file );
        throw PythonException();
    }

    if ( softspace )
    {
        PyFile_SoftSpace( file, !softspace );
    }

    assertObject( file );

    Py_DECREF( file );
#else
    if (likely( file == NULL ))
    {
        _python_builtin_print.call1(
            object
        );
    }
    else
    {
        PyObjectTemporary print_kw(
            MAKE_DICT2(
                _python_str_empty, _python_str_plain_end,
                GET_STDOUT(), _python_str_plain_file
            )
        );

        PyObjectTemporary print_args(
            MAKE_TUPLE1( object )
        );

        _python_builtin_print.call_args_kw(
            print_args.asObject(),
            print_kw.asObject()
        );
    }
#endif
}

void PRINT_NEW_LINE_TO( PyObject *file )
{
#if PYTHON_VERSION < 300
    if ( file == NULL || file == Py_None )
    {
        file = GET_STDOUT();
    }

    // need to hold a reference to the file or else __getattr__ may release "file" in the
    // mean time.
    Py_INCREF( file );

    if (unlikely( PyFile_WriteString( "\n", file ) == -1))
    {
        Py_DECREF( file );
        throw PythonException();
    }

    PyFile_SoftSpace( file, 0 );

    assertObject( file );

    Py_DECREF( file );
#else
    if (likely( file == NULL ))
    {
        _python_builtin_print.call();
    }
    else
    {
        PyObjectTemporary print_keyargs(
            MAKE_DICT1( // Note: Values for first for MAKE_DICT
                GET_STDOUT(), _python_str_plain_file
            )
        );

        _python_builtin_print.call_kw(
            print_keyargs.asObject()
        );
    }
#endif
}

void PRINT_REFCOUNT( PyObject *object )
{
#if PYTHON_VERSION < 300
   char buffer[ 1024 ];
   sprintf( buffer, " refcnt %" PY_FORMAT_SIZE_T "d ", Py_REFCNT( object ) );

   if (unlikely( PyFile_WriteString( buffer, GET_STDOUT() ) == -1 ))
   {
      throw PythonException();
   }
#else
   assert( false );
#endif
}




PyObject *GET_STDOUT()
{
    PyObject *result = PySys_GetObject( (char *)"stdout" );

    if (unlikely( result == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "lost sys.stdout" );
        throw PythonException();
    }

    return result;
}

PyObject *GET_STDERR()
{
    PyObject *result = PySys_GetObject( (char *)"stderr" );

    if (unlikely( result == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "lost sys.stderr" );
        throw PythonException();
    }

    return result;
}

#if PYTHON_VERSION < 300

void PRINT_NEW_LINE( void )
{
    PRINT_NEW_LINE_TO( GET_STDOUT() );
}

#endif

// We unstream some constant objects using the "cPickle" module function "loads"
static PyObject *_module_cPickle = NULL;
static PyObject *_module_cPickle_function_loads = NULL;

void UNSTREAM_INIT()
{
#if PYTHON_VERSION < 300
    _module_cPickle = PyImport_ImportModule( "cPickle" );
#else
    _module_cPickle = PyImport_ImportModule( "pickle" );
#endif
    assert( _module_cPickle );

    _module_cPickle_function_loads = PyObject_GetAttrString( _module_cPickle, "loads" );
    assert( _module_cPickle_function_loads );
}

PyObject *UNSTREAM_CONSTANT( char const *buffer, Py_ssize_t size )
{
    assert( buffer );
    assert( _module_cPickle_function_loads );

    PyObject *result = PyObject_CallFunction(
        _module_cPickle_function_loads,
#if PYTHON_VERSION < 300
        (char *)"(s#)", // TODO: Why the ()
#else
        (char *)"y#",
#endif
        buffer,
        size
    );

    if ( !result )
    {
        PyErr_Print();
    }

    assertObject( result );

    return result;
}

PyObject *UNSTREAM_STRING( char const *buffer, Py_ssize_t size, bool intern )
{
#if PYTHON_VERSION < 300
    PyObject *result = PyString_FromStringAndSize( buffer, size );
#else
    PyObject *result = PyUnicode_FromStringAndSize( buffer, size );
#endif

    assert( !ERROR_OCCURED() );
    assertObject( result );
    assert( Nuitka_String_Check( result ) );

#if PYTHON_VERSION < 300
    assert( PyString_Size( result ) == size );
#endif

    if ( intern )
    {
        Nuitka_StringIntern( &result );

        assertObject( result );
        assert( Nuitka_String_Check( result ) );

#if PYTHON_VERSION < 300
        assert( PyString_Size( result ) == size );
#else
        assert( PyUnicode_GET_SIZE( result ) == size );
#endif
    }

    return result;
}

PyObject *UNSTREAM_FLOAT( char const *buffer )
{
    double x = _PyFloat_Unpack8( (unsigned char *)buffer, 0 );
    assert( x != -1.0 || !PyErr_Occurred() );

    PyObject *result = PyFloat_FromDouble(x);
    assert( result != NULL );

    return result;
}

#if PYTHON_VERSION < 300

static void set_slot( PyObject **slot, PyObject *value )
{
    PyObject *temp = *slot;
    Py_XINCREF( value );
    *slot = value;
    Py_XDECREF( temp );
}

extern PyObject *_python_str_plain___getattr__;
extern PyObject *_python_str_plain___setattr__;
extern PyObject *_python_str_plain___delattr__;

static void set_attr_slots( PyClassObject *klass )
{
    set_slot( &klass->cl_getattr, FIND_ATTRIBUTE_IN_CLASS( klass, _python_str_plain___getattr__ ) );
    set_slot( &klass->cl_setattr, FIND_ATTRIBUTE_IN_CLASS( klass, _python_str_plain___setattr__ ) );
    set_slot( &klass->cl_delattr, FIND_ATTRIBUTE_IN_CLASS( klass, _python_str_plain___delattr__ ) );
}

static bool set_dict( PyClassObject *klass, PyObject *value )
{
    if ( value == NULL || !PyDict_Check( value ) )
    {
        PyErr_SetString( PyExc_TypeError, (char *)"__dict__ must be a dictionary object" );
        return false;
    }
    else
    {
        set_slot( &klass->cl_dict, value );
        set_attr_slots( klass );

        return true;
    }
}

static bool set_bases( PyClassObject *klass, PyObject *value )
{
    if ( value == NULL || !PyTuple_Check( value ) )
    {
        PyErr_SetString( PyExc_TypeError, (char *)"__bases__ must be a tuple object" );
        return false;
    }
    else
    {
        Py_ssize_t n = PyTuple_Size( value );

        for ( Py_ssize_t i = 0; i < n; i++ )
        {
            PyObject *base = PyTuple_GET_ITEM( value, i );

            if (unlikely( !PyClass_Check( base ) ))
            {
                PyErr_SetString( PyExc_TypeError, (char *)"__bases__ items must be classes" );
                return false;
            }

            if (unlikely( PyClass_IsSubclass( base, (PyObject *)klass) ))
            {
                PyErr_SetString( PyExc_TypeError, (char *)"a __bases__ item causes an inheritance cycle" );
                return false;
            }
        }

        set_slot( &klass->cl_bases, value );
        set_attr_slots( klass );

        return true;
    }
}

static bool set_name( PyClassObject *klass, PyObject *value )
{
    if ( value == NULL || !PyDict_Check( value ) )
    {
        PyErr_SetString( PyExc_TypeError, (char *)"__name__ must be a string object" );
        return false;
    }

    if ( strlen( PyString_AS_STRING( value )) != (size_t)PyString_GET_SIZE( value ) )
    {
        PyErr_SetString( PyExc_TypeError, (char *)"__name__ must not contain null bytes" );
        return false;
    }

    set_slot( &klass->cl_name, value );
    return true;
}

static int nuitka_class_setattr( PyClassObject *klass, PyObject *attr_name, PyObject *value )
{
    char *sattr_name = PyString_AsString( attr_name );

    if ( sattr_name[0] == '_' && sattr_name[1] == '_' )
    {
        Py_ssize_t n = PyString_Size( attr_name );

        if ( sattr_name[ n-2 ] == '_' && sattr_name[ n-1 ] == '_' )
        {
            if ( strcmp( sattr_name, "__dict__" ) == 0 )
            {
                if ( set_dict( klass, value ) == false )
                {
                    return -1;
                }
                else
                {
                    return 0;
                }
            }
            else if ( strcmp( sattr_name, "__bases__" ) == 0 )
            {
                if ( set_bases( klass, value ) == false )
                {
                    return -1;
                }
                else
                {
                    return 0;
                }
            }
            else if ( strcmp( sattr_name, "__name__" ) == 0 )
            {
                if ( set_name( klass, value ) == false )
                {
                    return -1;
                }
                else
                {
                    return 0;
                }
            }
            else if ( strcmp( sattr_name, "__getattr__" ) == 0 )
            {
                set_slot( &klass->cl_getattr, value );
            }
            else if ( strcmp(sattr_name, "__setattr__" ) == 0 )
            {
                set_slot( &klass->cl_setattr, value );
            }
            else if ( strcmp(sattr_name, "__delattr__" ) == 0 )
            {
                set_slot( &klass->cl_delattr, value );
            }
        }
    }

    if ( value == NULL )
    {
        int status = PyDict_DelItem( klass->cl_dict, attr_name );

        if ( status < 0 )
        {
            PyErr_Format( PyExc_AttributeError, "class %s has no attribute '%s'", PyString_AS_STRING( klass->cl_name ), sattr_name );
        }

        return status;
    }
    else
    {
        return PyDict_SetItem( klass->cl_dict, attr_name, value );
    }
}

static PyObject *nuitka_class_getattr( PyClassObject *klass, PyObject *attr_name )
{
    char *sattr_name = PyString_AsString( attr_name );

    if ( sattr_name[0] == '_' && sattr_name[1] == '_' )
    {
        if ( strcmp( sattr_name, "__dict__" ) == 0 )
        {
            return INCREASE_REFCOUNT( klass->cl_dict );
        }
        else if ( strcmp(sattr_name, "__bases__" ) == 0 )
        {
            return INCREASE_REFCOUNT( klass->cl_bases );
        }
        else if ( strcmp(sattr_name, "__name__" ) == 0 )
        {
            return klass->cl_name ? INCREASE_REFCOUNT( klass->cl_name ) : INCREASE_REFCOUNT( Py_None );
        }
    }

    PyObject *value = FIND_ATTRIBUTE_IN_CLASS( klass, attr_name );

    if (unlikely( value == NULL ))
    {
        PyErr_Format( PyExc_AttributeError, "class %s has no attribute '%s'", PyString_AS_STRING( klass->cl_name ), sattr_name );
        return NULL;
    }

    PyTypeObject *type = Py_TYPE( value );

    descrgetfunc tp_descr_get = PyType_HasFeature( type, Py_TPFLAGS_HAVE_CLASS ) ? type->tp_descr_get : NULL;

    if ( tp_descr_get == NULL )
    {
        return INCREASE_REFCOUNT( value );
    }
    else
    {
        return tp_descr_get( value, (PyObject *)NULL, (PyObject *)klass );
    }
}

#endif

void enhancePythonTypes( void )
{
#if PYTHON_VERSION < 300
    // Our own variant won't call PyEval_GetRestricted, saving quite some cycles not doing
    // that.
    PyClass_Type.tp_setattro = (setattrofunc)nuitka_class_setattr;
    PyClass_Type.tp_getattro = (getattrofunc)nuitka_class_getattr;
#endif
}

#ifdef __APPLE__
extern wchar_t* _Py_DecodeUTF8_surrogateescape(const char *s, Py_ssize_t size);
#endif

#ifdef __FreeBSD__
#include <floatingpoint.h>
#endif

#include <locale.h>

void setCommandLineParameters( int argc, char *argv[] )
{
#if PYTHON_VERSION < 300
    PySys_SetArgv( argc, argv );
#else
// Originally taken from CPython3: There seems to be no sane way to use

    wchar_t **argv_copy = (wchar_t **)PyMem_Malloc(sizeof(wchar_t*)*argc);
    /* We need a second copies, as Python might modify the first one. */
    wchar_t **argv_copy2 = (wchar_t **)PyMem_Malloc(sizeof(wchar_t*)*argc);

    char *oldloc;
    /* 754 requires that FP exceptions run in "no stop" mode by default,
     * and until C vendors implement C99's ways to control FP exceptions,
     * Python requires non-stop mode.  Alas, some platforms enable FP
     * exceptions by default.  Here we disable them.
     */
#ifdef __FreeBSD__
    fp_except_t m;

    m = fpgetmask();
    fpsetmask(m & ~FP_X_OFL);
#endif

    oldloc = strdup( setlocale( LC_ALL, NULL ) );

    setlocale( LC_ALL, "" );
    for ( int i = 0; i < argc; i++ )
    {
#ifdef __APPLE__
        argv_copy[i] = _Py_DecodeUTF8_surrogateescape( argv[ i ], strlen( argv[ i ] ) );
#else
        argv_copy[i] = _Py_char2wchar( argv[ i ], NULL );
#endif
        assert ( argv_copy[ i ] );

        argv_copy2[ i ] = argv_copy[ i ];
    }
    setlocale( LC_ALL, oldloc );
    free( oldloc );

    PySys_SetArgv( argc, argv_copy );
#endif
}

typedef struct {
    PyObject_HEAD
    PyTypeObject *type;
    PyObject *obj;
    PyTypeObject *obj_type;
} superobject;

extern PyObject *_python_str_plain___class__;

PyObject *BUILTIN_SUPER( PyObject *type, PyObject *object )
{
    assertObject( type );

    superobject *result = PyObject_GC_New( superobject, &PySuper_Type );
    assert( result );

    if ( object == Py_None )
    {
        object = NULL;
    }

    if (unlikely( PyType_Check( type ) == false ))
    {
        PyErr_Format( PyExc_TypeError, "must be type, not %s", Py_TYPE( type )->tp_name );
        throw PythonException();
    }

    result->type = (PyTypeObject *)INCREASE_REFCOUNT( type );
    if ( object )
    {
        result->obj = INCREASE_REFCOUNT( object );

        if ( PyType_Check( object ) && PyType_IsSubtype( (PyTypeObject *)object, (PyTypeObject *)type ))
        {
            result->obj_type = (PyTypeObject *)INCREASE_REFCOUNT( object );
        }
        else if ( PyType_IsSubtype( Py_TYPE(object ), (PyTypeObject *)type) )
        {
            result->obj_type = (PyTypeObject *)INCREASE_REFCOUNT( (PyObject *)Py_TYPE( object ) );
        }
        else
        {
            PyObject *class_attr = PyObject_GetAttr( object, _python_str_plain___class__);

            if (likely( class_attr != NULL && PyType_Check( class_attr ) && (PyTypeObject *)class_attr != Py_TYPE( object ) ))
            {
                result->obj_type = (PyTypeObject *)class_attr;
            }
            else
            {
                if ( class_attr == NULL )
                {
                    PyErr_Clear();
                }
                else
                {
                    Py_DECREF( class_attr );
                }

                PyErr_Format(
                    PyExc_TypeError,
                    "super(type, obj): obj must be an instance or subtype of type"
                );

                throw PythonException();
            }
        }
    }
    else
    {
        result->obj = NULL;
        result->obj_type = NULL;
    }

    Nuitka_GC_Track( result );

    assertObject( (PyObject *)result );
    assert( Py_TYPE( result ) == &PySuper_Type );

    return (PyObject *)result;
}

PyObject *BUILTIN_CALLABLE( PyObject *value )
{
    return PyBool_FromLong( (long)PyCallable_Check( value ) );
}

// Used by InspectPatcher too.
int Nuitka_IsInstance( PyObject *inst, PyObject *cls )
{
    assertObject( inst );
    assertObject( cls );

    // Quick path.
    if ( Py_TYPE( inst ) == (PyTypeObject *)cls )
    {
        return true;
    }

    if ( cls == (PyObject *)&PyFunction_Type && Nuitka_Function_Check( inst ) )
    {
        return true;
    }

    if ( cls == (PyObject *)&PyGen_Type && Nuitka_Generator_Check( inst ) )
    {
        return true;
    }

    if ( cls == (PyObject *)&PyMethod_Type && Nuitka_Method_Check( inst ) )
    {
        return true;
    }

    if ( PyTuple_Check( cls ) )
    {
        for ( Py_ssize_t i = 0, size = PyTuple_GET_SIZE( cls ); i < size; i++ )
        {
            PyObject *element = PyTuple_GET_ITEM( cls, i );

            if (unlikely( Py_EnterRecursiveCall( (char *)" in __instancecheck__" ) ))
            {
                return -1;
            }

            int res = Nuitka_IsInstance( inst, element );

            Py_LeaveRecursiveCall();

            if ( res != 0 )
            {
                return res;
            }
        }

        return 0;
    }
    else
    {
        return PyObject_IsInstance( inst, cls );
    }
}

bool BUILTIN_ISINSTANCE_BOOL( PyObject *inst, PyObject *cls )
{
    int res = Nuitka_IsInstance( inst, cls );

    if (unlikely( res < 0 ))
    {
        throw PythonException();
    }

    return res != 0;
}


PyObject *BUILTIN_GETATTR( PyObject *object, PyObject *attribute, PyObject *default_value )
{
#if PYTHON_VERSION < 300
    if ( PyUnicode_Check( attribute ) )
    {
        attribute = _PyUnicode_AsDefaultEncodedString( attribute, NULL );

        if (unlikely( attribute == NULL ))
        {
            throw PythonException();
        }
    }

    if (unlikely( !PyString_Check( attribute ) ))
    {
        PyErr_Format( PyExc_TypeError, "getattr(): attribute name must be string" );
        throw PythonException();
    }
#else
    if (!PyUnicode_Check( attribute ))
    {
        PyErr_Format( PyExc_TypeError, "getattr(): attribute name must be string" );
        throw PythonException();
    }
#endif

    PyObject *result = PyObject_GetAttr( object, attribute );

    if ( result == NULL )
    {
        if ( default_value != NULL && PyErr_ExceptionMatches( PyExc_AttributeError ))
        {
            PyErr_Clear();

            return INCREASE_REFCOUNT( default_value );
        }
        else
        {
            throw PythonException();
        }
    }
    else
    {
        return result;
    }
}

void BUILTIN_SETATTR( PyObject *object, PyObject *attribute, PyObject *value )
{
    int res = PyObject_SetAttr( object, attribute, value );

    if (unlikely( res != 0 ))
    {
        throw PythonException();
    }
}

PyDictObject *dict_builtin = NULL;
PyModuleObject *module_builtin = NULL;

#define ASSIGN_BUILTIN( name ) _python_original_builtin_value_##name = LOOKUP_BUILTIN( _python_str_plain_##name );

PyTypeObject PyBuiltinModule_Type =
{
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "compiled_module",                           // tp_name
    sizeof(PyModuleObject),                      // tp_size
};

extern PyObject *_python_str_plain_open;

int Nuitka_BuiltinModule_SetAttr( PyModuleObject *module, PyObject *name, PyObject *value )
{
    assertObject( (PyObject *)module );
    assertObject( name );

    // This is used for "del" as well.
    assert( value == NULL || Py_REFCNT( value ) > 0 );

    // only checks the builtins that we can refresh at this time, if we have many value to
    // check maybe need create a dict first.
    bool found = false;

    int res = PyObject_RichCompareBool( name, _python_str_plain_open, Py_EQ );

    if (unlikely( res == -1 ))
    {
        return -1;
    }
    if ( res == 1 )
    {
        _python_builtin_open.update( value );
        found = true;
    }

    if ( found == false )
    {
        res = PyObject_RichCompareBool( name, _python_str_plain___import__, Py_EQ );

        if (unlikely( res == -1 ))
        {
            return -1;
        }

        if ( res == 1 )
        {
            _python_builtin_import.update( value );
            found = true;
        }
    }

#if PYTHON_VERSION >= 300
    if ( found == false )
    {
        res = PyObject_RichCompareBool( name, _python_str_plain_print, Py_EQ );

        if (unlikely( res == -1 ))
        {
            return -1;
        }

        if ( res == 1 )
        {
            _python_builtin_print.update( value );
            found = true;
        }
    }
#endif

    return PyObject_GenericSetAttr( (PyObject *)module, name, value );
}

void _initBuiltinModule()
{
#if _NUITKA_MODULE
    if ( module_builtin ) return;
#else
    assert( module_builtin == NULL );
#endif

#if PYTHON_VERSION < 300
    module_builtin = (PyModuleObject *)PyImport_ImportModule( "__builtin__" );
#else
    module_builtin = (PyModuleObject *)PyImport_ImportModule( "builtins" );
#endif
    assert( module_builtin );
    dict_builtin = (PyDictObject *)module_builtin->md_dict;
    assert( PyDict_Check( dict_builtin ) );

    /* init PyBuiltinModule_Type, PyType_Ready wont copy all member from base type,
       so we need copy all members from PyModule_Type manual for safety.
       PyType_Ready will change tp_flags, we need define it again.
       set tp_setattro to PyBuiltinModule_SetAttr and we can detect value change.
       set tp_base to PyModule_Type and PyModule_Check will pass. */
    PyBuiltinModule_Type.tp_dealloc = PyModule_Type.tp_dealloc;
    PyBuiltinModule_Type.tp_repr = PyModule_Type.tp_repr;
    PyBuiltinModule_Type.tp_setattro = (setattrofunc) Nuitka_BuiltinModule_SetAttr;
    PyBuiltinModule_Type.tp_getattro = PyModule_Type.tp_getattro;
    PyBuiltinModule_Type.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_BASETYPE;
    PyBuiltinModule_Type.tp_doc = PyModule_Type.tp_doc;
    PyBuiltinModule_Type.tp_traverse = PyModule_Type.tp_traverse;
    PyBuiltinModule_Type.tp_members = PyModule_Type.tp_members;
    PyBuiltinModule_Type.tp_base = &PyModule_Type;
    PyBuiltinModule_Type.tp_dictoffset = PyModule_Type.tp_dictoffset;
    PyBuiltinModule_Type.tp_init = PyModule_Type.tp_init;
    PyBuiltinModule_Type.tp_alloc = PyModule_Type.tp_alloc;
    PyBuiltinModule_Type.tp_new = PyModule_Type.tp_new;
    PyBuiltinModule_Type.tp_free = PyModule_Type.tp_free;
    int ret = PyType_Ready( &PyBuiltinModule_Type );
    assert( ret == 0 );

    // replace type of builtin module
    ((PyObject *)module_builtin)->ob_type = &PyBuiltinModule_Type;
    assert( PyModule_Check( module_builtin ) == 1 );
}

#ifdef _NUITKA_PORTABLE
char *getBinaryDirectory( char *binary_path )
{
    int i;
    char *path = ( char* ) malloc( PATH_MAX + 1 );
    memset ( path, 0, PATH_MAX + 1 );
#if defined( _WIN32 )
    HMODULE hModule = GetModuleHandle( NULL );
    if ( !hModule )
    {
        fprintf( stderr, "getBinaryDirectory: get module handle failed\n" );
        free( path );
        return NULL;
    }
    GetModuleFileName( hModule , path, PATH_MAX + 1 );
    char sep = '\\';
#else
    if ( !realpath( binary_path, path ) )
    {
        fprintf( stderr, "getBinaryDirectory: get real path failed\n" );
        free( path );
        return NULL;
    }
    char sep = '/';
#endif
    for ( i = PATH_MAX; i > 0; i-- )
    {
        // need handle unicode here ?
        if ( path[i] == sep )
        {
            path[i] = '\x00';
            break;
        }
    }
    return path;
}

void _initPortableEnvironment( char *binary_path )
{
    // setup environ
    // orignal_value;binary_directory/_python;binary_directory/_python.zip
    char *binary_directory = getBinaryDirectory( binary_path );
    if ( !binary_directory )
        abort();

    // get orignal value
    char *orignal_home = getenv( "PYTHONHOME" );
    char *orignal_path = getenv( "PYTHONPATH" );
    size_t orignal_home_size = ( orignal_home ) ? strlen( orignal_home ) : 0;
    size_t orignal_path_size = ( orignal_path ) ? strlen( orignal_path ) : 0;

    // get insert value
    size_t insert_size = strlen( binary_directory ) * 2 + 50;
    char *insert_path = (char *) malloc( insert_size );
    memset( insert_path, 0, insert_size );
#if defined( _WIN32 )
    char env_string[] = "%s\\%s;%s\\%s;";
#else
    char env_string[] = "%s/%s:%s/%s:";
#endif
    snprintf( insert_path, insert_size, env_string,
        binary_directory, "_python",
        binary_directory, "_python.zip"
    );

    // set environment
    size_t python_home_size = orignal_home_size + insert_size;
    size_t python_path_size = orignal_path_size + insert_size;
    char *python_home = (char *) malloc( python_home_size );
    char *python_path = (char *) malloc( python_path_size );
    memset( python_home, 0, python_home_size );
    memset( python_path, 0, python_path_size );
    snprintf( python_home, python_home_size, "%s%s",
        insert_path, orignal_home ? orignal_home : "" );
    snprintf( python_path, python_path_size, "%s%s",
        insert_path, orignal_path ? orignal_path : "" );
#if defined( _WIN32 )
    Py_SetPythonHome( python_home );
#else
    if ( !( orignal_home && strstr( orignal_home, insert_path ) ) )
        setenv( "PYTHONHOME", python_home, 1 );
    if ( !( orignal_path && strstr( orignal_path, insert_path ) ) )
        setenv( "PYTHONPATH", python_path, 1 );
#endif

    // clean up
    free( binary_directory );
    free( insert_path );
}
#endif

#ifdef _NUITKA_EXE

#define DEFINE_BUILTIN( name ) extern PyObject *_python_str_plain_##name; PyObject *_python_original_builtin_value_##name = NULL;

DEFINE_BUILTIN( type )
DEFINE_BUILTIN( len )
DEFINE_BUILTIN( range )
DEFINE_BUILTIN( repr )
DEFINE_BUILTIN( int )
DEFINE_BUILTIN( iter )
#if PYTHON_VERSION < 300
DEFINE_BUILTIN( long )
#endif

void _initBuiltinOriginalValues()
{
    ASSIGN_BUILTIN( type );
    ASSIGN_BUILTIN( len );
    ASSIGN_BUILTIN( range );
    ASSIGN_BUILTIN( repr );
    ASSIGN_BUILTIN( int );
    ASSIGN_BUILTIN( iter );
#if PYTHON_VERSION < 300
    ASSIGN_BUILTIN( long );
#endif

    assertObject( _python_original_builtin_value_range );
}

#if PYTHON_VERSION >= 300
volatile int _Py_Ticker = _Py_CheckInterval;
#endif

#endif
