#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Templates for handling exceptions.

"""

template_publish_exception_to_handler = """\
if (%(keeper_tb)s == NULL) {
    %(keeper_tb)s = %(tb_making)s;
} else if (%(keeper_lineno)s != 0) {
    %(keeper_tb)s = ADD_TRACEBACK(%(keeper_tb)s, %(frame_identifier)s, %(keeper_lineno)s);
}
"""

template_error_catch_quick_exception = """\
if (%(condition)s) {
    if (!ERROR_OCCURRED()) {
        %(exception_type)s = %(quick_exception)s;
        Py_INCREF(%(exception_type)s);
        %(exception_value)s = NULL;
        %(exception_tb)s = NULL;
    } else {
        FETCH_ERROR_OCCURRED(&%(exception_type)s, &%(exception_value)s, &%(exception_tb)s);
    }
%(release_temps)s

%(var_description_code)s
%(line_number_code)s
    goto %(exception_exit)s;
}"""

template_error_catch_exception = """\
if (%(condition)s) {
    assert(ERROR_OCCURRED());

    FETCH_ERROR_OCCURRED(&%(exception_type)s, &%(exception_value)s, &%(exception_tb)s);
%(release_temps)s

%(line_number_code)s
%(var_description_code)s
    goto %(exception_exit)s;
}"""

template_error_format_string_exception = """\
if (%(condition)s) {
%(release_temps)s
%(set_exception)s

%(line_number_code)s
%(var_description_code)s
    goto %(exception_exit)s;
}
"""

template_error_format_name_error_exception = """\
if (unlikely(%(condition)s)) {
%(release_temps)s
%(set_exception)s

%(line_number_code)s
%(var_description_code)s
    goto %(exception_exit)s;
}
"""


from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())
