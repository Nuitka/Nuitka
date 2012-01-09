//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit patches or make the software available to licensors of
//     this software in either form, you automatically them grant them a
//     license for your part of the code under "Apache License 2.0" unless you
//     choose to remove this notice.
//
//     Kay Hayen uses the right to license his code under only GPL version 3,
//     to discourage a fork of Nuitka before it is "finished". He will later
//     make a new "Nuitka" release fully under "Apache License 2.0".
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
#ifndef __NUITKA_HELPER_INDEXES_H__
#define __NUITKA_HELPER_INDEXES_H__

NUITKA_MAY_BE_UNUSED static Py_ssize_t CONVERT_TO_INDEX( PyObject *value )
{
    assertObject( value );

#if PYTHON_VERSION < 300
    if ( PyInt_Check( value ) )
    {
        return PyInt_AS_LONG( value );
    }
    else
#endif
    if ( PyIndex_Check( value ) )
    {
        Py_ssize_t result = PyNumber_AsSsize_t( value, NULL );

        if (unlikely( result == -1 && PyErr_Occurred() ))
        {
            throw _PythonException();
        }

        return result;
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "slice indices must be integers or None or have an __index__ method" );
        throw _PythonException();
    }
}

#endif
