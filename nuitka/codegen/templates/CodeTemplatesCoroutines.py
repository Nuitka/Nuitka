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

template_coroutine_object_maker_template = """\
static PyObject *%(function_identifier)s_maker( void );
"""

template_coroutine_object_body_template = """
struct %(function_identifier)s_locals {
%(function_local_types)s
};

static PyObject *%(function_identifier)s_context( struct Nuitka_CoroutineObject *coroutine, PyObject *yield_return_value )
{
    CHECK_OBJECT( (PyObject *)coroutine );
    assert( Nuitka_Coroutine_Check( (PyObject *)coroutine ) );

    // Heap access if used.
%(heap_declaration)s

    // Dispatch to yield based on return label index:
%(function_dispatch)s

    // Local variable initialization
%(function_var_inits)s

    // Actual function code.
%(function_body)s

%(coroutine_exit)s
}

static PyObject *%(function_identifier)s_maker( void )
{
    return Nuitka_Coroutine_New(
        %(function_identifier)s_context,
        %(coroutine_module)s,
        %(coroutine_name_obj)s,
        %(coroutine_qualname_obj)s,
        %(code_identifier)s,
        %(closure_count)d,
        sizeof(struct %(function_identifier)s_locals)
    );
}
"""

template_make_coroutine = """\
%(to_name)s = %(coroutine_identifier)s_maker();
%(closure_copy)s
"""

template_coroutine_exception_exit = """\
    // Return statement must be present.
    NUITKA_CANNOT_GET_HERE( %(function_identifier)s );

    function_exception_exit:
%(function_cleanup)s\
    assert( %(exception_type)s );
    RESTORE_ERROR_OCCURRED( %(exception_type)s, %(exception_value)s, %(exception_tb)s );
    return NULL;
"""

template_coroutine_noexception_exit = """\
    // Return statement must be present.
    NUITKA_CANNOT_GET_HERE( %(function_identifier)s );

%(function_cleanup)s\

    return NULL;
"""

template_coroutine_return_exit = """\
    function_return_exit:;

    coroutine->m_returned = %(return_value)s;

    return NULL;
"""



from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
