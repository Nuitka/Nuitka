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

#include "nuitka/prelude.hpp"

#include "__constants.hpp"

static PythonBuiltin _python_builtin_compile( "compile" );

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

    if ( ( PyString_Check( source_code ) || PyUnicode_Check( source_code ) ) && strcmp( Nuitka_String_AsString( mode ), "exec" ) != 0 )
    {
        static PyObject *strip_str = PyString_FromString( "strip" );

        // TODO: There is an API to call a method, use it instead.
        source = LOOKUP_ATTRIBUTE( source_code, strip_str );
        source = PyObject_CallFunctionObjArgs( source, NULL );

        assert( source );
    }
    else if ( PyFile_Check( source_code ) && strcmp( Nuitka_String_AsString( mode ), "exec" ) == 0 )
    {
        static PyObject *read_str = PyString_FromString( "read" );

        // TODO: There is an API to call a method, use it instead.
        source = LOOKUP_ATTRIBUTE( source_code, read_str );
        source = PyObject_CallFunctionObjArgs( source, NULL );

        assert( source );
    }
    else
    {
        source = source_code;
    }

    PyObjectTemporary future_flags( PyInt_FromLong( flags ) );

    return _python_builtin_compile.call(
        Py_True,                 // dont_inherit
        future_flags.asObject(), // flags
        mode,
        file_name,
        source
    );
}

static PythonBuiltin _python_builtin_open( "open" );

PyObject *OPEN_FILE( PyObject *file_name, PyObject *mode, PyObject *buffering )
{
    if ( file_name == NULL )
    {
        return _python_builtin_open.call();

    }
    else if ( mode == NULL )
    {
        return _python_builtin_open.call(
           file_name
        );

    }
    else if ( buffering == NULL )
    {
        return _python_builtin_open.call(
           mode,
           file_name
        );
    }
    else
    {
        return _python_builtin_open.call(
           buffering,
           mode,
           file_name
        );
    }
}

PyObject *CHR( PyObject *value )
{
    long x = PyInt_AsLong( value );

    if ( x < 0 || x >= 256 )
    {
        PyErr_Format( PyExc_ValueError, "chr() arg not in range(256)" );
        throw _PythonException();
    }

    // TODO: A switch statement might be faster, because no object needs to be created at
    // all, this is how CPython does it.
    char s[1];
    s[0] = (char)x;

    return PyString_FromStringAndSize( s, 1 );
}

PyObject *ORD( PyObject *value )
{
    long result;

    if (likely( PyString_Check( value ) ))
    {
        Py_ssize_t size = PyString_GET_SIZE( value );

        if (likely( size == 1 ))
        {
            result = long( ((unsigned char *)PyString_AS_STRING( value ))[0] );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but string of length %" PY_FORMAT_SIZE_T "d found", size );
            throw _PythonException();
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
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but byte array of length %" PY_FORMAT_SIZE_T "d found", size );
            throw _PythonException();
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
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but unicode string of length %" PY_FORMAT_SIZE_T "d found", size );
            throw _PythonException();
        }
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "ord() expected string of length 1, but %s found", value->ob_type->tp_name );
        throw _PythonException();
    }

    return PyInt_FromLong( result );
}

PyObject *BUILTIN_TYPE1( PyObject *arg )
{
    return INCREASE_REFCOUNT( (PyObject *)Py_TYPE( arg ) );
}

PyObject *BUILTIN_TYPE3( PyObject *module_name, PyObject *name, PyObject *bases, PyObject *dict )
{

    PyObject *result = PyType_Type.tp_new( &PyType_Type, PyObjectTemporary( MAKE_TUPLE( dict, bases, name ) ).asObject(), NULL );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    PyTypeObject *type = result->ob_type;

    if (likely( PyType_IsSubtype( type, &PyType_Type ) ))
    {
        if ( PyType_HasFeature( type, Py_TPFLAGS_HAVE_CLASS ) && type->tp_init != NULL )
        {
            int res = type->tp_init( result, MAKE_TUPLE( dict, bases, name ), NULL );

            if (unlikely( res < 0 ))
            {
                Py_DECREF( result );
                throw _PythonException();
            }
        }
    }

    int res = PyObject_SetAttr( result, _python_str_plain___module__, module_name );

    if ( res == -1 )
    {
        throw _PythonException();
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

PyObject *BUILTIN_RANGE( long low, long high, long step )
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

    for( int i = 0; i < size; i++ )
    {
        PyList_SET_ITEM( result, i, PyInt_FromLong( current ) );
        current += step;
    }

    return result;
}

PyObject *BUILTIN_RANGE( long low, long high )
{
    return BUILTIN_RANGE( low, high, 1 );
}

PyObject *BUILTIN_RANGE( long boundary )
{
    return BUILTIN_RANGE( 0, boundary );
}

static PyObject *TO_RANGE_ARG( PyObject *value, char const *name )
{
    if (likely( PyInt_Check( value ) || PyLong_Check( value )) )
    {
        return INCREASE_REFCOUNT( value );
    }

    PyTypeObject *type = value->ob_type;
    PyNumberMethods *tp_as_number = type->tp_as_number;

    // Everything that casts to int is allowed.
    if (
#if !(PY_MAJOR_VERSION < 3 && PY_MINOR_VERSION < 7)
        PyFloat_Check( value ) ||
#endif
        tp_as_number == NULL ||
        tp_as_number->nb_int == NULL
       )
    {
        PyErr_Format( PyExc_TypeError, "range() integer %s argument expected, got %s.", name, type->tp_name );
        throw _PythonException();
    }

    PyObject *result = tp_as_number->nb_int( value );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

static PythonBuiltin _python_builtin_range( "range" );

PyObject *BUILTIN_RANGE( PyObject *boundary )
{
    PyObjectTemporary boundary_temp( TO_RANGE_ARG( boundary, "end" ) );

    long start = PyInt_AsLong( boundary_temp.asObject() );

    if ( start == -1 && PyErr_Occurred() )
    {
        PyErr_Clear();

        return _python_builtin_range.call( boundary_temp.asObject() );
    }

    return BUILTIN_RANGE( start );
}

PyObject *BUILTIN_RANGE( PyObject *low, PyObject *high )
{
    PyObjectTemporary low_temp( TO_RANGE_ARG( low, "start" ) );
    PyObjectTemporary high_temp( TO_RANGE_ARG( high, "end" ) );

    bool fallback = false;

    long start = PyInt_AsLong( low_temp.asObject() );

    if (unlikely( start == -1 && PyErr_Occurred() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    long end = PyInt_AsLong( high_temp.asObject() );

    if (unlikely( end == -1 && PyErr_Occurred() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    if ( fallback )
    {
        return _python_builtin_range.call( high_temp.asObject(), low_temp.asObject() );
    }
    else
    {
        return BUILTIN_RANGE( start, end );
    }
}

PyObject *BUILTIN_RANGE( PyObject *low, PyObject *high, PyObject *step )
{
    PyObjectTemporary low_temp( TO_RANGE_ARG( low, "start" ) );
    PyObjectTemporary high_temp( TO_RANGE_ARG( high, "end" ) );
    PyObjectTemporary step_temp( TO_RANGE_ARG( step, "step" ) );

    bool fallback = false;

    long start = PyInt_AsLong( low_temp.asObject() );

    if (unlikely( start == -1 && PyErr_Occurred() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    long end = PyInt_AsLong( high_temp.asObject() );

    if (unlikely( end == -1 && PyErr_Occurred() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    long step_long = PyInt_AsLong( step_temp.asObject() );

    if (unlikely( step_long == -1 && PyErr_Occurred() ))
    {
        PyErr_Clear();
        fallback = true;
    }

    if ( fallback )
    {
        return _python_builtin_range.call( step_temp.asObject(), high_temp.asObject(), low_temp.asObject() );
    }
    else
    {
        if (unlikely( step_long == 0 ))
        {
            PyErr_Format( PyExc_ValueError, "range() step argument must not be zero" );
            throw _PythonException();
        }

        return BUILTIN_RANGE( start, end, step_long );
    }
}

PyObject *BUILTIN_LEN( PyObject *value )
{
    Py_ssize_t res = PyObject_Size( value );

    if (unlikely( res < 0 && PyErr_Occurred() ))
    {
        throw _PythonException();
    }

    return PyInt_FromSsize_t( res );
}

// TODO: Move this to global init, so it's not pre-main code that may not be run.
static PyObject *empty_code = PyBuffer_FromMemory( NULL, 0 );

static PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name )
{
    assert( PyString_Check( filename ) );
    assert( PyString_Check( function_name ) );

    assert( empty_code );

    PyCodeObject *result = PyCode_New (
        0, 0, 0, 0,          // argcount, locals, stacksize, flags
        empty_code,          // code
        _python_tuple_empty, // consts (we are not going to be compatible)
        _python_tuple_empty, // names (we are not going to be compatible)
        _python_tuple_empty, // varnames (we are not going to be compatible)
        _python_tuple_empty, // freevars (we are not going to be compatible)
        _python_tuple_empty, // cellvars (we are not going to be compatible)
        filename,            // filename
        function_name,       // name
        0,                   // firstlineno (offset of the code object)
        _python_str_empty    // lnotab (table to translate code object)
    );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *MAKE_FRAME( PyCodeObject *code, PyObject *module )
{
    PyFrameObject *result = PyFrame_New(
        PyThreadState_GET(),                 // thread state
        code,                                // code
        ((PyModuleObject *)module)->md_dict, // globals (module dict)
        NULL                                 // locals (we are not going to be compatible (yet?))
    );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return (PyObject *)result;
}

PyObject *MAKE_FRAME( PyObject *filename, PyObject *function_name, PyObject *module )
{
    return MAKE_FRAME( MAKE_CODEOBJ( filename, function_name ), module );
}

#ifdef _NUITKA_EXE
extern bool *FIND_EMBEDDED_MODULE( PyObject *module_name );

PyObject *IMPORT_EMBEDDED_MODULE( PyObject *module_name, PyObject *import_name )
{
    if ( HAS_KEY( PySys_GetObject( (char *)"modules" ), module_name ) )
    {
        return LOOKUP_SUBSCRIPT( PySys_GetObject( (char *)"modules" ), import_name );
    }
    else
    {
        if ( FIND_EMBEDDED_MODULE( module_name ) )
        {
            return LOOKUP_SUBSCRIPT( PySys_GetObject( (char *)"modules" ), import_name );
        }
    }

    PyErr_Format( PyExc_RuntimeError, "couldn't find embedded module '%s'", PyString_AsString( module_name ) );
    throw _PythonException();
}
#endif

PyObject *IMPORT_MODULE( PyObject *module_name, PyObject *import_name, PyObject *package, PyObject *import_items, int level )
{
    assert( PyString_Check( module_name ) );

    // None doesn't count here.
    if ( package == Py_None )
    {
        package = NULL;
    }

    // Create a globals dict if necessary with the package string.
    PyObject *globals_dict = NULL;

    if ( package != NULL )
    {
        assert( PyString_Check( package ));

        globals_dict = MAKE_DICT( _python_str_plain___package__, package );
    }

    int line = _current_line;

    char *module_name_str = PyString_AS_STRING( module_name );

    PyObject *import_result = PyImport_ImportModuleLevel(
        module_name_str,
        globals_dict,
        NULL,
        import_items,
        level
    );

    Py_XDECREF( globals_dict );

    _current_line = line;

    if (unlikely( import_result == NULL ))
    {
        // printf( "FAIL Importing %s as level %d\n", module_name_str, level );

        throw _PythonException();
    }

    // printf( "PASS Importing %s as level %d\n", module_name_str, level );

    // Release the reference returned from the import, we don't trust it, because it
    // doesn't work well with packages. Look up in sys.modules instead.
    Py_DECREF( import_result );

    PyObject *sys_modules = PySys_GetObject( (char *)"modules" );

    PyObject *result;


    if ( level == 0 )
    {
        // Absolute import was requested, try only that.
        result = LOOKUP_SUBSCRIPT( sys_modules, import_name );
    }
    else if ( abs( level ) == 1 && HAS_KEY( sys_modules, import_name ))
    {
        // Absolute and relative import were both allowed, absolute works, so take that
        // first.
        result = LOOKUP_SUBSCRIPT( sys_modules, import_name );
    }
    else
    {
        // TODO: If we are here, and package is NULL, we lost and should raise
        // import error.
        assertObject( package );

        // Now that absolute import failed, try relative import to current package.
        level = abs( level );

        PyObjectTemporary package_temp( package );

        while( level > 1 )
        {
            PyObject *partition = PyObject_CallMethod( package_temp.asObject(), (char *)"rpartition", (char *)"O", _python_str_dot );

            if ( partition == NULL )
            {
                throw _PythonException();
            }

            package_temp.assign( SEQUENCE_ELEMENT( partition, 0 ) );
            Py_DECREF( partition );

            level -= 1;
        }

        package = package_temp.asObject();

        if ( PyString_Size( import_name ) > 0 )
        {
            PyObjectTemporary full_name(
                PyString_FromFormat(
                    "%s.%s",
                    PyString_AsString( package ),
                    PyString_AsString( import_name )
                )
            );

            result = LOOKUP_SUBSCRIPT( sys_modules, full_name.asObject() );
        }
        else
        {
            result = LOOKUP_SUBSCRIPT( sys_modules, package );
        }
    }

    return result;
}

void IMPORT_MODULE_STAR( PyObject *target, bool is_module, PyObject *module_name, PyObject *module )
{
    // Check parameters.
    assertObject( module );
    assertObject( target );

    PyObject *iter;
    bool all_case;

    if ( PyObject *all = PyMapping_GetItemString( module, (char *)"__all__" ) )
    {
        iter = MAKE_ITERATOR( all );
        all_case = true;
    }
    else
    {
        PyErr_Clear();

        iter = MAKE_ITERATOR( PyModule_GetDict( module ) );
        all_case = false;
    }

    while ( PyObject *item = ITERATOR_NEXT( iter ) )
    {
        assert( PyString_Check( item ) );

        // TODO: Not yet clear, what happens with __all__ and "_" of its contents.
        if ( all_case == false )
        {
            if ( PyString_AS_STRING( item )[0] == '_' )
            {
                continue;
            }
        }

        // TODO: Check if the reference is handled correctly
        if ( is_module )
        {
            SET_ATTRIBUTE( target, item, LOOKUP_ATTRIBUTE( module, item ) );
        }
        else
        {
            SET_SUBSCRIPT( target, item, LOOKUP_ATTRIBUTE( module, item ) );
        }

        Py_DECREF( item );
    }
}

// Helper functions for print. Need to play nice with Python softspace behaviour.

#if PY_MAJOR_VERSION < 3

void PRINT_ITEM_TO( PyObject *file, PyObject *object )
{
    assertObject( object );

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

#ifndef __NUITKA_NO_ASSERT__
        int status =
#endif
            PyString_AsStringAndSize( str, &buffer, &length );
        assert( status != -1 );

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

void PRINT_NEW_LINE_TO( PyObject *file )
{
    if (unlikely( PyFile_WriteString( "\n", file ) == -1))
    {
        throw _PythonException();
    }

    PyFile_SoftSpace( file, 0 );
}

#endif

PyObject *GET_STDOUT()
{
    PyObject *result = PySys_GetObject( (char *)"stdout" );

    if (unlikely( result == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "lost sys.stdout" );
        throw _PythonException();
    }

    return result;
}

#if PY_MAJOR_VERSION < 3

void PRINT_NEW_LINE( void )
{
    PRINT_NEW_LINE_TO( GET_STDOUT() );
}

#endif

// We unstream some constant objects using the "cPickle" module function "loads"
static PyObject *_module_cPickle = NULL;
static PyObject *_module_cPickle_function_loads = NULL;

void UNSTREAM_INIT( void )
{
#if PY_MAJOR_VERSION < 3
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
    PyObjectTemporary temp_str(
        PyString_FromStringAndSize( buffer, size )
    );

    PyObject *result = PyObject_CallFunctionObjArgs(
        _module_cPickle_function_loads,
        temp_str.asObject(),
        NULL
    );

    assert( result != NULL );

    return result;
}

PyObject *UNSTREAM_STRING( char const *buffer, Py_ssize_t size )
{
    PyObject *result = PyString_FromStringAndSize( buffer, size );

    assert( result != NULL );
    assert( PyString_Size( result ) == size );

    return result;
}
