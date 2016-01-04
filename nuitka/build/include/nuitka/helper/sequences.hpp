//     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_HELPER_SEQUENCES_H__
#define __NUITKA_HELPER_SEQUENCES_H__

NUITKA_MAY_BE_UNUSED static PyObject *SEQUENCE_CONTAINS( PyObject *element, PyObject *sequence )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        return NULL;
    }

    return BOOL_FROM( result == 1 );
}

NUITKA_MAY_BE_UNUSED static PyObject *SEQUENCE_CONTAINS_NOT( PyObject *element, PyObject *sequence )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        return NULL;
    }

    return BOOL_FROM( result == 0 );
}

NUITKA_MAY_BE_UNUSED static bool SEQUENCE_CONTAINS_BOOL( PyObject *element, PyObject *sequence )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        return NULL;
    }

    return result == 1;
}

NUITKA_MAY_BE_UNUSED static bool SEQUENCE_CONTAINS_NOT_BOOL( PyObject *element, PyObject *sequence )
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        return NULL;
    }

    return result == 0;
}

NUITKA_MAY_BE_UNUSED static bool SEQUENCE_SETITEM( PyObject *sequence, Py_ssize_t index, PyObject *value )
{
    CHECK_OBJECT( sequence );
    CHECK_OBJECT( value );

    PySequenceMethods *sequence_methods = Py_TYPE( sequence )->tp_as_sequence;

    if ( sequence_methods != NULL && sequence_methods->sq_ass_item )
    {
        if ( index < 0 )
        {
            if ( sequence_methods->sq_length )
            {
                Py_ssize_t length = (*sequence_methods->sq_length)( sequence );

                if ( length < 0 )
                {
                    return false;
                }

                index += length;
            }
        }

        int res = sequence_methods->sq_ass_item( sequence, index, value );

        if (unlikely( res == -1 ))
        {
            return false;
        }

        return true;
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object does not support item assignment",
            Py_TYPE( sequence )->tp_name
        );

        return false;
    }
}

#endif
