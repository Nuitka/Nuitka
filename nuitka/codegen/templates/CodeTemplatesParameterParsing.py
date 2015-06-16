#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
static PyObject *%(parse_function_identifier)s( Nuitka_FunctionObject *self, PyObject **args, Py_ssize_t args_size, PyObject *kw )
{
    assert( kw == NULL || PyDict_Check( kw ) );

    NUITKA_MAY_BE_UNUSED Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;
    NUITKA_MAY_BE_UNUSED Py_ssize_t kw_found = 0;
    NUITKA_MAY_BE_UNUSED Py_ssize_t kw_only_found = 0;
    Py_ssize_t args_given = args_size;
%(parameter_parsing_code)s

    return %(impl_function_identifier)s( %(parameter_objects_list)s );

error_exit:;

%(parameter_release_code)s
    return NULL;
}
"""

template_parameter_function_refuses = r"""
if (unlikely( args_given + kw_size > 0 ))
{
#if PYTHON_VERSION < 330
    ERROR_NO_ARGUMENTS_ALLOWED(
       self,
       args_given + kw_size
    );
#else
    ERROR_NO_ARGUMENTS_ALLOWED(
       self,
       kw_size > 0 ? kw : NULL,
       args_given
    );
#endif

    goto error_exit;
}
"""

parse_argument_template_check_counts_without_list_star_arg = r"""
// Check if too many arguments were given in case of non star args
if (unlikely( args_given > %(top_level_parameter_count)d ))
{
#if PYTHON_VERSION < 270
    ERROR_TOO_MANY_ARGUMENTS( self, args_given, kw_size );
#elif PYTHON_VERSION < 330
    ERROR_TOO_MANY_ARGUMENTS( self, args_given + kw_found );
#else
    ERROR_TOO_MANY_ARGUMENTS( self, args_given, kw_only_found );
#endif
    goto error_exit;
}

"""

parse_argument_usable_count = r"""
// Copy normal parameter values given as part of the argument list to the
// respective variables:

"""

argparse_template_plain_argument = """\
if (likely( %(parameter_position)d < args_given ))
{
     if (unlikely( _python_par_%(parameter_name)s != NULL ))
     {
         ERROR_MULTIPLE_VALUES( self, %(parameter_position)d );
         goto error_exit;
     }

    _python_par_%(parameter_name)s = args[ %(parameter_position)d ];
    Py_INCREF( _python_par_%(parameter_name)s );
}
else if ( _python_par_%(parameter_name)s == NULL )
{
    if ( %(parameter_position)d + self->m_defaults_given >= %(top_level_parameter_count)d  )
    {
        _python_par_%(parameter_name)s = PyTuple_GET_ITEM( self->m_defaults, self->m_defaults_given + %(parameter_position)d - %(top_level_parameter_count)d );
        Py_INCREF( _python_par_%(parameter_name)s );
    }
#if PYTHON_VERSION < 330
    else
    {
#if PYTHON_VERSION < 270
        ERROR_TOO_FEW_ARGUMENTS( self, kw_size, args_given + kw_found );
#elif PYTHON_VERSION < 300
        ERROR_TOO_FEW_ARGUMENTS( self, args_given + kw_found );
#else
        ERROR_TOO_FEW_ARGUMENTS( self, args_given + kw_found - kw_only_found );
#endif

        goto error_exit;
    }
#endif
}
"""

template_arguments_check = """
#if PYTHON_VERSION >= 330
if (unlikely( %(parameter_test)s ))
{
    PyObject *values[] = { %(parameter_list)s };
    ERROR_TOO_FEW_ARGUMENTS( self, values );

    goto error_exit;
}
#endif
"""

# TODO: Is there a missing INCREF in the first branch part. Other parts do
# have it, so this might be a reference loss here when taking from "args[]".
argparse_template_nested_argument = """\
if (likely( %(parameter_position)d < args_given ))
{
    _python_par_%(parameter_name)s = args[ %(parameter_position)d ];
}
else if ( _python_par_%(parameter_name)s == NULL )
{
    if ( %(parameter_position)d + self->m_defaults_given >= %(top_level_parameter_count)d  )
    {
        _python_par_%(parameter_name)s = PyTuple_GET_ITEM( self->m_defaults, self->m_defaults_given + %(parameter_position)d - %(top_level_parameter_count)d );
        Py_INCREF( _python_par_%(parameter_name)s );
    }
    else
    {
#if PYTHON_VERSION < 270
        ERROR_TOO_FEW_ARGUMENTS( self, kw_size, args_given + kw_found );
#else
        ERROR_TOO_FEW_ARGUMENTS( self, args_given + kw_found );
#endif

        goto error_exit;
    }
}
"""

parse_argument_template_copy_list_star_args = """
// Copy left-over argument values to the star list parameter given.
if ( args_given > %(top_level_parameter_count)d )
{
    _python_par_%(list_star_parameter_name)s = PyTuple_New( args_size - %(top_level_parameter_count)d );

    for( Py_ssize_t i = 0; i < args_size - %(top_level_parameter_count)d; i++ )
    {
        PyObject *value = args[%(top_level_parameter_count)d+i];
        PyTuple_SET_ITEM( _python_par_%(list_star_parameter_name)s, i, value );
        Py_INCREF( value );
    }
}
else
{
    _python_par_%(list_star_parameter_name)s = const_tuple_empty;
    Py_INCREF( const_tuple_empty );
}
"""

parse_argument_template_dict_star_copy = """
if ( kw == NULL )
{
    _python_par_%(dict_star_parameter_name)s = PyDict_New();
}
else
{
    if ( ((PyDictObject *)kw)->ma_used > 0 )
    {
#if PYTHON_VERSION < 330
        _python_par_%(dict_star_parameter_name)s = _PyDict_NewPresized( ((PyDictObject *)kw)->ma_used  );

        for ( int i = 0; i <= ((PyDictObject *)kw)->ma_mask; i++ )
        {
            PyDictEntry *entry = &((PyDictObject *)kw)->ma_table[ i ];

            if ( entry->me_value != NULL )
            {

#if PYTHON_VERSION < 300
                if (unlikely( !PyString_Check( entry->me_key ) && !PyUnicode_Check( entry->me_key ) ))
#else
                if (unlikely( !PyUnicode_Check( entry->me_key ) ))
#endif
                {
                    PyErr_Format( PyExc_TypeError, "%(function_name)s() keywords must be strings" );
                    goto error_exit;
                }

                int res = PyDict_SetItem( _python_par_%(dict_star_parameter_name)s, entry->me_key, entry->me_value );

                if (unlikely( res != 0 ))
                {
                    goto error_exit;
                }
            }
        }
#else
    if ( _PyDict_HasSplitTable( (PyDictObject *)kw) )
    {
        PyDictObject *mp = (PyDictObject *)kw;

        PyObject **newvalues = PyMem_NEW( PyObject *, mp->ma_keys->dk_size );
        assert( newvalues != NULL );

        PyDictObject *split_copy = PyObject_GC_New( PyDictObject, &PyDict_Type );
        assert( split_copy != NULL );

        split_copy->ma_values = newvalues;
        split_copy->ma_keys = mp->ma_keys;
        split_copy->ma_used = mp->ma_used;

        mp->ma_keys->dk_refcnt += 1;

        Nuitka_GC_Track( split_copy );

        Py_ssize_t size = mp->ma_keys->dk_size;
        for ( Py_ssize_t i = 0; i < size; i++ )
        {
            PyDictKeyEntry *entry = &split_copy->ma_keys->dk_entries[ i ];

            if ( ( entry->me_key != NULL ) && unlikely( !PyUnicode_Check( entry->me_key ) ))
            {
                PyErr_Format( PyExc_TypeError, "%(function_name)s() keywords must be strings" );
                goto error_exit;
            }

            split_copy->ma_values[ i ] = mp->ma_values[ i ];
            Py_XINCREF( split_copy->ma_values[ i ] );
        }

        _python_par_%(dict_star_parameter_name)s = (PyObject *)split_copy;
    }
    else
    {
        _python_par_%(dict_star_parameter_name)s = PyDict_New();

        PyDictObject *mp = (PyDictObject *)kw;

        Py_ssize_t size = mp->ma_keys->dk_size;
        for ( Py_ssize_t i = 0; i < size; i++ )
        {
            PyDictKeyEntry *entry = &mp->ma_keys->dk_entries[i];

            // TODO: One of these cases has been dealt with above.
            PyObject *value;
            if ( mp->ma_values )
            {
                value = mp->ma_values[ i ];
            }
            else
            {
                value = entry->me_value;
            }

            if ( value != NULL )
            {
                if (unlikely( !PyUnicode_Check( entry->me_key ) ))
                {
                    PyErr_Format( PyExc_TypeError, "%(function_name)s() keywords must be strings" );
                    goto error_exit;
                }

                int res = PyDict_SetItem( _python_par_%(dict_star_parameter_name)s, entry->me_key, value );

                if (unlikely( res != 0 ))
                {
                    goto error_exit;
                }
            }
        }
    }
#endif
    }
    else
    {
        _python_par_%(dict_star_parameter_name)s = PyDict_New();
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

        _python_par_%(parameter_name)s = kw_arg_value;
        Py_INCREF( kw_arg_value );

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

        _python_par_%(parameter_name)s = kw_arg_value;
        Py_INCREF( kw_arg_value );
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
               Nuitka_String_Check( key ) ? Nuitka_String_AsString( key ) : "<non-string>"
           );

           goto error_exit;
        }
    }

#if PYTHON_VERSION < 300
    assert( kw_found == kw_size );
    assert( kw_only_found == 0 );
#endif
}
"""

argparse_template_assign_from_dict_parameter_quick_path = """\
if ( found == false && %(parameter_name_object)s == key )
{
%(parameter_assign_from_kw)s
    found = true;
    kw_found += 1;
}
"""

argparse_template_assign_from_dict_parameter_quick_path_kw_only = """\
if ( found == false && %(parameter_name_object)s == key )
{
%(parameter_assign_from_kw)s
    found = true;
    kw_found += 1;
    kw_only_found += 1;
}
"""

argparse_template_assign_from_dict_parameter_slow_path = """\
if ( found == false && RICH_COMPARE_BOOL_EQ( %(parameter_name_object)s, key ) == 1 )
{
%(parameter_assign_from_kw)s
    found = true;
    kw_found += 1;
}
"""

argparse_template_assign_from_dict_parameter_slow_path_kw_only = """\
if ( found == false && RICH_COMPARE_BOOL_EQ( %(parameter_name_object)s, key ) == 1 )
{
%(parameter_assign_from_kw)s
    found = true;
    kw_found += 1;
    kw_only_found += 1;
}
"""


argparse_template_assign_from_dict_finding = """\
assert( _python_par_%(parameter_name)s == NULL );
_python_par_%(parameter_name)s = value;
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
    if (unlikely( UNPACK_ITERATOR_CHECK( _python_iter_%(parameter_name)s ) == false ))
    {
       Py_DECREF( _python_iter_%(parameter_name)s );
       goto error_exit;
    }
    Py_DECREF( _python_iter_%(parameter_name)s );
}"""

parse_argument_template_nested_argument_assign = """
    // Unpack to _python_par_%(parameter_name)s
    _python_par_%(parameter_name)s = UNPACK_NEXT( _python_iter_%(iter_name)s, %(unpack_count)d );

    if (unlikely (_python_par_%(parameter_name)s == NULL ))
    {
        Py_DECREF( _python_iter_%(iter_name)s );
        goto error_exit;
    }
"""

template_kwonly_argument_default = """\
if ( _python_par_%(parameter_name)s == NULL )
{
    _python_par_%(parameter_name)s = PyDict_GetItem( self->m_kwdefaults, %(parameter_name_object)s );

#if PYTHON_VERSION < 330
    if (unlikely (_python_par_%(parameter_name)s == NULL ))
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() needs keyword-only argument %(parameter_name)s" );
        goto error_exit;
    }

    Py_INCREF( _python_par_%(parameter_name)s );
#else
    Py_XINCREF( _python_par_%(parameter_name)s );
#endif

}"""

template_kwonly_arguments_check = """
#if PYTHON_VERSION >= 330
if (unlikely( %(parameter_test)s ))
{
    PyObject *values[] = { %(parameter_list)s };
    ERROR_TOO_FEW_KWONLY( self, values );

    goto error_exit;
}
#endif
"""

template_dparser = """
static PyObject *dparse_%(function_identifier)s( Nuitka_FunctionObject *self, PyObject **args, int size )
{
    if ( size == %(arg_count)d )
    {
        return impl_%(function_identifier)s( self%(args_forward)s );
    }
    else
    {
        PyObject *result = fparse_%(function_identifier)s( self, args, size, NULL );
        return result;
    }

}

"""
