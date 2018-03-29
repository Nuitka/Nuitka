//     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
#define NEW_STYLE_NUMBER( o ) ( true )
#endif

typedef PyObject *(unary_api)( PyObject * );

NUITKA_MAY_BE_UNUSED static PyObject *UNARY_OPERATION( unary_api api, PyObject *operand )
{
    CHECK_OBJECT( operand );
    PyObject *result = api( operand );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    CHECK_OBJECT( result );

    return result;
}

typedef PyObject *(binary_api)( PyObject *, PyObject * );

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION( binary_api api, PyObject *operand1, PyObject *operand2 )
{
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

    PyObject *result = api( operand1, operand2 );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static bool BINARY_OPERATION_INPLACE( binary_api api, PyObject **operand1, PyObject *operand2 )
{
    assert( operand1 );
    CHECK_OBJECT( *operand1 );
    CHECK_OBJECT( operand2 );

    // TODO: There is not really much point in these things.
    PyObject *result = BINARY_OPERATION( api, *operand1, operand2 );

    if (unlikely( result == NULL ))
    {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF( *operand1 );

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = result;

    return true;
}


NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_ADD( PyObject *operand1, PyObject *operand2 )
{
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

#if PYTHON_VERSION < 300
    // Something similar for Python3 should exist too.
    if ( PyInt_CheckExact( operand1 ) && PyInt_CheckExact( operand2 ) )
    {
        long a, b, i;

        a = PyInt_AS_LONG( operand1 );
        b = PyInt_AS_LONG( operand2 );

        i = a + b;

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here.
        if (likely(!( (i^a) < 0 && (i^b) < 0 ) ))
        {
            return PyInt_FromLong( i );
        }
    }
#endif

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
#include <stddef.h>

#define PyStringObject_SIZE ( offsetof( PyStringObject, ob_sval ) + 1 )

NUITKA_MAY_BE_UNUSED static bool STRING_RESIZE( PyObject **value, Py_ssize_t newsize )
{
    PyStringObject *sv;

    _Py_DEC_REFTOTAL;
    _Py_ForgetReference( *value );

    *value = (PyObject *)PyObject_REALLOC( (char *)*value, PyStringObject_SIZE + newsize );

    if (unlikely( *value == NULL ))
    {
        PyErr_NoMemory();

        return false;
    }
    _Py_NewReference( *value );

    sv = (PyStringObject *)*value;
    Py_SIZE( sv ) = newsize;

    sv->ob_sval[newsize] = '\0';
    sv->ob_shash = -1;

    return true;
}

NUITKA_MAY_BE_UNUSED static bool STRING_ADD_INCREMENTAL( PyObject **operand1, PyObject *operand2 )
{
    assert( PyString_CheckExact( *operand1 ) );
    assert( !PyString_CHECK_INTERNED( *operand1 ) );
    assert( PyString_CheckExact( operand2 ) );

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

    if (unlikely( STRING_RESIZE( operand1, new_size ) == false ))
    {
        return false;
    }

    memcpy(
        PyString_AS_STRING( *operand1 ) + operand1_size,
        PyString_AS_STRING( operand2 ),
        operand2_size
    );

    return true;
}
#else
NUITKA_MAY_BE_UNUSED static bool UNICODE_ADD_INCREMENTAL( PyObject **operand1, PyObject *operand2 )
{
#if PYTHON_VERSION < 330
    Py_ssize_t operand1_size = PyUnicode_GET_SIZE( *operand1 );
    Py_ssize_t operand2_size = PyUnicode_GET_SIZE( operand2 );

    Py_ssize_t new_size = operand1_size + operand2_size;

    if (unlikely( new_size < 0 ))
    {
        PyErr_Format(
            PyExc_OverflowError,
            "strings are too large to concat"
        );

        return false;
    }

    if (unlikely( PyUnicode_Resize( operand1, new_size ) != 0 ))
    {
        return false;
    }

    /* copy 'w' into the newly allocated area of 'v' */
    memcpy(
        PyUnicode_AS_UNICODE( *operand1 ) + operand1_size,
        PyUnicode_AS_UNICODE( operand2 ),
        operand2_size * sizeof( Py_UNICODE )
    );

    return true;
#else
    PyUnicode_Append( operand1, operand2 );
    return !ERROR_OCCURRED();
#endif
}

#endif

static bool FLOAT_ADD_INCREMENTAL( PyObject **operand1, PyObject *operand2 )
{
    assert( PyFloat_CheckExact( *operand1 ) );
    assert( PyFloat_CheckExact( operand2 ) );

    PyFPE_START_PROTECT("add", return false);
    PyFloat_AS_DOUBLE( *operand1 ) += PyFloat_AS_DOUBLE( operand2 );
    PyFPE_END_PROTECT( *operand1 );

    return true;
}

static bool FLOAT_MUL_INCREMENTAL( PyObject **operand1, PyObject *operand2 )
{
    assert( PyFloat_CheckExact( *operand1 ) );
    assert( PyFloat_CheckExact( operand2 ) );

    PyFPE_START_PROTECT("mul", return false);
    PyFloat_AS_DOUBLE( *operand1 ) *= PyFloat_AS_DOUBLE( operand2 );
    PyFPE_END_PROTECT( *operand1 );

    return true;
}


NUITKA_MAY_BE_UNUSED static bool BINARY_OPERATION_ADD_INPLACE( PyObject **operand1, PyObject *operand2 )
{
    assert( operand1 );
    CHECK_OBJECT( *operand1 );
    CHECK_OBJECT( operand2 );

#if PYTHON_VERSION < 300
    // Something similar for Python3 should exist too.
    if ( PyInt_CheckExact( *operand1 ) && PyInt_CheckExact( operand2 ) )
    {
        long a, b, i;

        a = PyInt_AS_LONG( *operand1 );
        b = PyInt_AS_LONG( operand2 );

        i = a + b;

        // Detect overflow, in which case, a "long" object would have to be
        // created, which we won't handle here. TODO: Add an else for that
        // case.
        if (likely(!( (i^a) < 0 && (i^b) < 0 ) ))
        {
            PyObject *result = PyInt_FromLong( i );
            Py_DECREF( *operand1 );

            *operand1 = result;

            return true;
        }
    }
#endif

#if PYTHON_VERSION < 300
    if ( Py_REFCNT( *operand1 ) == 1 )
    {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
        if ( PyString_CheckExact( *operand1 ) &&
             !PyString_CHECK_INTERNED( *operand1 ) &&
             PyString_CheckExact( operand2 ) )
        {
            return STRING_ADD_INCREMENTAL( operand1, operand2 );
        }
        else if ( PyFloat_CheckExact( *operand1 ) &&
                  PyFloat_CheckExact( operand2 ) )
        {
            return FLOAT_ADD_INCREMENTAL( operand1, operand2 );

        }
    }

    // Strings are to be treated differently.
    if ( PyString_CheckExact( *operand1 ) && PyString_CheckExact( operand2 ) )
    {
        PyString_Concat( operand1, operand2 );
        return !ERROR_OCCURRED();
    }
#else
    if ( Py_REFCNT( *operand1 ) == 1 )
    {
        // We more or less own the operand, so we might re-use its storage and
        // execute stuff in-place.
        if ( PyUnicode_CheckExact( *operand1 ) &&
             !PyUnicode_CHECK_INTERNED( *operand1 ) &&
             PyUnicode_CheckExact( operand2 ) )
        {
            return UNICODE_ADD_INCREMENTAL( operand1, operand2 );
        }
        else if ( PyFloat_CheckExact( *operand1 ) &&
                  PyFloat_CheckExact( operand2 ) )
        {
            return FLOAT_ADD_INCREMENTAL( operand1, operand2 );
        }
    }

    // Strings are to be treated differently.
    if ( PyUnicode_CheckExact( *operand1 ) && PyUnicode_CheckExact( operand2 ) )
    {
        PyObject *result = PyUnicode_Concat( *operand1, operand2 );

        if (unlikely( result == NULL ))
        {
            return false;
        }

        Py_DECREF( *operand1 );
        *operand1 = result;

        return true;
    }
#endif

    PyObject *result = PyNumber_InPlaceAdd( *operand1, operand2 );

    if (unlikely( result == NULL ))
    {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF( *operand1 );

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = result;

    return true;
}

NUITKA_MAY_BE_UNUSED static bool BINARY_OPERATION_MUL_INPLACE( PyObject **operand1, PyObject *operand2 )
{
    assert( operand1 );
    CHECK_OBJECT( *operand1 );
    CHECK_OBJECT( operand2 );

    if ( Py_REFCNT( *operand1 ) == 1 )
    {
        if ( PyFloat_CheckExact( *operand1 ) &&
             PyFloat_CheckExact( operand2 ) )
        {
            return FLOAT_MUL_INCREMENTAL( operand1, operand2 );

        }
    }

    PyObject *result = PyNumber_InPlaceMultiply( *operand1, operand2 );

    if (unlikely( result == NULL ))
    {
        return false;
    }

    // We got an object handed, that we have to release.
    Py_DECREF( *operand1 );

    // That's our return value then. As we use a dedicated variable, it's
    // OK that way.
    *operand1 = result;

    return true;
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
        PyObject *exception = GET_ERROR_OCCURRED();

        if (unlikely(  exception ))
        {
            if ( !EXCEPTION_MATCH_BOOL_SINGLE( exception, PyExc_OverflowError ) )
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
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

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
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

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
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

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

    PyErr_Format(
        PyExc_TypeError,
        "unsupported operand type(s) for /: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    return NULL;
}
#endif

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_FLOORDIV( PyObject *operand1, PyObject *operand2 )
{
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE( operand1 );
    PyTypeObject *type2 = Py_TYPE( operand2 );

    if ( type1->tp_as_number != NULL && NEW_STYLE_NUMBER( operand1 ) )
    {
        slot1 = type1->tp_as_number->nb_floor_divide;
    }

    if ( type1 != type2 )
    {
        if ( type2->tp_as_number != NULL && NEW_STYLE_NUMBER( operand2 ) )
        {
            slot2 = type2->tp_as_number->nb_floor_divide;

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
                binaryfunc slot = mv->nb_floor_divide;

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
        "unsupported operand type(s) for //: '%s' and '%s'",
        type1->tp_name,
        type2->tp_name
    );

    return NULL;
}

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_TRUEDIV( PyObject *operand1, PyObject *operand2 )
{
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

    binaryfunc slot1 = NULL;
    binaryfunc slot2 = NULL;

    PyTypeObject *type1 = Py_TYPE( operand1 );
    PyTypeObject *type2 = Py_TYPE( operand2 );

    if ( type1->tp_as_number != NULL && NEW_STYLE_NUMBER( operand1 ) )
    {
        slot1 = type1->tp_as_number->nb_true_divide;
    }

    if ( type1 != type2 )
    {
        if ( type2->tp_as_number != NULL && NEW_STYLE_NUMBER( operand2 ) )
        {
            slot2 = type2->tp_as_number->nb_true_divide;

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
                binaryfunc slot = mv->nb_true_divide;

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

NUITKA_MAY_BE_UNUSED static PyObject *BINARY_OPERATION_REMAINDER( PyObject *operand1, PyObject *operand2 )
{
    CHECK_OBJECT( operand1 );
    CHECK_OBJECT( operand2 );

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

NUITKA_MAY_BE_UNUSED static PyObject *POWER_OPERATION2( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_InPlacePower( operand1, operand2, Py_None );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}


NUITKA_MAY_BE_UNUSED static bool POWER_OPERATION_INPLACE( PyObject **operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_InPlacePower( *operand1, operand2, Py_None );

    if (unlikely( result == NULL ))
    {
        return false;
    }

    if ( result != *operand1 )
    {
        Py_DECREF( *operand1 );
        *operand1 = result;
    }

    return true;
}

#endif
