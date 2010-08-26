# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
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

parse_argument_template_refuse_parameters = """
    Py_ssize_t args_size = PyTuple_GET_SIZE( args );
    Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;

    if ( args_size + kw_size > 0 )
    {
        PyErr_Format( PyExc_TypeError, "%(function_name)s() takes no arguments (%%d given)", args_size+kw_size );
        throw _PythonException();
    }
"""
parse_argument_template_check_counts = """
    Py_ssize_t args_size = PyTuple_GET_SIZE( args );

    if ( !%(has_list_star_arg)s && args_size > %(top_level_parameter_count)d )
    {
        if ( %(top_level_parameter_count)d == 1 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 argument (%%d given)", args_size );
        }
        else
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%d given)", %(top_level_parameter_count)d, args_size );
        }

        throw _PythonException();
    }

    Py_ssize_t kw_size = kw ? PyDict_Size( kw ) : 0;

    if ( args_size + kw_size < %(required_parameter_count)d)
    {
        if ( %(top_level_parameter_count)d == 1 )
        {
            PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly 1 argument (%%d given)", args_size+kw_size );
        }
        else
        {
            if ( kw_size > 0 )
            {
                PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d non-keyword arguments (%%d given)", %(top_level_parameter_count)d, args_size+kw_size );
            }
            else
            {
                PyErr_Format( PyExc_TypeError, "%(function_name)s() takes exactly %%d arguments (%%d given)", %(top_level_parameter_count)d, args_size+kw_size );
            }
        }

        throw _PythonException();
    }

    int args_usable_count = args_size < %(top_level_parameter_count)d ? args_size : %(top_level_parameter_count)d;
    int kw_args_used = 0;
"""

parse_argument_template2 = """
    if ( %(parameter_position)d < args_usable_count)
    {
        %(parameter_identifier)s = INCREASE_REFCOUNT( PyTuple_GET_ITEM( args, %(parameter_position)d ) );
    }
"""

parse_argument_template3 = """
    // Copy left over argument values to the star list parameter given.
    if ( args_size > %(top_level_parameter_count)d )
    {
        %(list_star_parameter_identifier)s = PyTuple_GetSlice( args, %(top_level_parameter_count)d, args_size );
    }
    else
    {
        %(list_star_parameter_identifier)s = INCREASE_REFCOUNT( _python_tuple_empty );
    }
"""

parse_argument_template_dict_star_copy = """
    if ( kw == NULL )
    {
        %(dict_star_parameter_identifier)s = PyDict_New();
    }
    else
    {
        %(dict_star_parameter_identifier)s = PyDict_Copy( kw );
    }
"""

parse_argument_template_check_dict_parameter_with_star_dict = """
    {
        PyObject *kw_arg_value = PyDict_GetItem( %(dictionary_variable)s, %(parameter_name_object)s );

        if ( kw_arg_value != NULL )
        {
            if (unlikely( %(parameter_identifier)s.isInitialized() ) )
            {
                PyErr_Format( PyExc_TypeError, "%(function_name)s got multiple values for keyword argument '%(parameter_name)s'" );
                throw _PythonException();
            }

            %(parameter_identifier)s = INCREASE_REFCOUNT( kw_arg_value );

            PyDict_DelItem( %(dictionary_variable)s, %(parameter_name_object)s );
        }
    }
"""

parse_argument_template_check_dict_parameter_without_star_dict = """
    if ( kw != NULL )
    {
        PyObject *kw_arg_value = PyDict_GetItem( kw, %(parameter_name_object)s );

        if ( kw_arg_value != NULL )
        {
            if (unlikely( %(parameter_identifier)s.isInitialized() ) )
            {
                PyErr_Format( PyExc_TypeError, "%(function_name)s got multiple values for keyword argument '%(parameter_name)s'" );
                throw _PythonException();
            }

            %(parameter_identifier)s = INCREASE_REFCOUNT( kw_arg_value );

            kw_args_used += 1;
        }
    }
"""

parse_argument_template_copy_default_value = """
    if (!%(parameter_identifier)s.isInitialized() )
    {
        %(parameter_identifier)s = INCREASE_REFCOUNT( %(default_identifier)s );
    }
"""

parse_argument_template_check_dict_parameter_unused_without_star_dict = """
    if ( kw_args_used != kw_size )
    {
        Py_ssize_t ppos = 0;
        PyObject *key, *value;

        PyObject *_parameters_tuple = MAKE_TUPLE( %(parameter_name_objects)s );

        try
        {
            while( true )
            {
                int result = PyDict_Next( kw, &ppos, &key, &value );

                if (unlikely( result == 0 ))
                {
                    PyErr_Format( PyExc_RuntimeError, "Implementation error in dict varargs processing" );
                    throw _PythonException();
                }

                if ( PySequence_Contains( _parameters_tuple, key ) == 0 )
                {
                    PyErr_Format( PyExc_TypeError, "%(function_name)s() got an unexpected keyword argument '%%s'", PyString_Check( key ) ? PyString_AsString( key ) : "<non-string>" );
                    throw _PythonException();
                }
            }
        }
        catch(...)
        {
            Py_DECREF( _parameters_tuple );
            throw;
        }
    }
"""
