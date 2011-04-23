//
//     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
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
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
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


NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_LT( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_LT );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_LE( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_LE );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_EQ( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_EQ );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_NE( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_NE );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_GT( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_GT );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}


NUITKA_MAY_BE_UNUSED static PyObject *RICH_COMPARE_GE( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, Py_GE );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_LT( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_LT );
    _current_line = line;

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

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_LE( PyObject *operand2, PyObject *operand1 )
{
    // Quick path for avoidable checks.
    if ( operand1 == operand2 )
    {
        return true;
    }

    int line = _current_line;
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_LE );
    _current_line = line;

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

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_EQ_PARAMETERS( PyObject *operand2, PyObject *operand1 )
{
    // TODO: Clarify if there is a point in preserving the current line just yet.
    int line = _current_line;
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_EQ );
    _current_line = line;

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

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_EQ( PyObject *operand2, PyObject *operand1 )
{
    // Quick path for avoidable checks.
    if ( operand1 == operand2 )
    {
        return true;
    }

    int line = _current_line;
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_EQ );
    _current_line = line;

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

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_NE( PyObject *operand2, PyObject *operand1 )
{
    // Quick path for avoidable checks.
    if ( operand1 == operand2 )
    {
        return false;
    }

    int line = _current_line;
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_NE );
    _current_line = line;

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

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_GT( PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_GT );
    _current_line = line;

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

NUITKA_MAY_BE_UNUSED static bool RICH_COMPARE_BOOL_GE( PyObject *operand2, PyObject *operand1 )
{
    // Quick path for avoidable checks.
    if ( operand1 == operand2 )
    {
        return true;
    }

    int line = _current_line;
    PyObject *rich_result = PyObject_RichCompare( operand1, operand2, Py_GE );
    _current_line = line;

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
