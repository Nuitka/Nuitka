#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
static PyObject *MAKE_FUNCTION_%(function_identifier)s(%(function_creation_args)s);
"""

template_function_direct_declaration = """\
%(file_scope)s PyObject *impl_%(function_identifier)s(%(direct_call_arg_spec)s);
"""

template_maker_function_body = """
static PyObject *%(function_maker_identifier)s(%(function_creation_args)s) {
    struct Nuitka_FunctionObject *result = Nuitka_Function_New(
        %(function_impl_identifier)s,
        %(function_name_obj)s,
#if PYTHON_VERSION >= 0x300
        %(function_qualname_obj)s,
#endif
        %(code_identifier)s,
        %(defaults)s,
#if PYTHON_VERSION >= 0x300
        %(kw_defaults)s,
        %(annotations)s,
#endif
        %(module_identifier)s,
        %(function_doc)s,
        %(closure_name)s,
        %(closure_count)d
    );
%(constant_return_code)s

    return (PyObject *)result;
}
"""

template_make_function = """\
%(closure_copy)s
%(to_name)s = %(function_maker_identifier)s(%(args)s);
"""

template_function_body = """\
static PyObject *impl_%(function_identifier)s(%(parameter_objects_decl)s) {
    // Preserve error status for checks
#ifndef __NUITKA_NO_ASSERT__
    NUITKA_MAY_BE_UNUSED bool had_error = ERROR_OCCURRED();
#endif

    // Local variable declarations.
%(function_locals)s

    // Actual function body.
%(function_body)s

%(function_exit)s
}
"""

template_function_exception_exit = """\
function_exception_exit:
%(function_cleanup)s
    assert(%(exception_type)s);
    RESTORE_ERROR_OCCURRED(%(exception_type)s, %(exception_value)s, %(exception_tb)s);

    return NULL;
"""

template_function_return_exit = """
function_return_exit:
   // Function cleanup code if any.
%(function_cleanup)s

   // Actual function exit with return value, making sure we did not make
   // the error status worse despite non-NULL return.
   CHECK_OBJECT(tmp_return_value);
   assert(had_error || !ERROR_OCCURRED());
   return tmp_return_value;"""

function_direct_body_template = """\
%(file_scope)s PyObject *impl_%(function_identifier)s(%(direct_call_arg_spec)s) {
#ifndef __NUITKA_NO_ASSERT__
    NUITKA_MAY_BE_UNUSED bool had_error = ERROR_OCCURRED();
    assert(!had_error); // Do not enter inlined functions with error set.
#endif

    // Local variable declarations.
%(function_locals)s

    // Actual function body.
%(function_body)s

%(function_exit)s
}
"""

from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())
