//
//     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
//     This is to reserve my ability to re-license the code at a later time to
//     the PSF. With this version of Nuitka, using it for a Closed Source and
//     distributing the binary only is not allowed.
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
#ifndef __NUITKA_HELPER_RICHCOMPARISONS_H__
#define __NUITKA_HELPER_RICHCOMPARISONS_H__

#define RICH_COMPARE_LT( operand1, operand2 ) _RICH_COMPARE_LT( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static PyObject *_RICH_COMPARE_LT( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_LT );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define RICH_COMPARE_LE( operand1, operand2 ) _RICH_COMPARE_LE( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static PyObject *_RICH_COMPARE_LE( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_LE );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define RICH_COMPARE_EQ( operand1, operand2 ) _RICH_COMPARE_EQ( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static PyObject *_RICH_COMPARE_EQ( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_EQ );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define RICH_COMPARE_NE( operand1, operand2 ) _RICH_COMPARE_NE( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static PyObject *_RICH_COMPARE_NE( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_NE );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define RICH_COMPARE_GT( operand1, operand2 ) _RICH_COMPARE_GT( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static PyObject *_RICH_COMPARE_GT( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_GT );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define RICH_COMPARE_GE( operand1, operand2 ) _RICH_COMPARE_GE( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static PyObject *_RICH_COMPARE_GE( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_GE );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

#define RICH_COMPARE_BOOL_LT( operand1, operand2 ) _RICH_COMPARE_BOOL_LT( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static bool _RICH_COMPARE_BOOL_LT( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_LT );

    if (unlikely( rich_result == NULL ))
    {
        throw _PythonException();
    }

    bool result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = true;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = false;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

#define RICH_COMPARE_BOOL_LE( operand1, operand2 ) _RICH_COMPARE_BOOL_LE( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static bool _RICH_COMPARE_BOOL_LE( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    // Quick path for avoidable checks.
    if ( operand1 == operand2 )
    {
        return true;
    }

    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_LE );

    if (unlikely( rich_result == NULL ))
    {
        throw _PythonException();
    }

    bool result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = true;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = false;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_EQ_PARAMETERS( PyObject *operand1, PyObject *operand2 )
{
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_EQ );

    // String comparisons cannot fail they say.
    assertObject( rich_result );

    bool result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = true;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = false;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

#define RICH_COMPARE_BOOL_EQ( operand1, operand2 ) _RICH_COMPARE_BOOL_EQ( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static bool _RICH_COMPARE_BOOL_EQ( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    // Quick path for avoidable checks, compatible with CPython.
    if ( operand1 == operand2 )
    {
        return true;
    }

    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_EQ );

    if (unlikely( rich_result == NULL ))
    {
        throw _PythonException();
    }

    bool result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = true;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = false;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

#define RICH_COMPARE_BOOL_NE( operand1, operand2 ) _RICH_COMPARE_BOOL_NE( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static bool _RICH_COMPARE_BOOL_NE( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    // Quick path for avoidable checks.
    if ( operand1 == operand2 )
    {
        return false;
    }

    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_NE );

    if (unlikely( rich_result == NULL ))
    {
        throw _PythonException();
    }

    bool result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = true;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = false;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

#define RICH_COMPARE_BOOL_GT( operand1, operand2 ) _RICH_COMPARE_BOOL_GT( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static bool _RICH_COMPARE_BOOL_GT( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_GT );

    if (unlikely( rich_result == NULL ))
    {
        throw _PythonException();
    }

    bool result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = true;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = false;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

#define RICH_COMPARE_BOOL_GE( operand1, operand2 ) _RICH_COMPARE_BOOL_GE( EVAL_ORDERED_2( operand1, operand2 ) )

NUITKA_MAY_BE_UNUSED static bool _RICH_COMPARE_BOOL_GE( EVAL_ORDERED_2( PyObject *operand1, PyObject *operand2 ) )
{
    // Quick path for avoidable checks.
    if ( operand1 == operand2 )
    {
        return true;
    }

    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_GE );

    if (unlikely( rich_result == NULL ))
    {
        throw _PythonException();
    }

    bool result;

    // Doing the quick tests on the outside spares the function call, with
    // "partial inline" this should become unneeded.
    if ( rich_result == Py_True )
    {
        result = true;
    }
    else if ( rich_result == Py_False || rich_result == Py_None )
    {
        result = false;
    }
    else
    {
        result = CHECK_IF_TRUE( rich_result );
    }

    Py_DECREF( rich_result );

    return result;
}

#endif
