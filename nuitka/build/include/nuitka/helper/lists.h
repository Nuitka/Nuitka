//     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_LISTS_H__
#define __NUITKA_HELPER_LISTS_H__

NUITKA_MAY_BE_UNUSED static PyObject *LIST_COPY( PyObject *list )
{
    CHECK_OBJECT( list );
    assert( PyList_CheckExact( list ) );

    Py_ssize_t size = PyList_GET_SIZE( list );
    PyObject *result = PyList_New( size );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        PyObject *item = PyList_GET_ITEM( list, i );
        Py_INCREF( item );
        PyList_SET_ITEM( result, i, item );
    }

    return result;
}


#endif
