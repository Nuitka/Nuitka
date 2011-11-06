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

template<typename... P>
static PyObject *MAKE_TUPLE( P...eles )
{
    int size = sizeof...(eles);
    assert( size > 0 );

    PyObject *elements[] = {eles...};

    PyObject *result = PyTuple_New( size );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        assertObject( elements[ i ] );

        PyTuple_SET_ITEM(
            result,
            i,
            INCREASE_REFCOUNT(
#if NUITKA_REVERSED_ARGS == 1
            elements[ size - 1 - i ]
#else
            elements[ i ]
#endif
            )
        );
    }

    assert( result->ob_refcnt == 1 );

    return result;
}

NUITKA_MAY_BE_UNUSED static inline PyObject *MAKE_TUPLE()
{
    return INCREASE_REFCOUNT( _python_tuple_empty );
}

template<typename... P>
static PyObject *MAKE_LIST( P...eles )
{
    PyObject *elements[] = {eles...};

    int size = sizeof...(eles);
    assert( size > 0 );

    PyObject *result = PyList_New( size );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        assertObject( elements[ i ] );

        PyList_SET_ITEM(
            result,
            i,
#if NUITKA_REVERSED_ARGS == 1
            elements[ size - 1 - i ]
#else
            elements[ i ]
#endif
        );
    }

    assert( result->ob_refcnt == 1 );

    return result;
}

NUITKA_MAY_BE_UNUSED static inline PyObject *MAKE_LIST()
{
    PyObject *result = PyList_New( 0 );

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

NUITKA_MAY_BE_UNUSED static PyObject *SEQUENCE_ELEMENT( PyObject *sequence, Py_ssize_t element )
{
    assertObject( sequence );

    PyObject *result = PySequence_GetItem( sequence, element );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#endif
