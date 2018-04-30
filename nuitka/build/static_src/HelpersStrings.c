//     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

/* This helpers is used to quickly create a string object from C char.

   Currently this is used for string subscript code, but may also be used
   for the "char" C type in the future.
*/
PyObject *STRING_FROM_CHAR( unsigned char c )
{
    // TODO: A switch statement might be faster, because no object needs to be
    // created at all, this here is how CPython does it.
    char s[1];
    s[0] = (char)c;

#if PYTHON_VERSION < 300
    return PyString_FromStringAndSize( s, 1 );
#else
    return PyUnicode_FromStringAndSize( s, 1 );
#endif
}

/* The "chr" built-in.

   This could also use a table for the interned single char strings, to be
   faster on Python2. For Python3 no such table is reasonable.
*/

PyObject *BUILTIN_CHR( PyObject *value )
{
    long x = PyInt_AsLong( value );

#if PYTHON_VERSION < 300
    if ( x < 0 || x >= 256 )
    {
        PyErr_Format( PyExc_ValueError, "chr() arg not in range(256)" );
        return NULL;
    }

    // TODO: A switch statement might be faster, because no object needs to be
    // created at all, this is how CPython does it.
    char s[1];
    s[0] = (char)x;

    return PyString_FromStringAndSize( s, 1 );
#else
    PyObject *result = PyUnicode_FromOrdinal( x );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    assert( PyUnicode_Check( result ));

    return result;
#endif
}

/* The "ord" built-in.

*/

PyObject *BUILTIN_ORD( PyObject *value )
{
    long result;

    if (likely( PyBytes_Check( value ) ))
    {
        Py_ssize_t size = PyBytes_GET_SIZE( value );

        if (likely( size == 1 ))
        {
            result = (long)( ((unsigned char *)PyBytes_AS_STRING( value ))[0] );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but string of length %zd found", size );
            return NULL;
        }
    }
    else if ( PyByteArray_Check( value ) )
    {
        Py_ssize_t size = PyByteArray_GET_SIZE( value );

        if (likely( size == 1 ))
        {
            result = (long)( ((unsigned char *)PyByteArray_AS_STRING( value ))[0] );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but byte array of length %zd found", size );
            return NULL;
        }
    }
    else if ( PyUnicode_Check( value ) )
    {
#if PYTHON_VERSION >= 330
        if (unlikely( PyUnicode_READY( value ) == -1 ))
        {
            return NULL;
        }

        Py_ssize_t size = PyUnicode_GET_LENGTH( value );
#else
        Py_ssize_t size = PyUnicode_GET_SIZE( value );
#endif

        if (likely( size == 1 ))
        {
#if PYTHON_VERSION >= 330
            result = (long)( PyUnicode_READ_CHAR( value, 0 ) );
#else
            result = (long)( *PyUnicode_AS_UNICODE( value ) );
#endif
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "ord() expected a character, but unicode string of length %zd found", size );
            return NULL;
        }
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "ord() expected string of length 1, but %s found", Py_TYPE( value )->tp_name );
        return NULL;
    }

    return PyInt_FromLong( result );
}
