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
#ifndef __NUITKA_OPERATIONS_H__
#define __NUITKA_OPERATIONS_H__

#if PYTHON_VERSION < 300
#define NEW_STYLE_NUMBER( o ) PyType_HasFeature( Py_TYPE( o ), Py_TPFLAGS_CHECKTYPES )
#else
#define NEW_STYLE_NUMBER( o ) (true)
#endif


NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_ADD( PyObject *operand1, PyObject *operand2 )
{
    assertObject( operand1 );
    assertObject( operand2 );

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE( operand1 );
    PyTypeObject *type2 = Py_TYPE( operand2 );

    if ( type1->tp_as_number != NULL && NEW_STYLE_NUMBER( operand1 ) )
    {
        slot1 = type1->tp_as_number->nb_add;
    }

    if ( type1 != type2 )
    {
        if ( type2->tp_as_number != NULL && NEW_STYLE_NUMBER( operand2 ) )
        {
            slot2 = type2->tp_as_number->nb_add;

            if ( slot1 == slot2 )
            {
                slot2 = NULL;
            }
        }
    }

    if ( slot1 != NULL )
    {
        if ( slot2 && PyType_IsSubtype( type2, type1 ) )
        {
            PyObject *x = slot2( operand1, operand2 );

            if ( x != Py_NotImplemented )
            {
                if ( x == 0 )
                {
                    throw _PythonException();
                }

                return x;
            }

            Py_DECREF( x );
            slot2 = NULL;
        }

        PyObject *x = slot1( operand1, operand2 );

        if ( x != Py_NotImplemented )
        {
            if ( x == 0 )
            {
                throw _PythonException();
            }

            return x;
        }

        Py_DECREF( x );
    }

    if ( slot2 != NULL )
    {
        PyObject *x = slot2( operand1, operand2 );

        if ( x != Py_NotImplemented )
        {
            if ( x == 0 )
            {
                throw _PythonException();
            }

            return x;
        }

        Py_DECREF( x );
    }

#if PYTHON_VERSION < 300
    if ( !NEW_STYLE_NUMBER( operand1 ) || !NEW_STYLE_NUMBER( operand2 ) )
    {
        int err = PyNumber_CoerceEx( &operand1, &operand2 );

        if ( err < 0 )
        {
            throw _PythonException();
        }

        if ( err == 0 )
        {
            PyNumberMethods *mv = Py_TYPE( operand1 )->tp_as_number;

            if ( mv )
            {
                binaryfunc slot = mv->nb_add;

                if ( slot != NULL )
                {
                    PyObject *x = slot( operand1, operand2 );

                    Py_DECREF( operand1 );
                    Py_DECREF( operand2 );

                    if ( x == NULL )
                    {
                        throw _PythonException();
                    }

                    return x;
                }
            }

            // CoerceEx did that
            Py_DECREF( operand1 );
            Py_DECREF( operand2 );
        }
    }
#endif

    // Special case for "+", also works as sequence concat.
    PySequenceMethods *seq_methods = Py_TYPE( operand1 )->tp_as_sequence;

    if ( seq_methods && seq_methods->sq_concat )
    {
        PyObject *result = (*seq_methods->sq_concat)( operand1, operand2 );

        if ( result == NULL )
        {
            throw _PythonException();
        }

        return result;
    }

    PyErr_Format(
        PyExc_TypeError,
        "unsupported operand type(s) for +: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    throw _PythonException();
}

#endif
