//     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

        if ( Py_TYPE( object )->tp_as_number != NULL && Py_TYPE( object )->tp_as_number->nb_nonzero != NULL )
        {
            result = (*Py_TYPE( object )->tp_as_number->nb_nonzero)( object );
        }
        else if ( Py_TYPE( object )->tp_as_mapping != NULL && Py_TYPE( object )->tp_as_mapping->mp_length != NULL )
        {
            result = (*Py_TYPE( object )->tp_as_mapping->mp_length)( object );
        }
        else if ( Py_TYPE( object )->tp_as_sequence != NULL && Py_TYPE( object )->tp_as_sequence->sq_length != NULL )
        {
            result = (*Py_TYPE( object )->tp_as_sequence->sq_length)( object );
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
            throw PythonException();
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
