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
""" Normal function (no yield) related templates.

"""

template_function_make_declaration = """\
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_arg_spec)s );
"""

template_function_direct_declaration = """\
%(file_scope)s PyObject *impl_%(function_identifier)s( %(direct_call_arg_spec)s );
"""

function_context_body_template = """
// This structure is for attachment as self of %(function_identifier)s.
// It is allocated at the time the function object is created.
struct _context_%(function_identifier)s_t
{
    // The function can access a read-only closure of the creator.
%(context_decl)s
};

static void _context_%(function_identifier)s_destructor( void *context_voidptr )
{
    _context_%(function_identifier)s_t *_python_context = (_context_%(function_identifier)s_t *)context_voidptr;

%(context_free)s

    delete _python_context;
}
"""

make_function_with_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    struct _context_%(function_identifier)s_t *_python_context = new _context_%(function_identifier)s_t;

    // Copy the parameter default values and closure values over.
%(context_copy)s

    PyObject *result = Nuitka_Function_New(
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
        _python_context,
        _context_%(function_identifier)s_destructor
    );

    return result;
}
"""

make_function_without_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    PyObject *result = Nuitka_Function_New(
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

    return result;
}
"""

template_function_body = """\
static PyObject *impl_%(function_identifier)s( %(parameter_objects_decl)s )
{
%(context_access_function_impl)s

    // Local variable declarations.
%(function_locals)s

    // Actual function code.
%(function_body)s

%(function_exit)s
}
"""

template_function_exception_exit = """\
    // Return statement must be present.
    assert(false);
function_exception_exit:
%(function_cleanup)s\
    assert( exception_type );
    PyErr_Restore( exception_type, exception_value, (PyObject *)exception_tb );

    assert( ERROR_OCCURRED() );
    return NULL;
"""

template_function_noexception_exit = """\
    // Return statement must be present.
    assert(false);
    return NULL;
"""

template_function_return_exit = """\
function_return_exit:
%(function_cleanup)s\
    assertObject( tmp_return_value );
    assert( !ERROR_OCCURRED() );
    return tmp_return_value;
"""

function_direct_body_template = """\
%(file_scope)s PyObject *impl_%(function_identifier)s( %(direct_call_arg_spec)s )
{
%(context_access_function_impl)s

    // Local variable declarations.
%(function_locals)s

    // Actual function code.
%(function_body)s

%(function_exit)s
}
"""


function_dict_setup = """\
// Locals dictionary setup.
PyObject *locals_dict = PyDict_New();
"""

# Bad to read, but the context declaration should be on one line.
# pylint: disable=C0301

function_context_access_template = """\
    // The context of the function.
    struct _context_%(function_identifier)s_t *_python_context = (struct _context_%(function_identifier)s_t *)self->m_context;"""

function_context_unused_template = """\
    // No context is used."""
