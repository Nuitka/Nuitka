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

template_genfunc_yielder_maker_decl = """\
static PyObject *%(function_identifier)s_maker( void );
"""

template_genfunc_yielder_body_template = """
struct %(function_identifier)s_locals {
%(function_local_types)s
};

static PyObject *%(function_identifier)s_context( struct Nuitka_GeneratorObject *generator, PyObject *yield_return_value )
{
    CHECK_OBJECT( (PyObject *)generator );
    assert( Nuitka_Generator_Check( (PyObject *)generator ) );

    // Heap access if used.
%(heap_declaration)s

    // Dispatch to yield based on return label index:
%(function_dispatch)s

    // Local variable initialization
%(function_var_inits)s

    // Actual function code.
%(function_body)s

%(generator_exit)s
}

static PyObject *%(function_identifier)s_maker( void )
{
    return Nuitka_Generator_New(
        %(function_identifier)s_context,
        %(generator_module)s,
        %(generator_name_obj)s,
#if PYTHON_VERSION >= 350
        %(generator_qualname_obj)s,
#endif
        %(code_identifier)s,
        %(closure_count)d,
        sizeof(struct %(function_identifier)s_locals)
    );
}
"""

template_make_generator = """\
%(to_name)s = %(generator_identifier)s_maker();
%(closure_copy)s
"""


template_generator_exception_exit = """\
%(function_cleanup)s
    return NULL;

    function_exception_exit:
%(function_cleanup)s\
    assert( %(exception_type)s );
    RESTORE_ERROR_OCCURRED( %(exception_type)s, %(exception_value)s, %(exception_tb)s );

    return NULL;
"""

template_generator_noexception_exit = """\
    // Return statement need not be present.
%(function_cleanup)s\

    return NULL;
"""

# TODO: Clarify if cannot get here function is to be used.
template_generator_return_exit = """\
    // The above won't return, but we need to make it clear to the compiler
    // as well, or else it will complain and/or generate inferior code.
    assert(false);
    return NULL;

    function_return_exit:
#if PYTHON_VERSION >= 300
    generator->m_returned = %(return_value)s;
#endif

    return NULL;
"""



from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
