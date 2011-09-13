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
#ifndef __NUITKA_HELPER_SLICES_H__
#define __NUITKA_HELPER_SLICES_H__

#define LOOKUP_SLICE( source, lower, upper ) _LOOKUP_SLICE( EVAL_ORDERED_3( source, lower, upper ) )

NUITKA_MAY_BE_UNUSED static PyObject *_LOOKUP_SLICE( EVAL_ORDERED_3( PyObject *source, Py_ssize_t lower, Py_ssize_t upper ) )
{
    assertObject( source );

    PyObject *result = PySequence_GetSlice( source, lower, upper);

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define SET_SLICE( target, lower, upper, value ) _SET_SLICE( EVAL_ORDERED_4( target, lower, upper, value ) )

NUITKA_MAY_BE_UNUSED static void _SET_SLICE( EVAL_ORDERED_4( PyObject *target, Py_ssize_t lower, Py_ssize_t upper, PyObject *value ) )
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
