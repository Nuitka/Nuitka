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

/**
 * This is responsible for providing API not available on older Python, but
 * workarounds for them.
 */

// TODO: Seems dead now that 3.2 is not supported anymore.
#if 0

#define Py_MIN(x, y) (((x) > (y)) ? (y) : (x))

extern PyObject *const_str_empty;


/**
 * This is not available before Python3.3, but used in the module package name
 * logic.
 */
PyObject *PyUnicode_Substring( PyObject *self, Py_ssize_t start, Py_ssize_t end )
{
    Py_ssize_t length = PyUnicode_GetLength( self );
    end = Py_MIN( end, length );

    if ( start == 0 && end == length )
    {
        return PyUnicode_FromObject( self );
    }

    if ( start < 0 || end < 0 )
    {
        PyErr_SetString(PyExc_IndexError, "string index out of range");
        return NULL;
    }

    if ( start >= length || end < start )
    {
        Py_INCREF( const_str_empty );
        return const_str_empty;
    }

    length = end - start;

    return PyUnicode_FromUnicode( PyUnicode_AsUnicode( self ) + start, length );
}

#endif
