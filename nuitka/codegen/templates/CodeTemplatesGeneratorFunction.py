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
""" Generator function (with yield) related templates.

"""

template_genfunc_yielder_decl_template = """\
static void %(function_identifier)s_context( Nuitka_GeneratorObject *generator );
"""

template_genfunc_yielder_body_template = """
static void %(function_identifier)s_context( Nuitka_GeneratorObject *generator )
{
    CHECK_OBJECT( (PyObject *)generator );
    assert( Nuitka_Generator_Check( (PyObject *)generator ) );

    // Local variable initialization
%(function_var_inits)s

    // Actual function code.
%(function_body)s

%(generator_exit)s
}
"""

template_generator_exception_exit = """\
    RESTORE_ERROR_OCCURRED( PyExc_StopIteration, NULL, NULL );
    Py_INCREF( PyExc_StopIteration );

    generator->m_yielded = NULL;
    return;

    function_exception_exit:
    assert( exception_type );
    RESTORE_ERROR_OCCURRED( exception_type, exception_value, exception_tb );
    generator->m_yielded = NULL;
    return;
"""

template_generator_noexception_exit = """\
    // Return statement must be present.
    NUITKA_CANNOT_GET_HERE( %(function_identifier)s );

    generator->m_yielded = NULL;
    return;
"""

template_generator_return_exit = """\
    // The above won't return, but we need to make it clear to the compiler
    // as well, or else it will complain and/or generate inferior code.
    assert(false);
    return;

    function_return_exit:
#if PYTHON_VERSION < 330
    RESTORE_ERROR_OCCURRED( PyExc_StopIteration, NULL, NULL );
#else
    RESTORE_ERROR_OCCURRED( PyExc_StopIteration, tmp_return_value, NULL );
#endif
    Py_INCREF( PyExc_StopIteration );
    generator->m_yielded = NULL;
    return;
"""

template_generator_making_without_context = """\
%(to_name)s = Nuitka_Generator_New(
    %(generator_identifier)s_context,
    %(generator_name_obj)s,
#if PYTHON_VERSION >= 350
    %(generator_qualname_obj)s,
#endif
    %(code_identifier)s,
    NULL,
    0
);
"""

template_generator_making_with_context = """\
{
%(closure_making)s
    %(to_name)s = Nuitka_Generator_New(
        %(generator_identifier)s_context,
        %(generator_name_obj)s,
#if PYTHON_VERSION >= 350
        %(generator_qualname_obj)s,
#endif
        %(code_identifier)s,
        closure,
        %(closure_count)d
    );
}
"""


from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
