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
#ifndef __NUITKA_CALLING_H__
#define __NUITKA_CALLING_H__

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION( PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    assertObject( function_object );
    assertObject( function_object );
    assertObject( positional_args );
    assert( named_args == NULL || named_args->ob_refcnt > 0 );

    int line = _current_line;
    PyObject *result = PyObject_Call( function_object, positional_args, named_args );
    _current_line = line;

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

static char const *GET_CALLABLE_DESC( PyObject *object )
{
    if ( Nuitka_Function_Check( object ) || Nuitka_Generator_Check( object ) || PyMethod_Check( object ) || PyFunction_Check( object ) || PyCFunction_Check( object ) )
    {
        return "()";
    }
#if PY_MAJOR_VERSION < 3
    else if ( PyClass_Check( object ) )
    {
        return " constructor";
    }
    else if ( PyInstance_Check( object ))
    {
        return " instance";
    }
#endif
    else
    {
        return " object";
    }
}

extern PyObject *_python_dict_empty;

static inline bool COULD_CONTAIN_NON_STRINGS( PyObject *dict )
{
    return ( ((PyDictObject *)( dict ))->ma_lookup != ((PyDictObject *)_python_dict_empty)->ma_lookup );
}

static inline void CHECK_NON_STRINGS_DICT_ARG( PyObject *dict, PyObject *function_object )
{
    // Check if the dictionary has only string keys. The condition of the if statement works very
    // well for that already, because the ma_lookup will change only when a non-string was ever
    // added. It could have been removed. This makes this check very fast in the common case.
    if (unlikely( COULD_CONTAIN_NON_STRINGS( dict ) ))
    {
        PyObject *key, *value;
        Py_ssize_t pos = 0;

        while ( PyDict_Next( dict, &pos, &key, &value ) )
        {
#if PY_MAJOR_VERSION < 3
            if (unlikely( PyString_Check( key ) == 0 && PyUnicode_Check( key ) == 0 ))
#else
                if (unlikely( PyUnicode_Check( key ) == 0 ))
#endif
                {
                    PyErr_Format( PyExc_TypeError, "%s%s keywords must be strings", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ) );
                    throw _PythonException();
                }
        }
    }

}

static PyObject *CALL_FUNCTION_STAR_DICT( PyObject *dict_star_arg, PyObject *positional_args, PyObject *function_object )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), dict_star_arg->ob_type->tp_name );
        throw _PythonException();
    }

    if (likely( PyDict_Check( dict_star_arg ) ))
    {
        CHECK_NON_STRINGS_DICT_ARG( dict_star_arg, function_object );

        return CALL_FUNCTION( dict_star_arg, positional_args, function_object );
    }

    PyObjectTemporary merged_dict( PyDict_New() );

    int status = PyDict_Merge( merged_dict.asObject(), dict_star_arg, 1 );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    CHECK_NON_STRINGS_DICT_ARG( merged_dict.asObject(), function_object );

    return CALL_FUNCTION( merged_dict.asObject(), positional_args, function_object );
}


NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_DICT( PyObject *dict_star_arg, PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), dict_star_arg->ob_type->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_Copy( named_args ) );

    int status = PyDict_Merge( result.asObject(), dict_star_arg, 1 );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    if (unlikely( PyMapping_Size( dict_star_arg ) + PyDict_Size( named_args ) != PyDict_Size( result.asObject() )))
    {
        PyObject *key, *value;
        Py_ssize_t pos = 0;

        while ( PyDict_Next( named_args, &pos, &key, &value ) )
        {
            if ( PyMapping_HasKey( dict_star_arg, key ))
            {
                PyErr_Format( PyExc_TypeError, "%s%s got multiple values for keyword argument '%s'", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Nuitka_String_AsString( key ) );
                throw _PythonException();
            }
        }

        PyErr_Format( PyExc_RuntimeError, "%s%s got multiple values for keyword argument", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ) );
        throw _PythonException();
    }

    CHECK_NON_STRINGS_DICT_ARG( result.asObject(), function_object );

    return CALL_FUNCTION( result.asObject(), positional_args, function_object );
}

static PyObject *MERGE_STAR_LIST_ARGS( PyObject *list_star_arg, PyObject *positional_args, PyObject *function_object )
{
    PyObject *list_star_arg_tuple;

    if ( PyTuple_Check( list_star_arg ) == 0 )
    {
        list_star_arg_tuple = PySequence_Tuple( list_star_arg );

        if (unlikely( list_star_arg_tuple == NULL ))
        {
            if ( PyErr_ExceptionMatches( PyExc_TypeError ) )
            {
                PyErr_Format( PyExc_TypeError, "%s%s argument after * must be a sequence, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), list_star_arg->ob_type->tp_name );
            }

            throw _PythonException();
        }
    }
    else
    {
        list_star_arg_tuple = list_star_arg;
    }

    PyObject *result;

    int positional_args_size = PyTuple_Size( positional_args );

    if ( positional_args_size > 0 )
    {
        // TODO: This is actually only a TUPLE_CONCAT from here on, should be reused once
        // we do that.

        int list_star_arg_size = PyTuple_Size( list_star_arg_tuple );

        result = PyTuple_New( positional_args_size + list_star_arg_size );

        for ( int i = 0; i < positional_args_size; i++ )
        {
            PyTuple_SET_ITEM( result, i, INCREASE_REFCOUNT( PyTuple_GET_ITEM( positional_args, i ) ) );
        }

        for ( int i = 0; i < list_star_arg_size; i++ )
        {
            PyTuple_SET_ITEM( result, positional_args_size + i, INCREASE_REFCOUNT( PyTuple_GET_ITEM( list_star_arg_tuple, i ) ) );
        }

        if ( list_star_arg_tuple != list_star_arg )
        {
            Py_DECREF( list_star_arg_tuple );
        }
    }
    else
    {
        if ( list_star_arg_tuple == list_star_arg )
        {
            Py_INCREF( list_star_arg_tuple );
        }

        result = list_star_arg_tuple;
    }

    return result;
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_LIST( PyObject *list_star_arg, PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    return CALL_FUNCTION( named_args, PyObjectTemporary( MERGE_STAR_LIST_ARGS( list_star_arg, positional_args, function_object ) ).asObject(), function_object );
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_BOTH( PyObject *dict_star_arg, PyObject *list_star_arg, PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    return CALL_FUNCTION_STAR_DICT( dict_star_arg, named_args, PyObjectTemporary( MERGE_STAR_LIST_ARGS( list_star_arg, positional_args, function_object ) ).asObject(), function_object );
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_BOTH( PyObject *dict_star_arg, PyObject *list_star_arg, PyObject *positional_args, PyObject *function_object )
{
    return CALL_FUNCTION_STAR_DICT( dict_star_arg, PyObjectTemporary( MERGE_STAR_LIST_ARGS( list_star_arg, positional_args, function_object ) ).asObject(), function_object );
}

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_STAR_ONLY( PyObject *dict_star_arg, PyObject *list_star_arg, PyObject *function_object )
{
    if (unlikely( PyTuple_Check( list_star_arg ) == 0 ))
    {
        PyObject *list_star_arg_tuple = PySequence_Tuple( list_star_arg );

        if (unlikely( list_star_arg_tuple == NULL ))
        {
            if ( PyErr_ExceptionMatches( PyExc_TypeError ) )
            {
                PyErr_Format( PyExc_TypeError, "%s%s argument after * must be a sequence, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), list_star_arg->ob_type->tp_name );
            }

            throw _PythonException();
        }

        return CALL_FUNCTION_STAR_DICT( dict_star_arg, PyObjectTemporary( list_star_arg_tuple ).asObject(), function_object );
    }
    else
    {
        return CALL_FUNCTION_STAR_DICT( dict_star_arg, list_star_arg, function_object );
    }

}


#endif
