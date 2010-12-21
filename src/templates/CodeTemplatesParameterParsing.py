#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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

parse_argument_template_take_counts = """
Py_ssize_t args_size = PyTuple_GET_SIZE( args );
Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;
int args_usable_count = args_size < %(top_level_parameter_count)d ? args_size : %(top_level_parameter_count)d;
int kw_args_used = 0;
"""

parse_argument_template_refuse_parameters = """
if (unlikely( args_size + kw_size > 0 ))
{
    PyErr_Format( PyExc_TypeError, "%(function_name)s() takes no arguments (%%zd given)", args_size+kw_size );
    goto error_exit;
}
"""

parse_argument_template_check_counts_with_list_star_arg = """
// Check if too little arguments were given.
if (unlikely( args_size + kw_size < %(required_parameter_count)d ))
{
    if ( %(top_level_parameter_count)d == 1 )
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least 1 argument (%%zd given)", args_size+kw_size );
    }
    else
    {
        if ( kw_size > 0 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least %%d non-keyword arguments (%%zd given)", %(top_level_parameter_count)d, args_size+kw_size );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes at least %%d arguments (%%zd given)", %(top_level_parameter_count)d, args_size+kw_size );
        }
    }

    goto error_exit;
}
"""

parse_argument_template_check_counts_without_list_star_arg = """
// Check if too many arguments were given in case of non star args
if (unlikely( args_size > %(top_level_parameter_count)d ))
{
    if ( %(top_level_parameter_count)d == 1 )
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 argument (%%zd given)", args_size );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%zd given)", %(top_level_parameter_count)d, args_size );
    }

    goto error_exit;
}

// Check if too little arguments were given.
if (unlikely( args_size + kw_size < %(required_parameter_count)d ))
{
    if ( %(top_level_parameter_count)d == 1 )
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 argument (%%zd given)", args_size+kw_size );
    }
    else
    {
        if ( kw_size > 0 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d non-keyword arguments (%%zd given)", %(top_level_parameter_count)d, args_size+kw_size );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%zd given)", %(top_level_parameter_count)d, args_size+kw_size );
        }
    }

    goto error_exit;
}
"""

parse_argument_template2 = """\
if (likely( %(parameter_position)d < args_usable_count ))
{
    _python_par_%(parameter_name)s = INCREASE_REFCOUNT( PyTuple_GET_ITEM( args, %(parameter_position)d ) );
}
"""

parse_argument_template_copy_list_star_args = """
// Copy left over argument values to the star list parameter given.
if ( args_size > %(top_level_parameter_count)d )
{
    _python_par_%(list_star_parameter_name)s = PyTuple_GetSlice( args, %(top_level_parameter_count)d, args_size );
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
    _python_par_%(parameter_name)s = INCREASE_REFCOUNT( %(default_identifier)s );
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

parse_argument_template_nested_argument_unpack = """
// Unpack from _python_par_%(parameter_name)s
{
    PyObject *_python_iter_%(parameter_name)s = PyObject_GetIter( %(unpack_source_identifier)s );

    if (unlikely( _python_iter_%(parameter_name)s == NULL ))
    {
        goto error_exit;
    }

%(unpack_code)s

    PyObject *attempt = PyIter_Next( _python_iter_%(parameter_name)s );
    Py_DECREF( _python_iter_%(parameter_name)s );

    // Check if the sequence was too long maybe.
    if (likely( attempt == NULL ))
    {
        PyErr_Clear();
    }
    else
    {
        Py_DECREF( attempt );

        PyErr_Format( PyExc_ValueError, "too many values to unpack" );
        goto error_exit;
    }

    Py_XDECREF( _python_iter_%(parameter_name)s );
    _python_iter_%(parameter_name)s = NULL;
}
"""

parse_argument_template_nested_argument_assign = """
    _python_par_%(parameter_name)s = PyIter_Next( _python_iter_%(iter_name)s );

    if (unlikely (_python_par_%(parameter_name)s == NULL))
    {
        Py_DECREF( _python_iter_%(iter_name)s );

        if ( %(unpack_count)d == 1 )
        {
            PyErr_Format( PyExc_ValueError, "need more than 1 value to unpack" );
        }
        else
        {
            PyErr_Format( PyExc_ValueError, "need more than %%d values to unpack", %(unpack_count)d+1 );
        }

        goto error_exit;
    }
"""
