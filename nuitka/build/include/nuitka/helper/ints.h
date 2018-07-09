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
#ifndef __NUITKA_HELPER_INTS_H__
#define __NUITKA_HELPER_INTS_H__

NUITKA_MAY_BE_UNUSED static PyObject *TO_INT2( PyObject *value, PyObject *base )
{
#if PYTHON_VERSION < 340
    long base_int = PyInt_AsLong( base );
#else
    Py_ssize_t base_int = PyNumber_AsSsize_t( base, NULL );
#endif

    if (unlikely( base_int == -1 ))
    {
        PyObject *error = GET_ERROR_OCCURRED();

        if (likely( error ))
        {
#if PYTHON_VERSION >= 300
            if ( EXCEPTION_MATCH_BOOL_SINGLE( error, PyExc_OverflowError ) )
            {
                PyErr_Format(
                        PyExc_ValueError,
#if PYTHON_VERSION < 324
                        "int() arg 2 must be >= 2 and <= 36"
#elif PYTHON_VERSION < 364
                        "int() base must be >= 2 and <= 36"
#else
                        "int() base must be >= 2 and <= 36, or 0"
#endif
                );
            }
#endif
            return NULL;
        }
    }

#if PYTHON_VERSION >= 300
    if (unlikely( ( base_int != 0 && base_int < 2 ) || base_int > 36 ))
    {
        PyErr_Format(
                PyExc_ValueError,
#if PYTHON_VERSION < 324
                "int() arg 2 must be >= 2 and <= 36"
#elif PYTHON_VERSION < 364
                "int() base must be >= 2 and <= 36"
#else
                "int() base must be >= 2 and <= 36, or 0"
#endif
        );

        return NULL;
    }
#endif

#if PYTHON_VERSION < 300
    if (unlikely( !Nuitka_String_Check( value ) && !PyUnicode_Check( value ) ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "int() can't convert non-string with explicit base"
        );
        return NULL;
    }

    char *value_str = Nuitka_String_AsString( value );
    if (unlikely( value_str == NULL ))
    {
        return NULL;
    }

    PyObject *result = PyInt_FromString( value_str, NULL, base_int );
    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
#else
    if ( PyUnicode_Check( value ) )
    {
#if PYTHON_VERSION < 330
        char *value_str = Nuitka_String_AsString( value );

        if (unlikely( value_str == NULL ))
        {
            return NULL;
        }

        PyObject *result = PyInt_FromString( value_str, NULL, base_int );

        if (unlikely( result == NULL ))
        {
            return NULL;
        }

        return result;
#else
        return PyLong_FromUnicodeObject( value, (int)base_int );
#endif
    }
    else if ( PyBytes_Check( value ) || PyByteArray_Check( value ) )
    {
        // Check for "NUL" as PyLong_FromString has no length parameter,
        Py_ssize_t size = Py_SIZE( value );
        char *value_str;

        if ( PyByteArray_Check( value ) )
        {
            value_str = PyByteArray_AS_STRING( value );
        }
        else
        {
            value_str = PyBytes_AS_STRING( value );
        }

        PyObject *result = NULL;

        if ( size != 0 && strlen( value_str ) == (size_t)size )
        {
            result = PyInt_FromString( value_str, NULL, (int)base_int );
        }

        if (unlikely( result == NULL ))
        {
            PyErr_Format(
                PyExc_ValueError,
                "invalid literal for int() with base %d: %R",
                base_int,
                value
            );

            return NULL;
        }

        return result;
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "int() can't convert non-string with explicit base"
        );
        return NULL;
    }
#endif
}


#if PYTHON_VERSION < 300
// Note: Python3 uses TO_INT2 function.
NUITKA_MAY_BE_UNUSED static PyObject *TO_LONG2( PyObject *value, PyObject *base )
{
    long base_int = PyInt_AsLong( base );

    if (unlikely( base_int == -1 ))
    {
        if (likely( ERROR_OCCURRED() ))
        {
            return NULL;
        }
    }

    if (unlikely( !Nuitka_String_Check( value ) && !PyUnicode_Check( value ) ))
    {
        PyErr_Format( PyExc_TypeError, "long() can't convert non-string with explicit base" );
        return NULL;
    }

    char *value_str = Nuitka_String_AsString( value );
    if (unlikely( value_str == NULL ))
    {
        return NULL;
    }

    PyObject *result = PyLong_FromString( value_str, NULL, base_int );
    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}
#endif

#endif
