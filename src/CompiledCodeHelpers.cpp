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

#include "nuitka/prelude.hpp"

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

    PyObject *future_flags = PyInt_FromLong( flags );

    PyObject *result = PyObject_CallFunctionObjArgs(
        _python_builtin_compile.asObject(),
        source,
        file_name,
        mode,
        future_flags,      // flags
        _python_bool_True, // dont_inherit
        NULL
    );

    Py_DECREF( future_flags );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

static PythonBuiltin _python_builtin_open( "open" );

PyObject *OPEN_FILE( PyObject *file_name, PyObject *mode, PyObject *buffering )
{
    PyObject *result = PyObject_CallFunctionObjArgs(
        _python_builtin_open.asObject(),
        file_name,
        mode,
        buffering,
        NULL
    );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
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
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but string of length %d found", size );
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
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but byte array of length %d found", size );
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
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but unicode string of length %d found", size );
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


static PyObject *empty_code = PyBuffer_FromMemory( NULL, 0 );

static PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name, int line )
{
    // TODO: Potentially it is possible to create a line2no table that will allow to use
    // only one code object per function, this could then be cached and presumably be much
    // faster, because it could be reused.

    assert( PyString_Check( filename ) );
    assert( PyString_Check( function_name ) );

    assert( empty_code );

    // printf( "MAKE_CODEOBJ code object %d\n", empty_code->ob_refcnt );

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

PyObject *MAKE_FRAME( PyObject *module, PyObject *filename, PyObject *function_name, int line )
{
    PyCodeObject *code = MAKE_CODEOBJ( filename, function_name, line );

    PyFrameObject *result = PyFrame_New(
        PyThreadState_GET(),
        code,
        ((PyModuleObject *)module)->md_dict,
        NULL // No locals yet
    );

    Py_DECREF( code );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    result->f_lineno = line;

    return (PyObject *)result;
}

#ifdef _NUITKA_EXE
extern bool FIND_EMBEDDED_MODULE( char const *name );
#endif

PyObject *IMPORT_MODULE( PyObject *module_name, PyObject *import_name )
{

#ifdef _NUITKA_EXE
    // First try our own package resistent form of frozen modules if we have them
    // embedded. And avoid recursion here too, in case of cyclic dependencies.
    if ( !HAS_KEY( PySys_GetObject( (char *)"modules" ), module_name ) )
    {
        if ( FIND_EMBEDDED_MODULE( PyString_AsString( module_name ) ) )
        {
            return LOOKUP_SUBSCRIPT( PySys_GetObject( (char *)"modules" ), import_name );
        }
    }
#endif

    int line = _current_line;
    PyObject *result = PyImport_ImportModuleEx( PyString_AsString( module_name ), NULL, NULL, NULL );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    // Release the reference returned from the import, we don't trust it, because it
    // doesn't work well with packages. Look up in sys.modules instead.
    Py_DECREF( result );

    return LOOKUP_SUBSCRIPT( PySys_GetObject( (char *)"modules" ), import_name );
}

void IMPORT_MODULE_STAR( PyObject *target, bool is_module, PyObject *module_name )
{
    PyObject *module = IMPORT_MODULE( module_name, module_name );

    // IMPORT_MODULE would raise exception already
    assert( module != NULL );

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

    while ( PyObject *item = PyIter_Next( iter ) )
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

    if ( PyErr_Occurred() )
    {
        throw _PythonException();
    }
}
