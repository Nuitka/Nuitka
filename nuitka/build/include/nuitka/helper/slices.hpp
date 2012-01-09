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
#ifndef __NUITKA_HELPER_SLICES_H__
#define __NUITKA_HELPER_SLICES_H__

static inline bool IS_INDEXABLE( PyObject *value )
{
    return
        value == Py_None ||
#if PYTHON_VERSION < 300
        PyInt_Check( value ) ||
#endif
        PyLong_Check( value ) ||
        PyIndex_Check( value );
}

#if PYTHON_VERSION < 300
// TODO: It appears that Python3 has no index slicing operations anymore, but uses slice
// objects all the time. That's fine by us for now.

#define LOOKUP_SLICE( source, lower, upper ) _LOOKUP_SLICE( EVAL_ORDERED_3( source, lower, upper ) )

NUITKA_MAY_BE_UNUSED static PyObject *_LOOKUP_SLICE( EVAL_ORDERED_3( PyObject *source, PyObject *lower, PyObject *upper ) )
{
    assertObject( source );
    assertObject( lower );
    assertObject( upper );

    PySequenceMethods *tp_as_sequence = source->ob_type->tp_as_sequence;

    if ( tp_as_sequence && tp_as_sequence->sq_slice && IS_INDEXABLE( lower ) && IS_INDEXABLE( upper ) )
    {
        Py_ssize_t ilow = 0;

        if ( lower != Py_None )
        {
            ilow = CONVERT_TO_INDEX( lower );
        }

        Py_ssize_t ihigh = PY_SSIZE_T_MAX;

        if ( upper != Py_None )
        {
            ihigh = CONVERT_TO_INDEX( upper );
        }

        PyObject *result = PySequence_GetSlice( source, ilow, ihigh );

        if (unlikely( result == NULL ))
        {
            throw _PythonException();
        }

        return result;
    }
    else
    {
        PyObject *slice = PySlice_New( lower, upper, NULL );

        if (unlikely( slice == NULL ))
        {
            throw _PythonException();
        }

        PyObject *result = PyObject_GetItem( source, slice );
        Py_DECREF( slice );

        if (unlikely( result == NULL ))
        {
            throw _PythonException();
        }

        return result;
    }
}

#define LOOKUP_INDEX_SLICE( source, lower, upper ) _LOOKUP_INDEX_SLICE( EVAL_ORDERED_3( source, lower, upper ) )

NUITKA_MAY_BE_UNUSED static PyObject *_LOOKUP_INDEX_SLICE( EVAL_ORDERED_3( PyObject *source, Py_ssize_t lower, Py_ssize_t upper ) )
{
    assertObject( source );

    PyObject *result = PySequence_GetSlice( source, lower, upper );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define SET_SLICE( value, target, upper, lower ) _SET_SLICE( EVAL_ORDERED_4( value, target, upper, lower ) )

NUITKA_MAY_BE_UNUSED static void _SET_SLICE( EVAL_ORDERED_4( PyObject *value, PyObject *target, PyObject *lower, PyObject *upper ) )
{
    assertObject( target );
    assertObject( lower );
    assertObject( upper );
    assertObject( value );

    PySequenceMethods *tp_as_sequence = target->ob_type->tp_as_sequence;

    if ( tp_as_sequence && tp_as_sequence->sq_ass_slice && IS_INDEXABLE( lower ) && IS_INDEXABLE( upper ) )
    {
        Py_ssize_t lower_int = 0;

        if ( lower != Py_None )
        {
            lower_int = CONVERT_TO_INDEX( lower );
        }

        Py_ssize_t upper_int = PY_SSIZE_T_MAX;

        if ( upper != Py_None )
        {
            upper_int = CONVERT_TO_INDEX( upper );
        }

        int status = PySequence_SetSlice( target, lower_int, upper_int, value );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
    else
    {
        PyObject *slice = PySlice_New( lower, upper, NULL );

        if (unlikely( slice == NULL ))
        {
            throw _PythonException();
        }

        int status = PyObject_SetItem( target, slice, value );
        Py_DECREF( slice );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

#define SET_INDEX_SLICE( target, lower, upper, value ) _SET_INDEX_SLICE( EVAL_ORDERED_4( target, lower, upper, value ) )

NUITKA_MAY_BE_UNUSED static void _SET_INDEX_SLICE( EVAL_ORDERED_4( PyObject *target, Py_ssize_t lower, Py_ssize_t upper, PyObject *value ) )
{
    assertObject( target );
    assertObject( value );

    int status = PySequence_SetSlice( target, lower, upper, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

#define DEL_SLICE( target, lower, upper ) _DEL_SLICE( EVAL_ORDERED_3( target, lower, upper ) )


NUITKA_MAY_BE_UNUSED static void _DEL_SLICE( EVAL_ORDERED_3( PyObject *target, Py_ssize_t lower, Py_ssize_t upper ) )
{
    assertObject( target );

    if ( target->ob_type->tp_as_sequence && target->ob_type->tp_as_sequence->sq_ass_slice )
    {
        int status = PySequence_DelSlice( target, lower, upper );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
    else
    {
        PyObjectTemporary lower_obj( PyInt_FromSsize_t( lower ) );
        PyObjectTemporary upper_obj( PyInt_FromSsize_t( upper ) );

        PyObject *slice = PySlice_New( lower_obj.asObject(), upper_obj.asObject(), NULL );

        if (unlikely( slice == NULL ))
        {
            throw _PythonException();
        }

        int status = PyObject_DelItem( target, slice );

        Py_DECREF( slice );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

#endif

#define MAKE_SLICEOBJ( start, stop, step ) _MAKE_SLICEOBJ( EVAL_ORDERED_3( start, stop, step ) )

NUITKA_MAY_BE_UNUSED static PyObject *_MAKE_SLICEOBJ( EVAL_ORDERED_3( PyObject *start, PyObject *stop, PyObject *step ) )
{
    assertObject( start );
    assertObject( stop );
    assertObject( step );

    PyObject *result = PySlice_New( start, stop, step );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#endif
