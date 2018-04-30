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
""" Async generator (await/async + yield) related templates.

"""

template_asyncgen_object_decl_template = """\
static void %(function_identifier)s( struct Nuitka_AsyncgenObject *asyncgen );
"""

template_asyncgen_object_body_template = """
static void %(function_identifier)s( struct Nuitka_AsyncgenObject *asyncgen )
{
    CHECK_OBJECT( (PyObject *)asyncgen );
    assert( Nuitka_Asyncgen_Check( (PyObject *)asyncgen ) );

    // Local variable initialization
%(function_var_inits)s

    // Actual function code.
%(function_body)s

%(asyncgen_exit)s
}
"""

template_asyncgen_exception_exit = """\
    // Return statement must be present.
    NUITKA_CANNOT_GET_HERE( %(function_identifier)s );

    function_exception_exit:
%(function_cleanup)s\
    assert( exception_type );
    RESTORE_ERROR_OCCURRED( exception_type, exception_value, exception_tb );
    asyncgen->m_yielded = NULL;
    return;
"""

template_asyncgen_noexception_exit = """\
    // Return statement must be present.
    NUITKA_CANNOT_GET_HERE( %(function_identifier)s );

%(function_cleanup)s\
    asyncgen->m_yielded = NULL;
    return;
"""

template_asyncgen_return_exit = """\
    function_return_exit:;
    asyncgen->m_yielded = NULL;
    asyncgen->m_status = status_Finished;
    return;
"""


template_make_asyncgen_template = """
%(to_name)s = Nuitka_Asyncgen_New(
    %(asyncgen_identifier)s,
    %(asyncgen_name_obj)s,
    %(asyncgen_qualname_obj)s,
    %(code_identifier)s,
    %(closure_count)d
);
%(closure_copy)s
"""

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
