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
#ifndef __NUITKA_HELPER_SEQUENCES_H__
#define __NUITKA_HELPER_SEQUENCES_H__

NUITKA_MAY_BE_UNUSED static PyObject *TO_LIST( PyObject *seq_obj )
{
    PyObject *result = PySequence_List( seq_obj );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *TO_TUPLE( PyObject *seq_obj )
{
    PyObject *result = PySequence_Tuple( seq_obj );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define SEQUENCE_CONTAINS( element, sequence ) _SEQUENCE_CONTAINS( EVAL_ORDERED_2( element, sequence ) )

NUITKA_MAY_BE_UNUSED static PyObject *_SEQUENCE_CONTAINS( EVAL_ORDERED_2( PyObject *element, PyObject *sequence ) )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 1 );
}

#define SEQUENCE_CONTAINS_NOT( element, sequence ) _SEQUENCE_CONTAINS_NOT( EVAL_ORDERED_2( element, sequence ) )

NUITKA_MAY_BE_UNUSED static PyObject *_SEQUENCE_CONTAINS_NOT( EVAL_ORDERED_2( PyObject *element, PyObject *sequence ) )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 0 );
}

#define SEQUENCE_CONTAINS_BOOL( element, sequence ) _SEQUENCE_CONTAINS_BOOL( EVAL_ORDERED_2( element, sequence ) )

NUITKA_MAY_BE_UNUSED static bool _SEQUENCE_CONTAINS_BOOL( EVAL_ORDERED_2( PyObject *element, PyObject *sequence ) )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return result == 1;
}

#define SEQUENCE_CONTAINS_NOT_BOOL( element, sequence ) _SEQUENCE_CONTAINS_NOT_BOOL( EVAL_ORDERED_2( element, sequence ) )

NUITKA_MAY_BE_UNUSED static bool _SEQUENCE_CONTAINS_NOT_BOOL( EVAL_ORDERED_2( PyObject *element, PyObject *sequence ) )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return result == 0;
}

#endif
