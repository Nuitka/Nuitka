#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
%(parameter_parsing_code)s

    return %(impl_function_identifier)s( %(parameter_objects_list)s );
}
"""


template_parse_argument_check_counts_without_list_star_arg = r"""
// Check if too many arguments were given in case of non list star arg
if (unlikely( args_size > %(top_level_parameter_count)d ))
{
#if PYTHON_VERSION >= 330
    ERROR_TOO_MANY_ARGUMENTS( self, args_size, kw_only_found );
    goto error_exit;
#endif
}

"""

template_parse_arguments = r"""
// Copy normal parameter values given as part of the argument list to the
// respective variables:

bool res = PARSE_ARGUMENTS( self, python_pars, kw, args, args_size );
if (unlikely( res == false )) return NULL;
"""


template_parameter_dparser_entry_point = """
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

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
