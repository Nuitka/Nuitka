//     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
#ifndef __NUITKA_CALLING_H__
#define __NUITKA_CALLING_H__

#include "__helpers.hpp"

// Note: We do the reversal for function call arguments completely ourselves and here, so
// we don't have to do it in generated code. For each CALL_FUNCTION variant there is a
// define that includes a use of EVAL_ORDERED_x and a _CALL_FUNCTION implementation that
// does the actual work.

// Some helpers for common code.

extern PyObject *_python_tuple_empty;

static char const *GET_CALLABLE_DESC( PyObject *object )
{
    if ( Nuitka_Function_Check( object ) || Nuitka_Generator_Check( object ) || PyMethod_Check( object ) || PyFunction_Check( object ) || PyCFunction_Check( object ) )
    {
        return "()";
    }
#if PYTHON_VERSION < 300
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
#if PYTHON_VERSION < 300
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

static PyObject *STAR_LIST_ARG_AS_TUPLE( PyObject *function_object, PyObject *list_star_arg )
{
    PyObject *list_star_arg_tuple;

    if ( PyTuple_Check( list_star_arg ) == 0 )
    {
        list_star_arg_tuple = PySequence_Tuple( list_star_arg );

        if (unlikely( list_star_arg_tuple == NULL ))
        {
            if ( PyErr_ExceptionMatches( PyExc_TypeError ) )
            {
                PyErr_Format( PyExc_TypeError, "%s%s argument after * must be a sequence, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( list_star_arg )->tp_name );
            }

            throw _PythonException();
        }
    }
    else
    {
        list_star_arg_tuple = list_star_arg;
    }

    return list_star_arg_tuple;
}

static PyObject *MERGE_STAR_LIST_ARGS( PyObject *list_star_arg, PyObject *positional_args, PyObject *function_object )
{
    PyObject *list_star_arg_tuple = STAR_LIST_ARG_AS_TUPLE( function_object, list_star_arg );

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

static void MERGE_STAR_DICT_ARGS( PyObject *function_object, PyObject *named_args, PyObject *dict_star_arg, PyObject *result  )
{
    int status = PyDict_Merge( result, dict_star_arg, 1 );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    if (unlikely( PyMapping_Size( dict_star_arg ) + PyDict_Size( named_args ) != PyDict_Size( result ) ))
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

    CHECK_NON_STRINGS_DICT_ARG( result, function_object );
}

// The real CALL_FUNCTION variants:

#define CALL_FUNCTION( function_object, positional_args, named_args ) _CALL_FUNCTION( EVAL_ORDERED_3( function_object, positional_args, named_args ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION( EVAL_ORDERED_3( PyObject *function_object, PyObject *positional_args, PyObject *named_args ) )
{
    assertObject( function_object );
    assertObject( positional_args );
    assert( named_args == NULL || Py_REFCNT( named_args ) > 0 );

    ternaryfunc call_slot = function_object->ob_type->tp_call;

    if (unlikely( call_slot == NULL ))
    {
        PyErr_Format(
            PyExc_TypeError,
            "'%s' object is not callable",
            function_object->ob_type->tp_name
        );

        throw _PythonException();
    }

    if (unlikely( Py_EnterRecursiveCall( (char *)" while calling a Python object") ))
    {
        throw _PythonException();
    }

    PyObject *result = (*call_slot)( function_object, positional_args, named_args );

    Py_LeaveRecursiveCall();

    if ( result == NULL )
    {
        if (unlikely( !ERROR_OCCURED() ))
        {
            PyErr_Format(
                PyExc_SystemError,
                "NULL result without error in PyObject_Call"
            );
        }

        throw _PythonException();
    }
    else
    {
        return result;
    }
}

// Function call variant with no arguments provided at all.

NUITKA_MAY_BE_UNUSED static PyObject *CALL_FUNCTION_NO_ARGS( PyObject *function_object )
{
    return CALL_FUNCTION(
        function_object,
        _python_tuple_empty,
        NULL
    );
}

#define CALL_FUNCTION_WITH_POSARGS( function_object, positional_args ) _CALL_FUNCTION_WITH_POSARGS( EVAL_ORDERED_2( function_object, positional_args ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_POSARGS( EVAL_ORDERED_2( PyObject *function_object, PyObject *positional_args ) )
{
    return CALL_FUNCTION(
        function_object,
        positional_args,
        NULL
    );
}

#define CALL_FUNCTION_WITH_KEYARGS( function_object, named_args ) _CALL_FUNCTION_WITH_KEYARGS( EVAL_ORDERED_2( function_object, named_args ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_KEYARGS( EVAL_ORDERED_2( PyObject *function_object, PyObject *named_args ) )
{
    return CALL_FUNCTION(
        function_object,
        _python_tuple_empty,
        named_args
    );
}

#define CALL_FUNCTION_WITH_STAR_DICT( function_object, dict_star_arg ) _CALL_FUNCTION_WITH_STAR_DICT( EVAL_ORDERED_2( function_object, dict_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_STAR_DICT( EVAL_ORDERED_2( PyObject *function_object, PyObject *dict_star_arg ) )
{
    // Check for mapping.
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    // Check for non-strings in keys.
    CHECK_NON_STRINGS_DICT_ARG( dict_star_arg, function_object );

    return CALL_FUNCTION_WITH_KEYARGS(
        function_object,
        dict_star_arg
    );
}

#define CALL_FUNCTION_WITH_POSARGS_STAR_DICT( function_object, positional_args, dict_star_arg ) _CALL_FUNCTION_WITH_POSARGS_STAR_DICT( EVAL_ORDERED_3( function_object, positional_args, dict_star_arg ) )

static PyObject *_CALL_FUNCTION_WITH_POSARGS_STAR_DICT( EVAL_ORDERED_3( PyObject *function_object, PyObject *positional_args, PyObject *dict_star_arg ) )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    if (likely( PyDict_Check( dict_star_arg ) ))
    {
        CHECK_NON_STRINGS_DICT_ARG( dict_star_arg, function_object );

        return CALL_FUNCTION(
            function_object,
            positional_args,
            dict_star_arg
        );
    }

    PyObjectTemporary merged_dict( PyDict_New() );

    int status = PyDict_Merge( merged_dict.asObject(), dict_star_arg, 1 );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    CHECK_NON_STRINGS_DICT_ARG( merged_dict.asObject(), function_object );

    return CALL_FUNCTION(
        function_object,
        positional_args,
        merged_dict.asObject()
    );
}

#define CALL_FUNCTION_WITH_KEYARGS_STAR_DICT( function_object, named_args, dict_star_arg ) _CALL_FUNCTION_WITH_KEYARGS_STAR_DICT( EVAL_ORDERED_3( function_object, named_args, dict_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_KEYARGS_STAR_DICT( EVAL_ORDERED_3( PyObject *function_object, PyObject *named_args, PyObject *dict_star_arg ) )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_Copy( named_args ) );

    MERGE_STAR_DICT_ARGS(
        function_object,
        named_args,
        dict_star_arg,
        result.asObject()
    );

    return CALL_FUNCTION_WITH_KEYARGS(
        function_object,
        result.asObject()
    );
}

#define CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_DICT( function_object, positional_args, named_args, dict_star_arg ) _CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_DICT( EVAL_ORDERED_4( function_object, positional_args, named_args, dict_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_DICT( EVAL_ORDERED_4( PyObject *function_object, PyObject *positional_args, PyObject *named_args, PyObject *dict_star_arg ) )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_Copy( named_args ) );

    MERGE_STAR_DICT_ARGS(
        function_object,
        named_args,
        dict_star_arg,
        result.asObject()
    );

    return CALL_FUNCTION(
        function_object,
        positional_args,
        result.asObject()
    );
}


#define CALL_FUNCTION_WITH_KEYARGS_STAR_LIST_STAR_DICT( function_object, named_args, list_star_arg, dict_star_arg ) _CALL_FUNCTION_WITH_KEYARGS_STAR_LIST_STAR_DICT( EVAL_ORDERED_4( function_object, named_args, list_star_arg, dict_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_KEYARGS_STAR_LIST_STAR_DICT( EVAL_ORDERED_4( PyObject *function_object, PyObject *named_args, PyObject *list_star_arg, PyObject *dict_star_arg ) )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_Copy( named_args ) );

    MERGE_STAR_DICT_ARGS(
        function_object,
        named_args,
        dict_star_arg,
        result.asObject()
    );


    // The list star arg could just as well have been an argument tuple, so
    // this can is easy.
    PyObject *list_star_arg_tuple = STAR_LIST_ARG_AS_TUPLE( function_object, list_star_arg );

    if ( list_star_arg_tuple == list_star_arg )
    {
        return CALL_FUNCTION(
            function_object,
            list_star_arg_tuple,
            result.asObject()
        );
    }
    else
    {
        return CALL_FUNCTION(
            function_object,
            PyObjectTemporary( list_star_arg_tuple ).asObject(),
            result.asObject()
        );
    }
}

#define CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST( function_object, positional_args, named_args, list_star_arg ) _CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST( EVAL_ORDERED_4( function_object, positional_args, named_args, list_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST( EVAL_ORDERED_4( PyObject *function_object, PyObject *positional_args, PyObject *named_args, PyObject *list_star_arg ) )
{
    return CALL_FUNCTION(
        function_object,
        PyObjectTemporary( MERGE_STAR_LIST_ARGS( list_star_arg, positional_args, function_object ) ).asObject(),
        named_args
    );
}

#define CALL_FUNCTION_WITH_POSARGS_STAR_LIST( function_object, positional_args, list_star_arg ) _CALL_FUNCTION_WITH_POSARGS_STAR_LIST( EVAL_ORDERED_3( function_object, positional_args, list_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_POSARGS_STAR_LIST( EVAL_ORDERED_3( PyObject *function_object, PyObject *positional_args, PyObject *list_star_arg ) )
{
    return CALL_FUNCTION_WITH_POSARGS(
        function_object,
        PyObjectTemporary( MERGE_STAR_LIST_ARGS( list_star_arg, positional_args, function_object ) ).asObject()
    );
}

#define CALL_FUNCTION_WITH_KEYARGS_STAR_LIST( function_object, named_args, list_star_arg ) _CALL_FUNCTION_WITH_KEYARGS_STAR_LIST( EVAL_ORDERED_3( function_object, named_args, list_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_KEYARGS_STAR_LIST( EVAL_ORDERED_3( PyObject *function_object, PyObject *named_args, PyObject *list_star_arg ) )
{
    // The list star arg could just as well have been an argument tuple, so
    // this can is easy.
    PyObject *list_star_arg_tuple = STAR_LIST_ARG_AS_TUPLE( function_object, list_star_arg );

    if ( list_star_arg_tuple == list_star_arg )
    {
        return CALL_FUNCTION(
            function_object,
            list_star_arg_tuple,
            named_args
        );
    }
    else
    {
        return CALL_FUNCTION(
            function_object,
            PyObjectTemporary( list_star_arg_tuple ).asObject(),
            named_args
        );
    }
}

#define CALL_FUNCTION_WITH_POSARGS_STAR_LIST_STAR_DICT( function_object, positional_args, list_star_arg, dict_star_arg ) _CALL_FUNCTION_WITH_POSARGS_STAR_LIST_STAR_DICT( EVAL_ORDERED_4( function_object, positional_args, list_star_arg, dict_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_POSARGS_STAR_LIST_STAR_DICT( EVAL_ORDERED_4( PyObject *function_object, PyObject *positional_args, PyObject *list_star_arg, PyObject *dict_star_arg ) )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_New() );

    MERGE_STAR_DICT_ARGS(
        function_object,
        _python_dict_empty,
        dict_star_arg,
        result.asObject()
    );

    return CALL_FUNCTION_WITH_POSARGS_STAR_DICT(
        function_object,
        PyObjectTemporary(
            MERGE_STAR_LIST_ARGS(
                list_star_arg,
                positional_args,
                function_object
            )
        ).asObject(),
        dict_star_arg
     );
}

#define CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST_STAR_DICT( function_object, positional_args, named_args, list_star_arg, dict_star_arg ) _CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST_STAR_DICT( EVAL_ORDERED_5( function_object, positional_args, named_args, list_star_arg, dict_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_POSARGS_KEYARGS_STAR_LIST_STAR_DICT( EVAL_ORDERED_5( PyObject *function_object, PyObject *positional_args, PyObject *named_args, PyObject *list_star_arg, PyObject *dict_star_arg ) )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_Copy( named_args ) );

    MERGE_STAR_DICT_ARGS(
        function_object,
        named_args,
        dict_star_arg,
        result.asObject()
    );

    return CALL_FUNCTION(
        function_object,
        PyObjectTemporary(
            MERGE_STAR_LIST_ARGS(
                list_star_arg,
                positional_args,
                function_object
            )
        ).asObject(),
        result.asObject()
     );
}

#define CALL_FUNCTION_WITH_STAR_LIST_STAR_DICT( function_object, list_star_arg, dict_star_arg ) _CALL_FUNCTION_WITH_STAR_LIST_STAR_DICT( EVAL_ORDERED_3( function_object, list_star_arg, dict_star_arg ) )

NUITKA_MAY_BE_UNUSED static PyObject *_CALL_FUNCTION_WITH_STAR_LIST_STAR_DICT( EVAL_ORDERED_3( PyObject *function_object, PyObject *list_star_arg, PyObject *dict_star_arg ) )
{
    if (unlikely( PyMapping_Check( dict_star_arg ) == 0 ))
    {
        PyErr_Format( PyExc_TypeError, "%s%s argument after ** must be a mapping, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( dict_star_arg )->tp_name );
        throw _PythonException();
    }

    PyObjectTemporary result( PyDict_New() );

    MERGE_STAR_DICT_ARGS(
        function_object,
        _python_dict_empty,
        dict_star_arg,
        result.asObject()
    );

    if (unlikely( PyTuple_Check( list_star_arg ) == 0 ))
    {
        PyObject *list_star_arg_tuple = PySequence_Tuple( list_star_arg );

        if (unlikely( list_star_arg_tuple == NULL ))
        {
            if ( PyErr_ExceptionMatches( PyExc_TypeError ) )
            {
                PyErr_Format( PyExc_TypeError, "%s%s argument after * must be a sequence, not %s", GET_CALLABLE_NAME( function_object ), GET_CALLABLE_DESC( function_object ), Py_TYPE( list_star_arg )->tp_name );
            }

            throw _PythonException();
        }

        return CALL_FUNCTION(
            function_object,
            PyObjectTemporary( list_star_arg_tuple ).asObject(),
            result.asObject()
        );
    }
    else
    {
        return CALL_FUNCTION(
            function_object,
            list_star_arg,
            result.asObject()
        );
    }
}

#endif
