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
#ifndef __NUITKA_PRINTING_H__
#define __NUITKA_PRINTING_H__

// Helper functions for print. Need to play nice with Python softspace behaviour.

#if PY_MAJOR_VERSION < 3

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

        int status = PyString_AsStringAndSize( str, &buffer, &length );
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

static void PRINT_NEW_LINE_TO( PyObject *file )
{
    if (unlikely( PyFile_WriteString( "\n", file ) == -1))
    {
        throw _PythonException();
    }

    PyFile_SoftSpace( file, 0 );
}

#endif

static PyObject *GET_STDOUT()
{
    PyObject *stdout = PySys_GetObject( (char *)"stdout" );

    if (unlikely( stdout == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "lost sys.stdout" );
        throw _PythonException();
    }

    return stdout;
}

#if PY_MAJOR_VERSION < 3

template<typename... P>
static void PRINT_ITEMS( bool new_line, PyObject *file, P...eles )
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


static void PRINT_NEW_LINE( void )
{
    PRINT_NEW_LINE_TO( GET_STDOUT() );
}

#endif

#endif
