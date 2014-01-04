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
#ifndef __NUITKA_OPERATIONS_H__
#define __NUITKA_OPERATIONS_H__

#if PYTHON_VERSION < 300
#define NEW_STYLE_NUMBER( o ) PyType_HasFeature( Py_TYPE( o ), Py_TPFLAGS_CHECKTYPES )
#else
#define NEW_STYLE_NUMBER( o ) (true)
#endif

typedef PyObject *(unary_api)( PyObject * );

NUITKA_MAY_BE_UNUSED static PyObject *UNARY_OPERATION( unary_api api, PyObject *operand )
{
    assertObject( operand );
    PyObject *result = api( operand );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    assertObject( result );

    return result;
}

typedef PyObject *(binary_api)( PyObject *, PyObject * );

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION( binary_api api, PyObject *operand1, PyObject *operand2 )
{
    assertObject( operand1 );
    assertObject( operand2 );

    PyObject *result = api( operand1, operand2 );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

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
                if (unlikely( x == NULL ))
                {
                    return NULL;
                }

                return x;
            }

            Py_DECREF( x );
            slot2 = NULL;
        }

        PyObject *x = slot1( operand1, operand2 );

        if ( x != Py_NotImplemented )
        {
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            return NULL;
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

                    if (unlikely( x == NULL ))
                    {
                        return NULL;
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

        if (unlikely( result == NULL ))
        {
            return NULL;
        }

        return result;
    }

    PyErr_Format(
        PyExc_TypeError,
        "unsupported operand type(s) for +: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    return NULL;
}

#if PYTHON_VERSION < 300
NUITKA_MAY_BE_UNUSED static bool STRING_ADD_INCREMENTAL( PyObject **operand1, PyObject *operand2 )
{
    if ( !PyString_CHECK_INTERNED( *operand1 ) )
    {
        Py_ssize_t operand1_size = PyString_GET_SIZE( *operand1 );
        Py_ssize_t operand2_size = PyString_GET_SIZE( operand2 );

        Py_ssize_t new_size = operand1_size + operand2_size;

        if (unlikely( new_size < 0 ))
        {
            PyErr_Format(
                PyExc_OverflowError,
                "strings are too large to concat"
            );

            return false;
        }

        if (unlikely( _PyString_Resize( operand1, new_size ) != 0 ))
        {
            return false;
        }

        memcpy(
            PyString_AS_STRING( *operand1 ) + operand1_size,
            PyString_AS_STRING( operand2 ),
            operand2_size
        );
    }
    else
    {
        // Otherwise, normal concat. TODO: Errors?
        PyString_Concat( operand1, operand2 );
    }

    return true;
}
#endif


NUITKA_MAY_BE_UNUSED static bool BINARY_OPERATION_ADD_INCREMENTAL( PyObject **operand1, PyObject *operand2 )
{
    assert( operand1 );
    assertObject( *operand1 );
    assertObject( operand2 );

#if PYTHON_VERSION < 300
    if ( Py_REFCNT( operand1 ) == 1 )
    {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
        if ( PyString_CheckExact( operand1 ) && PyString_CheckExact( operand2 ) )
        {
            return STRING_ADD_INCREMENTAL( operand1, operand2 );
        }
    }
#endif

    PyObject *result = BINARY_OPERATION_ADD( *operand1, operand2 );

    if (unlikely( result == NULL ))
    {
        return false;
    }
    else
    {
        *operand1 = result;
        return true;
    }
}


static PyObject *SEQUENCE_REPEAT( ssizeargfunc repeatfunc, PyObject *seq, PyObject *n )
{
    if (unlikely( !PyIndex_Check( n ) ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "can't multiply sequence by non-int of type '%s'",
            Py_TYPE( n )->tp_name
        );

        return NULL;
    }

    PyObject *index_value = PyNumber_Index( n );

    if (unlikely( index_value == NULL ))
    {
        return NULL;
    }

    /* We're done if PyInt_AsSsize_t() returns without error. */
#if PYTHON_VERSION < 300
    Py_ssize_t count = PyInt_AsSsize_t( index_value );
#else
    Py_ssize_t count = PyLong_AsSsize_t( index_value );
#endif

    Py_DECREF( index_value );

    if (unlikely( count == -1 )) // Note: -1 is an unlikely repetition count
    {
        PyObject *exception = GET_ERROR_OCCURED();

        if (unlikely(  exception ))
        {
            if ( !PyErr_GivenExceptionMatches( exception, PyExc_OverflowError ) )
            {
                return NULL;
            }

            PyErr_Format(
                PyExc_OverflowError,
                "cannot fit '%s' into an index-sized integer",
                Py_TYPE( n )->tp_name
            );

            return NULL;
        }
    }

    PyObject *result = (*repeatfunc)( seq, count );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_MUL( PyObject *operand1, PyObject *operand2 )
{
    assertObject( operand1 );
    assertObject( operand2 );

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE( operand1 );
    PyTypeObject *type2 = Py_TYPE( operand2 );

    if ( type1->tp_as_number != NULL && NEW_STYLE_NUMBER( operand1 ) )
    {
        slot1 = type1->tp_as_number->nb_multiply;
    }

    if ( type1 != type2 )
    {
        if ( type2->tp_as_number != NULL && NEW_STYLE_NUMBER( operand2 ) )
        {
            slot2 = type2->tp_as_number->nb_multiply;

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
                if (unlikely( x == NULL ))
                {
                    return NULL;
                }

                return x;
            }

            Py_DECREF( x );
            slot2 = NULL;
        }

        PyObject *x = slot1( operand1, operand2 );

        if ( x != Py_NotImplemented )
        {
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            return NULL;
        }

        if ( err == 0 )
        {
            PyNumberMethods *mv = Py_TYPE( operand1 )->tp_as_number;

            if ( mv )
            {
                binaryfunc slot = mv->nb_multiply;

                if ( slot != NULL )
                {
                    PyObject *x = slot( operand1, operand2 );

                    Py_DECREF( operand1 );
                    Py_DECREF( operand2 );

                    if (unlikely( x == NULL ))
                    {
                        return NULL;
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
    PySequenceMethods *seq_methods1 = Py_TYPE( operand1 )->tp_as_sequence;
    PySequenceMethods *seq_methods2 = Py_TYPE( operand2 )->tp_as_sequence;

    if  ( seq_methods1 != NULL && seq_methods1->sq_repeat )
    {
        return SEQUENCE_REPEAT( seq_methods1->sq_repeat, operand1, operand2 );
    }

    if  ( seq_methods2 != NULL && seq_methods2->sq_repeat )
    {
        return SEQUENCE_REPEAT( seq_methods2->sq_repeat, operand2, operand1 );
    }

    PyErr_Format(
        PyExc_TypeError,
        "unsupported operand type(s) for *: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    return NULL;
}

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_SUB( PyObject *operand1, PyObject *operand2 )
{
    assertObject( operand1 );
    assertObject( operand2 );

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE( operand1 );
    PyTypeObject *type2 = Py_TYPE( operand2 );

    if ( type1->tp_as_number != NULL && NEW_STYLE_NUMBER( operand1 ) )
    {
        slot1 = type1->tp_as_number->nb_subtract;
    }

    if ( type1 != type2 )
    {
        if ( type2->tp_as_number != NULL && NEW_STYLE_NUMBER( operand2 ) )
        {
            slot2 = type2->tp_as_number->nb_subtract;

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
                if (unlikely( x == NULL ))
                {
                    return NULL;
                }

                return x;
            }

            Py_DECREF( x );
            slot2 = NULL;
        }

        PyObject *x = slot1( operand1, operand2 );

        if ( x != Py_NotImplemented )
        {
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            return NULL;
        }

        if ( err == 0 )
        {
            PyNumberMethods *mv = Py_TYPE( operand1 )->tp_as_number;

            if ( mv )
            {
                binaryfunc slot = mv->nb_subtract;

                if ( slot != NULL )
                {
                    PyObject *x = slot( operand1, operand2 );

                    Py_DECREF( operand1 );
                    Py_DECREF( operand2 );

                    if (unlikely( x == NULL ))
                    {
                        return NULL;
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

    PyErr_Format(
        PyExc_TypeError,
        "unsupported operand type(s) for -: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    return NULL;
}

#if PYTHON_VERSION < 300

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_DIV( PyObject *operand1, PyObject *operand2 )
{
    assertObject( operand1 );
    assertObject( operand2 );

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE( operand1 );
    PyTypeObject *type2 = Py_TYPE( operand2 );

    if ( type1->tp_as_number != NULL && NEW_STYLE_NUMBER( operand1 ) )
    {
        slot1 = type1->tp_as_number->nb_divide;
    }

    if ( type1 != type2 )
    {
        if ( type2->tp_as_number != NULL && NEW_STYLE_NUMBER( operand2 ) )
        {
            slot2 = type2->tp_as_number->nb_divide;

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
                if (unlikely( x == NULL ))
                {
                    return NULL;
                }

                return x;
            }

            Py_DECREF( x );
            slot2 = NULL;
        }

        PyObject *x = slot1( operand1, operand2 );

        if ( x != Py_NotImplemented )
        {
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            return NULL;
        }

        if ( err == 0 )
        {
            PyNumberMethods *mv = Py_TYPE( operand1 )->tp_as_number;

            if ( mv )
            {
                binaryfunc slot = mv->nb_divide;

                if ( slot != NULL )
                {
                    PyObject *x = slot( operand1, operand2 );

                    Py_DECREF( operand1 );
                    Py_DECREF( operand2 );

                    if (unlikely( x == NULL ))
                    {
                        return NULL;
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

    PyErr_Format(
        PyExc_TypeError,
        "unsupported operand type(s) for /: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    return NULL;
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_REMAINDER( PyObject *operand1, PyObject *operand2 )
{
    assertObject( operand1 );
    assertObject( operand2 );

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE( operand1 );
    PyTypeObject *type2 = Py_TYPE( operand2 );

    if ( type1->tp_as_number != NULL && NEW_STYLE_NUMBER( operand1 ) )
    {
        slot1 = type1->tp_as_number->nb_remainder;
    }

    if ( type1 != type2 )
    {
        if ( type2->tp_as_number != NULL && NEW_STYLE_NUMBER( operand2 ) )
        {
            slot2 = type2->tp_as_number->nb_remainder;

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
                if (unlikely( x == NULL ))
                {
                    return NULL;
                }

                return x;
            }

            Py_DECREF( x );
            slot2 = NULL;
        }

        PyObject *x = slot1( operand1, operand2 );

        if ( x != Py_NotImplemented )
        {
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            if (unlikely( x == NULL ))
            {
                return NULL;
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
            return NULL;
        }

        if ( err == 0 )
        {
            PyNumberMethods *mv = Py_TYPE( operand1 )->tp_as_number;

            if ( mv )
            {
                binaryfunc slot = mv->nb_remainder;

                if ( slot != NULL )
                {
                    PyObject *x = slot( operand1, operand2 );

                    Py_DECREF( operand1 );
                    Py_DECREF( operand2 );

                    if (unlikely( x == NULL ))
                    {
                        return NULL;
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

    PyErr_Format(
        PyExc_TypeError,
        "unsupported operand type(s) for %%: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    return NULL;
}

NUITKA_MAY_BE_UNUSED static PyObject *POWER_OPERATION( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_Power( operand1, operand2, Py_None );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *POWER_OPERATION_INPLACE( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_InPlacePower( operand1, operand2, Py_None );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

#endif
