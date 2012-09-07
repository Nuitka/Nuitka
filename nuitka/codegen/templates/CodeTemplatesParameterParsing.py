#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Parameter parsing related templates.

"""

template_parameter_function_entry_point = """\
static PyObject *%(parse_function_identifier)s( Nuitka_FunctionObject *self, PyObject *args, PyObject *kw )
{
%(context_access)s
    Py_ssize_t args_size = PyTuple_GET_SIZE( args );
    NUITKA_MAY_BE_UNUSED Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;
    NUITKA_MAY_BE_UNUSED Py_ssize_t kw_found = 0;
    Py_ssize_t args_given = args_size;
%(parameter_parsing_code)s

    return %(impl_function_identifier)s( %(parameter_objects_list)s );

error_exit:;

%(parameter_release_code)s
    return NULL;
}
"""

template_parameter_method_entry_point = """\
static PyObject *%(parse_function_identifier)s( Nuitka_FunctionObject *self, PyObject *_python_par_self, PyObject *args, PyObject *kw )
{
    Py_INCREF( _python_par_self );
%(context_access)s
    Py_ssize_t args_size = PyTuple_GET_SIZE( args );
    NUITKA_MAY_BE_UNUSED Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;
    NUITKA_MAY_BE_UNUSED Py_ssize_t kw_found = 0;
    Py_ssize_t args_given = args_size + 1; // Count the self parameter already given as well.
%(parameter_parsing_code)s

    return %(impl_function_identifier)s( %(parameter_objects_list)s );

error_exit:;

%(parameter_release_code)s
    return NULL;
}
"""

parse_argument_template_take_counts3 = """\
int args_usable_count;
"""


template_parameter_function_refuses = r"""
if (unlikely( args_given + kw_size > 0 ))
{
    PyErr_Format( PyExc_TypeError, "%(function_name)s() takes no arguments (%%" PY_FORMAT_SIZE_T "d given)", args_given + kw_size );
    goto error_exit;
}
"""

parse_argument_template_check_counts_with_list_star_arg = r"""
// Check if too little arguments were given.

if (unlikely( args_given + kw_found < %(required_parameter_count)d ))
{
    if ( %(top_level_parameter_count)d == 1 )
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least 1 argument (%%" PY_FORMAT_SIZE_T "d given)", args_given + kw_found );
    }
    else
    {
#if PYTHON_VERSION < 270
        if ( kw_size > 0 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least %%d non-keyword arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_found );
        }
        else
#endif
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least %%d arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_found );
        }
    }

    goto error_exit;
}
"""

parse_argument_template_check_counts_without_list_star_arg = r"""
// Check if too many arguments were given in case of non star args
if (unlikely( args_given > %(top_level_parameter_count)d ))
{
    if ( %(top_level_parameter_count)d == 1 )
    {
#if PYTHON_VERSION < 300
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 argument (%%" PY_FORMAT_SIZE_T "d given)", args_given + kw_size );
#else
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 positional argument (%%" PY_FORMAT_SIZE_T "d given)", args_given );
#endif
    }
    else
    {
#if PYTHON_VERSION < 300
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_size );
#else
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d positional arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given );
#endif
    }

    goto error_exit;
}

// Check if too little arguments were given.
if (unlikely( args_given + kw_size < %(required_parameter_count)d ))
{
    if ( %(top_level_parameter_count)d == 1 )
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 argument (%%" PY_FORMAT_SIZE_T "d given)", args_given + kw_size );
    }
    else
    {
#if PYTHON_VERSION < 270
        if ( kw_size > 0 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d non-keyword arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_size );
        }
        else
#endif
        {
            if ( %(top_level_parameter_count)d == %(required_parameter_count)d )
            {
                PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%" PY_FORMAT_SIZE_T "d given)", %(required_parameter_count)d, args_given + kw_size );
            }
            else
            {
                PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least %%d arguments (%%" PY_FORMAT_SIZE_T "d given)", %(required_parameter_count)d, args_given + kw_size );
            }
        }
    }

    goto error_exit;
}
"""

parse_argument_usable_count = r"""
// Copy normal parameter values given as part of the args list to the respective variables:
args_usable_count = args_given < %(top_level_parameter_count)d ? args_given : %(top_level_parameter_count)d;

"""

argparse_template_plain_argument = """\
if (likely( %(parameter_position)d < args_usable_count ))
{
     if (unlikely( _python_par_%(parameter_name)s != NULL ))
     {
         PyErr_Format( PyExc_TypeError, "%(function_name)s() got multiple values for keyword argument '%(parameter_name)s'" );
         goto error_exit;
     }

    _python_par_%(parameter_name)s = INCREASE_REFCOUNT( PyTuple_GET_ITEM( args, %(parameter_args_index)d ) );
}
"""

argparse_template_nested_argument = """\
if (likely( %(parameter_position)d < args_usable_count ))
{
    _python_par_%(parameter_name)s = PyTuple_GET_ITEM( args, %(parameter_args_index)d );
}
"""

parse_argument_template_copy_list_star_args = """
// Copy left over argument values to the star list parameter given.
if ( args_given > %(top_level_parameter_count)d )
{
    _python_par_%(list_star_parameter_name)s = PyTuple_GetSlice( args, %(top_level_max_index)d, args_size );
}
else
{
    _python_par_%(list_star_parameter_name)s = INCREASE_REFCOUNT( _python_tuple_empty );
}
"""

parse_argument_template_dict_star_copy = """
if ( kw == NULL )
{
    _python_par_%(dict_star_parameter_name)s = PyDict_New();
}
else
{
    _python_par_%(dict_star_parameter_name)s = PyDict_Copy( kw );

    if (unlikely( _python_par_%(dict_star_parameter_name)s == NULL ))
    {
        PyErr_Clear();

        _python_par_%(dict_star_parameter_name)s = MAKE_DICT0();

        if (unlikely( PyDict_Update( _python_par_%(dict_star_parameter_name)s, kw ) != 0 ))
        {
            PyErr_Format( PyExc_TypeError, "after ** must be a mapping, not %%s", Py_TYPE( kw )->tp_name );

            goto error_exit;
        }
    }
}
"""

parse_argument_template_check_dict_parameter_with_star_dict = """
// Check if argument %(parameter_name)s was given as keyword argument
if ( kw_size > 0 )
{
    PyObject *kw_arg_value = PyDict_GetItem( _python_par_%(dict_star_parameter_name)s, %(parameter_name_object)s );

    if ( kw_arg_value != NULL )
    {
        assert( _python_par_%(parameter_name)s == NULL );

        _python_par_%(parameter_name)s = INCREASE_REFCOUNT( kw_arg_value );
        PyDict_DelItem( _python_par_%(dict_star_parameter_name)s, %(parameter_name_object)s );

        kw_found += 1;
    }
}
"""

parse_argument_template_check_dict_parameter_without_star_dict = """
// Check if argument %(parameter_name)s was given as keyword argument
if ( kw_size > 0 )
{
    PyObject *kw_arg_value = PyDict_GetItem( kw, %(parameter_name_object)s );

    if ( kw_arg_value != NULL )
    {
        assert( _python_par_%(parameter_name)s == NULL );

        _python_par_%(parameter_name)s = INCREASE_REFCOUNT( kw_arg_value );
    }
}
"""

argparse_template_assign_from_dict_parameters = """\
if ( kw_size > 0 )
{
    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while( PyDict_Next( kw, &ppos, &key, &value ) )
    {
#if PYTHON_VERSION < 300
        if (unlikely( !PyString_Check( key ) && !PyUnicode_Check( key ) ))
#else
        if (unlikely( !PyUnicode_Check( key ) ))
#endif
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() keywords must be strings" );
            goto error_exit;
        }

        NUITKA_MAY_BE_UNUSED bool found = false;

        Py_INCREF( key );
        Py_INCREF( value );

        // Quick path, could be our value.
%(parameter_quick_path)s
        // Slow path, compare against all parameter names.
%(parameter_slow_path)s

        Py_DECREF( key );

        if ( found == false )
        {
           Py_DECREF( value );

           PyErr_Format(
               PyExc_TypeError,
               "%(function_name)s() got an unexpected keyword argument '%%s'",
#if PYTHON_VERSION < 300
               PyString_Check( key ) ?
#else
               PyUnicode_Check( key ) ?
#endif
                   Nuitka_String_AsString( key ) : "<non-string>"
           );

           goto error_exit;
        }
    }
}
"""

argparse_template_assign_from_dict_parameter_quick_path = """\
if ( found == false && %(parameter_name_object)s == key )
{
%(parameter_assign_from_kw)s
    found = true;
}
"""

argparse_template_assign_from_dict_parameter_slow_path = """\
if ( found == false && RICH_COMPARE_BOOL_EQ_PARAMETERS( %(parameter_name_object)s, key ) )
{
%(parameter_assign_from_kw)s
    found = true;
}
"""

argparse_template_assign_from_dict_finding = """\
if (unlikely( _python_par_%(parameter_name)s ))
{
    PyErr_Format( PyExc_TypeError, "%(function_name)s() got multiple values for keyword argument '%(parameter_name)s'" );
    goto error_exit;
}

_python_par_%(parameter_name)s = value;
"""

parse_argument_template_copy_default_value = """\
if ( _python_par_%(parameter_name)s == NULL )
{
    _python_par_%(parameter_name)s = %(default_identifier)s;
}
"""

parse_argument_template_nested_argument_unpack = """\
// Unpack from _python_par_%(parameter_name)s
{
    PyObject *_python_iter_%(parameter_name)s = PyObject_GetIter( %(unpack_source_identifier)s );

    if (unlikely( _python_iter_%(parameter_name)s == NULL ))
    {
        goto error_exit;
    }
%(unpack_code)s
    // Check that the unpack was complete.
    if (unlikely( UNPACK_PARAMETER_ITERATOR_CHECK( _python_iter_%(parameter_name)s ) == false ))
    {
       Py_DECREF( _python_iter_%(parameter_name)s );
       goto error_exit;
    }
    Py_DECREF( _python_iter_%(parameter_name)s );
}"""

parse_argument_template_nested_argument_assign = """
    // Unpack to _python_par_%(parameter_name)s
    _python_par_%(parameter_name)s = UNPACK_PARAMETER_NEXT( _python_iter_%(iter_name)s, %(unpack_count)d );

    if (unlikely (_python_par_%(parameter_name)s == NULL ))
    {
        Py_DECREF( _python_iter_%(iter_name)s );
        goto error_exit;
    }
"""
