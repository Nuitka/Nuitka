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
#ifndef __NUITKA_PRINTING_H__
#define __NUITKA_PRINTING_H__

// Helper functions for print. Need to play nice with Python softspace behaviour.

#if PY_MAJOR_VERSION < 3

extern void PRINT_ITEM_TO( PyObject *file, PyObject *object );

extern void PRINT_NEW_LINE_TO( PyObject *file );
extern void PRINT_NEW_LINE( void );

extern PyObject *GET_STDOUT();

template<typename... P>
extern void PRINT_ITEMS( bool new_line, PyObject *file, P...eles )
{
    int size = sizeof...(eles);

    if ( file == NULL || file == Py_None )
    {
        file = GET_STDOUT();
    }

    // Need to hold a reference for the case that the printing somehow removes
    // the last reference to "file" while printing.
    Py_INCREF( file );
    PyObjectTemporary file_reference( file );

    PyObject *elements[] = {eles...};

    for( int i = 0; i < size; i++ )
    {
        PRINT_ITEM_TO( file, elements[ i ] );
    }

    if ( new_line )
    {
        PRINT_NEW_LINE_TO( file );
    }
}

// Helper functions to debug the compiler operation.
NUITKA_MAY_BE_UNUSED static void PRINT_REFCOUNT( PyObject *object )
{
   char buffer[ 1024 ];
   sprintf( buffer, " refcnt %" PY_FORMAT_SIZE_T "d ", object->ob_refcnt );

   if (unlikely( PyFile_WriteString( buffer, GET_STDOUT() ) == -1 ))
   {
      throw _PythonException();
   }
}

#endif

#endif
