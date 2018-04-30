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
""" Coroutines function (await/async) related templates.

"""

template_coroutine_object_decl_template = """\
static void %(function_identifier)s( struct Nuitka_CoroutineObject *coroutine );
"""

template_coroutine_object_body_template = """
static void %(function_identifier)s( struct Nuitka_CoroutineObject *coroutine )
{
    CHECK_OBJECT( (PyObject *)coroutine );
    assert( Nuitka_Coroutine_Check( (PyObject *)coroutine ) );

    // Local variable initialization
%(function_var_inits)s

    // Actual function code.
%(function_body)s

%(coroutine_exit)s
}
"""

template_coroutine_exception_exit = """\
    // Return statement must be present.
    NUITKA_CANNOT_GET_HERE( %(function_identifier)s );

    function_exception_exit:
%(function_cleanup)s\
    assert( exception_type );
    RESTORE_ERROR_OCCURRED( exception_type, exception_value, exception_tb );
    coroutine->m_yielded = NULL;
    return;
"""

template_coroutine_noexception_exit = """\
    // Return statement must be present.
    NUITKA_CANNOT_GET_HERE( %(function_identifier)s );

%(function_cleanup)s\
    coroutine->m_yielded = NULL;
    return;
"""

template_coroutine_return_exit = """\
    function_return_exit:;
    coroutine->m_yielded = NULL;
    coroutine->m_returned = tmp_return_value;
    return;
"""


template_make_coroutine_template = """
%(to_name)s = Nuitka_Coroutine_New(
    %(coroutine_identifier)s,
    self->m_name,
    self->m_qualname,
    %(code_identifier)s,
    %(closure_count)d
);
%(closure_copy)s
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
