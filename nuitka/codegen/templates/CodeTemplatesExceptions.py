#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Templates for raising exceptions, making assertions, and try/finally
    construct.

"""

template_publish_exception_to_handler = """\
if (exception_tb == NULL)
{
    exception_tb = %(tb_making)s;
}
else if ( exception_tb->tb_frame != %(frame_identifier)s || exception_tb->tb_lineno != %(frame_identifier)s->f_lineno )
{
    exception_tb = ADD_TRACEBACK( %(frame_identifier)s, exception_tb );
}
"""

template_error_catch_quick_exception = """\
if ( %(condition)s )
{
    if ( !ERROR_OCCURED() )
    {
        exception_type = INCREASE_REFCOUNT( %(quick_exception)s );
        exception_value = NULL;
        exception_tb = NULL;
    }
    else
    {
        PyErr_Fetch( &exception_type, &exception_value, (PyObject **)&exception_tb );
    }
%(release_temps)s

%(line_number_code)s
    goto %(exception_exit)s;
}"""

template_error_catch_exception = """\
if ( %(condition)s )
{
    assert( ERROR_OCCURED() );

    PyErr_Fetch( &exception_type, &exception_value, (PyObject **)&exception_tb );
%(release_temps)s

%(line_number_code)s
    goto %(exception_exit)s;
}"""

template_error_format_string_exception = """\
if ( %(condition)s )
{
%(release_temps)s
%(set_exception)s

%(line_number_code)s
    goto %(exception_exit)s;
}
"""


template_final_handler_start = """\
// Tried block ends with no exception occured, note that.
exception_type = NULL;
exception_value = NULL;
exception_tb = NULL;
%(final_error_target)s:;
%(keeper_type)s = exception_type;
%(keeper_value)s = exception_value;
%(keeper_tb)s = exception_tb;
exception_type = NULL;
exception_value = NULL;
exception_tb = NULL;
"""

template_final_handler_start_python3 = """\
// Tried block ends with no exception occured, note that.
exception_type = NULL;
exception_value = NULL;
exception_tb = NULL;
%(final_error_target)s:;
"""



template_final_handler_reraise = """\
// Reraise exception if any.
if ( %(keeper_type)s != NULL )
{
    exception_type = %(keeper_type)s;
    exception_value = %(keeper_value)s;
    exception_tb = %(keeper_tb)s;

    goto %(exception_exit)s;
}
"""

template_final_handler_return_reraise = """\
// Return value if any.
if ( tmp_return_value != NULL )
{
    goto %(parent_return_target)s;
}
"""

template_final_handler_generator_return_reraise = """\
if ( tmp_generator_return )
{
    goto %(parent_return_target)s;
}
"""

template_final_handler_continue_reraise = """\
// Continue if entered via continue.
if ( %(continue_name)s )
{
    goto %(parent_continue_target)s;
}
"""

template_final_handler_break_reraise = """\
// Break if entered via break.
if (  %(break_name)s )
{
    goto %(parent_break_target)s;
}
"""
