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
#ifndef __NUITKA_HELPER_ITERATORS_H__
#define __NUITKA_HELPER_ITERATORS_H__

#if PYTHON_VERSION >= 270
// Initialize value for "tp_iternext" to compare with, needed by HAS_ITERNEXT
// which emulates PyCheck_Iter but bug free.
extern iternextfunc default_iternext;
extern void _initSlotIternext( void );
#endif

// This is like "PyIter_Check" but without bugs due to shared library pointers.
NUITKA_MAY_BE_UNUSED static inline bool HAS_ITERNEXT( PyObject *value )
{
#if PYTHON_VERSION < 300
    if ( !PyType_HasFeature( Py_TYPE( value ), Py_TPFLAGS_HAVE_ITER ) )
    {
        return false;
    }
#endif

    iternextfunc tp_iternext = Py_TYPE( value )->tp_iternext;

    if ( tp_iternext == NULL )
    {
        return false;
    }

#if PYTHON_VERSION >= 270
    return tp_iternext != default_iternext;
#else
    return true;
#endif
}

// Stolen from CPython implementation, so we can access it.
typedef struct {
    PyObject_HEAD
#if PYTHON_VERSION < 340
    long      it_index;
#else
    Py_ssize_t it_index;
#endif
    PyObject *it_seq;
} seqiterobject;

NUITKA_MAY_BE_UNUSED static PyObject *MAKE_ITERATOR( PyObject *iterated )
{

#if PYTHON_VERSION < 300
    getiterfunc tp_iter = NULL;
    if ( PyType_HasFeature( Py_TYPE( iterated ), Py_TPFLAGS_HAVE_ITER ))
    {
        tp_iter = Py_TYPE( iterated )->tp_iter;
    }
#else
    getiterfunc tp_iter = Py_TYPE( iterated )->tp_iter;
#endif

    if ( tp_iter )
    {
        PyObject *result = (*tp_iter)( iterated );

        if (unlikely( result == NULL ))
        {
            return NULL;
        }
        else if (unlikely( !HAS_ITERNEXT( result )) )
        {
            PyErr_Format(
                PyExc_TypeError,
                "iter() returned non-iterator of type '%s'",
                Py_TYPE( result )->tp_name
            );

            Py_DECREF( result );

            return NULL;
        }
        else
        {
            return result;
        }
    }
    else if ( PySequence_Check( iterated ) )
    {
        seqiterobject *result = PyObject_GC_New( seqiterobject, &PySeqIter_Type );
        assert( result );

        result->it_index = 0;
        result->it_seq = INCREASE_REFCOUNT( iterated );

        Nuitka_GC_Track( result );

        return (PyObject *)result;
    }
    else
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object is not iterable",
            Py_TYPE( iterated )->tp_name
        );

        return NULL;
    }
}

NUITKA_MAY_BE_UNUSED static PyObject *ITERATOR_NEXT( PyObject *iterator )
{
    CHECK_OBJECT( iterator );

    iternextfunc iternext = Py_TYPE( iterator )->tp_iternext;

    if (unlikely( iternext == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
#if PYTHON_VERSION < 330
            "%s object is not an iterator",
#else
            "'%s' object is not an iterator",
#endif
            Py_TYPE( iterator )->tp_name
        );

        return NULL;
    }

    PyObject *result = (*iternext)( iterator );

#if PYTHON_VERSION < 330
    if ( result == NULL )
    {
        PyObject *error = GET_ERROR_OCCURRED();
        if ( error )
        {
            if (likely( EXCEPTION_MATCH_BOOL_SINGLE( error, PyExc_StopIteration ) ))
            {
                CLEAR_ERROR_OCCURRED();
            }
        }
    }
#endif

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_NEXT1( PyObject *iterator )
{
    CHECK_OBJECT( iterator );

    iternextfunc iternext = Py_TYPE( iterator )->tp_iternext;

    if (unlikely( iternext == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
#if PYTHON_VERSION < 330
            "%s object is not an iterator",
#else
            "'%s' object is not an iterator",
#endif
            Py_TYPE( iterator )->tp_name
        );

        return NULL;
    }

    PyObject *result = (*iternext)( iterator );

    if (unlikely( result == NULL ))
    {
        // The iteration can return NULL with no error, which means
        // StopIteration.
        if ( !ERROR_OCCURRED() )
        {
            PyErr_SetNone( PyExc_StopIteration );
        }

        return NULL;
    }
    else
    {
        CHECK_OBJECT( result );
    }

    return result;
}


NUITKA_MAY_BE_UNUSED static PyObject *BUILTIN_NEXT2( PyObject *iterator, PyObject *default_value )
{
    CHECK_OBJECT( iterator );
    CHECK_OBJECT( default_value );

    PyObject *result = (*Py_TYPE( iterator )->tp_iternext)( iterator );

    if (unlikely( result == NULL ))
    {
        PyObject *error = GET_ERROR_OCCURRED();

        if ( error != NULL )
        {
            if ( EXCEPTION_MATCH_BOOL_SINGLE( error, PyExc_StopIteration ))
            {
                DROP_ERROR_OCCURRED();

                return INCREASE_REFCOUNT( default_value );
            }
            else
            {
                return NULL;
            }
        }
        else
        {
            return INCREASE_REFCOUNT( default_value );
        }
    }
    else
    {
        CHECK_OBJECT( result );
    }

    return result;
}

#if PYTHON_VERSION < 350
NUITKA_MAY_BE_UNUSED static PyObject *UNPACK_NEXT( PyObject *iterator, int seq_size_so_far )
#else
NUITKA_MAY_BE_UNUSED static PyObject *UNPACK_NEXT( PyObject *iterator, int seq_size_so_far, int expected )
#endif
{
    CHECK_OBJECT( iterator );
    assert( HAS_ITERNEXT( iterator ) );

    PyObject *result = (*Py_TYPE( iterator )->tp_iternext)( iterator );

    if (unlikely( result == NULL ))
    {
#if PYTHON_VERSION < 300
        if (unlikely( !ERROR_OCCURRED() ))
#else
        if (unlikely( !ERROR_OCCURRED() || EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_StopIteration ) ))
#endif
        {
#if PYTHON_VERSION < 350
            if ( seq_size_so_far == 1 )
            {
                PyErr_Format( PyExc_ValueError, "need more than 1 value to unpack" );
            }
            else
            {
                PyErr_Format( PyExc_ValueError, "need more than %d values to unpack", seq_size_so_far );
            }
#else
            PyErr_Format( PyExc_ValueError, "not enough values to unpack (expected %d, got %d)", expected, seq_size_so_far );
#endif
        }

        return NULL;
    }

    CHECK_OBJECT( result );

    return result;
}


NUITKA_MAY_BE_UNUSED static bool UNPACK_ITERATOR_CHECK( PyObject *iterator )
{
    CHECK_OBJECT( iterator );
    assert( HAS_ITERNEXT( iterator ) );

    PyObject *attempt = (*Py_TYPE( iterator )->tp_iternext)( iterator );

    if (likely( attempt == NULL ))
    {
        return CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED();
    }
    else
    {
        Py_DECREF( attempt );

        PyErr_Format( PyExc_ValueError, "too many values to unpack" );
        return false;
    }
}

#endif

