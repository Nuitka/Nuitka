#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

template_coroutine_object_maker = """\
static PyObject *%(coroutine_maker_identifier)s(%(coroutine_creation_args)s);
"""

template_coroutine_object_body = """
struct %(function_identifier)s_locals {
%(function_local_types)s
};

static PyObject *%(function_identifier)s_context(struct Nuitka_CoroutineObject *coroutine, PyObject *yield_return_value) {
    CHECK_OBJECT(coroutine);
    assert(Nuitka_Coroutine_Check((PyObject *)coroutine));

    // Heap access if used.
%(heap_declaration)s

    // Dispatch to yield based on return label index:
%(function_dispatch)s

    // Local variable initialization
%(function_var_inits)s

    // Actual coroutine body.
%(function_body)s

%(coroutine_exit)s
}

static PyObject *%(coroutine_maker_identifier)s(%(coroutine_creation_args)s) {
    return Nuitka_Coroutine_New(
        %(function_identifier)s_context,
        %(coroutine_module)s,
        %(coroutine_name_obj)s,
        %(coroutine_qualname_obj)s,
        %(code_identifier)s,
        %(closure_name)s,
        %(closure_count)d,
        sizeof(struct %(function_identifier)s_locals)
    );
}
"""

template_make_coroutine = """\
%(closure_copy)s
%(to_name)s = %(coroutine_maker_identifier)s(%(args)s);
"""

# TODO: For functions NUITKA_CANNOT_GET_HERE is injected by composing code.
template_coroutine_exception_exit = """\
    NUITKA_CANNOT_GET_HERE("Return statement must be present");

    function_exception_exit:
%(function_cleanup)s
    assert(%(exception_type)s);
    RESTORE_ERROR_OCCURRED(%(exception_type)s, %(exception_value)s, %(exception_tb)s);
    return NULL;
"""

template_coroutine_noexception_exit = """\
    NUITKA_CANNOT_GET_HERE("Return statement must be present");

%(function_cleanup)s
    return NULL;
"""

template_coroutine_return_exit = """\
    function_return_exit:;

    coroutine->m_returned = %(return_value)s;

    return NULL;
"""


from . import TemplateDebugWrapper  # isort:skip

TemplateDebugWrapper.checkDebug(globals())
