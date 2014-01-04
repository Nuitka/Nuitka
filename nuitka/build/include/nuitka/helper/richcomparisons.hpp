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
#ifndef __NUITKA_HELPER_RICHCOMPARISONS_H__
#define __NUITKA_HELPER_RICHCOMPARISONS_H__

static inline bool IS_SANE_TYPE( PyTypeObject *type )
{
    return
#if PYTHON_VERSION < 300
        type == &PyString_Type ||
        type == &PyInt_Type ||
#endif
        type == &PyLong_Type ||
        type == &PyList_Type ||
        type == &PyTuple_Type;
}

extern PyObject *MY_RICHCOMPARE( PyObject *v, PyObject *w, int op );
extern PyObject *MY_RICHCOMPARE_NORECURSE( PyObject *v, PyObject *w, int op );

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_LT( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = MY_RICHCOMPARE( operand1, operand2, Py_LT );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_LE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }

    PyObject *result = MY_RICHCOMPARE( operand1, operand2, Py_LE );

    if (unlikely( result == NULL ))
    {
        return NULL;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_EQ( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }

    return MY_RICHCOMPARE( operand1, operand2, Py_EQ );
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_EQ_NORECURSE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }

    return MY_RICHCOMPARE_NORECURSE( operand1, operand2, Py_EQ );
}



NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_NE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return INCREASE_REFCOUNT( Py_False );
    }

    return MY_RICHCOMPARE( operand1, operand2, Py_NE );
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_GT( PyObject *operand1, PyObject *operand2 )
{
    return MY_RICHCOMPARE( operand1, operand2, Py_GT );
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_GE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return INCREASE_REFCOUNT( Py_True );
    }

    return MY_RICHCOMPARE( operand1, operand2, Py_GE );
}

NUITKA_MAY_BE_UNUSED static int RICH_COMPARE_BOOL_LT( PyObject *operand1, PyObject *operand2 )
{
    PyObject *rich_result = MY_RICHCOMPARE( operand1, operand2, Py_LT );

    if (unlikely( rich_result == NULL ))
    {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = 1;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = 0;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

NUITKA_MAY_BE_UNUSED static int RICH_COMPARE_BOOL_LE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return 1;
    }

    PyObject *rich_result = MY_RICHCOMPARE( operand1, operand2, Py_LE );

    if (unlikely( rich_result == NULL ))
    {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = 1;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = 0;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

NUITKA_MAY_BE_UNUSED static int RICH_COMPARE_BOOL_EQ( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return 1;
    }

    PyObject *rich_result = MY_RICHCOMPARE( operand1, operand2, Py_EQ );

    if (unlikely( rich_result == NULL ))
    {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = 1;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = 0;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

NUITKA_MAY_BE_UNUSED static int RICH_COMPARE_BOOL_EQ_NORECURSE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return 1;
    }

    PyObject *rich_result = MY_RICHCOMPARE_NORECURSE( operand1, operand2, Py_EQ );

    if (unlikely( rich_result == NULL ))
    {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = 1;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = 0;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}


NUITKA_MAY_BE_UNUSED static int RICH_COMPARE_BOOL_NE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return 0;
    }

    PyObject *rich_result = MY_RICHCOMPARE( operand1, operand2, Py_NE );

    if (unlikely( rich_result == NULL ))
    {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = 1;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = 0;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

NUITKA_MAY_BE_UNUSED static int RICH_COMPARE_BOOL_GT( PyObject *operand1, PyObject *operand2 )
{
    PyObject *rich_result = MY_RICHCOMPARE( operand1, operand2, Py_GT );

    if (unlikely( rich_result == NULL ))
    {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = 1;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = 0;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

NUITKA_MAY_BE_UNUSED static int RICH_COMPARE_BOOL_GE( PyObject *operand1, PyObject *operand2 )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 && IS_SANE_TYPE( Py_TYPE( operand1 ) ) )
    {
        return 1;
    }

    PyObject *rich_result = MY_RICHCOMPARE( operand1, operand2, Py_GE );

    if (unlikely( rich_result == NULL ))
    {
        return -1;
    }

    int result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = 1;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = 0;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

#endif
