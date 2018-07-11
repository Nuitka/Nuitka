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
""" Generator function (with yield) related templates.

"""

template_genfunc_yielder_decl_template = """\
#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
static PyObject *%(function_identifier)s_context( struct Nuitka_GeneratorObject *generator, PyObject *yield_return_value );
#else
static void %(function_identifier)s_context( struct Nuitka_GeneratorObject *generator );
#endif
"""

template_genfunc_yielder_body_template = """
#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
struct %(function_identifier)s_locals {
%(function_local_types)s
};
#endif

#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
static PyObject *%(function_identifier)s_context( struct Nuitka_GeneratorObject *generator, PyObject *yield_return_value )
#else
static void %(function_identifier)s_context( struct Nuitka_GeneratorObject *generator )
#endif
{
    CHECK_OBJECT( (PyObject *)generator );
    assert( Nuitka_Generator_Check( (PyObject *)generator ) );

    // Local variable initialization
%(function_var_inits)s

    // Dispatch to yield based on return label index:
%(function_dispatch)s

    // Actual function code.
%(function_body)s

%(generator_exit)s
}
"""

template_generator_exception_exit = """\
%(function_cleanup)s\
#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
    return NULL;
#else
    generator->m_yielded = NULL;
    return;
#endif

    function_exception_exit:
%(function_cleanup)s\
    assert( exception_type );
    RESTORE_ERROR_OCCURRED( exception_type, exception_value, exception_tb );

#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
    return NULL;
#else
    generator->m_yielded = NULL;
    return;
#endif
"""

template_generator_noexception_exit = """\
    // Return statement need not be present.
%(function_cleanup)s\

#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
    return NULL;
#else
    generator->m_yielded = NULL;
    return;
#endif
"""

template_generator_return_exit = """\
    // The above won't return, but we need to make it clear to the compiler
    // as well, or else it will complain and/or generate inferior code.
    assert(false);
    return;

    function_return_exit:
#if PYTHON_VERSION >= 300
    generator->m_returned = tmp_return_value;
#endif

#if _NUITKA_EXPERIMENTAL_GENERATOR_GOTO
    return NULL;
#else
    generator->m_yielded = NULL;
    return;
#endif
"""

template_generator_making = """\
%(to_name)s = Nuitka_Generator_New(
    %(generator_identifier)s_context,
    %(generator_module)s,
    %(generator_name_obj)s,
#if PYTHON_VERSION >= 350
    %(generator_qualname_obj)s,
#endif
    %(code_identifier)s,
    %(closure_count)d
);
%(closure_copy)s
"""


from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
