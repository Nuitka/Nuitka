#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Templates for the iterator handling.

"""


template_iterator_check = """\
// Check if iterator has left-over elements.
CHECK_OBJECT( %(iterator_name)s ); assert( HAS_ITERNEXT( %(iterator_name)s ) );

%(attempt_name)s = (*Py_TYPE( %(iterator_name)s )->tp_iternext)( %(iterator_name)s );

if (likely( %(attempt_name)s == NULL ))
{
    PyObject *error = GET_ERROR_OCCURRED();

    if ( error != NULL )
    {
        if ( EXCEPTION_MATCH_BOOL_SINGLE( error, PyExc_StopIteration ))
        {
            CLEAR_ERROR_OCCURRED();
        }
        else
        {
            FETCH_ERROR_OCCURRED( &%(exception_type)s, &%(exception_value)s, &%(exception_tb)s );
%(release_temps_1)s
%(var_description_code_1)s
%(line_number_code_1)s
            goto %(exception_exit)s;
        }
    }
}
else
{
    Py_DECREF( %(attempt_name)s );

    // TODO: Could avoid PyErr_Format.
#if PYTHON_VERSION < 300
    PyErr_Format( PyExc_ValueError, "too many values to unpack" );
#else
    PyErr_Format( PyExc_ValueError, "too many values to unpack (expected %(count)d)" );
#endif
    FETCH_ERROR_OCCURRED( &%(exception_type)s, &%(exception_value)s, &%(exception_tb)s );
%(release_temps_2)s
%(var_description_code_2)s
%(line_number_code_2)s
    goto %(exception_exit)s;
}"""

template_loop_break_next = """\
if ( %(to_name)s == NULL )
{
    if ( CHECK_AND_CLEAR_STOP_ITERATION_OCCURRED() )
    {
%(break_indicator_code)s
        goto %(break_target)s;
    }
    else
    {
%(release_temps)s
        FETCH_ERROR_OCCURRED( &%(exception_type)s, &%(exception_value)s, &%(exception_tb)s );
%(var_description_code)s
%(line_number_code)s
        goto %(exception_target)s;
    }
}
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
