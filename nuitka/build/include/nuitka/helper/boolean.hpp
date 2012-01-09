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
#ifndef __NUITKA_HELPER_BOOLEAN_H__
#define __NUITKA_HELPER_BOOLEAN_H__

#if PYTHON_VERSION >= 300
#define nb_nonzero nb_bool
#endif

NUITKA_MAY_BE_UNUSED static bool CHECK_IF_TRUE( PyObject *object )
{
    assertObject( object );

    if ( object == Py_True )
    {
        return true;
    }
    else if ( object == Py_False || object == Py_None )
    {
        return false;
    }
    else
    {
        Py_ssize_t result;

        if ( object->ob_type->tp_as_number != NULL && object->ob_type->tp_as_number->nb_nonzero != NULL )
        {
            result = (*object->ob_type->tp_as_number->nb_nonzero)( object );
        }
        else if ( object->ob_type->tp_as_mapping != NULL && object->ob_type->tp_as_mapping->mp_length != NULL )
        {
            result = (*object->ob_type->tp_as_mapping->mp_length)( object );
        }
        else if ( object->ob_type->tp_as_sequence != NULL && object->ob_type->tp_as_sequence->sq_length != NULL )
        {
            result = (*object->ob_type->tp_as_sequence->sq_length)( object );
        }
        else
        {
            return true;
        }

        if ( result > 0 )
        {
            return true;
        }
        else if ( result == 0 )
        {
            return false;
        }
        else
        {
            throw _PythonException();
        }
    }
}

NUITKA_MAY_BE_UNUSED static bool CHECK_IF_FALSE( PyObject *object )
{
    return CHECK_IF_TRUE( object ) == false;
}

NUITKA_MAY_BE_UNUSED static PyObject *BOOL_FROM( bool value )
{
    return value ? Py_True : Py_False;
}

NUITKA_MAY_BE_UNUSED static PyObject *UNARY_NOT( PyObject *object )
{
    return BOOL_FROM( CHECK_IF_FALSE( object ) );
}

#undef nb_nonzero

#endif
