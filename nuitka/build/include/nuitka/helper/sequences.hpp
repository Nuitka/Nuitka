//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

NUITKA_MAY_BE_UNUSED static void SEQUENCE_SETITEM( PyObject *sequence, Py_ssize_t index, PyObject *value )
{
    assertObject( sequence );
    assertObject( value );

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
                    throw _PythonException();
                }

                index += length;
            }
        }

        int res = sequence_methods->sq_ass_item( sequence, index, value );

        if (unlikely( res == -1 ))
        {
            throw _PythonException();
        }
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object does not support item assignment",
            Py_TYPE( sequence )->tp_name
        );

        throw _PythonException();
    }
}


#endif
