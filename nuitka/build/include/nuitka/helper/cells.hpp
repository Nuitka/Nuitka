//     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_CELLS_H__
#define __NUITKA_CELLS_H__

NUITKA_MAY_BE_UNUSED static PyCellObject *PyCell_NEW0( PyObject *value )
{
    CHECK_OBJECT( value );

    PyCellObject *result;

    result = (PyCellObject *)PyObject_GC_New( PyCellObject, &PyCell_Type );
    assert( result != NULL );

    result->ob_ref = value;
    Py_INCREF( value );

    Nuitka_GC_Track( result );
    return result;
}

NUITKA_MAY_BE_UNUSED static PyCellObject *PyCell_NEW1( PyObject *value )
{
    CHECK_OBJECT( value );

    PyCellObject *result;

    result = (PyCellObject *)PyObject_GC_New( PyCellObject, &PyCell_Type );
    assert( result != NULL );

    result->ob_ref = value;

    Nuitka_GC_Track( result );
    return result;
}

NUITKA_MAY_BE_UNUSED static PyCellObject *PyCell_EMPTY( void )
{
    PyCellObject *result;

    result = (PyCellObject *)PyObject_GC_New( PyCellObject, &PyCell_Type );
    assert( result != NULL );

    result->ob_ref = NULL;

    Nuitka_GC_Track( result );
    return result;
}

#endif
