#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#


template_parameter_function_entry_point = """\
static PyObject *%(parse_function_identifier)s( PyObject *self, PyObject *args, PyObject *kw )
{
%(context_access)s
    Py_ssize_t args_size = PyTuple_GET_SIZE( args );
    Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;
    Py_ssize_t args_given = args_size;
%(parameter_parsing_code)s

    return %(impl_function_identifier)s( self%(parameter_objects_list)s );

error_exit:;

%(parameter_release_code)s
    return NULL;
}
"""

template_parameter_method_entry_point = """\
static PyObject *%(parse_function_identifier)s( PyObject *self, PyObject *_python_par_self, PyObject *args, PyObject *kw )
{
    Py_INCREF( _python_par_self );
%(context_access)s
    Py_ssize_t args_size = PyTuple_GET_SIZE( args );
    Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;
    Py_ssize_t args_given = args_size + 1; // Count the self parameter already given as well.
%(parameter_parsing_code)s

    return %(impl_function_identifier)s( self%(parameter_objects_list)s );

error_exit:;

%(parameter_release_code)s
    return NULL;
}
"""


parse_argument_template_take_counts2 = """\
int kw_args_used = 0;
"""

parse_argument_template_take_counts3 = """\
int args_usable_count;
"""


function_context_access_template = """
    // The context of the function.
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)self;
"""

function_context_unused_template = """\
    // No context is used.
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
if (unlikely( args_given + kw_size < %(required_parameter_count)d ))
{
    if ( %(top_level_parameter_count)d == 1 )
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least 1 argument (%%" PY_FORMAT_SIZE_T "d given)", args_given + kw_size );
    }
    else
    {
#if PY_MAJOR_VERSION < 3 && PY_MINOR_VERSION < 7
        if ( kw_size > 0 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least %%d non-keyword arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_size );
        }
        else
#endif
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least %%d arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_size );
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
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 argument (%%" PY_FORMAT_SIZE_T "d given)", args_given + kw_size );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_size );
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
#if PY_MAJOR_VERSION < 3 && PY_MINOR_VERSION < 7
        if ( kw_size > 0 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d non-keyword arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_size );
        }
        else
#endif
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%" PY_FORMAT_SIZE_T "d given)", %(top_level_parameter_count)d, args_given + kw_size );
        }
    }

    goto error_exit;
}
"""

parse_argument_usable_count = r"""
// Copy normal parameter values given as part of the args list to the respective variables:
args_usable_count = args_given < %(top_level_parameter_count)d ? args_given : %(top_level_parameter_count)d;

"""

parse_argument_template2 = """\
if (likely( %(parameter_position)d < args_usable_count ))
{
    _python_par_%(parameter_name)s = INCREASE_REFCOUNT( PyTuple_GET_ITEM( args, %(parameter_args_index)d ) );
}
"""

parse_argument_template2a = """\
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

        _python_par_%(dict_star_parameter_name)s = MAKE_DICT();

        if (unlikely( PyDict_Update( _python_par_%(dict_star_parameter_name)s, kw ) != 0 ))
        {
            PyErr_Format( PyExc_TypeError, "after ** must be a mapping, not %%s", kw->ob_type->tp_name );

            goto error_exit;
        }
    }
}
"""

parse_argument_template_check_dict_parameter_with_star_dict = """
// Check if argument %(parameter_name)s was given as plain and keyword argument
{
    PyObject *kw_arg_value = PyDict_GetItem( _python_par_%(dict_star_parameter_name)s, %(parameter_name_object)s );

    if ( kw_arg_value != NULL )
    {
        if (unlikely( _python_par_%(parameter_name)s ))
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() got multiple values for keyword argument '%(parameter_name)s'" );
            goto error_exit;
        }

        _python_par_%(parameter_name)s = INCREASE_REFCOUNT( kw_arg_value );

        PyDict_DelItem( _python_par_%(dict_star_parameter_name)s, %(parameter_name_object)s );
    }
}
"""

parse_argument_template_check_dict_parameter_without_star_dict = """
// Check if argument %(parameter_name)s was given as plain and keyword argument
if ( kw_size > 0 )
{
    PyObject *kw_arg_value = PyDict_GetItem( kw, %(parameter_name_object)s );

    if ( kw_arg_value != NULL )
    {
        if (unlikely( _python_par_%(parameter_name)s ))
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() got multiple values for keyword argument '%(parameter_name)s'" );
            goto error_exit;
        }

        _python_par_%(parameter_name)s = INCREASE_REFCOUNT( kw_arg_value );

        kw_args_used += 1;
    }
}
"""

parse_argument_template_copy_default_value = """\
if ( _python_par_%(parameter_name)s == NULL )
{
    _python_par_%(parameter_name)s = %(default_identifier)s;
}
"""

parse_argument_template_check_dict_parameter_unused_without_star_dict = """
if ( kw_args_used != kw_size )
{
    Py_ssize_t ppos = 0;
    PyObject *key, *value;

    while( PyDict_Next( kw, &ppos, &key, &value ) )
    {
        if (unlikely( PySequence_Contains( %(parameter_names_tuple)s, key ) == 0 ))
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() got an unexpected keyword argument '%%s'", PyString_Check( key ) ? PyString_AsString( key ) : "<non-string>" );
            goto error_exit;
        }
    }
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
