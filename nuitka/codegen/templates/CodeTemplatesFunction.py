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
""" Normal function (no generator, not yielding) related templates.

"""

template_function_make_declaration = """\
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_arg_spec)s );
"""

template_function_direct_declaration = """\
%(file_scope)s PyObject *impl_%(function_identifier)s( %(direct_call_arg_spec)s );
"""

template_function_closure_making = """\
    PyCellObject **closure = (PyCellObject **)malloc(%(closure_count)d * sizeof(PyCellObject *));
%(closure_copy)s
"""

template_make_function_with_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    // Copy the parameter default values and closure values over.
%(closure_making)s

    PyObject *result = Nuitka_Function_New(
        %(function_impl_identifier)s,
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

    return result;
}
"""

template_make_function_without_context_template = """
static PyObject *MAKE_FUNCTION_%(function_identifier)s( %(function_creation_args)s )
{
    PyObject *result = Nuitka_Function_New(
        %(function_impl_identifier)s,
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
    // Preserve error status for checks
#ifndef __NUITKA_NO_ASSERT__
    NUITKA_MAY_BE_UNUSED bool had_error = ERROR_OCCURRED();
#endif

    // Local variable declarations.
%(function_locals)s

    // Actual function code.
%(function_body)s

%(function_exit)s
}
"""

template_function_exception_exit = """\
function_exception_exit:
%(function_cleanup)s\
    assert( exception_type );
    RESTORE_ERROR_OCCURRED( exception_type, exception_value, exception_tb );

    return NULL;
"""

template_function_return_exit = """\
function_return_exit:
%(function_cleanup)s
CHECK_OBJECT( tmp_return_value );
assert( had_error || !ERROR_OCCURRED() );
return tmp_return_value;
"""

function_direct_body_template = """\
%(file_scope)s PyObject *impl_%(function_identifier)s( %(direct_call_arg_spec)s )
{
#ifndef __NUITKA_NO_ASSERT__
    NUITKA_MAY_BE_UNUSED bool had_error = ERROR_OCCURRED();
    assert(!had_error); // Do not enter inlined functions with error set.
#endif

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

from . import TemplateDebugWrapper # isort:skip
TemplateDebugWrapper.checkDebug(globals())
