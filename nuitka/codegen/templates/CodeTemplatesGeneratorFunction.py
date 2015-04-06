#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

make_genfunc_with_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    // Copy the parameter default values and closure values over.
%(context_copy)s

    return Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(dparse_function_identifier)s,
        %(function_name_obj)s,
#if PYTHON_VERSION >= 330
        %(function_qualname_obj)s,
#endif
        %(code_identifier)s,
        %(defaults)s,
#if PYTHON_VERSION >= 300
        %(kw_defaults)s,
        %(annotations)s,
#endif
        %(module_identifier)s,
        %(function_doc)s,
        closure,
        %(closure_count)d
    );
}
"""

make_genfunc_without_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    return Nuitka_Function_New(
        %(fparse_function_identifier)s,
        %(dparse_function_identifier)s,
        %(function_name_obj)s,
#if PYTHON_VERSION >= 330
        %(function_qualname_obj)s,
#endif
        %(code_identifier)s,
        %(defaults)s,
#if PYTHON_VERSION >= 300
        %(kw_defaults)s,
        %(annotations)s,
#endif
        %(module_identifier)s,
        %(function_doc)s
    );
}
"""

# TODO: Make the try/catch below unnecessary by detecting the presence
# or return statements in generators.
genfunc_yielder_template = """
static void %(function_identifier)s_context2( Nuitka_GeneratorObject *generator )
{
    // Local variable initialization
%(function_var_inits)s

    // Actual function code.
%(function_body)s

%(generator_exit)s
}

#ifdef _NUITKA_MAKECONTEXT_INTS
static void %(function_identifier)s_context( int generator_address_1, int generator_address_2 )
{
    // Restore the pointer from ints should it be necessary, often it can be
    // directly received.
    int generator_addresses[2] = {
        generator_address_1,
        generator_address_2
    };

    Nuitka_GeneratorObject *generator = (Nuitka_GeneratorObject *)*(uintptr_t *)&generator_addresses[0];
#else
static void %(function_identifier)s_context( Nuitka_GeneratorObject *generator )
{
#endif

    CHECK_OBJECT( (PyObject *)generator );
    assert( Nuitka_Generator_Check( (PyObject *)generator ) );

    %(function_identifier)s_context2( generator );

    swapFiber( &generator->m_yielder_context, &generator->m_caller_context );
}"""

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

genfunc_generator_no_parameters = """\
    PyObject **parameters = NULL;
"""

genfunc_generator_with_parameters = """\
    PyObject **parameters = (PyObject **)malloc(%(parameter_count)d * sizeof(PyObject *));
%(parameter_copy)s
"""

genfunc_generator_no_closure = """\
    PyCellObject **closure = NULL;
"""

genfunc_generator_with_parent_closure = """\
    PyCellObject **closure = (PyCellObject **)malloc(%(closure_count)d * sizeof(PyCellObject *));
    for( Py_ssize_t i = 0; i < %(closure_count)d; i++ )
    {
        closure[ i ] = self->m_closure[ i ];
        Py_INCREF( closure[ i ] );
    }
"""
genfunc_generator_with_own_closure = """\
    PyCellObject **closure = (PyCellObject **)malloc(%(closure_count)d * sizeof(PyCellObject *));
%(closure_copy)s
"""

genfunc_function_impl_template = """
static PyObject *impl_%(function_identifier)s( %(parameter_objects_decl)s )
{
%(parameter_decl)s
%(closure_decl)s

    PyObject *result = Nuitka_Generator_New(
        %(function_identifier)s_context,
        %(function_name_obj)s,
        %(code_identifier)s,
        closure,
        %(closure_count)d,
        parameters,
        %(parameter_count)d
    );
    if (unlikely( result == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "cannot create generator %(function_name)s" );
        return NULL;
    }

    return result;
}
"""
